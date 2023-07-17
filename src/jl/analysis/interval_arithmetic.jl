
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
    @assert n.low == n.high
    return x^n.low
end
Base.min(x::Interval, y::Interval) = Interval(min(x.low, y.low), min(x.high, y.high))
Base.max(x::Interval, y::Interval) = Interval(max(x.low, y.low), max(x.high, y.high))

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

    error("Encountered unsupported node $(node) with kind $(kind(node))")
end

# Assumptions: SSA and only elementary functions -> all definitions in same scope
# Only exception: one assignment per if branch
# Elements of array all have same interval
function static_interval_eval(scoped_tree::ScopedTree, node_to_evaluate::SyntaxNode, valuation::Dict{Symbol, Interval})::Interval
    # get all data dependencies by recursively calling and traversing data_deps_for_node
    # should be only assingments
    data_deps = Set{Assignment}()
    nodes = [node_to_evaluate]
    while !isempty(nodes)
        node = popfirst!(nodes)
        for dep in data_deps_for_node(scoped_tree, node)
            if !(dep in data_deps)
                if !haskey(valuation, dep.name) # otherwise already abstracted away
                    push!(data_deps, dep)
                    push!(nodes, dep.node)
                end
            end
        end
    end
    # list of assignments in sequential order
    data_deps = sort(collect(data_deps), lt=(x,y) -> JuliaSyntax.first_byte(x.node) < JuliaSyntax.first_byte(y.node))
    # println(data_deps)
    
    # statically evaluate in sequential order
    tmp_valuation = Dict{Symbol, Interval}()
    evaluator = StaticIntervalEvaluator(valuation)
    for (i,dep) in enumerate(data_deps)
        @assert kind(dep.node) == K"=" # only support assignments

        rhs = dep.node[2]
        res = visit(evaluator, rhs)

        if haskey(valuation, dep.name)
            # multiple assignments
            # should only happen if assignments are in different branches
            # this over-approximates resulting set (union of intervals) as interval
            # this is used after if branches, i.e. last time dep.name was assigned (lexicographically)
            if !haskey(tmp_valuation, dep.name)
                tmp_valuation[dep.name] = valuation[dep.name] # this is first assignment of dep.name
            end
            tmp_valuation[dep.name] = res ∪ tmp_valuation[dep.name] # union of all assignments
        end
        
        valuation[dep.name] = res # (is used also by evaluator)

        if haskey(tmp_valuation, dep.name)
            if !any(future_dep.name == dep.name for future_dep in data_deps[i+1:end])
                # we reached last (of multiple) assignment of dep.name
                # we now write the over-approximation (union of intervals of all assignments)
                valuation[dep.name] = tmp_valuation[dep.name]
            end
        end
    end

    # lastly, evaluate node where all dependencies are masked with their intervals
    res = visit(evaluator, node_to_evaluate)
    
    return res
end