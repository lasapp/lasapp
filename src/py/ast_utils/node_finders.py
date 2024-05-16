import ast
from ppls import PPL, VariableDefinition, Model
from .node_finder import NodeFinder


def VariableDefinitionCollector(ppl):
    return NodeFinder(
        lambda node: ppl.is_random_variable_definition(node),
        lambda node: VariableDefinition(node))

def find_model_or_guide(root_node: ast.Module, ppl: PPL, keyword: str):
    assert isinstance(root_node, ast.Module), type(root_node)
    # find global variable model = ... specifying model name
    model_name = ""
    for stmt in root_node.body:
        match stmt:
            case ast.Assign(targets=[ast.Name(id=_keyword)], value=ast.Name(id=name)):
                if _keyword == keyword:
                    model_name = name
                    break

    if model_name == "":
        print(f"{keyword.title()} name not found. Defaulting to '{keyword}'.")
        model_name = keyword

    result = NodeFinder(
        lambda node: ppl.is_model(node) and ppl.get_model_name(node) == model_name,
        lambda node: node
    ).visit(root_node)

    assert len(result) > 0, f"No model {keyword} definition found."
    assert len(result) == 1, f"Multiple {keyword} definition found."

    return Model(model_name, result[0])
    
def find_model(root_node: ast.Module, ppl: PPL):
    return find_model_or_guide(root_node, ppl, "model")

def find_guide(root_node: ast.Module, ppl: PPL):
    return find_model_or_guide(root_node, ppl, "guide")

def get_user_defined_functions(root_node: ast.AST):
    functions = NodeFinder(
        lambda node: isinstance(node, ast.FunctionDef),
        lambda node: node,
        visit_matched_nodes=True
        ).visit(root_node)
    return functions