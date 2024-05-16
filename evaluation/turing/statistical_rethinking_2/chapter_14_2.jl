# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_14.jl

using Turing

@model function m14_2(L, tid, actor, block_id)
    tid_len = length(levels(tid))
    act_len = length(levels(actor))
    blk_len = length(levels(block_id))
    g ~ filldist(Normal(), tid_len)

    σ_actor ~ filldist(Exponential(), tid_len)
    ρ_actor ~ LKJ(tid_len, 2)
    Σ_actor = (σ_actor .* σ_actor') .* ρ_actor
    alpha ~ filldist(MvNormal(zeros(tid_len), Σ_actor), act_len)

    σ_block ~ filldist(Exponential(), tid_len)
    ρ_block ~ LKJ(tid_len, 2)
    Σ_block = (σ_block .* σ_block') .* ρ_block
    beta ~ filldist(MvNormal(zeros(tid_len), Σ_block), blk_len)
    
    for i ∈ eachindex(L)
        p = logistic(g[tid[i]] + alpha[tid[i], actor[i]] + beta[tid[i], block_id[i]])
        L[i] ~ Bernoulli(p)
    end
end

model = m14_2

# MODELGRAPH:
# nodes:
# g, σ_actor, ρ_actor, alpha, σ_block, ρ_block, beta, L[i]
# edges:
# g -> L[i]
# σ_actor -> alpha
# ρ_actor -> alpha
# alpha -> L[i]
# σ_block -> beta
# ρ_block -> beta
# beta -> L[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge L[i] -> L[i]

# NOTE: constraint violation due to multivariate covariance matrix