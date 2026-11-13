"""Prototipo ejecutable de la gramatica, código intermedio (Polaca Inversa) y Assembler."""

from dataclasses import asdict, dataclass

from .assembler import AssemblerGenerator
from .intermediate import IntermediateGenerator, RpnStep
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
    rpn: list[RpnStep]
    assembler: str

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
                      key=lambda node: node.order)

    def to_dict(self):
        return {
            "ok": self.ok,
            "tokens": to_data(self.tokens),
            "symbols": to_data(self.symbols.entries),
            "tree": to_data(self.tree),
            "structures": [{"kind": n.kind, "line": n.line, "column": n.column}
                           for n in self.structures],
            "rpn": [asdict(step) for step in self.rpn],
            "assembler": self.assembler,
            "diagnostics": to_data(self.diagnostics),
        }


def analyze(source: str, check_semantics: bool = True) -> Analysis:
    """Ejecuta análisis léxico, sintáctico, semántico, Polaca Inversa y Assembler."""
    source = source.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    symbols = SymbolTable()
    diagnostics: list[Diagnostic] = []
    lexer = ProjectLexer(symbols, diagnostics)
    tokens = list(lexer.tokenize(source))
    tree = GrammarParser(symbols, diagnostics, source).parse(iter(tokens))

    rpn_steps: list[RpnStep] = []
    asm_code = ""
    has_syntax_errors = any(d.severity == "error" for d in diagnostics)
    if check_semantics and tree is not None and not has_syntax_errors:
        inter = IntermediateGenerator(symbols, diagnostics)
        rpn_steps = inter.generate(tree)
        asm_gen = AssemblerGenerator(symbols, diagnostics)
        asm_code = asm_gen.translate(rpn_steps)
        if any(d.severity == "error" for d in diagnostics):
            asm_code = ""

    diagnostics.sort(key=lambda d: (d.line, d.column, d.phase))
    return Analysis(source, [t.value for t in tokens], symbols, tree, diagnostics, rpn_steps, asm_code)