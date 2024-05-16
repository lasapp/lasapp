import ast

def parse_torch_distribution(name, args, kwargs) -> tuple[str, dict[str, ast.AST]]:
    dist_name = name

    # always use probs, logits not supported
    if name in ("Bernoulli", "Geometric"):
        dist_params = {'p':  kwargs.get('probs', args[0])}
    elif name in ("Categorical", "OneHotCategorical"):
        dist_name = 'Categorical'
        dist_params = {'p':  kwargs.get('probs', args[0])}
    elif name == "Beta":
        dist_params = {'alpha': kwargs.get('concentration1', args[0]), 'beta': kwargs.get('concentration0', args[1])}
    elif name == "Binomial":
        dist_params = {'n': kwargs.get('total_count', args[0]), 'p': kwargs.get('probs', args[1])}
    elif name == "Cauchy":
        dist_params = {'location': kwargs.get('loc', args[0]), 'scale': kwargs.get('scale', args[1])}
    elif name == "Chi2":
        dist_name = "ChiSquared"
        dist_params = {'df': kwargs.get('df', args[0])}
    elif name == "Dirichlet":
        dist_params = {'alpha': kwargs.get('concentration', args[0])}
    elif name in ("Exponential", "Poisson"):
        dist_params = {'rate': kwargs.get('rate', args[0])}
    elif name in ("Gamma", "InverseGamma"):
        dist_params = {'shape': kwargs.get('concentration', args[0]), 'rate': kwargs.get('rate', args[1])}
    elif name in ("HalfCauchy", "HalfNormal"):
        dist_params = {'scale': kwargs.get('scale', args[0])}
    elif name == "LKJ":
        dist_name = "LKJCholesky"
        dist_params = {'size': kwargs.get('dim', args[0]), 'shape': kwargs.get('dim', args[1])}
    elif name in ("LogNormal", "Normal"):
        dist_params = {'location': kwargs.get('loc', args[0]), 'scale': kwargs.get('scale', args[1])}
    elif name == "Multinomial":
        dist_params = {'n': kwargs.get('total_count', args[0]), 'p': kwargs.get('probs', args[1])}
    elif name == "MultivariateNormal":
        dist_params = {'location': kwargs.get('loc', args[0])}
        if len(args) == 2:
            dist_params['covariance'] = args[1]
        if 'covariance_matrix' in kwargs:
            dist_params['covariance'] = kwargs['covariance_matrix']
        if 'precision_matrix' in kwargs:
            dist_params['precision'] = kwargs['precision_matrix']
    elif name == "StudentT":
        dist_params = {'df': kwargs.get('df', args[0])}
        dist_params['location'] = 0.
        dist_params['scale'] = 1.
        if len(args) >= 2:
            dist_params['location'] = args[1]
        if len(args) == 3:
            dist_params['scale'] = args[2]
        if 'loc' in kwargs:
            dist_params['location'] = kwargs['loc']
        if 'scale' in kwargs:
            dist_params['scale'] = kwargs['scale']
    elif name == "Uniform":
        dist_params = {'a': kwargs.get('low', args[0]), 'b': kwargs.get('high', args[1])}
    elif name == "Wishart":
        dist_params = {'df': kwargs.get('low', args[0])}
        if len(args) == 2:
            dist_params['scale'] = args[1]
        if 'covariance_matrix' in kwargs:
            dist_params['scale'] = kwargs['covariance_matrix']
    elif name == "Delta":
        dist_name = "Dirac"
        dist_params = {'location': kwargs.get('v', args[0])}
    else:
        dist_name = f"Unknown-{name}"
        dist_params = {**{f"param_{i}": a for i,a in enumerate(args)}, **kwargs}

    return dist_name, dist_params