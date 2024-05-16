
function _show_syntax_node_sexpr(io, node::JuliaSyntax.AbstractSyntaxNode, tab="")
    if !JuliaSyntax.haschildren(node)
        if JuliaSyntax.is_error(node)
            println(io, tab, "(", JuliaSyntax.untokenize(JuliaSyntax.head(node)), ")")
        else
            val = node.val
            println(io, tab, val isa Symbol ? string(val) : JuliaSyntax.repr(val))
        end
    else
        println(io, tab, JuliaSyntax.untokenize(JuliaSyntax.head(node)))
        first = true
        for n in children(node)
            _show_syntax_node_sexpr(io, n, tab*"  ")
            first = false
        end
        println(io, tab, ')')
    end
end
function Base.show(io::IO, ::MIME"text/plain", node::JuliaSyntax.AbstractSyntaxNode)
    JuliaSyntax._show_syntax_node_sexpr(io, node)
    # _show_syntax_node_sexpr(io, node)
end
function try_unparse(node::SyntaxNode)
    if kind(node) == K"Identifier" || JuliaSyntax.is_literal(kind(node))
        return string(node.val)
    end
    if kind(node) == K"string"
        return "\"" * join(map(c -> kind(c) == K"String" ? try_unparse(c) : "\$(" * try_unparse(c) * ")", node.children), "") * "\""
    end
    if kind(node) == K"ref"
        return try_unparse(node[1]) * "[" * try_unparse(node[2]) * "]"
    end
    if kind(node) == K"quote" && JuliaSyntax.flags(node) == JuliaSyntax.COLON_QUOTE
        return ":" * try_unparse(node[1])
    end
    if kind(node) == K"tuple"
        return "(" * join(try_unparse.(node.children), ",") * ")"
    end
    if kind(node) == K"call"
        if JuliaSyntax.is_infix_op_call(node)
            return try_unparse(node[1]) * string(node[2].val) * try_unparse(node[3])
        elseif JuliaSyntax.is_postfix_op_call(node)
        else
            return try_unparse(node[1]) * "(" * join(try_unparse.(node.children[2:end]), ",") * ")"
        end
    end
    error("Cannot unparse node of kind $(kind(node))")
end

function get_file_content_as_string(path::String)::String
    filecontent = read(path, String)
    return filecontent
end

# Returns the Identifier SyntaxNode of a function name.
# If function has module prefix, the prefix is omitted.
function get_function_identifier(node::SyntaxNode)::SyntaxNode
    @assert kind(node) == K"function"
    if kind(node[1]) == K"::"
        # typed return value
        call = node[1,1]
    else
        call = node[1]
    end
    @assert kind(call) == K"call"

    if kind(call[1]) == K"Identifier"
        # function func()...
        return call[1]
    else
        # function Module.func() ...
        @assert kind(call[1]) == K"."
        @assert kind(call[1,2]) == K"quote"
        return call[1,2,1]
    end
end
function get_function_name(node::SyntaxNode)::Symbol
    return get_function_identifier(node).val
end

# For a call SyntaxNode, returns the Identifier SyntaxNode of the called function.
# If the function has module prefix, the prefix is omitted.
function get_call_identifier(node::SyntaxNode)::SyntaxNode
    @assert kind(node) == K"call" || kind(node) == K"dotcall"

    call = node

    if JuliaSyntax.is_infix_op_call(call)
        call_name_node = call[2]
    elseif JuliaSyntax.is_postfix_op_call(call)
        call_name_node = call[length(JuliaSyntax.children(call))]
    else
        call_name_node = call[1]
    end

    if kind(call_name_node) == K"Identifier"
        # func(...)
        return call_name_node
    elseif kind(call_name_node) == K"."
        # Module.func(...)
        @assert kind(call_name_node[2]) == K"quote" call
        return call_name_node[2,1]
    else
        # fallback, create Identifier from sourcetext, e.g. Vector{Int}(...)
        return get_empty_syntax_node(K"Identifier", val=Symbol(sourcetext(call_name_node)))
    end
