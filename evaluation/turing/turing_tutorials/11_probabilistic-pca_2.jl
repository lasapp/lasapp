# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function pPCA_ARD(X)
    # Dimensionality of the problem.
    N, D = size(X)

    # latent variable Z
    Z ~ filldist(Normal(), D, N)

    # weights/loadings w with Automatic Relevance Determination part
    α ~ filldist(Gamma(1.0, 1.0), D)
    W ~ filldist(MvNormal(zeros(D), 1.0 ./ sqrt.(α)), D)

    mu = (W' * Z)'

    tau ~ Gamma(1.0, 1.0)
    return X ~ arraydist([MvNormal(m, 1.0 / sqrt(tau)) for m in eachcol(mu)])
end

model = pPCA_ARD

# MODELGRAPH:
# nodes:
# W, α, Z, tau,  X
# edges:
# α -> W
# W -> X
# Z -> X
# tau -> X
# END_MODELGRAPH

# NOTE: sample in return
# NOTE: generator