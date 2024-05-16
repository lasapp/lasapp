
# Abstract Interpretation
# Cousot, Patrick; Cousot, Radhia (1976). "Static determination of dynamic properties of programs"

# supports following elementary functions:
# +, *, -, /
# exp, log, sqrt, ^{float}, min, max

struct Interval
    low::Real
    high::Real
end
Base.:(==)(x::Interval, y::Interval) = x.low == y.low && x.high == y.high

function Interval(x::Real)
    return Interval(x, x)
end

Base.:∪(x::Interval, y::Interval) = Interval(min(x.low, y.low), max(x.high, y.high)) # over-approximate if disjoint

Base.:+(x::Interval, y::Interval) = Interval(x.low + y.low, x.high + y.high)
Base.:-(x::Interval, y::Interval) = Interval(x.low - y.high, x.high - y.low)
function Base.:*(x::Interval, y::Interval)
    E = [x.low * y.low, x.low * y.high, x.high * y.low, x.high * y.high]
    E = E[.!isnan.(E)]
    return Interval(minimum(E), maximum(E))
end
function Base.:/(x::Interval, y::Interval)
    if y.low != 0 && y.high != 0
        y = Interval(1/y.high, 1/y.low)
    elseif y.low != 0
        y = Interval(-Inf, 1/y.low)
    elseif y.high != 0
        y = Interval(1/y.high, Inf)
    else
        error("Division by zero.")
    end
    return x * y
end

Base.exp(x::Interval) = Interval(exp(x.low), exp(x.high))
Base.log(x::Interval) = Interval(log(x.low), log(x.high))
Base.sqrt(x::Interval) = Interval(sqrt(x.low), sqrt(x.high))
function Base.:^(x::Interval, n::Real)
    if isodd(n)
        return Interval(x.low^n, x.high^n)
    else
        if x.low >= 0
            return Interval(x.low^n, x.high^n)
        else
            return Interval(0., x.high^n)
        end
    end
end
function Base.:^(x::Interval, n::Interval)
    if n.low == n.high
        return x^n.low
    else
        # fallback
        return Interval(0., Inf)
    end
end
Base.min(x::Interval, y::Interval) = Interval(min(x.low, y.low), min(x.high, y.high))
Base.max(x::Interval, y::Interval) = Interval(max(x.low, y.low), max(x.high, y.high))

logistic(x::Interval) = Interval(0., 1.)

Base.clamp(x::Interval, a::Interval, b::Interval) = max(a, min(x, b))

const SYMBOL_TO_FUNC = Dict(
    :+ => +,
    :* => *,
    :- => -,
    :/ => /,
    :exp => exp,
    :log => log,
    :sqrt => sqrt,
    :^ => ^,
    :min => min,
    :max => max,
    :logistic => logistic,
    :clamp => clamp,
)


mutable struct StaticIntervalEvaluator <: NodeVisitor
    valuation::Dict{Symbol, Interval}
end

function visit(visitor::StaticIntervalEvaluator, node::SyntaxNode)::Interval
    @assert kind(node) != K"="
    if kind(node) == K"Integer" || kind(node) == K"Float"
        # Build intervals from constants.
        return Interval(node.val)
    end

    if kind(node) == K"Identifier"
        if !haskey(visitor.valuation, node.val)
            if node.val == :I
                return Interval(0, 1) # Identity matrix form LinearAlgebra package
            end
            # no valuation for identifier found -> overapproximate as arbitary real number
            @warn "Unknown symbol $(node.val) encountered."
            return Interval(-Inf, Inf)
        end
        # return current interval valuation for identifier
        return visitor.valuation[node.val]
    end

    if kind(node) == K"ref"
        # array elements are all masked as one interval
        return visit(visitor, node[1])
    end

    if kind(node) == K"call" || kind(node) == K"dotcall"
        # map call to interval arithmetic operation

        # get call name node and remove from children
        children = copy(node.children)
        if JuliaSyntax.is_infix_op_call(node)
            call_name_node = children[2]
            deleteat!(children, 2)
        elseif JuliaSyntax.is_postfix_op_call(node)
            call_name_node = children[end]
            deleteat!(children, length(children))
        else
            call_name_node = children[1]
            deleteat!(children, 1)
        end

        # map call name node to function name (Symbol)
        if kind(call_name_node) in (K"+", K"-", K"*", K"/", K"^")
            # special operations
            fname = Symbol(string(kind(call_name_node)))
        elseif kind(call_name_node) == K"Identifier"
            # arbitary identifier (e.g. min, max, exp, ...)
            fname = call_name_node.val
        else
            # fallback
            fname = sourcetext(call_name_node)
        end

        if haskey(visitor.valuation, fname)
            # function can also be masked
            return visitor.valuation[fname]
        end

        # check that we can map to function
        if !haskey(SYMBOL_TO_FUNC, fname)
            # if not overapproximate as arbitary real number
            @warn "Unsupported function $fname."
            return Interval(-Inf, Inf)
        end

        # evaluate interval operation
        func = SYMBOL_TO_FUNC[fname]
        args = [visit(visitor, child) for child in children]
        return func(args...)
    end

    if kind(node) == K"parens"
        # handle parenthesis
        return visit(visitor, node[1])
    end

    if kind(node) == K"macrocall" && node[1].val == Symbol("@.")
        return visit(visitor, node[2])
    end

    if kind(node) == K"vect" && length(node.children) > 0
        # arrays are approximated by having one interval for *all* elements
        args = [visit(visitor, child) for child in node.children]
        return reduce(∪, args)
    end

    error("Encountered unsupported node $(node) with kind $(kind(node))")
end

function _static_interval_eval(cfg_progr_repr::CFGRepresentation, node_to_evaluate::SyntaxNode, valuation::Dict{Symbol, Interval})
    identifiers = get_identifiers_read_in_syntaxnode(cfg_progr_repr.scoped_tree, node_to_evaluate)
    _, cfgnode = get_cfgnode_for_syntaxnode(cfg_progr_repr, node_to_evaluate)
    
    # update valuation by trying to estimate interval for each identifier read in syntaxnode
    for identifier in identifiers
        identifier_name = identifier.val
        if !haskey(valuation, identifier_name)

            rds = get_RDs(cfg_progr_repr.scoped_tree, cfgnode, identifier)
            if length(rds) == 0
                # no reaching definition found
            else # length(rds) > 0
                intervals = Interval[]
                for rd in rds
                    if rd.type == ASSIGN_NODE
                        @assert kind(rd.syntaxnode) == K"=" "Unsupported assign node $(rd.syntaxnode)"
                        rhs = rd.syntaxnode[2]
                        push!(intervals, _static_interval_eval(cfg_progr_repr, rhs, valuation))
                    else # else rd.type == FUNCARG_NODE, we do not evaluate
                        push!(intervals, Interval(-Inf, Inf))
                    end
                end
                valuation[identifier_name] = reduce(∪, intervals)
            end
        end
    end
    return visit(StaticIntervalEvaluator(valuation), node_to_evaluate)
end

# Assumptions: SSA and only elementary functions -> all definitions in same scope
# Only exception: one assignment per if branch
# Elements of array all have same interval
function static_interval_eval(cfg_progr_repr::CFGRepresentation, node_to_evaluate::SyntaxNode, valuation::Dict{Symbol, Interval})::Interval
    try
        return _static_interval_eval(cfg_progr_repr, node_to_evaluate, valuation)
    catch e
        if e isa StackOverflowError
            # we could catch recusion already in _static_interval_eval, but this is simpler
            return Interval(-Inf, Inf)
        else
            rethrow(e)
        end
    end
end