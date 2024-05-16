
abstract type SymbolicExpression end

struct Operation <: SymbolicExpression
    op::String
    args::Vector{SymbolicExpression}
    function Operation(op::String, args...)
        return new(op, SymbolicExpression[arg for arg in args])
    end
end
function Base.show(io::IO, op::Operation)
    if length(op.args) == 1
        s = "$(op.op)$(op.args[1])"
    elseif length(op.args) == 2
        s = "($(op.args[1]) $(op.op) $(op.args[2]))"
    else
        s = join([sprint(show, arg) for arg in op.args], ", ")
        s = "$(op.op)($s)"
    end
    print(io, s)
end
function Base.:(==)(self::Operation, other::SymbolicExpression)::Bool
    if !(other isa Operation)
        return false
    end
    return (self.op == other.op && 
            length(self.args) == length(other.args) && 
            all(self.args .== other.args)
            )
end

function Not(sexp::SymbolicExpression)
    if sexp isa Operation
        if sexp.op == "!"
            return sexp.args[1]
        end
    end
    return Operation("!", sexp)
end

struct TypedSymbol <: SymbolicExpression
    name::String
    type::String
    function TypedSymbol(name::String, type::String="Real")
        return new(name, type)
    end
end
# Type(Name)
function TypedSymbol_from_str(s::String)::TypedSymbol
    type, name = split(s[1:end-1], "(", limit=2)
    return TypedSymbol(string(name), string(type))
end
function Base.show(io::IO, symbol::TypedSymbol)
    print(io, symbol.name)
end
function Base.:(==)(self::TypedSymbol, other::SymbolicExpression)::Bool
    if !(other isa TypedSymbol)
        return false
    end
    return self.name == other.name && self.type == other.type
end
    
struct Constant <: SymbolicExpression
    value::Any
end
function Base.show(io::IO, constant::Constant)
    print(io, constant.value)
end
function Base.:(==)(self::Constant, other::SymbolicExpression)::Bool
    if !(other isa Constant)
        return false
    end
    return self.value == other.value
end

function path_condition_to_str(expr::Constant)
    return "Constant($(expr.value))"
end
function path_condition_to_str(expr::TypedSymbol)
    return "$(expr.type)($(expr.name))"
end
function path_condition_to_str(expr::Operation)
    s = join(path_condition_to_str.(expr.args), ",")
    return "$(expr.op)($s)"
end

const _SYM_AST_NODE_TO_OP = Dict(
    K"+" => "+",
    K"-" => "-",
    K"*" => "*",
    K"/" => "/",
    K"^" => "^",
    K"&&" => "&",
    K"||" => "|",
    K"!" => "!",
    K"==" => "==",
    K"!=" => "!=",
    K">" => ">",
    K">=" => ">=",
    K"<" => "<",
    K"<=" => "<="
)

mutable struct SymbolicEvaluator <: NodeVisitor
    result::Dict{SyntaxNode,Vector{Vector{SymbolicExpression}}} # keys are all nodes for which we want pathconditions
    root_node::SyntaxNode
    node_to_symbol::Dict{Union{Symbol,SyntaxNode}, TypedSymbol} # nodes we want to mask with symbol
    name_to_symbol::Dict{String, SymbolicExpression} # dict to store symbolic evaluations of assignments
    path_condition::Vector{SymbolicExpression} # keeps track of all branching conditions
    path::Dict{SyntaxNode, Bool} # keeps track of branching choice
    function SymbolicEvaluator(result, root_node, node_to_symbol)
        return new(result, root_node, node_to_symbol, Dict(), [], Dict())
    end
end

