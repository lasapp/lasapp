# https://github.com/TuringLang/TuringTutorials/tree/8515a567321adf1531974dd14eb29c00eea05648

using Turing

@model function bayes_nn(xs, ts, nparameters, reconstruct; alpha=0.09)
    # Create the weight and bias vector.
    parameters ~ MvNormal(Zeros(nparameters), I / alpha)

    # Construct NN from parameters
    nn = reconstruct(parameters)
    # Forward NN to make predictions
    preds = nn(xs)

    # Observe each prediction.
    for i in 1:length(ts)
        ts[i] ~ Bernoulli(preds[i])
    end
end

model = bayes_nn

# MODELGRAPH:
# nodes:
# parameters, ts[i]
# edges:
# parameters -> ts[i]
# END_MODELGRAPH

# NOTE: unroll loops to remove spurious edge ts[i] -> ts[i]