# A simple Gaussian Mixture Model

using Gen

@gen function model(K, x)
    w ~ dirichlet(fill(1/K, K))
    
    means = Vector{Float64}(undef, K)
    prec = Vector{Float64}(undef, K)
    for k in 1:K
        means[k] = {:μ => k} ~ normal(0., 3.)
        prec[k] = {:τ => k} ~ gamma(2, 3)
    end

    for i in eachindex(x)
        z = {:z => i} ~ categorical(w)
        {:x => i} ~ normal(means[z], sqrt(1/prec[z]))
    end
end


import Random

Random.seed!(0)
z = (rand(50) .< 0.4) .+ 1
x = randn(length(z), 2) .* [1 2] .+ [-2 3]
x = x[hcat(z .== 1, z .== 2)]

observations = choicemap()
for i in eachindex(x)
    observations[:x => i] = x[i]
end

tr, _ = generate(model, (2,x), observations)
get_choices(tr)