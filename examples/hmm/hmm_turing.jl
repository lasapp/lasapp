
using Turing
import Random
using StatsPlots

Random.seed!(0)

# Define the emission parameter.
y = [
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    2.0,
    2.0,
    2.0,
    2.0,
    2.0,
    2.0,
    3.0,
    3.0,
    3.0,
    3.0,
    3.0,
    3.0,
    3.0,
    2.0,
    2.0,
    2.0,
    2.0,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
    1.0,
]
N = length(y)
K = 3

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

model = BayesHmm(y, 3)
g = Gibbs(HMC(0.01, 50, :m, :T), PG(120, :s))
chn = sample(model, g, 1000)


subchain = chn[["T[1][1]", "T[2][2]", "T[3][3]"]]

plot(subchain; seriestype=:traceplot, title="Persistence Probability", legend=false)