end
function get_call_name(node::SyntaxNode)::Symbol
    return get_call_identifier(node).val
end

function get_call_args(node::SyntaxNode)::Vector{SyntaxNode}
    @assert kind(node) == K"call" || kind(node) == K"dotcall"
    call_args = copy(JuliaSyntax.children(node))

    # remove call name
    if JuliaSyntax.is_infix_op_call(node)
        deleteat!(call_args, 2)
    elseif JuliaSyntax.is_postfix_op_call(node)
        deleteat!(call_args, length(call_args))
    else
        deleteat!(call_args, 1)
    end
    return call_args
end

# For a function parameter, returns the Identifier corresponding to the parameter name.
# func(a, b=1, c::Int, c::Int=1)
function get_parameter_identifier(node::SyntaxNode)::SyntaxNode
    if kind(node) == K"Identifier"
        return node
    end
    if kind(node) == K"="
        # has default value
        return get_parameter_identifier(node.children[1])
    end
    if kind(node) == K"::"
        # typed parameter
        return get_parameter_identifier(node.children[1])
    end
    error("Could not find identifier for node $node")
end

function get_parameter_nodes_of_function(func::SyntaxNode)::Vector{SyntaxNode}
    parameters = SyntaxNode[]
    @assert kind(func) == K"function"
    if kind(func[1]) == K"::"
        call = func[1,1]
        # typed return
    else
        call = func[1]
    end
    @assert kind(call) == K"call"
    for child in call.children[2:end] # 1 is function name
        if kind(child) == K"parameters"
            # named parameters
            for c in child.children
                push!(parameters, c)
            end
        else
            push!(parameters, child)
        end
    end
    return parameters
end

function is_parameter_of_function(node::SyntaxNode)::Bool
    if kind(node.parent) == K"parameters"
        return true
    else
        if kind(node.parent) == K"call"
            call_node = node.parent
            return (
                (kind(call_node.parent) == K"function") ||
                (kind(call_node.parent) == K"::" && kind(call_node.parent.parent) == K"function")
            )
        end
    end
    return false
end

function is_keyword_parameter(node::SyntaxNode)::Bool
    return kind(node.parent) == K"parameters"
end

function get_function_for_parameter(node::SyntaxNode)
    @assert is_parameter_of_function(node)
    current_node = node.parent
    while kind(current_node) != K"function"
        current_node = current_node.parent
    end
    return current_node
end


function is_function_signature(node::SyntaxNode)::Bool
    return (kind(node) == K"call" && kind(node.parent) == K"function") || (kind(node) == K"::" && kind(node.parent) == K"function")
end
function get_function_for_signature_node(node::SyntaxNode)
    @assert is_function_signature(node)
    current_node = node.parent
    while kind(current_node) != K"function"
        current_node = current_node.parent
    end
    return current_node
end


# Returns all parameter names of a function definition.
function get_parameter_names_of_function(func::SyntaxNode)::Vector{Symbol}
    return [get_parameter_identifier(p).val for p in get_parameter_nodes_of_function(func)]
end

# Returns the identifier of an assignment target.
# For indexed assignment, returns container identifier.
function get_identifier_of_assignment_target(node::SyntaxNode)::SyntaxNode
    if kind(node) == K"Identifier"
        # y
        return node
    elseif kind(node) == K"::"
        # y::...
        @assert kind(node[1]) == K"Identifier"
        return node[1]
    elseif kind(node) == K"ref"
        # y[...]
        @assert kind(node.children[1]) == K"Identifier" "Referenced assignment target is no identifier: $node"
        return node.children[1]
    end
    error("Could not find identifier for node $node.")
end

