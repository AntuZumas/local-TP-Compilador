"""Prototipo ejecutable de la gramatica"""

from dataclasses import dataclass

from .lexer import ProjectLexer
from .model import Diagnostic, Lexeme, Node, SymbolTable, to_data, walk_nodes
from .parser import GrammarParser, grammar_report


@dataclass
class Analysis:
    source: str
    tokens: list[Lexeme]
    symbols: SymbolTable
    tree: Node | None
    diagnostics: list[Diagnostic]

    @property
    def ok(self):
        return self.tree is not None and not any(
            d.severity == "error" for d in self.diagnostics)

    @property
    def structures(self):
        selected = {
            "variable_declaration", "object_declaration", "comptime_declaration",
            "function_declaration", "class_declaration", "method_declaration",
            "attribute_declaration", "assignment", "inline_assignment", "output",
            "return", "if", "repeat", "call_statement", "import", "export", "inheritance",
        }
        return sorted((node for node in walk_nodes(self.tree) if node.kind in selected),
                      key=lambda node: (node.line, node.column))

    def to_dict(self):
        return {"ok": self.ok, "tokens": to_data(self.tokens),
                "symbols": to_data(self.symbols.entries), "tree": to_data(self.tree),
                "structures": [{"kind": n.kind, "line": n.line, "column": n.column}
                               for n in self.structures],
                "diagnostics": to_data(self.diagnostics)}


def analyze(source: str) -> Analysis:
    """Cada archivo tiene su propio lexer/parser/TS. No ejecuta el programa."""
    source = source.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    symbols = SymbolTable()
    diagnostics = []
    lexer = ProjectLexer(symbols, diagnostics)
    # Batch para conservar una instantánea del flujo y facilitar la inspección.
    tokens = list(lexer.tokenize(source))
    tree = GrammarParser(symbols, diagnostics, source).parse(iter(tokens))
    diagnostics.sort(key=lambda d: (d.line, d.column, d.phase))
    return Analysis(source, [t.value for t in tokens], symbols, tree, diagnostics)
