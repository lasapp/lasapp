
function parse_distribution(name::Symbol, params::Vector{SyntaxNode}; parameter_renames=nothing)::Tuple{String, Dict{String,SyntaxNode}}
    dist_name = string(name)

    if name == :Beta
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        end
        α = params[1]
        β = params[2]
        dist_params = Dict("alpha"=>α, "beta"=>β)
    elseif name == :Cauchy || name == :LogNormal || name == :Normal
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        end
        μ = params[1]
        σ = params[2]
        dist_params = Dict("location"=>μ, "scale"=>σ)
    elseif name == :Chisq
        dist_name = "ChiSquared"
        df = params[1]
        dist_params = Dict("df"=>df)
    elseif name == :Exponential
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        end
        scale = params[1]
        dist_params = Dict("scale"=>scale)
    elseif name == :Gamma || name == :InverseGamma
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        end
        shape = params[1]
        scale = params[2]
        dist_params = Dict("shape"=>shape, "scale"=>scale)
    elseif name == :TDist
        dist_name = "StudentT"
        df = params[1]
        dist_params = Dict("df"=>df)
    elseif name == :Uniform || name == :DiscreteUniform
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        end
        a = params[1]
        b = params[2]
        dist_params = Dict("a"=>a,"b"=>b)
    elseif name == :Bernoulli || name == :Categorical || name == :Geometric
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        end
        p = params[1]
        dist_params = Dict("p"=>p)
    elseif name == :Binomial
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        end
        n = params[1]
        p = params[2]
        dist_params = Dict("n"=>n, "p"=>p)
    elseif name == :NegativeBinomial
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        end
        r = params[1]
        p = params[2]
        dist_params = Dict("r"=>r, "p"=>p)
    elseif name == :Dirac
        dist_params = Dict("location"=>params[1])
    elseif name == :Poisson
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        end
        rate = params[1]
        dist_params = Dict("rate"=>rate)
    elseif name == :Multinomial
        n = params[1]
        if kind(params[2]) == K"Integer"
            dist_params = Dict("n"=>n, "k"=>params[2])
        else
            dist_params = Dict("n"=>n, "p"=>params[2])
        end
    elseif name in (:MvNormal, :MultivariateNormal)
        dist_name = "MultivariateNormal"
        dist_params = Dict("location"=>params[1], "covariance"=>params[2])
    elseif name == :Dirichlet
        if length(params) == 1
            dist_params = Dict("alpha"=>params[1],)
        else
            dist_params = Dict("k"=>params[1], "a"=>params[2])
        end
    elseif name == :Wishart || name == :InverseWishart
        dist_params = Dict("df"=>params[1], "scale"=>params[2])
    elseif name == :LKJCholesky || name == :LKJ
        dist_name = "LKJCholesky"
        dist_params = Dict("size"=>params[1], "shape"=>params[2])

    elseif name == :TruncatedNormal
        if length(params) < 3
            error("Default parameters are not supported (in $dist_name).")
        end

        μ = params[1]
        σ = params[2]

        if length(params) == 3
            # truncated(Normal(); lower=..., upper=...)
            dist_params = Dict("location"=>μ, "scale"=>σ)
            truncated_params = params[3]
            for kw_arg in truncated_params.children
                dist_params[string(kw_arg[1].val)] = kw_arg[2]
            end
        else
            @assert length(params) == 4 # TruncatedNormal(mu, sigma, l, u)
            lower = params[3]
            upper = params[4]
            dist_params = Dict("location"=>μ, "scale"=>σ, "lower"=>lower, "upper"=>upper)
        end

    elseif name == :OrderedLogistic
        # https://mc-stan.org/docs/functions-reference/bounded_discrete_distributions.html#ordered-logistic-distribution

        η = params[1]
        c = params[2]

        dist_params = Dict("eta"=>η, "c"=>c)
    else
        dist_name = "Unknown-$name"
        dist_params = Dict("param_$i"=>p for (i,p) in enumerate(params))
    end

    if !isnothing(parameter_renames)
        for (old, new) in parameter_renames
            dist_params[new] = dist_params[old]
            delete!(dist_params, old)
        end
    end


    return dist_name, dist_params
end


mutable struct DistributionPreprocessor <: NodeTransformer
    syntaxtree::SyntaxTree
    function DistributionPreprocessor(syntaxtree::SyntaxTree)
        return new(syntaxtree)
    end
end

