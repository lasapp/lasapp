# https://github.com/StatisticalRethinkingJulia/SR2TuringPluto.jl/tree/75072280947a45f030bd45a62710c558d60a2a80
# notebooks/Chapter_11.jl

using Turing

@model function ppl11_1(pulled_left)
    a ~ Normal(0, 10)
    p = logistic(a)     # inverse of the `logit` function
    pulled_left ~ Binomial(1, p)
end

@model function ppl11_2(pulled_left, treatment)
    a ~ Normal(0, 1.5)
    treat_levels = length(levels(treatment))
    b ~ MvNormal(zeros(treat_levels), 10)
    
    p = @. logistic(a + b[treatment])
    for i ∈ eachindex(pulled_left)
        pulled_left[i] ~ Binomial(1, p[i])
    end
end

@model function m11_3(pulled_left, treatment)
    a ~ Normal(0, 1.5)
    treat_levels = length(levels(treatment))
    b ~ MvNormal(zeros(treat_levels), 0.5)
    
    p = @. logistic(a + b[treatment])
    for i ∈ eachindex(pulled_left)
        pulled_left[i] ~ Binomial(1, p[i])
    end
end

@model function m11_4(actor, treatment, pulled_left)
    act_levels = length(levels(actor))
    a ~ MvNormal(zeros(act_levels), 1.5)
    treat_levels = length(levels(treatment))
    b ~ MvNormal(zeros(treat_levels), 0.5)
    
    p = @. logistic(a[actor] + b[treatment])
    for i ∈ eachindex(pulled_left)
        pulled_left[i] ~ Binomial(1, p[i])
    end
end

@model function m11_5(actor, side, cond, pulled_left)
    act_levels = length(levels(actor))
    a ~ MvNormal(zeros(act_levels), 1.5)
    side_levels = length(levels(side))
    bs ~ MvNormal(zeros(side_levels), 0.5)    
    cond_levels = length(levels(cond))
    bc ~ MvNormal(zeros(cond_levels), 0.5)
    
    p = @. logistic(a[actor] + bs[side] + bc[cond])
    for i ∈ eachindex(pulled_left)
        pulled_left[i] ~ Binomial(1, p[i])
    end
end

@model function m11_6(actor, treatment, left_pulls)
    act_levels = length(levels(actor))
    a ~ MvNormal(zeros(act_levels), 1.5)
    treat_levels = length(levels(treatment))
    b ~ MvNormal(zeros(treat_levels), 0.5)
    
    p = @. logistic(a[actor] + b[treatment])
    for i ∈ eachindex(left_pulls)
        left_pulls[i] ~ Binomial(18, p[i])
    end
end

@model function m11_7(admit, applications, gid)
    a ~ MvNormal([0, 0], 1.5)
    p = @. logistic(a[gid])
    for i ∈ eachindex(applications)
        admit[i] ~ Binomial(applications[i], p[i])
    end
end

@model function model_m11_8(admit, applications, gid, dept_id)
    a ~ MvNormal([0, 0], 1.5)
    delta ~ MvNormal(zeros(6), 1.5)
    p = @. logistic(a[gid] + delta[dept_id])
    for i ∈ eachindex(applications)
        admit[i] ~ Binomial(applications[i], p[i])
    end
end

@model function m11_8(admit, applications, gid, dept_id)
    a ~ MvNormal([0, 0], 1.5)
    delta ~ MvNormal(zeros(6), 1.5)
    p = @. logistic(a[gid] + delta[dept_id])
    for i ∈ eachindex(applications)
        admit[i] ~ Binomial(applications[i], p[i])
    end
end

@model function m11_9(T)
    a ~ Normal(3, 0.5)
    λ = exp(a)
    T ~ Poisson(λ)
end

@model function m11_10(T, cid, P)
    a ~ MvNormal([3, 3], 0.5)
    b ~ MvNormal([0, 0], 0.2)
    λ = @. exp(a[cid] + b[cid]*P)
    for i ∈ eachindex(T)
        T[i] ~ Poisson(λ[i])
    end
end

@model function m11_11(T, P, cid)
    a ~ MvNormal([1,1], 1)
    b₁ ~ Exponential(1)
    b₂ ~ Exponential(1)
    b = [b₁, b₂]
    g ~ Exponential(1)
    λ = @. exp(a[cid]) * P ^ b[cid] / g
    for i ∈ eachindex(T)
        T[i] ~ Poisson(λ[i])
    end
end

@model function m11_12(y, log_days, monastery)
    a ~ Normal()
    b ~ Normal()
    λ = @. exp(log_days + a + b*monastery)
    @. y ~ Poisson(λ)
end

@model function m11_13(career, income)
    a ~ MvNormal([0, 0], 1)
    b ~ TruncatedNormal(0, 0.5, 0, Inf)
    p = softmax([a[1] + b*income[1], a[2] + b*income[2], 0])
    career ~ Categorical(p)
end

@model function m11_14(career, family_income)
    a ~ MvNormal([0, 0], 1.5)
    b ~ MvNormal([0, 0], 1)
    
    for i ∈ eachindex(career)
        income = family_income[i]
        s = [a[1] + b[1] * income, a[2] + b[2] * income, 0]
        p = softmax(s)
        career[i] ~ Categorical(p)
    end
end

@model function m_binom(admit, applications)
    a ~ Normal(0, 1.5)
    p = logistic(a)
    @. admit ~ Binomial(applications, p)
end

@model function m_pois(admit, reject)
    a ~ MvNormal([0, 0], 1.5)
    λ = exp.(a)
    admit ~ Poisson(λ[1])
    reject ~ Poisson(λ[2])
end