function visit(visitor::SymbolicEvaluator, node::SyntaxNode)
    if haskey(visitor.result, node)
        # encounterd a node for which we want to evaluate the path_condition
        push!(visitor.result[node], visitor.path_condition)
    end
    if haskey(visitor.node_to_symbol, node)
        # encounterd a node which we want to mask with symbol
        if kind(node) == K"="
            # hack for now node is an assignment x = <masked>
            # we map target x to mask symbol in name_to_symbol
            @assert kind(node[1]) == K"Identifier"
            name = String(node[1].val)
            @assert !haskey(visitor.node_to_symbol, name) # only one assignment per name
            visitor.name_to_symbol[name] = visitor.node_to_symbol[node]
        end
        # return mask symbol
        return visitor.node_to_symbol[node]
    end

    if kind(node) == K"function"
        args = node[1].children[2:end]
        body = node[2]
        # mask parameters as symbols
        # does not support keyword arguments for now
        for arg in args
            if kind(arg) == K"Identifier"
                # untyped parameter
                sym = TypedSymbol(String(arg.val), "Real")
            elseif kind(arg) == K"::"
                # typed parameter
                @assert kind(arg[1]) == K"Identifier"
                type = arg[2].val
                @assert type in (:Bool, :Int, :Real)
                sym = TypedSymbol(String(arg[1].val), String(type))
            else
                error("Unsupported argument $arg")
            end
            # add to name_to_symbol
            visitor.name_to_symbol[sym.name] = sym
        end
        # traverse function body
        generic_visit(visitor, body)

    elseif kind(node) == K"if"
        test = visit(visitor, node[1])

        if haskey(visitor.path, node)
            # we have already a choice for this if statement
            choice = visitor.path[node]

            res = nothing
            # follow the choice
            if choice
                # add if condition to path condition
                push!(visitor.path_condition, test)
                # evaluate then branch
                res = visit(visitor, node[2])
            else
                # add negated if condition to path condition
                push!(visitor.path_condition, Not(test))
                # evaluate else branch if present
                if length(children(node)) > 2
                    res = visit(visitor, node[3])
                end
            end

            # return the symbolic evaluation
            return res
        end

        # we do not have a choice for this if statement

        # fork the evaluation
        forkpath = copy(visitor.path)
        forkpath[node] = false # fork evaluator will explore else branch
        fork = SymbolicEvaluator(
            visitor.result,
            visitor.root_node,
            visitor.node_to_symbol
        )
        fork.path = forkpath

        visitor.path[node] = true # this evaluator will explore then branch

        # start fork from root node
        visit(fork, fork.root_node)

        # continue visiting if statement by following then branch
        visit(visitor, node)

    elseif kind(node) == K"="
        @assert kind(node[1]) == K"Identifier"
        name = String(node[1].val)
        @assert !haskey(visitor.node_to_symbol, name) # only one assignment per name

        # symbolically evaluate right hand side
        value = visit(visitor, node[2])

        # map name to evaluation
        visitor.name_to_symbol[name] = value

    elseif kind(node) in (K"Integer", K"Float", K"true", K"false")
        # simply evaluates to constant
        return Constant(node.val)

    elseif kind(node) == K"Identifier"
        # identifier has to be evaluated and stored before
        name = String(node.val)
        @assert haskey(visitor.name_to_symbol, name) (visitor.name_to_symbol, name)
        # return symbolic evaluation for this identifier
        return visitor.name_to_symbol[name]
    
    elseif kind(node) == K"block"
        # iterate over each statement in block, return last result
        res = nothing
        for child in children(node)
            res = visit(visitor, child)
        end
        return res

    elseif kind(node) == K"call" || kind(node) == K"dotcall"
        # map function call to symbolic operation
        if JuliaSyntax.is_prefix_op_call(node)
            # !X -> Operation("!", X)
            op = _SYM_AST_NODE_TO_OP[kind(node[1])]
            return Operation(op, visit(visitor, node[2]))
        elseif JuliaSyntax.is_infix_op_call(node)
            # X + Y -> Operation("+", X, Y)
            op = _SYM_AST_NODE_TO_OP[kind(node[2])]
            return Operation(op, visit(visitor, node[1]), visit(visitor, node[3]))
        else
            # f(X,Y) -> Operation("f", X, Y)
            name = get_call_name(node)
            values = [visit(visitor, arg) for arg in node.children[2:end]]
            return Operation(String(name), values...)
        end
    elseif kind(node) in (K"&&", K"||")
        # X && Y -> Operation("&", X, Y)
        # X || Y -> Operation("|", X, Y)
        op = _SYM_AST_NODE_TO_OP[kind(node)]
        return Operation(op, visit(visitor, node[1]), visit(visitor, node[2]))
    else
        error("Unsupported node $(kind(node))")
    end
end

# We will collect multiple path conditions that can be combined by following rule
# (A and B and ...) or (!A and B and ...) => B and ...
function combine_paths(paths::Vector{Vector{SymbolicExpression}})::SymbolicExpression
    new_paths = []
    for path_condition in paths
        # we try to find a second path in new_paths which we can use to combine
        # we keep trying until there is no path in new_paths to combine with
        pc = deepcopy(path_condition)
        while true
            did_change = false
            for i in 1:length(new_paths)
                other_pc = new_paths[i]
                if length(other_pc) != length(pc)
                    continue
                end
                # Not(A) and A have to be exactly at same index in path condition
                # correspond to same if statement
                matching = 0
                index = nothing
                for j in 1:length(pc)
                    if pc[j] == Not(other_pc[j])
                        index = j # are opposites at index
                    end
                    if pc[j] == other_pc[j]
                        matching += 1 # match in all other places
                    end
                end

                if matching == length(pc)-1 && !isnothing(index)
                    # found a matching path 
                    deleteat!(new_paths, i) # remove other_pc
                    deleteat!(pc, index) # (A and B and ...) or (!A and B and ...) => B and ...
                    did_change = true
                    break
                end
            end

            if !did_change
                # no path to combine with -> stop
                break
            end
        end
        
        # we have new (simplified) path
        push!(new_paths, pc)
    end

    # empty path corresponds to Constant(true) path_condition
    new_paths = [path for path in new_paths if length(path) > 0]

    if length(new_paths) == 0
        # node appears in every program path
        return Constant(true)
    end
    if length(new_paths) == 1
        # node appears in exactly one program path
        path = new_paths[1]
        # reduce multiple if conditions with and operation
        return length(path) == 1 ? path[1] : Operation("&", path...) 
    end
    
    # reduce multiple program paths with or operation
    return Operation("|", [length(path) == 1 ? path[1] : Operation("&", path...) for path in new_paths]...)
end

function get_path_condition_for_nodes(func::SyntaxNode, nodes::Vector{SyntaxNode}, node_to_symbol::Dict{SyntaxNode, TypedSymbol})
    if kind(func) == K"macrocall"
        func = func[2]
    end
    @assert kind(func) == K"function"

    evaluator = SymbolicEvaluator(Dict(node=>[] for node in nodes), func, node_to_symbol)
    visit(evaluator, func)
    result = Dict(node=>combine_paths(paths) for (node, paths) in evaluator.result)

    return result
end