function visit!(visitor::DistributionPreprocessor, node::SyntaxNode)::Union{Nothing,SyntaxNode}
    if kind(node) == K"call"
        call_name = get_call_name(node)
        if call_name == :Beta
            if length(JuliaSyntax.children(node)) == 1
                # Beta() -> Beta(1,1)
                α_node = get_empty_syntax_node(K"Float", val=1.0)
                β_node = get_empty_syntax_node(K"Float", val=1.0)
                add_child!(node, α_node)
                add_child!(node, β_node)
                add_node!(visitor.syntaxtree, α_node)
                add_node!(visitor.syntaxtree, β_node)
                return node
            elseif length(JuliaSyntax.children(node)) == 2
                # Beta(k) -> Beta(k,k)
                β_node = get_empty_syntax_node(K"Float", val=node[2].val)
                add_child!(node, β_node)
                add_node!(visitor.syntaxtree, β_node)
            end
        end

        if call_name == :Cauchy || call_name == :LogNormal || call_name == :Normal
            # Normal() -> Normal(0,1)
            if length(JuliaSyntax.children(node)) == 1
                μ_node = get_empty_syntax_node(K"Float", val=0.0)
                σ_node = get_empty_syntax_node(K"Float", val=1.0)
                add_child!(node, μ_node)
                add_child!(node, σ_node)
                add_node!(visitor.syntaxtree, μ_node)
                add_node!(visitor.syntaxtree, σ_node)
                return node
            end
        end

        if call_name == :Gamma || call_name == :InverseGamma
            # Gamma() -> Gamma(1,1)
            if length(JuliaSyntax.children(node)) == 1
                α_node = get_empty_syntax_node(K"Float", val=1.0)
                β_node = get_empty_syntax_node(K"Float", val=1.0)
                add_child!(node, α_node)
                add_child!(node, β_node)
                add_node!(visitor.syntaxtree, α_node)
                add_node!(visitor.syntaxtree, β_node)
                return node
            end
        end

        if call_name == :Exponential
            # Exponential() -> Exponential(1)
            if length(JuliaSyntax.children(node)) == 1
                scale_node = get_empty_syntax_node(K"Float", val=1.0)
                add_child!(node, scale_node)
                add_node!(visitor.syntaxtree, scale_node)
            end
        end

        if call_name == :Bernoulli || call_name == :Geometric
            # Bernoulli() -> Bernoulli(0.5)
            if length(JuliaSyntax.children(node)) == 1
                p_node = get_empty_syntax_node(K"Float", val=0.5)
                add_child!(node, p_node)
                add_node!(visitor.syntaxtree, p_node)
            end
        end

        if call_name == :Poisson
            # Poisson() -> Poisson(1.)
            if length(JuliaSyntax.children(node)) == 1
                λ_node = get_empty_syntax_node(K"Float", val=1.0)
                add_child!(node, λ_node)
                add_node!(visitor.syntaxtree, λ_node)
            end
        end

        if call_name in (:MvNormal, :MultivariateNormal)
            if length(JuliaSyntax.children(node)) == 2
                mu_node = get_empty_syntax_node(K"Float", val=0.0)
                insert_child!(node, 2, mu_node)
                add_node!(visitor.syntaxtree, mu_node)

            end
        end

        if call_name == :truncated
            truncated_params = node[3]
            if kind(truncated_params) != K"parameters"
                truncated_params = get_empty_syntax_node(K"parameters")
                add_node!(visitor.syntaxtree, truncated_params)
                set_children!(truncated_params, node.children[3:end])
                node.children = node.children[1:2]
                add_child!(node, truncated_params)
            end
            if length(truncated_params.children) < 2
                present_kws = Set{Symbol}(p[1].val for p in truncated_params.children)
                if !(:upper in present_kws)
                    ass_node = get_empty_syntax_node(K"=")
                    id_node = get_empty_syntax_node(K"Identifier", val=:upper)
                    p_node = get_empty_syntax_node(K"Identifier", val=:Inf)
                    set_children!(ass_node, [id_node, p_node])
                    add_child!(node, ass_node)
                    add_node!(visitor.syntaxtree, ass_node)
                    add_node!(visitor.syntaxtree, id_node)
                    add_node!(visitor.syntaxtree, p_node)
                end
                if !(:lower in present_kws)
                    ass_node = get_empty_syntax_node(K"=")
                    id_node = get_empty_syntax_node(K"Identifier", val=:lower)
                    c_node = get_empty_syntax_node(K"call", flags=JuliaSyntax.PREFIX_OP_FLAG, val=:-)
                    p_node = get_empty_syntax_node(K"Identifier", val=:Inf)
                    add_child!(node, ass_node)
                    set_children!(ass_node, [id_node, c_node])
                    set_children!(c_node, [p_node])
                    add_node!(visitor.syntaxtree, ass_node)
                    add_node!(visitor.syntaxtree, id_node)
                    add_node!(visitor.syntaxtree, c_node)
                    add_node!(visitor.syntaxtree, p_node)
                end
            end
        end
    end

    return generic_visit!(visitor, node)
end


# test truncated
# s = """
# Normal()
# truncated(Normal(); lower=-Inf, upper=Inf)
# truncated(Normal(); lower=1)
# truncated(Normal(), upper=1)
# """
# st = get_syntax_tree_for_str(s);
# st.root_node
# JuliaSyntax.head(st.root_node[2,3,1,2])
# kind(st.root_node[2,3,2,2])

# visit!(DistributionPreprocessor(st), st.root_node)
# st.root_node[2]
# st.root_node[3]
# st.root_node[4]