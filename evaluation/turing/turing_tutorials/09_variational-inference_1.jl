# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function model(x)
    s ~ InverseGamma(2, 3)
    m ~ Normal(0.0, sqrt(s))
    for i in 1:length(x)
        x[i] ~ Normal(m, sqrt(s))
    end
end;

# MODELGRAPH:
# nodes:
# s, m, x[i]
# edges:
# s -> x[i]
# s -> m
# m -> x[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge x[i] -> x[i]