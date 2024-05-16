# Mak, C., Zaiser, F., & Ong, L. (2021, July). Nonparametric hamiltonian monte carlo. In International Conference on Machine Learning (pp. 7336-7347). PMLR.

using Gen

@gen function model()
    start ~ uniform_continuous(0,3)
    t = 0
    position = start
    distance = 0.0
    while position > 0 && distance < 10
        step = {:step=>t} ~ uniform_continuous(-1, 1)
        distance = distance + abs(step)
        position = position + step
        t = t + 1
    end
    end_distance ~ normal(distance, 0.1)
    return start
end

observations = choicemap(:end_distance=>1.1)

tr, _ = generate(model, (), observations)
get_choices(tr)