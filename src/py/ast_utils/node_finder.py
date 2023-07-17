import ast

class NodeFinder(ast.NodeVisitor):
    def __init__(self, predicate, map, visit_matched_nodes=False, visit_predicate=None):
        super().__init__()
        self.predicate = predicate
        self.map = map
        if visit_predicate is None:
            if visit_matched_nodes:
                visit_predicate = lambda _: True
            else:
                visit_predicate = lambda node: not predicate(node)
        self.visit_predicate = visit_predicate
        self.result = []

    def visit(self, node):
        if self.predicate(node):
            self.result.append(self.map(node))
        if self.visit_predicate(node):
            self.generic_visit(node)
            
        return self.result