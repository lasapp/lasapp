# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function pPCA(X::AbstractMatrix{<:Real}, k::Int)
    # retrieve the dimension of input matrix X.
    N, D = size(X)

    # weights/loadings W
    W ~ filldist(Normal(), D, k)

    # latent variable z
    Z ~ filldist(Normal(), k, N)

    # mean offset
    μ ~ MvNormal(Eye(D))
    genes_mean = W * Z .+ reshape(μ, n_genes, 1)
    return X ~ arraydist([MvNormal(m, Eye(N)) for m in eachcol(genes_mean')])
end


model = pPCA

# MODELGRAPH:
# nodes:
# W, Z, μ, X
# edges:
# W -> X
# Z -> X
# μ -> X
# END_MODELGRAPH

# NOTE: sample in return
# NOTE: generator