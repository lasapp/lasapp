# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_13.jl

using Turing

@model function m13_1(S, N, tank)
    tank_size = length(levels(tank))
    a ~ filldist(Normal(0, 1.5), tank_size)
    p = logistic.(a)
    @. S ~ Binomial(N, p)
end

@model function m13_2(S, N, tank)
    tank_size = length(levels(tank))
    σ ~ Exponential()
    ā ~ Normal(0, 1.5)
    a ~ filldist(Normal(ā, σ), tank_size)
    p = logistic.(a)
    @. S ~ Binomial(N, p)
end

@model function m13_3(Si, Ni, pond)
    σ ~ Exponential()
    ā ~ Normal(0, 1.5)
    a_pond ~ filldist(Normal(ā, σ), nponds)
    p = logistic.(a_pond)
    @. Si ~ Binomial(Ni, p)
end

@model function m13_4(pulled_left, actor, block_id, treatment)
    σ_a ~ Exponential()
    σ_g ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    blocks_count = length(levels(block_id))
    treats_count = length(levels(treatment))
    a ~ filldist(Normal(ā, σ_a), actors_count)
    g ~ filldist(Normal(0, σ_g), blocks_count)
    b ~ filldist(Normal(0, 0.5), treats_count)
    
    p = @. logistic(a[actor] + g[block_id] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end

@model function m13_5(pulled_left, actor, treatment)
    σ_a ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    treats_count = length(levels(treatment))
    a ~ filldist(Normal(ā, σ_a), actors_count)
    b ~ filldist(Normal(0, 0.5), treats_count)
    
    p = @. logistic(a[actor] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end

@model function m13_6(pulled_left, actor, block_id, treatment)
    σ_a ~ Exponential()
    σ_g ~ Exponential()
    σ_b ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    blocks_count = length(levels(block_id))
    treats_count = length(levels(treatment))
    a ~ filldist(Normal(ā, σ_a), actors_count)
    g ~ filldist(Normal(0, σ_g), blocks_count)
    b ~ filldist(Normal(0, σ_b), treats_count)
    
    p = @. logistic(a[actor] + g[block_id] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end

@model function m13_7(N)
    v ~ Normal(0, 3)
    x ~ Normal(0, exp(v))
end

@model function m13_7nc(N)
    v ~ Normal(0, 3)
    z ~ Normal()
    x = z * exp(v)
end

@model function m13_4nc(pulled_left, actor, block_id, treatment)
    σ_a ~ Exponential()
    σ_g ~ Exponential()
    ā ~ Normal(0, 1.5)
    actors_count = length(levels(actor))
    blocks_count = length(levels(block_id))
    treats_count = length(levels(treatment))
    b ~ filldist(Normal(0, 0.5), treats_count)
    z ~ filldist(Normal(), actors_count)
    x ~ filldist(Normal(), blocks_count)
    a = @. ā + σ_a*z
    g = σ_g*x
    
    p = @. logistic(a[actor] + g[block_id] + b[treatment])
    @. pulled_left ~ Binomial(1, p)
end

