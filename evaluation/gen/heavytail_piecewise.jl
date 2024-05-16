# Mohasel Afshar, H., & Domke, J. (2015). Reflection, refraction, and hamiltonian monte carlo. Advances in neural information processing systems, 28
# Some adaptions to phrase it as a probabilistic program, but the characteristics of the density are the same.

using Gen
import LinearAlgebra: norm

@gen function model(N)
    x = zeros(N)
    for i in 1:N
        x[i] = {:x => i} ~ uniform_continuous(-6,6)
    end
    if maximum(abs, x) < 3
        upper = exp(-norm(x)/12) * 12^N
    else
        upper = exp(-norm(x)/12 - 1) * 12^N
    end

    y ~ uniform_continuous(0, 1/upper)
end

observations = choicemap(:y => 0.)

tr, = generate(model, (2,), observations)
get_choices(tr)

function p(x)
    N = length(x)
    tr = choicemap()
    for i in 1:N
        tr[:x => i] = x[i]
    end
    lj, _ = assess(model, (N,), merge(tr, observations))
    return exp(lj)
end
function p2(x1, x2)
    return p([x1,x2])
end

using Plots

contour(range(-6,6,200), range(-6,6,200), p2, aspect_ratio=:equal, levels=[0.2,0.25,0.5,0.75,0.8,0.85,0.9,0.95])

# NOTE: random control flow