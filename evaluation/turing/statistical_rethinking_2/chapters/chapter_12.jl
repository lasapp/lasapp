# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_12.jl

using Turing

@model function m12_1(A, N, gid)
    a ~ MvNormal([0, 0], 1.5)
    p̄ = @. logistic(a[gid])
    ϕ ~ Exponential(1)
    θ = ϕ + 2
    @. A ~ BetaBinomial2(N, p̄, θ)
end

@model function m12_2(T, P, cid)
    g ~ Exponential()
    ϕ ~ Exponential()
    a ~ MvNormal([1,1], 1)
    b₁ ~ Exponential()
    b₂ ~ Exponential()
    b = [b₁, b₂]
    λ = @. exp(a[cid])*(P^b[cid]) / g
    p = 1/(ϕ+1)
    r = λ/ϕ
    clamp!(r, 0.01, Inf)
    p = clamp(p, 0.01, 1)
    @. T ~ NegativeBinomial(r, p)
end

@model function m12_3(y)
    ap ~ Normal(-1.5, 1)
    al ~ Normal(1, 0.5)
    λ = exp(al)
    p = logistic(ap)
    y .~ ZIPoisson(λ, p)
end

@model function m12_4(R)
    # to ensure sorted cutpoints, use deltas
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -2 .+ cumsum(Δ_cutpoints)
    R .~ OrderedLogistic(0, cutpoints)
end

@model function m12_5(R, A, I, C)
    # to ensure sorted cutpoints, use deltas
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -3 .+ cumsum(Δ_cutpoints)
    
    bA ~ Normal(0, 0.5)
    bI ~ Normal(0, 0.5)
    bC ~ Normal(0, 0.5)
    bIA ~ Normal(0, 0.5)
    bIC ~ Normal(0, 0.5)
    BI = @. bI + bIA*A + bIC*C
    phi = @. bA*A + bC*C + BI*I
    
    for i in eachindex(R)
        R[i] ~ OrderedLogistic(phi[i], cutpoints)
    end
end

@model function m12_6(R, action, intention, contact, E)
    delta ~ Dirichlet(7, 2)
    pushfirst!(delta, 0.0)
    
    bA ~ Normal()
    bI ~ Normal()
    bC ~ Normal()
    bE ~ Normal()

    # sum all education's deltas
    sE = sum.(map(i -> delta[1:i], E))
    phi = @. bE*sE + bA*action + bI*intention + bC*contact

    # use same cutpoints as before
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -3 .+ cumsum(Δ_cutpoints)
    
    for i ∈ eachindex(R)
        R[i] ~ OrderedLogistic(phi[i], cutpoints)
    end
end

@model function m12_7(R, action, intention, contact, edu_norm)
    bA ~ Normal()
    bI ~ Normal()
    bC ~ Normal()
    bE ~ Normal()

    phi = @. bE*edu_norm + bA*action + bI*intention + bC*contact

    # use same cutpoints as before
    Δ_cutpoints ~ filldist(Exponential(), 6)
    cutpoints = -3 .+ cumsum(Δ_cutpoints)
    
    for i ∈ eachindex(R)
        R[i] ~ OrderedLogistic(phi[i], cutpoints)
    end
end