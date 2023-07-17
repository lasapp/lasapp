
import lasapp
import lasapp.distributions as dists
from .utils import is_descendant

class ConstraintViolation:
    def __init__(self, random_variable, parameter, constraint, estimated_range, distribution):
        self.random_variable = random_variable
        self.parameter = parameter
        self.constraint = constraint
        self.estimated_range = estimated_range
        self.distribution = distribution

    def __repr__(self) -> str:
        rv_text = highlight_in_node(self.random_variable.node, self.parameter.node.first_byte, self.parameter.node.last_byte, "101m")
        s = f"Possible constraint violation in \"{rv_text}\":\n"
        dist_name = self.distribution["name"]
        s += f"    Parameter {self.parameter.name} of {dist_name} distribution has constraint {self.constraint}, but values are estimated to be in {self.estimated_range}.\n"
        return s


def get_param_with_name(distribution: lasapp.server_interface.Distribution, name: str):
    for param in distribution.params:
        if param.name == name:
            return param
    return None

def Interval(program: lasapp.ProbabilisticProgram,
             assumptions: dict[lasapp.RandomVariable, lasapp.Interval],
             rv: lasapp.RandomVariable,
             support: dists.Constraint):
    
    support = dists.to_interval(support)
    if support is not None:
        # if the support contains a symbol, we statically evaluate the support first
        
        if isinstance(support.low, str):
            # parameter dependent support
            param = get_param_with_name(rv.distribution, support.low)
            if param is not None: # we don't support expressions over params yet like len(p)-1
                estimated_range = program.estimate_value_range(
                    expr=param.node,
                    assumptions=assumptions # assumptions up to now, rvs are sorted
                )
                support.low = float(estimated_range.low) # probably estimated_range.low == estimated_range.high
            else:
                return None

        if isinstance(support.high, str):
            # parameter dependent support
            param = get_param_with_name(rv.distribution, support.high)
            if param is not None: # we don't support expressions over params yet like len(p)-1
                estimated_range = program.estimate_value_range(
                    expr=param.node,
                    assumptions=assumptions # assumptions up to now, rvs are sorted
                )
                support.high = float(estimated_range.high) # probably estimated_range.low == estimated_range.high
            else:
                return None
            
        return lasapp.Interval(low=str(support.low), high=str(support.high))
    
    return None

def validate_distribution_arg_constraints(program: lasapp.ProbabilisticProgram):
    model = program.get_model()
    random_variables = [rv for rv in program.get_random_variables() if is_descendant(model.node, rv.node)]

    # We abstract the value of a random variable by its support.
    assumptions = {}
    for rv in random_variables:
        properties = lasapp.infer_distribution_properties(rv)
        if properties is not None:
            interval = Interval(program, assumptions, rv, properties.support)
            if interval is not None:
                assumptions[rv] = interval
    
    # print("Assumptions:")
    # for (rv, support) in assumptions:
    #     print(rv.name, support)
    # print()

    # For each variable and each of its parameters,
    # we compare the parameter constraints with the static interval evaluation
    violations = []
    for rv in random_variables:
        properties = lasapp.infer_distribution_properties(rv)
        if properties is not None:
            for param in rv.distribution.params:
                if param.name in properties.param_constraints:
                    constraint = dists.to_interval(properties.param_constraints[param.name])
                    if constraint is None: # we don't support strings like simplex
                        continue

                    estimated_range = program.estimate_value_range(
                        expr=param.node,
                        assumptions=assumptions
                    )
                    estimated_range = dists.Interval(low=float(estimated_range.low),high=float(estimated_range.high))


                    # compare estimated value range with constraint
                    if estimated_range.low < constraint.low or estimated_range.high > constraint.high:
                        constraint.left_open = False
                        constraint.right_open = False
                        violations.append(ConstraintViolation(rv, param, constraint, estimated_range, properties))

    return violations

from .utils import highlight_in_node

def print_source_highlight_violations(violations):
    print()
    
    if len(violations) == 0:
        print("No constraint violations.")
        print()

    for (i, v) in enumerate(violations):
        rv_text = highlight_in_node(v.random_variable.node, v.parameter.node.first_byte, v.parameter.node.last_byte, "101m")
        print(f"{i+1:2d}. Possible constraint violation in \"{rv_text}\":")
        dist_name = v.distribution.name
        print(f"    Parameter {v.parameter.name} of {dist_name} distribution has constraint {v.constraint}, but values are estimated to be in {v.estimated_range}.")
        print()


