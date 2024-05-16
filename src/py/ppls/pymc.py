from .ppl import PPL, VariableDefinition
import ast
from ast_utils.utils import get_call_name
from ast_utils.preprocess import SyntaxTree
from .pyro_pymc_preproc import PyroPyMCPreprocessor

class PyMCPreprocessor(ast.NodeTransformer):
        def __init__(self, syntax_tree: SyntaxTree) -> None:
            self.syntax_tree = syntax_tree

        def visit_Call(self, node: ast.Call):
            match node:
                case ast.Call(
                    func=ast.Call(func=ast.Attribute(value=ast.Name(id=id), attr=attr), args=[dist, lower, upper])):
                    if id == 'pm' and attr == 'Bound':
                        dist.attr = "Truncated" + dist.attr
                        node.func = dist
                        lower_kw = ast.keyword(arg="lower", value=lower)
                        lower_kw.parent = node
                        node.keywords.append(lower_kw)
                        self.syntax_tree.add_node(lower_kw)
                        upper_kw = ast.keyword(arg="upper", value=upper)
                        upper_kw.parent = node
                        self.syntax_tree.add_node(upper_kw)
                        node.keywords.append(upper_kw)

                        return node
                        
            return super().generic_visit(node)
        
        
class PyMC(PPL):
    def __init__(self) -> None:
        super().__init__()
        self.distributions = {
            'Deterministic',

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

            'Mixture', 'NormalMixture',

            'Lognormal',

            'DensityDist',

            # there are other 'submodels' like AR
        }

    def is_random_variable_definition(self, node: ast.AST) -> bool:
        match node:
            case ast.Assign(value=ast.Call(func=ast.Attribute(value=ast.Name(id=_id), attr=_attr))) if _id in ('pm', 'pymc') and _attr in self.distributions:
                return True
            case _:
                return False
        
    def get_random_variable_name(self, variable:VariableDefinition) -> str:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        return ast.unparse(call_node.args[0])

    def get_address_node(self, variable: VariableDefinition) -> ast.AST:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        return call_node.args[0]
    
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
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        for kw in call_node.keywords:
            if kw.arg == 'observed':
                return True
        return False
    
    def get_distribution_node(self, variable: VariableDefinition) -> ast.AST:
        assert isinstance(variable.node, ast.Assign)
        call_node = variable.node.value
        return call_node
        
    def get_distribution(self, distribution_node: ast.AST) -> tuple[str, dict[str, ast.AST]]:
        name =  get_call_name(distribution_node)

        dist_name = name

        args = distribution_node.args
        kwargs = {kw.arg: kw.value for kw in distribution_node.keywords}
        
        # we do not check all parameters, but only the conventional
        # e.g. we do not check mu and sigma for Beta, but only alpha and beta
        # dont use logits

        try:
            if name == 'Beta':
                param_order = ['alpha', 'beta']
                param_names = ['alpha', 'beta']
            elif name == 'Cauchy':
                param_order = ['alpha', 'beta']
                param_names = ['location', 'scale']
            elif name == 'ChiSquared':
                param_order = ['nu']
                param_names = ['df']
            elif name == 'Exponential':
                param_order = ['lam']
                param_names = ['rate']
            elif name == 'Gamma':
                param_order = ['alpha', 'beta']
                param_names = ['shape', 'rate']
            elif name == 'HalfCauchy':
                param_order = ['beta']
                param_names = ['scale']
            elif name == 'HalfFlat':
                param_order = []
                param_names = []
            elif name == 'HalfNormal':
                param_order = [['sd','sigma','tau']]
                param_names = [['scale','scale','precision']]
            elif name == 'InverseGamma':
                param_order = ['alpha', 'beta']
                param_names = ['shape', 'scale']
            elif name in ('LogNormal', 'Lognormal', 'Normal'):
                param_order = ['mu', ['sigma', 'sd', 'tau']]
                param_names = ['location', ['scale', 'scale', 'precision']]
                if name == 'Lognormal':
                    dist_name = 'LogNormal'
            elif name == 'StudentT':
                param_order = ['nu', 'mu', ['sigma', 'sd']]
                param_names = ['df'', location', ['scale', 'scale']]
            elif name == 'Triangular':
                param_order = ['lower', 'c', 'upper']
                param_names = ['a', 'c', 'b']
            elif name in ('Uniform', 'DiscreteUniform'):
                param_order = ['lower', 'upper']
                param_names = ['a', 'b']
            elif name in ('Bernoulli', 'Categorical', 'Geometric'):
                param_order = ['p']
                param_names = ['p']
            elif name == 'Binomial':
                param_order = ['n', 'p']
                param_names = ['n', 'p']
            elif name == 'DiracDelta':
                dist_name = 'Dirac'
                param_order = ['c']
                param_names = ['location']
            elif name == 'Deterministic':
                dist_name = 'Deterministic'
                param_order = ['var']
                param_names = ['location']
            elif name == 'Poisson':
                param_order = ['mu']
                param_names = ['rate']
            elif name == 'Dirichlet':
                param_order = ['a']
                param_names = ['alpha']
            elif name == 'Multinomial':
                param_order = ['n', 'p']
                param_names = ['n', 'p']
            elif name == 'MvNormal':
                dist_name = 'MultivariateNormal'
                param_order = ['mu', ['cov', 'tau']]
                param_names = ['location', ['covariance', 'precision']]
            elif name == 'Wishart':
                param_order = ['mu', 'V']
                param_names = ['df', 'scale']
            elif name in ('LKJCholeskyCov', 'LKJCorr'):
                dist_name = 'LKJCholesky'
                param_order = ['n', 'eta']
                param_names = ['size', 'shape']
            elif name == 'TruncatedNormal':
                param_order = ['mu', ['sigma', 'sd', 'tau'], 'lower', 'upper']
                param_names = ['location', ['scale', 'scale', 'precision'], 'lower', 'upper']
            else:
                dist_name = f'Unknown-{name}'
                param_order = []
                param_names = []
                

            dist_params = {}
            for i in range(len(args)-1):
                arg = args[i+1]
                name = param_names[i]
                if isinstance(name, list):
                    name = name[0] # default to first parameter name
                dist_params[name] = arg
            for (param, arg) in kwargs.items():
                name = None
                for p, n in zip(param_order, param_names):
                    if param == p:
                        name = n
                        break
                    if isinstance(p, list):
                        for pp, nn in zip(p, n):
                            if param == pp:
                                name = nn
                                break
                        if name is not None:
                            break
                if name is not None:
                    dist_params[name] = arg

            # print(dist_name, dist_params, args)
            return dist_name, dist_params
        
        except KeyError:
            raise Exception(f"Default parameters not supported (in {dist_name})")
        

    def is_rogue_rv_node(self, node: ast.Call) -> bool:
        match node:
            case ast.Call(func=ast.Attribute(value=ast.Name(id=_id), attr=_attr)) if _id in ('pm', 'pymc') and _attr in self.distributions:
                return True
        return False

    def preprocess_syntax_tree(self, syntax_tree: SyntaxTree) -> SyntaxTree:
        PyMCPreprocessor(syntax_tree).visit(syntax_tree.root_node)
        PyroPyMCPreprocessor(syntax_tree, lambda node: self.is_rogue_rv_node(node)).visit(syntax_tree.root_node)
        # print(ast.dump(syntax_tree.root_node, indent=1))
        # print(ast.unparse(syntax_tree.root_node))
        return syntax_tree