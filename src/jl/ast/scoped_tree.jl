

# We introduce scope for all assignments and function definitions.

# Assumptions:
# - assigments and function definitions do not define the same symbol
# - functions are pure: no side effects + same output for same arguments (no closures)
#   function body does not have free variabels except function parameters
# - keywords module, try, catch, finally, do, macro, let, local, global, outer, generators are not supported
# - no new scopes and assignments in call parameters
#   e.g. f(begin x=1; x+1 end, (function a() 1 end)()) not allowed
# - loop variable is not used in loop range
#   i = 1
#   for i in i:(i+10)
#   end
#   not allowed

abstract type NameDefinition end

struct Assignment <: NameDefinition
    node::SyntaxNode
    identifier::SyntaxNode
    name::Symbol
    function Assignment(node::SyntaxNode, identifier::SyntaxNode)
        @assert kind(identifier) == K"Identifier"
        name = identifier.val
        return new(node, identifier, name)
    end
end

function Assignment(node::SyntaxNode)
    @assert JuliaSyntax.is_prec_assignment(node)
    identifier = get_assignment_identifier(node)
    return Assignment(node, identifier)
end

function Base.show(io::IO, def::Assignment)
    print(io, def.name, ": ", def.node)
end

struct FunctionDefinition <: NameDefinition
    node::SyntaxNode
    identifier::SyntaxNode
    name::Symbol

    function FunctionDefinition(node::SyntaxNode)
        @assert kind(node) == K"function"
        identifier = get_function_identifier(node)
        name = get_function_name(node)
        return new(node, identifier, name)
    end
end

struct Scope
    id::Int
    kind::Symbol # global, (local) soft, (local) hard
    parent::Union{Nothing, Scope}
    children::Vector{Scope}
    node::SyntaxNode
    definitions::Vector{Assignment} # all assignments in scope
    functions::Vector{FunctionDefinition} # all function definitions in scope
    symbols::Set{Symbol} # all symbols that are defined in scope
    function Scope(id::Int, kind::Symbol, parent::Union{Nothing, Scope}, node::SyntaxNode)
        @assert kind == :global || kind == :soft || kind == :hard
        this = new(id, kind, parent, Scope[], node, Assignment[], FunctionDefinition[], Set{Symbol}())
        if !isnothing(parent)
            push!(parent.children, this)
        end
        return this
    end   
end

Base.isequal(x::Scope, y::Scope) = x.id == y.id


function Base.show(io::IO, scope::Scope)
    print(io, "Scope(", scope.id, ", ", scope.kind, ", ", length(scope.definitions), " definitions, ", length(scope.functions), " functions, ", length(scope.children), " children)")
end

function print_scope_tree(scope::Scope, tab="")
    println(tab, "Scope ", scope)
    # println(scope.node)
    # if !isempty(scope.symbols)
    println(tab, " Symbols: ", scope.symbols)
    # end
    for def in scope.definitions
        print(tab, " ", def)
        println()
    end
    if !isempty(scope.children)
        println(tab, " Children: ")
    end
    for childscope in scope.children
        print_scope_tree(childscope, tab*" | ")
    end
end


# Visitor to traverse syntac tree and collect all scopes,
# assigments, and function definitions

mutable struct ScopeCollector <: NodeVisitor
    number_of_scopes::Int
    scope_stack::Vector{Scope}
    definitions::Vector{Assignment}
    functions::Vector{FunctionDefinition}
    function ScopeCollector(topscope=nothing)
        scope_stack = !isnothing(topscope) ? Scope[topscope] : Scope[]
        return new(length(scope_stack), scope_stack, Assignment[], FunctionDefinition[])
    end
end


