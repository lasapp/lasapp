from dataclasses import dataclass
from dataclasses_json import dataclass_json

@dataclass_json
@dataclass
class SyntaxNode:
    node_id: str
    first_byte: int
    last_byte: int
    source_text: str

    def __hash__(self) -> int:
        return self.node_id.__hash__()
    def __eq__(self, other) -> bool:
        if isinstance(other, SyntaxNode):
            return self.node_id == other.node_id
        return False

@dataclass_json 
@dataclass
class ControlDependency:
    node: SyntaxNode
    kind: str
    control_node: SyntaxNode
    body: list[SyntaxNode]

@dataclass_json 
@dataclass
class CallGraphNode:
    caller: SyntaxNode
    called: list[SyntaxNode]


@dataclass_json
@dataclass
class Model:
    name: str
    node: SyntaxNode

@dataclass_json
@dataclass
class DistributionParam:
    name: str
    node: SyntaxNode

@dataclass_json
@dataclass
class Distribution:
    name: str
    node: SyntaxNode
    params: list[DistributionParam]

@dataclass_json
@dataclass
class RandomVariable:
    node: SyntaxNode
    name: str
    address_node: SyntaxNode
    distribution: Distribution
    is_observed: bool
    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, RandomVariable):
            return self.node.node_id == __value.node.node_id
        return False
    def __hash__(self) -> int:
        return hash(self.node.node_id)
    def __repr__(self) -> str:
        return f"RandomVariable({self.node.source_text})"


@dataclass_json
@dataclass
class Interval:
    low: str
    high: str


@dataclass_json
@dataclass
class SymbolicExpression:
    expr: str
