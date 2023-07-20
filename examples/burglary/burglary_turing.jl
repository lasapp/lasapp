
using Turing
import Random

@model function burglary(called, mary_wakes, phone_working)
    earthquake ~ Bernoulli(0.0001)
    burglary ~ Bernoulli(0.001)
    phone_working ~ Bernoulli(earthquake ? 0.7 : 0.99)

    alarm = earthquake | burglary

    if alarm && earthquake
        p_mary_wakes = 0.8
    elseif alarm
        p_mary_wakes = 0.6
    else
        p_mary_wakes = 0.2
    end
    mary_wakes ~ Bernoulli(p_mary_wakes)

    called ~ Dirac(mary_wakes && phone_working)

end

# model = burglary(true, missing, missing)
model = burglary(true, true, true)

chain = sample(model, IS(), 1_000_000);
W = exp.(chain["lp"])
W = W / sum(W)

chain["burglary"]'W

chain = sample(m, MH(), 1_000_000);
mean(chain["burglary"])

2969983/992160802