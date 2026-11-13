"""Datos del compilador: apariciones, simbolos, diagnosticos y arbol sintactico."""

from dataclasses import asdict, dataclass, field
from itertools import count


_node_counter = count(1)


@dataclass(frozen=True)
class Diagnostic:
    phase: str
    code: str
    message: str
    line: int
    column: int
    severity: str = "error"


@dataclass
class Lexeme:
    type: str
    text: str
    line: int
    column: int
    value: str
    symbol: int | None = None


@dataclass
class Symbol:
    reference: int
    category: str
    text: str
    data_type: str | None
    value: str
    usage: str | None = None
    attrs: dict = field(default_factory=dict)


class SymbolTable:
    """Tabla de Símbolos léxica y semántica."""

    def __init__(self):
        self.entries: list[Symbol] = []
        self._references: dict[tuple, int] = {}

    def intern(self, category, text, data_type=None, value=None, usage=None, **attrs):
        key = (category, data_type, text)
        if key not in self._references:
            reference = len(self.entries) + 1
            default_usage = usage or (
                "constante" if category == "constant"
                else "cadena" if category == "string"
                else "identificador"
            )
            sym = Symbol(
                reference=reference,
                category=category,
                text=text,
                data_type=data_type,
                value=text if value is None else str(value),
                usage=default_usage,
                attrs=dict(attrs),
            )
            self._references[key] = reference
            self.entries.append(sym)
        else:
            sym = self.get(self._references[key])
            if data_type and not sym.data_type:
                sym.data_type = data_type
            if usage and (not sym.usage or sym.usage == "identificador"):
                sym.usage = usage
            if attrs:
                sym.attrs.update(attrs)
        return self._references[key]

    def get(self, reference: int) -> Symbol:
        return self.entries[reference - 1]

    def find_by_text(self, text: str) -> Symbol | None:
        for entry in self.entries:
            if entry.text == text:
                return entry
        return None

    def rebuild_without_unscoped_identifiers(self):
        """Elimina entradas léxicas crudas de identificadores que fueron reemplazadas por nombres con ámbito."""
        kept = [
            e for e in self.entries
            if not (e.category == "identifier" and e.usage == "identificador" and ":" not in e.text)
        ]
        self.entries = []
        self._references = {}
        for idx, entry in enumerate(kept, start=1):
            entry.reference = idx
            self.entries.append(entry)
            self._references[(entry.category, entry.data_type, entry.text)] = idx


@dataclass(frozen=True)
class Node:
    kind: str
    children: tuple
    line: int
    column: int
    order: int = 0


def make_node(kind, parts):
    children = []
    for part in parts:
        if isinstance(part, list):
            children.extend(part)
        elif part is not None:
            children.append(part)
    first = next((p for p in children if isinstance(p, (Node, Lexeme))), None)
    return Node(
        kind,
        tuple(children),
        first.line if first else 1,
        first.column if first else 1,
        next(_node_counter),
    )


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