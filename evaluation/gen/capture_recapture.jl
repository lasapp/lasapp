# Nishimura, A., Dunson, D. B., & Lu, J. (2020). Discontinuous Hamiltonian Monte Carlo for discrete parameters and discontinuous likelihoods. Biometrika, 107(2), 365-380.

using Gen

n = [54, 146, 169, 209, 220, 209, 250, 176, 172, 127, 123, 120, 142]
R = [54, 143, 164, 202, 214, 207, 243, 175, 169, 126, 120, 120]
r = [24, 80, 70, 71, 109, 101, 108, 99, 70, 58, 44, 35]
m = [0, 10, 37, 56, 53, 77, 112, 86, 110, 84, 77, 72, 95]
z = [0, 14, 57, 71, 89, 121, 110, 132, 121, 107, 88, 60, 0]
u = n .- m
T = length(n)

struct RecaptureDist <: Gen.Distribution{Tuple{Vector{Float64},Vector{Float64},Vector{Float64}}}
end
recapture_dist = RecaptureDist()
function Gen.logpdf(dist::RecaptureDist,
    value::Tuple{Vector{Float64},Vector{Float64},Vector{Float64}},
    p::Vector{Float64}, phi::Vector{Float64}, R::Vector{Int})

    r, z, m = value
    T = length(p)
    xi = zeros(T-1)
    xi[T-1] = 1 - phi[T-1]*p[T]
    for i in T-2:-1:1
        x[i] = 1 - phi[i]*(p[i+1] + (1-p[i+1]) * (1-xi[i+1]))
    end
    lp = 0
    for i in 1:T-1
        lp += (R[i] - r[i]) * log(xi[i]) + z[i+1] * log(phi[i] * (1-p[i+1])) + m[i+1] * log(phi[i] * p[i+1])
    end
    return lp
end

@gen function model(T, u, σ_B)

    # priors
    p = zeros(T) # capture probability of each animal at the ith capture occasion
    for i in 1:T
        p[i] = {:p => i} ~ uniform_continuous(0,1)
    end
    phi = zeros(T-1) # survival probability of each animal from the ith to (i + 1)th capture occasion
    for i in 1:T-1
        phi[i] = {:phi => i} ~ uniform_continuous(0,1)
    end
    U = zeros(Int, T) # number of unmarked animals right before the ith capture occasion
    _U1 = {:U => 1} ~ uniform_continuous(100,200)
    U[1] = floor(_U1)
    for i in 1:T-1
        _U = {:U => i+1} ~ normal(phi[i]*(U[i] - u[i]), sqrt(σ_B^2 + phi[i]*(1-phi[i])))
        U[i+1] = max(0,floor(_U))
    end

    # likelihood of first captures
    for i in 1:T
        {:u => i} ~ binom(U[i], p[i])
    end

    # likelihood of recaptures
    {:recapture} ~ recapture_dist(p, phi, R)
end

observations = choicemap()
for i in 1:T
    observations[:u => i] = u[i]
end
observations[:recapture] = (r, z, m)

tr, = generate(model, (T,u, sqrt(500)), observations)
get_choices(tr)

# NOTE: cannot detect that floor is discontinuous