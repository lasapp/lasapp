# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function GPLVM(Y, K)
    # Dimensionality of the problem.
    N, D = size(Y)
    # K is the dimension of the latent space
    @assert K <= D
    noise = 1e-3

    # Priors
    α ~ MvLogNormal(MvNormal(Zeros(K), I))
    σ ~ LogNormal(0.0, 1.0)
    Z ~ filldist(Normal(), K, N)
    mu ~ filldist(Normal(), N)

    gp = GP(sekernel(α, σ))
    gpz = gp(ColVecs(Z), noise)
    Y ~ filldist(MvNormal(mu, cov(gpz)), D)

    return nothing
end

model = GPLVM

# MODELGRAPH:
# nodes:
# α, σ, Z, mu, Y
# edges:
# α -> Y
# σ -> Y
# Z -> Y
# mu -> Y
# END_MODELGRAPH

# NOTE: MvLogNormal