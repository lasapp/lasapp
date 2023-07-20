using Turing

@model function model_orig(g)
    d ~ Bernoulli(0.6)
    i ~ Bernoulli(0.7)

    if (!i && !d)
        g ~ Bernoulli(0.3)
    else
        if (i && !d)
            g ~ Bernoulli(0.9)
        else
            g ~ Bernoulli(0.5)
        end
    end

    if !i
        s ~ Bernoulli(0.2)
    else
        s ~ Bernoulli(0.95)
    end

    if !g
        l ~ Bernoulli(0.1)
    else
        l ~ Bernoulli(0.4)
    end
end



@model function model_adapted(g)
    d ~ Bernoulli(0.6)
    i ~ Bernoulli(0.7)

    if (!i && !d)
        g_prob = 0.3
    else
        if (i && !d)
            g_prob = 0.9
        else
            g_prob = 0.5
        end
    end
    g ~ Bernoulli(g_prob)
    s ~ Bernoulli(i ? 0.95 : 0.2)
    l ~ Bernoulli(g ? 0.5 : 0.1)
end

model = model_orig(false)
# model = model_adapted(false)