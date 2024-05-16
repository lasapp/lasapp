# Mak, C., Zaiser, F., & Ong, L. (2021, July). Nonparametric hamiltonian monte carlo. In International Conference on Machine Learning (pp. 7336-7347). PMLR.

using Gen

@gen function model()
    q = {:q} ~ normal(0,1)
    i = 0
    s = 0
    while s < q
        i += 1
        step = {:s => i} ~ normal(0.,1)
        s += step
    end
    diff ~ normal(q-s, 1)
end

observations = choicemap(:diff => 0.)

tr, _ = generate(model, (), observations)
get_choices(tr)
