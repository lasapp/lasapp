import lasapp.server_interface as server_interface
from enum import Enum
from typing import Dict, Optional

class DistributionType(Enum):
    Continuous=1
    Discrete=2

class DistributionDimensionality(Enum):
    Univariate=1
    Multivariate=2

class Constraint:
    pass
class GreaterThan(Constraint):
    def __init__(self, low):
        self.low = low
    def __repr__(self):
        return f"> {self.low}"
class GreaterEqThan(Constraint):
    def __init__(self, low):
        self.low = low
    def __repr__(self):
        return f">= {self.low}"
class Interval(Constraint):
    def __init__(self, low, high, left_open=False, right_open=False, open=False):
        self.low = low
        self.high = high
        self.left_open = left_open or open
        self.right_open = right_open or open
    def __repr__(self):
        return f"{'(' if self.left_open else '['}{self.low}, {self.high}{')' if self.right_open else ']'}"
    def is_subset(self, other):
        return other.low <= self.low and self.high <= other.high
class Real(Constraint):
    def __repr__(self):
        return "Real"
    
class DiscreteGreaterEqThan(Constraint):
    def __init__(self, x):
        self.x = x
    def __repr__(self):
        return f"{self.x}, ..."
class DiscreteInterval(Constraint):
    def __init__(self, low, high, left_open=False, right_open=False, open=False):
        self.low = low
        self.high = high
        self.left_open = left_open or open
        self.right_open = right_open or open
    def __repr__(self):
        return f"[{self.low}, ..., {self.high}]"
    def is_subset(self, other):
        return other.low <= self.low and self.high <= other.high
class Integer(Constraint):
    def __repr__(self):
        return "Integer"
    
class Vector(Constraint):
    def __repr__(self):
        return "Vector"
    
class Matrix(Constraint):
    def __repr__(self):
        return "Matrix"
    
class PositiveDefinite(Constraint):
    def __repr__(self):
        return "PositiveDefinite"
    
class Simplex(Constraint):
    def __repr__(self):
        return "Simplex"


def to_interval(constraint: Constraint):
    if isinstance(constraint, GreaterThan):
        return Interval(low=constraint.low, left_open=True, high=float('inf'), right_open=True)
    if isinstance(constraint, GreaterEqThan):
        return Interval(low=constraint.low, left_open=False, high=float('inf'), right_open=True)
    if isinstance(constraint, Real):
        return Interval(low=float('-inf'), left_open=True, high=float('inf'), right_open=True)
    if isinstance(constraint, Interval):
        return constraint
    
    if isinstance(constraint, DiscreteGreaterEqThan):
        return DiscreteInterval(low=constraint.x, left_open=False, high=float('inf'), right_open=True)
    if isinstance(constraint, Integer):
        return DiscreteInterval(low=float('-inf'), left_open=True, high=float('inf'), right_open=True)
    if isinstance(constraint, DiscreteInterval):
        return constraint

    return None
    # raise ValueError(f"Could not convert to interval: {constraint}.")


class DistributionProperties:
    def __init__(self, 
                name: str,
                param_constraints: Dict[str, Constraint],
                support: Constraint,
                type: DistributionType,
                dimensionality: DistributionDimensionality
        ) -> None:
        self.name = name
        self.param_constraints = param_constraints
        self.support = support
        self.type = type
        self.dimensionality = dimensionality

    def is_discrete(self):
        return self.type == DistributionType.Discrete

    def is_continuous(self):
        return self.type == DistributionType.Continuous
    
    def is_univariate(self):
        return self.dimensionality == DistributionDimensionality.Univariate
    
    def is_multivariate(self):
        return self.dimensionality == DistributionDimensionality.Multivariate

