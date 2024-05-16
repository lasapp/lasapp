# Nishimura, A., Dunson, D. B., & Lu, J. (2020). Discontinuous Hamiltonian Monte Carlo for discrete parameters and discontinuous likelihoods. Biometrika, 107(2), 365-380.

using Gen

@gen function model(x, y)
    n,d = size(x)
    beta = zeros(d)
    for k in 1:d
        beta[k] = {:beta => k} ~ normal(0, 1)
    end
    loss = 0
    for i in 1:n
        if y[i] * x[i,:]'beta < 0
            loss += 1
        end
    end
    {:loss} ~ normal(-sqrt(loss), 1)
end

observations = choicemap(:loss => 0.)
x = randn(3, 20)
y = 2*rand(Bool, 20).-1

tr, _ = generate(model, (x, y), observations)
get_choices(tr)