function visit(visitor::ScopeCollector, node::SyntaxNode)::Scope
    node_kind = kind(node)

    # scopes
    is_scope_node = false
    if node_kind == K"toplevel"
        # global scope
        @assert isempty(visitor.scope_stack)
        visitor.number_of_scopes += 1
        scope = Scope(visitor.number_of_scopes, :global, nothing, node)
        is_scope_node = true

    elseif node_kind == K"function"
        # hard scope
        # function parameters and let assignments are always new local
        visitor.number_of_scopes += 1
        scope = Scope(visitor.number_of_scopes, :hard, visitor.scope_stack[end], node)
        is_scope_node = true
        func_def = FunctionDefinition(node)
        # add function definition to encompassing (parent) scope
        push!(visitor.scope_stack[end].functions, func_def)
        # add function definition to all collected functions
        push!(visitor.functions, func_def)

    elseif node_kind == K"call"
        # no new scopes or assignments allowed
        return visitor.scope_stack[end]

    # elseif node_kind == K"let"
    #     visitor.number_of_scopes += 1
    #     scope = Scope(visitor.number_of_scopes, :hard, visitor.scope_stack[end], node)
    #     is_scope_node = true

    elseif node_kind == K"for" || node_kind == K"while" || node_kind == K"struct"
        # soft scope
        visitor.number_of_scopes += 1
        scope = Scope(visitor.number_of_scopes, :soft, visitor.scope_stack[end], node)
        is_scope_node = true

    elseif node_kind == K"generator"
        visitor.number_of_scopes += 1
        scope = Scope(visitor.number_of_scopes, :soft, visitor.scope_stack[end], node)
        is_scope_node = true

    elseif (node_kind == K"module" ||
        node_kind == K"try" || node_kind == K"catch" || node_kind == K"finally" ||
        node_kind == K"do" || node_kind == K"macro" || node_kind == K"let")#||
        # node_kind == K"comprehension" || node_kind == K"generator")
        error("Scope block $node_kind not supported.")

    elseif node_kind == K"local" || node_kind == K"global" || node_kind == K"outer" || node_kind == K"->"
        error("Keyword $node_kind not supported.")
    end

    # assignments
    if JuliaSyntax.is_prec_assignment(node_kind)
        lhs = node[1]
        if kind(lhs) == K"tuple"
            for child in JuliaSyntax.children(lhs)
                assignment = Assignment(node, child)
                # add assignment to current scope
                push!(visitor.scope_stack[end].definitions, assignment)
                # add assignment to all collected assigments
                push!(visitor.definitions, assignment)
            end
        else
            assignment = Assignment(node)
            # add assignment to current scope
            push!(visitor.scope_stack[end].definitions, assignment)
            # add assignment to all collected assigments
            push!(visitor.definitions, assignment)
        end
    end

    if is_scope_node
        # add scope to scope stack
        push!(visitor.scope_stack, scope)
        # visit all children of scope
        generic_visit(visitor, node)
        # remove scope from stack and return
        return pop!(visitor.scope_stack)
    else
        generic_visit(visitor, node)
        return visitor.scope_stack[end]
    end
end

# Get all parent scopes, including scope passed as argument
function get_scope_closure(scope::Scope)::Vector{Scope}
    if isnothing(scope.parent)
        return Scope[scope]
    else
        return push!(get_scope_closure(scope.parent), scope)
    end
end


function islocalvariable(scope::Scope, symbol::Symbol)::Bool
    if scope.kind == :global
        return false
    end
    if symbol in scope.symbols
        return true
    else
        return islocalvariable(scope.parent, symbol)
    end
end

function isglobalvariable(scope::Scope, symbol::Symbol)::Bool
    if scope.kind == :global
        return symbol in scope.symbols
    else
        # traverse up parents until global scope
        return isglobalvariable(scope.parent, symbol)
    end
end

