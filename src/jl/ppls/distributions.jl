
function parse_distribution(name::Symbol, params::Vector{SyntaxNode}; parameter_renames=nothing)::Tuple{String, Dict{String,SyntaxNode}}
    dist_name = string(name)

    if name == :Beta
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        else
            α = params[1]
            β = params[2]
        end
        dist_params = Dict("alpha"=>α, "beta"=>β)
    elseif name == :Cauchy || name == :LogNormal || name == :Normal
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        else
            μ = params[1]
            σ = params[2]
        end
        dist_params = Dict("location"=>μ, "scale"=>σ)
    elseif name == :Chisq
        dist_name = "ChiSquared"
        df = params[1]
        dist_params = Dict("df"=>df)
    elseif name == :Exponential
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        else
            scale = params[1]
        end
        dist_params = Dict("scale"=>scale)
    elseif name == :Gamma || name == :InverseGamma
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        else
            shape = params[1]
            scale = params[2]
        end
        dist_params = Dict("shape"=>shape, "scale"=>scale)
    elseif name == :TDist
        dist_name = "StudentT"
        df = params[1]
        dist_params = Dict("df"=>df)
    elseif name == :Uniform || name == :DiscreteUniform
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        else
            a = params[1]
            b = params[2]
        end
        dist_params = Dict("a"=>a,"b"=>b)
    elseif name == :Bernoulli || name == :Categorical || name == :Geometric
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        elseif length(params) == 1
            p = params[1]
        end
        dist_params = Dict("p"=>p)
    elseif name == :Binomial
        if length(params) <= 1
            error("Default parameters are not supported (in $dist_name).")
        else
            n = params[1]
            p = params[2]
        end
        dist_params = Dict("n"=>n, "p"=>p)
    elseif name == :Dirac
        dist_params = Dict("location"=>params[1])
    elseif name == :Poisson
        if length(params) == 0
            error("Default parameters are not supported (in $dist_name).")
        elseif length(params) == 1
            rate = params[1]
        end
        dist_params = Dict("rate"=>rate)
    elseif name == :Multinomial
        n = params[1]
        if kind(params[2]) == K"Integer"
            dist_params = Dict("n"=>n, "k"=>params[2])
        else
            dist_params = Dict("n"=>n, "p"=>params[2])
        end
    elseif name == :MvNormal
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
    elseif name == :LKJCholesky
        dist_params = Dict("size"=>params[1], "shape"=>params[2])
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