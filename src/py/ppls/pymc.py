from .ppl import PPL, VariableDefinition
import ast
from ast_utils.utils import get_call_name, get_name
from typing import Union

class PyMC(PPL):
    def __init__(self) -> None:
        super().__init__()
        self.distributions = {
            'AsymmetricLaplace', 'Beta', 'Cauchy', 'ChiSquared', 'ExGaussian',
            'Exponential', 'Flat', 'Gamma', 'Gumbel', 'HalfCauchy',
            'HalfFlat', 'HalfNormal', 'HalfStudentT', 'Interpolated', 'InverseGamma',
            'Kumaraswamy', 'Laplace', 'Logistic', 'LogitNormal', 'LogNormal',
            'Moyal', 'Normal', 'Pareto', 'PolyaGamma', 'Rice',
            'SkewNormal', 'StudentT', 'Triangular', 'TruncatedNormal', 'Uniform',
            'VonMises', 'Wald', 'Weibull',

            'Bernoulli', 'BetaBinomial', 'Binomial', 'Categorical', 'DiracDelta',
            'DiscreteUniform', 'DiscreteWeibull', 'Geometric', 'HyperGeometric', 'NegativeBinomial',
            'OrderedLogistic', 'OrderedProbit', 'Poisson', 'ZeroInflatedBinomial', 'ZeroInflatedNegativeBinomial',
            'ZeroInflatedPoisson',

            'CAR', 'Dirichlet', 'DirichletMultinomial', 'KroneckerNormal', 'LKJCholeskyCov',
            'LKJCorr', 'MatrixNormal', 'Multinomial', 'MvNormal', 'MvStudentT',
            'OrderedMultinomial', 'StickBreakingWeights', 'Wishart', 'WishartBartlett', 'ZeroSumNormal',

            'Mixture', 'NormalMixture'

            # there are other 'submodels' like AR
        }

    def is_random_variable_definition(self, node: ast.AST) -> bool:
        if isinstance(node, ast.Assign):
            return self.is_random_variable_definition(node.value)
        
        if not isinstance(node, ast.Call):
            return False
        
        if isinstance(node.func, ast.Name) and node.func.id in self.distributions:
            return True
        elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
            return node.func.value.id in ('pm', 'pymc') and node.func.attr in self.distributions # TODO: check how pymc is imported
        else:
            return False
        
    def get_random_variable_name(self, variable:VariableDefinition) -> str:
        call_node = variable.node.value if isinstance(variable.node, ast.Assign) else variable.node
        return ast.unparse(call_node.args[0])

    def get_program_variable_name(self, variable:VariableDefinition) -> Union[str,None]:
        if isinstance(variable.node, ast.Assign):
            return get_name(variable.node.targets[0]).id
        else:
            return None

    def is_model(self, node: ast.AST) -> bool:
        if not isinstance(node, ast.With):
            return False

        call = node.items[0].context_expr
        if not isinstance(call, ast.Call):
            return False
        
        if isinstance(call.func, ast.Name) and call.func.id == "Model":
            return True
        elif isinstance(call.func, ast.Attribute) and isinstance(call.func.value, ast.Name):
            return call.func.value.id in ('pm', 'pymc') and call.func.attr == "Model"
        
        return False
    
    def get_model_name(self, node: ast.AST) -> str:
        return node.items[0].optional_vars.id
    
    def is_observed(self, variable: VariableDefinition) -> bool:
        call_node = variable.node.value if isinstance(variable.node, ast.Assign) else variable.node
        for kw in call_node.keywords:
            if kw.arg == 'observed':
                return True
        return False
    
    def get_distribution_node(self, variable: VariableDefinition) -> ast.AST:
        call_node = variable.node.value if isinstance(variable.node, ast.Assign) else variable.node
        return call_node
    
    def get_distribution(self, distribution_node: ast.AST) -> tuple[str, dict[str, ast.AST]]:
        name =  get_call_name(distribution_node)

        dist_name = name

        args = distribution_node.args
        kwargs = {kw.arg: kw.value for kw in distribution_node.keywords}

        if len(args) > 1:
            # we assume that all parameters are given by keyword
            # first and only positional argument is variable name
            return "Unknown", {"distribution": distribution_node}
        
        # we do not check all parameters, but only the conventional
        # e.g. we do not check mu and sigma for Beta, but only alpha and beta
        # always use scale (sigma) instead of precision
        # dont use logits

        try:
            if name == 'Beta':
                dist_params = {'alpha': kwargs['alpha'], 'beta': kwargs['beta']}
            elif name == 'Cauchy':
                dist_params = {'location': kwargs['alpha'], 'scale': kwargs['beta']}
            elif name == 'ChiSquared':
                dist_params = {'df': kwargs['nu']}
            elif name == 'Exponential':
                dist_params = {'rate': kwargs['lam']}
            elif name == 'Gamma':
                dist_params = {'shape': kwargs['alpha'], 'rate': kwargs['beta']}
            elif name == 'HalfCauchy':
                dist_params = {'scale': kwargs['beta']}
            elif name == 'HalfNormal':
                dist_params = {'scale': kwargs['sigma']}
            elif name == 'InverseGamma':
                dist_params = {'shape': kwargs['alpha'], 'scale': kwargs['beta']}
            elif name in ('LogNormal', 'Normal'):
                dist_params = {'location': kwargs['mu'], 'scale': kwargs['sigma']}
            elif name == 'StudentT':
                dist_params = {'df': kwargs['nu'], 'location': kwargs['mu'], 'scale': kwargs['sigma']}
            elif name in ('Uniform', 'DiscreteUniform'):
                dist_params = {'a': kwargs['lower'], 'b': kwargs['upper']}
            elif name in ('Bernoulli', 'Categorical', 'Geometric'):
                dist_params = {'p': kwargs['p']}
            elif name == 'Binomial':
                dist_params = {'n': kwargs['n'], 'p': kwargs['p']}
            elif name == 'DiracDelta':
                dist_name = 'Dirac'
                dist_params = {'location': kwargs['c']}
            elif name == 'Poisson':
                dist_params = {'rate': kwargs['mu']}
            elif name == 'Dirichlet':
                dist_params = {'alpha': kwargs['a']}
            elif name == 'Multinomial':
                dist_params = {'n': kwargs['n'], 'p': kwargs['p']}
            elif name == 'MvNormal':
                dist_name = 'MultivariateNormal'
                dist_params = {'location': kwargs['mu'], 'covariance': kwargs['cov']}
            elif name == 'Wishart':
                dist_params = {'df': kwargs['mu'], 'scale': kwargs['V']}
            elif name == 'LKJCorr':
                dist_name = 'LKJCholesky'
                dist_params = {'size': kwargs['n'], 'shape': kwargs['eta']}
            else:
                dist_name = f'Unknown-{name}'
                dist_params = kwargs

            return dist_name, dist_params
        except KeyError:
            raise Exception(f"Default parameters not supported (in {dist_name})")