DISTRIBUTIONS = [
    DistributionProperties(
        name='Beta',
        param_constraints={'alpha': GreaterThan(0.), 'beta': GreaterThan(0.)},
        support=Interval(0., 1.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Cauchy',
        param_constraints={'location': Real(), 'scale': GreaterThan(0.)},
        support=Real(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='HalfCauchy',
        param_constraints={'scale': GreaterThan(0.)},
        support=GreaterThan(0.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='LogNormal',
        param_constraints={'location': Real(), 'scale': GreaterThan(0.)},
        support=Real(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Normal',
        param_constraints={'location': Real(), 'scale': GreaterThan(0.)},
        support=Real(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='HalfNormal',
        param_constraints={'scale': GreaterThan(0.)},
        support=GreaterThan(0.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='ChiSquared',
        param_constraints={'df': DiscreteGreaterEqThan(1)},
        support=GreaterEqThan(0.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Exponential',
        param_constraints={'scale': GreaterThan(0.), 'rate': GreaterThan(0.)},
        support=GreaterEqThan(0.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Gamma',
        param_constraints={'shape': GreaterThan(0.), 'scale': GreaterThan(0.), 'rate': GreaterThan(0.)},
        support=GreaterThan(0.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='InverseGamma',
        param_constraints={'shape': GreaterThan(0.), 'scale': GreaterThan(0.), 'rate': GreaterThan(0.)},
        support=GreaterThan(0.),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='StudentT',
        param_constraints={'df': GreaterThan(0.), 'location': Real(), 'scale': GreaterThan(0.)},
        support=Real(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Uniform',
        param_constraints={'a': Real(), 'b': Real()},
        support=Interval('a', 'b'),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='DiscreteUniform',
        param_constraints={'a': Integer(), 'b': Integer()},
        support=DiscreteInterval('a', 'b'),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Bernoulli',
        param_constraints={'p': Interval(0., 1.)},
        support=DiscreteInterval(0, 1),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Categorical',
        param_constraints={'p': 'simplex'},
        support=DiscreteInterval(0, 'len(p)-1'),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Geometric',
        param_constraints={'p': Interval(0., 1.)},
        support=DiscreteGreaterEqThan(0),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Binomial',
        param_constraints={'p': Interval(0., 1.), 'n': DiscreteGreaterEqThan(0)},
        support=DiscreteInterval(0, 'n'),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Dirac',
        param_constraints={'location': Real()},
        support=DiscreteInterval('location', 'location'),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Poisson',
        param_constraints={'rate': GreaterEqThan(0.)},
        support=DiscreteGreaterEqThan(0),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='Multinomial',
        param_constraints={'n': DiscreteGreaterEqThan(1), 'p': Simplex()},
        support=DiscreteInterval(0, 'n'),
        type=DistributionType.Discrete,
        dimensionality=DistributionDimensionality.Univariate
    ),
    DistributionProperties(
        name='MultivariateNormal',
        param_constraints={'location': Real(), 'covariance': PositiveDefinite(), 'precision': PositiveDefinite()},
        support=Vector(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Multivariate
    ),
    DistributionProperties(
        name='Dirichlet',
        param_constraints={'alpha': GreaterThan(0.)},
        support=Simplex(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Multivariate
    ),
    DistributionProperties(
        name='Wishart',
        param_constraints={'df': GreaterThan(0.), 'scale': PositiveDefinite()},
        support=Matrix(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Multivariate
    ),
    DistributionProperties(
        name='InverseWishart',
        param_constraints={'df': GreaterThan(0.), 'scale': PositiveDefinite()},
        support=Matrix(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Multivariate
    ),
    DistributionProperties(
        name='LKJCholesky',
        param_constraints={'size': DiscreteGreaterEqThan(1), 'shape': GreaterThan(0.)},
        support=Matrix(),
        type=DistributionType.Continuous,
        dimensionality=DistributionDimensionality.Multivariate
    ),
]

_DISTRIBUTION_DICT = {dist.name: dist for dist in DISTRIBUTIONS}


def infer_distribution_properties(random_variable: server_interface.RandomVariable) -> Optional[DistributionProperties]:
    return _DISTRIBUTION_DICT.get(random_variable.distribution.name, None)