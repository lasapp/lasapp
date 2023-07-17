
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
    @assert kind(node) == K"call"
    call = node
    if kind(call[1]) == K"Identifier"
        # func(...)
        return call[1]
    elseif kind(call[1]) == K"."
        # Module.func(...)
        @assert kind(call[1,2]) == K"quote" call
        return call[1,2,1]
    else
        # fallback, create Identifier from sourcetext, e.g. Vector{Int}(...)
        return get_empty_syntax_node(K"Identifier", val=Symbol(sourcetext(call[1])))
    end
end
function get_call_name(node::SyntaxNode)::Symbol
    return get_call_identifier(node).val
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

# Returns all parameter names of a function definition.
function get_parameters_of_function(func::SyntaxNode)::Vector{Symbol}
    parameters = Symbol[]
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
                identifier = get_parameter_identifier(c)
                push!(parameters, identifier.val)
            end
        else
            identifier = get_parameter_identifier(child)
            push!(parameters, identifier.val)
        end
    end
    return parameters
end

# Returns the identifier of an assignment target.
# For indexed assignment, returns container identifier.
function get_identifier(node::SyntaxNode)::SyntaxNode
    if kind(node) == K"Identifier"
        # y
        return node
    elseif kind(node) == K"::"
        # y::...
        @assert kind(node[1]) == K"Identifier"
        return node[1]
    elseif kind(node) == K"ref"
        # y[...]
        @assert kind(node.children[1]) == K"Identifier"
        return node.children[1]
    end
    error("Could not find identifier for node $node.")
end

function get_assignment_identifier(node::SyntaxNode)::SyntaxNode
    @assert JuliaSyntax.is_prec_assignment(node)
    lhs = node[1]
    @assert kind(lhs) != K"tuple"
    return get_identifier(lhs)
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
const EMPTY_SOURCE = SourceFile("")

# Created node does not map to a GreenNode, because we change source code
function get_empty_syntax_node(kind::Kind; source::SourceFile=EMPTY_SOURCE, span::UInt32=UInt32(0), position::Int=0, val::Any=nothing)::SyntaxNode
    SyntaxNode(
        nothing,
        nothing,
        SyntaxData(
            source,
            GreenNode(SyntaxHead(kind, EMPTY_FLAGS), span, ()),
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

# Returns true of a syntax node is an identifier, corresponding to a program variable.
function is_variable_identifier(node::SyntaxNode)::Bool
    if kind(node) == K"Identifier" 
        if !isnothing(node.parent) 
            if kind(node.parent) != K"quote"
                return true
            else
                # Could be symbol :x ~ (quote x) or module identifier Main.x ~ (. Main (quote x))
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