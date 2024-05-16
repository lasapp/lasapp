# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function turing_m(x)
    a ~ Normal(0.5, 1)
    b ~ Normal(a, 2)
    x ~ Normal(b, 0.5)
    return nothing
end

model = turing_m

# MODELGRAPH:
# nodes:
# a, b, x
# edges:
# a -> b
# b -> x
# END_MODELGRAPH