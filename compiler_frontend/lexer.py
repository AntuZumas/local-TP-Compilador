"""Lexico de apoyo SLY. La alternativa de matrices sigue pendiente de catedra."""

import re
from decimal import Decimal, DecimalException

from sly import Lexer

from .model import Diagnostic, Lexeme, SymbolTable


reserved = {word.upper(): word.upper() for word in (
    "if else end_if begin end pout ret class function integer singlef repeat "
    "until comptime import from export to extends toi"
).split()}
token_types = set(reserved.values()) | {
    "ID", "INT", "FLOAT", "STRING", "ASSIGN", "GE", "LE", "EQ", "NE"
}
integer_pattern = re.compile(r"[0-9]+\$i\Z")
float_pattern = re.compile(r"[0-9]*\.[0-9]+(?:s[+-]?[0-9]+)?\Z")
single_min = Decimal("1.17549435e-38")
single_max = Decimal("3.40282347e38")


class ProjectLexer(Lexer):
    tokens = token_types
    literals = set("+-*/=<>(),;[].")
    ignore = " \t"

    # Prefijos largos antes de los cortos: // antes de /; == antes de =.
    ignore_comment = r"//[^\n]*"
    ASSIGN = r":="
    GE = r">="
    LE = r"<="
    EQ = r"=="
    NE = r"!="

    def __init__(self, symbols: SymbolTable, diagnostics: list[Diagnostic]):
        self.symbols = symbols
        self.diagnostics = diagnostics
        self.source = ""

    def column(self, index):
        return index - self.source.rfind("\n", 0, index)

    def report(self, token, code, message, severity="error"):
        self.diagnostics.append(Diagnostic("lexical", code, message,
                                           token.lineno, self.column(token.index), severity))

    def wrap(self, token, value=None, symbol=None):
        raw = token.value
        token.value = Lexeme(token.type, raw, token.lineno, self.column(token.index),
                             raw if value is None else str(value), symbol)
        return token

    @_(r"\n+")
    def ignore_newline(self, token):
        self.lineno += len(token.value)

    @_(r'"[^"]*(?:"|\Z)')
    def STRING(self, token):
        raw = token.value
        self.lineno += raw.count("\n")
        if len(raw) < 2 or not raw.endswith('"'):
            self.report(token, "L_UNCLOSED_STRING", "Cadena sin comillas de cierre.")
            return None
        value = raw[1:-1].replace("\n", "")
        ref = self.symbols.intern("string", value, value=value)
        return self.wrap(token, value, ref)

    # Reconocer tambien candidatos incorrectos evita ocultar un sufijo invalido.
    @_(r"(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[sSdD][+-]?[0-9]*)?(?:\$[A-Za-z]*)?[A-Za-z0-9_]*")
    def INT(self, token):
        raw = token.value
        if integer_pattern.fullmatch(raw):
            digits = raw[:-2].lstrip("0") or "0"
            if len(digits) > 5 or int(digits) > 32768:
                self.report(token, "L_INTEGER_RANGE", "Magnitud INTEGER mayor que 32768.")
                return None
            value = str(int(digits))
            # El alta en TS se realiza en el parser una vez resuelto el signo.
            return self.wrap(token, value, None)
        if float_pattern.fullmatch(raw):
            try:
                number = Decimal(raw.replace("s", "e"))
                magnitude = number.copy_abs()
                valid = magnitude == 0 or single_min < magnitude < single_max
            except (DecimalException, ValueError):
                valid = False
            if not valid:
                self.report(token, "L_FLOAT_RANGE", "Constante fuera del rango SINGLEF adoptado.")
                return None
            token.type = "FLOAT"
            # El alta en TS se realiza en el parser una vez resuelto el signo.
            return self.wrap(token, str(number), None)
        self.report(token, "L_NUMBER_FORMAT", f"Constante mal formada: {raw}.")
        return None

    @_(r"[A-Za-z_][A-Za-z0-9_]*")
    def ID(self, token):
        raw = token.value
        if raw.upper() in reserved:
            token.type = reserved[raw.upper()]
            return self.wrap(token, raw.lower())
        if not re.fullmatch(r"[a-z][a-z0-9_]*", raw):
            self.report(token, "L_IDENTIFIER", f"Identificador inválido: {raw}.")
            return None
        name = raw[:22]
        if len(raw) > 22:
            self.report(token, "L_TRUNCATED_ID", f"Identificador {raw} truncado a {name}.",
                        "warning")
        ref = self.symbols.intern("identifier", name)
        return self.wrap(token, name, ref)

    def error(self, token):
        self.report(token, "L_CHARACTER", f"Carácter inválido: {token.value[0]!r}.")
        self.index += 1

    def tokenize(self, text, lineno=1, index=0):
        self.source = text
        for token in super().tokenize(text, lineno, index):
            if not isinstance(token.value, Lexeme):
                self.wrap(token)
            yield token