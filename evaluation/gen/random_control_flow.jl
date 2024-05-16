# Bernstein, R. (2023). Abstractions for Probabilistic Programming to Support Model Development. Columbia University. Chapter 5.1

using Gen

@gen function model()
    a ~ uniform_continuous(-1,1)
    x = a * a

    if x > 0
        m = 1
    else
        m = 2
    end

    for i in 0:m
        {:b => i} ~ normal(i, 1)
    end
end

observations = choicemap()
tr, _ = generate(model, (), observations)
get_choices(tr)