# Collects all symbols that are defined in scope.
function compute_scope_symbols(scope::Scope)
    scope_kind = kind(scope.node)

    if scope_kind == K"function"
        # parameters of function are always local to function scope
        for param in get_parameters_of_function(scope.node)
            push!(scope.symbols, param)
        end
    # elseif scope_kind == K"let"
    #     # add assignments to symbols here
    elseif scope_kind == K"for"
        # loop parameters are always local to for scope
        loop_vars = scope.node[1,1]
        for var in visit(IdentifierSymbolFinder(), loop_vars)
            push!(scope.symbols, var)
        end
    elseif scope_kind == K"generator"
        loop_vars = scope.node[2]
        for var in visit(IdentifierSymbolFinder(), loop_vars)
            push!(scope.symbols, var)
        end
    elseif scope_kind == K"while" || scope_kind == K"struct"
        # nothing todo
    end

    if scope.kind == :global
        # each toplevel assignment is defines a symbol
        for def in scope.definitions
            push!(scope.symbols, def.name)
        end
        # each toplevel function definition defines a symbol
        function_symbols = Symbol[func.name for func in scope.functions]

        # assigments and function definitions should not define the same symbol
        conflicts = function_symbols ∩ scope.symbols
        @assert isempty(conflicts) "Function name conflicts with global variable $conflicts."
        for sym in function_symbols
            push!(scope.symbols, sym)
        end
    else
        # https://docs.julialang.org/en/v1/manual/variables-and-scoping/#local-scope
        for def in scope.definitions
            # `x` = <value> occurs in a local scope
            if !islocalvariable(scope, def.name)
                # `x` is not already a local variable

                if any(s.kind == :hard for s in get_scope_closure(scope))
                    # assignment occurs inside of any hard scope construct
                    # -> current scope defines variable
                    push!(scope.symbols, def.name)
                else
                    # all of the scope constructs containing the assignment are soft scopes
                    # if global `x` is defined, the assignment is considered ambiguous
                    # @assert !isglobalvariable(scope, def.name) def.name
                    if isglobalvariable(scope, def.name)
                        # assume interactive context
                        @warn "$(def.name) is defined globally and assigned in soft scope. This is ambiguous. Assuming interactive context."
                    else
                        # global `x` is undefined, a new local named x is created in the scope of the assignment
                        push!(scope.symbols, def.name)
                    end
                end
            else
                # `x` is already a local variable
                if scope_kind == K"function" && !(def.name in scope.symbols)
                    # if there is a local variable it has to be defined in function body
                    # TODO: maybe remove assumption
                    error("Function: $(get_function_name(scope.node)) is not pure. Undefined symbol in $def.")
                end
            end
        end
        
        # functions can be defined in any order
        # e.g.
        # x = func()
        # function func() 1 end
        # is ok (before 1.9?)
        function_symbols = Symbol[func.name for func in scope.functions]

        # assigments and function definitions should not define the same symbol
        conflicts = function_symbols ∩ scope.symbols
        @assert isempty(conflicts) "Function name conflicts with local variable $conflicts."
        for sym in function_symbols
            push!(scope.symbols, sym)
        end
    end

    # compute symbols of parent scope before children scopes
    for child in scope.children
        compute_scope_symbols(child)
    end
end


# after compute_scope_symbols, we can collect all symbols by traversing scope tree
function get_all_user_defined_variables(scope::Scope)
    symbols = scope.symbols
    for child in scope.children
        symbols = symbols ∪ get_all_user_defined_variables(child)
    end
    return symbols
end

# returns all variables that are defined in scope,
# e.g. all defined symbols in scope and in all of its parents
get_all_variables_in_scope(::Nothing) = Set{Symbol}()
function get_all_variables_in_scope(scope::Scope)
    symbols = scope.symbols ∪ get_all_variables_in_scope(scope.parent)
    return symbols
end

