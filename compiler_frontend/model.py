"""Datos del prototipo: apariciones, simbolos, diagnosticos y arbol sintactico."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Diagnostic:
    phase: str
    code: str
    message: str
    line: int
    column: int
    severity: str = "error"


@dataclass(frozen=True)
class Lexeme:
    type: str
    text: str
    line: int
    column: int
    value: str
    symbol: int | None = None


@dataclass(frozen=True)
class Symbol:
    reference: int
    category: str
    text: str
    data_type: str | None
    value: str


class SymbolTable:
    """Registro léxico. No resuelve declaraciones ni ámbitos semánticos."""

    def __init__(self):
        self.entries: list[Symbol] = []
        self._references: dict[tuple, int] = {}

    def intern(self, category, text, data_type=None, value=None):
        key = (category, data_type, text)
        if key not in self._references:
            reference = len(self.entries) + 1
            self._references[key] = reference
            self.entries.append(Symbol(reference, category, text, data_type,
                                       text if value is None else str(value)))
        return self._references[key]


@dataclass(frozen=True)
class Node:
    kind: str
    children: tuple
    line: int
    column: int


def make_node(kind, parts):
    children = []
    for part in parts:
        if isinstance(part, list):
            children.extend(part)
        elif part is not None:
            children.append(part)
    first = next((p for p in children if isinstance(p, (Node, Lexeme))), None)
    return Node(kind, tuple(children), first.line if first else 1,
                first.column if first else 1)


def walk_nodes(tree):
    """Recorrido iterativo para listas largas de sentencias."""
    pending = [tree]
    while pending:
        item = pending.pop()
        if isinstance(item, Node):
            yield item
            pending.extend(reversed(item.children))


def to_data(value):
    if isinstance(value, Node):
        return {"kind": value.kind, "line": value.line, "column": value.column,
                "children": [to_data(child) for child in value.children]}
    if isinstance(value, (Lexeme, Symbol, Diagnostic)):
        return asdict(value)
    if isinstance(value, (tuple, list)):
        return [to_data(item) for item in value]
    return value
