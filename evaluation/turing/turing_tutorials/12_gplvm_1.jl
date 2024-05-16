# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function pPCA(x)
    # Dimensionality of the problem.
    N, D = size(x)
    # latent variable z
    z ~ filldist(Normal(), D, N)
    # weights/loadings W
    w ~ filldist(Normal(), D, D)
    mu = (w * z)'
    for d in 1:D
        x[:, d] ~ MvNormal(mu[:, d], I)
    end
    return nothing
end

model = pPCA

# MODELGRAPH:
# nodes:
# z - w - x[:, d]
# edges:
# z -> x[:, d]
# w -> x[:, d]
# END_MODELGRAPH