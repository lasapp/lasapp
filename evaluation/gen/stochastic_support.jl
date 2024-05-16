# Zhou, Y., Yang, H., Teh, Y. W., & Rainforth, T. (2020, November). Divide, conquer, and combine: a new inference strategy for probabilistic programs with stochastic support. In International Conference on Machine Learning (pp. 11534-11545). PMLR.

using Gen

@gen function model()
    z0 ~ normal(0, 2)
    if z0 < 0
        z1 ~ normal(-5, 2)
        y1 ~ normal(z1, 2)
    else
        z2 ~ normal(5, 2)
        z3 ~ normal(z2, 2)
        y1 ~ normal(z3, 2)
    end
end

observations = choicemap(:y1 => 9.)

tr, _ = generate(model, (), observations)
get_choices(tr)
