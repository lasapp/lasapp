
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
        dist_name = self.distribution.name
        s += f"    Parameter {self.parameter.name} of {dist_name} distribution has constraint {self.constraint}, but values are estimated to be in {self.estimated_range}.\n"
        return s
    

class VerficationFailedConstraint:
    def __init__(self, random_variable, parameter, constraint, distribution):
        self.random_variable = random_variable
        self.parameter = parameter
        self.constraint = constraint
        self.distribution = distribution
    
    def __repr__(self) -> str:
        rv_text = highlight_in_node(self.random_variable.node, self.parameter.node.first_byte, self.parameter.node.last_byte, "101m")
        s = f"Could not verify constraint in \"{rv_text}\":\n"
        dist_name = self.distribution.name
        s += f"    Parameter {self.parameter.name} of {dist_name} distribution has constraint {self.constraint} which could not be verified.\n"
        return s
    

class VerficationFailedProperties:
    def __init__(self, random_variable):
        self.random_variable = random_variable
    def __repr__(self) -> str:
        rv_text = self.random_variable.node.source_text
        s = f"Could not verify constraints in \"{rv_text}\":\n"
        dist_name = self.random_variable.distribution.name
        s += f"    Could not infer properties of distribution {dist_name}.\n"
        return s



def get_param_with_name(distribution: lasapp.server_interface.Distribution, name: str):
    for param in distribution.params:
        if param.name == name:
            return param
    return None

def Interval(program: lasapp.ProbabilisticProgram,
             mask: dict[lasapp.SyntaxNode, lasapp.Interval],
             rv: lasapp.RandomVariable,
             _support: dists.Constraint):
    support = dists.to_interval(_support)
    if support is not None:
        # if the support contains a symbol, we statically evaluate the support first
        
        if isinstance(support.low, dists.ParamDependentBound):
            # parameter dependent support
            param = get_param_with_name(rv.distribution, support.low.param)
            if param is not None:
                estimated_range = program.estimate_value_range(
                    expr=param.node,
                    mask=mask # mask up to now, rvs are sorted
                )
                support.low = float(estimated_range.low) # probably estimated_range.low == estimated_range.high
            else:
                return None

        if isinstance(support.high, dists.ParamDependentBound):
            # parameter dependent support
            param = get_param_with_name(rv.distribution, support.high.param)
            if param is not None:
                estimated_range = program.estimate_value_range(
                    expr=param.node,
                    mask=mask # mask up to now, rvs are sorted
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
    mask = {}
    # TODO: this has to be done in correct order, because we have to know the support of all parent rvs.
    for rv in random_variables:
        properties = lasapp.infer_distribution_properties(rv)
        if properties is not None:
            interval = Interval(program, mask, rv, properties.support)
            if interval is not None:
                mask[rv.node] = interval
            else:
                print(f"Could not mask support as interval for {rv.node.source_text}")
        else:
            print(f"Could not find properties for {rv.node.source_text}")
    
    # print("Mask:")
    # for (rv, support) in mask.items():
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
                    if constraint is None: # we don't support strings like simplex yet
                        violations.append(VerficationFailedConstraint(rv, param, properties.param_constraints[param.name], properties))
                        continue

                    estimated_range = program.estimate_value_range(
                        expr=param.node,
                        mask=mask
                    )
                    estimated_range = dists.Interval(low=float(estimated_range.low),high=float(estimated_range.high))

                    # compare estimated value range with constraint
                    if not estimated_range.is_subset_of(constraint):
                        constraint.left_open = False
                        constraint.right_open = False
                        violations.append(ConstraintViolation(rv, param, constraint, estimated_range, properties))
        else:
            violations.append(VerficationFailedProperties(rv))


    return violations

from .utils import highlight_in_node

def get_source_highlight_for_violation(v):
    rv_text = highlight_in_node(v.random_variable.node, v.parameter.node.first_byte, v.parameter.node.last_byte, "101m")
    s = f"Possible constraint violation in \"{rv_text}\":\n"
    dist_name = v.distribution.name
    s += f"    Parameter {v.parameter.name} of {dist_name} distribution has constraint {v.constraint}, but values are estimated to be in {v.estimated_range}."
    return s
    
def print_source_highlight_violations(violations):
    print()
    
    if len(violations) == 0:
        print("No constraint violations.")
        print()

    violation_strs = set(get_source_highlight_for_violation(v) for v in violations if not isinstance(v, (VerficationFailedConstraint,VerficationFailedProperties)))
    for (i, v) in enumerate(violation_strs):
        print(f"{i+1:2d}. {v}")
        print()
