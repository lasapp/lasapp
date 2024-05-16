# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_05_1_Spurious_Associations.jl

using Turing

@model function m5_3A(A, M, D)
	# A → D ← M
	σ ~ Exponential(1)
	a ~ Normal(0, 0.2)
	bA ~ Normal(0, 0.5)
	bM ~ Normal(0, 0.5)
	μ = @. a + bA * A + bM * M
	D ~ MvNormal(μ, σ)
	# A → M
	σ_M ~ Exponential(1)
	aM ~ Normal(0, 0.2)
	bAM ~ Normal(0, 0.5)
	μ_M = @. aM + bAM * A
	M ~ MvNormal(μ_M, σ_M)
end

model = m5_3A

# MODELGRAPH:
# nodes:
# σ, a, bA, bM, D, σ_M, aM, bAM, M
# edges:
# σ -> D
# a -> D
# bA -> D
# bM -> D
# σ_M -> M
# aM -> M
# bAM -> M
# END_MODELGRAPH