# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function BayesHmm(y, K)
    # Get observation length.
    N = length(y)

    # State sequence.
    s = tzeros(Int, N)

    # Emission matrix.
    m = Vector(undef, K)

    # Transition matrix.
    T = Vector{Vector}(undef, K)

    # Assign distributions to each element
    # of the transition matrix and the
    # emission matrix.
    for i in 1:K
        T[i] ~ Dirichlet(ones(K) / K)
        m[i] ~ Normal(i, 0.5)
    end

    # Observe each point of the input.
    s[1] ~ Categorical(K)
    y[1] ~ Normal(m[s[1]], 0.1)

    for i in 2:N
        s[i] ~ Categorical(vec(T[s[i - 1]]))
        y[i] ~ Normal(m[s[i]], 0.1)
    end
end


model = BayesHmm

# MODELGRAPH:
# nodes:
# T[i], m[i], s[1], y[1], s[i], y[i]
# edges:
# s[1] -> s[i]
# s[1] -> y[1]
# s[i] -> s[i]
# T[i] -> s[i]
# m[i] -> y[i]
# m[i] -> y[1]
# s[i] -> y[i]
# END_MODELGRAPH

# NOTE: loop unrolling fails, because s[i - 1], or we make loop unroller more sophisticated