# returns the innermost scope that contains node
# e.g. we can start with global scope and find the innermost scope
function find_innermost_scope_for_node(scope::Scope, node::SyntaxNode)
    # node should be descendant of scope
    @assert isdescendant(scope.node, node) (scope, node)
    # node should be descendent of scope direclty or at most one child, this check is redundant
    @assert sum(isdescendant(child_scope.node, node) for child_scope in scope.children; init=0) <= 1

    for child_scope in scope.children
        if isdescendant(child_scope.node, node) && child_scope.node != node
            # child scope contains node, therefore child scope is more inner than current scope
            # we have to check if child_scope.node != node, because functions define hard scopes
            # and are its own descendants. But innermost scope of function definition should be
            # the scope in which the function is definded.
            return find_innermost_scope_for_node(child_scope, node)
        end
    end

    if kind(scope.node) == K"function" && node == get_function_identifier(scope.node)
        # identifier is function name -> use scope that function is defined in
        # a function should not be its own innermost scope
        scope = scope.parent
    end

    # node is not descendant of any children, therefore current scope is innermost scope
    return scope
end


# Now we can map every identifier to its defining scope.

mutable struct Identifier2Scope <: NodeVisitor
    d::Dict{SyntaxNode, Scope}
    all_user_symbols::Set{Symbol} # all user defined symbols
    topscope::Scope
    function Identifier2Scope(all_user_symbols::Set{Symbol}, topscope::Scope)
        return new(Dict{SyntaxNode, Scope}(), all_user_symbols, topscope)
    end
end

function visit(visitor::Identifier2Scope, node::SyntaxNode)
    if is_variable_identifier(node)
        name = node.val
        if name in visitor.all_user_symbols
            # symbol was defined by user

            scope = find_innermost_scope_for_node(visitor.topscope, node)
            # println("find_innermost_scope_for_node: ", node, " -> ", scope)

            # from innermost scope traverse up the scope tree to find scope that defined the symbol
            while !(name in scope.symbols)
                scope = scope.parent # at very last global scope should have defined the variable
            end

            visitor.d[node] = scope
        end
    end
    generic_visit(visitor, node)
end

# At last: define the ScopedTree

struct ScopedTree
    root_node::SyntaxNode
    syntaxtree::SyntaxTree
    topscope::Scope
    node_to_scope::Dict{SyntaxNode, Scope} # Identifier -> Scope (Not FunctionDefinition)
    all_definitions::Vector{Assignment}
    all_functions::Vector{FunctionDefinition}
    all_user_symbols::Set{Symbol}
end


function get_scoped_tree(syntaxtree::SyntaxTree)
    root_node = syntaxtree.root_node
    globalscope = kind(root_node) == K"toplevel" ? nothing : Scope(0, :global, nothing, root_node)
    scope_collector = ScopeCollector(globalscope)
    
    # Compute scope tree.
    topscope = visit(scope_collector, root_node)
    # println("topscope: ", topscope)


    # For each scope, collect all symbols that are defined in scope.
    compute_scope_symbols(topscope)
    # print_scope_tree(topscope)
    
    # Get all user defined symbols.
    all_user_symbols = get_all_user_defined_variables(topscope)
    # println("all_user_symbols: ", all_user_symbols)

    # Map every identifier to its defining scope.
    identifier2Scope = Identifier2Scope(all_user_symbols, topscope)
    visit(identifier2Scope, root_node)
    # println("identifier2Scope:")
    # for (k,v) in identifier2Scope.d
    #     println(k, "->", v)
    # end

    return ScopedTree(
        root_node,
        syntaxtree,
        topscope, 
        identifier2Scope.d,
        scope_collector.definitions,
        scope_collector.functions,
        all_user_symbols
    )
end


# function range_from_id(id::String)::UnitRange{Int}
#     a, b = split(id[6:end], "_")
#     a = parse(Int, a)
#     b = parse(Int, b)
#     return a:b
# end

# function id_from_range(r::UnitRange{Int})::String
#     a = first(r)
#     b = last(r)
#     return "node_$(a)_$(b)"
# end

# function get_node_for_id(scoped_tree::ScopedTree, id::String)
#     return get_subnode_for_range(scoped_tree.root_node, range_from_id(id))
# end

function get_node_for_id(scoped_tree::ScopedTree, id::String)::SyntaxNode
    return scoped_tree.syntaxtree.id_to_node[id]
end