# returns true if get_identifier_of_assignment_target does not error
function is_supported_assignment_target(node::SyntaxNode)::Bool
    if kind(node) == K"Identifier"
        return true
    elseif kind(node) == K"::" && kind(node[1]) == K"Identifier"
        return true
    elseif kind(node) == K"ref" && kind(node.children[1]) == K"Identifier"
        return true
    end
    return false
end

function get_assignment_identifier(node::SyntaxNode)::SyntaxNode
    @assert JuliaSyntax.is_prec_assignment(node)
    lhs = node[1]
    @assert kind(lhs) != K"tuple"
    return get_identifier_of_assignment_target(lhs)
end

function print_stree(io, node::SyntaxNode, tab="")
    if !JuliaSyntax.haschildren(node)
        if JuliaSyntax.is_error(node)
            print(io, tab, "(", JuliaSyntax.untokenize(JuliaSyntax.head(node)), ")")
        else
            val = node.val
            print(io, tab, val isa Symbol ? string(val) : repr(val))
        end
    else
        print(io, tab, "(", JuliaSyntax.untokenize(JuliaSyntax.head(node)), "\n")
        for n in children(node)
            print_stree(io, n, tab*"|  ")
            print(io, "\n")
        end
        print(io, tab, ")")
    end
end

# SyntaxNodes can be uniquely identified by their range in the UTF8 source code.
# This function returns the node of a tree for a given range.
function get_subnode_for_range(tree::SyntaxNode, r::UnitRange{Int})::SyntaxNode
    node = tree
    node_range = range(node)
    if node_range == r
        return node
    end

    for child in children(tree)
        child_range = range(child)
        if first(child_range) <= first(r)  && last(r) <= last(child_range)
            return get_subnode_for_range(child, r)
        end
    end

    error("Node not found.")
end


import JuliaSyntax: SourceFile, Kind
const EMPTY_SOURCE = SourceFile(" ")

# Created node does not map to a GreenNode, because we change source code
function get_empty_syntax_node(kind::Kind; flags::JuliaSyntax.RawFlags=EMPTY_FLAGS, source::SourceFile=EMPTY_SOURCE, span::UInt32=UInt32(0), position::Int=1, val::Any=nothing)::SyntaxNode
    SyntaxNode(
        nothing,
        nothing,
        SyntaxData(
            source,
            GreenNode(SyntaxHead(kind, flags), span, ()),
            position,
            val
        )
    )
end

# We can check if one node is a descendant of another,
# by traversing up the parent
function isdescendant(parent::SyntaxNode, node::SyntaxNode)
    if parent == node
        return true
    end
    while !isnothing(node.parent)
        node = node.parent
        if parent == node
            return true
        end
    end
    return false
end

# Returns true if a syntax node is an identifier, corresponding to a program variable.
# x or Module.x
function is_variable_identifier(node::SyntaxNode)::Bool
    if kind(node) == K"Identifier" 
        if !isnothing(node.parent) 
            if kind(node.parent) != K"quote"
                return true
            else
                # Could be symbol :x ~ (quote x) or module identifier Main.x ~ (. Main (quote x))
                # return true if identifier is x or Main.x
                return !isnothing(node.parent.parent) && kind(node.parent.parent) == K"."
            end
        else
            return true
        end
    else
        return false
    end
end

# Returns true if the two nodes are located in mutually exclusive if branches
# i.e. if node is in descendant of if branch and other of else branch, and vice versa
function is_in_different_branch(node::SyntaxNode, other::SyntaxNode)::Bool
    current_parent = node.parent
    while !isnothing(current_parent)
        if kind(current_parent) == K"if" || kind(current_parent) == K"elseif"
            if length(children(current_parent)) == 3
                # two branches
                branch_1 = current_parent[2]
                branch_2 = current_parent[3]
                if isdescendant(branch_1, node) && isdescendant(branch_2, other)
                    return true
                end
                if isdescendant(branch_1, other) && isdescendant(branch_2, node)
                    return true
                end
            end
        end
        current_parent = current_parent.parent
    end
    return false
end