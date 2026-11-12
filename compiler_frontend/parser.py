"""Gramática LALR(1) ejecutable. Cada decorador es una producción del lenguaje.

Las familias plain_* propagan la prohibición de asignaciones internas anidadas.
Las familias global_* y function_* impiden RET fuera de funciones/metodos.
"""

from dataclasses import replace
from decimal import Decimal

from sly import Parser

from .lexer import ProjectLexer
from .model import Diagnostic, Node, make_node


class GrammarParser(Parser):
    tokens = ProjectLexer.tokens
    start = "program"

    def __init__(self, symbols, diagnostics, source):
        self.symbols = symbols
        self.diagnostics = diagnostics
        self.source = source
        self.last_error = (1, 1)

    def node(self, kind, production):
        return make_node(kind, [production[i] for i in range(len(production))])

    # Programa y declaraciones. Declaraciones opcionales; cuerpos no vacíos.
    @_('ID declarations BEGIN global_statements END')
    def program(self, p):
        return self.node("program", p)

    @_('declarations declaration', '')
    def declarations(self, p):
        return p[0] + [p[1]] if len(p) else []

    @_('variable_declaration', 'object_declaration', 'function_declaration',
       'class_declaration', 'comptime_declaration')
    def declaration(self, p):
        return p[0]

    @_('INTEGER', 'SINGLEF')
    def basic_type(self, p):
        return p[0]

    @_('basic_type', 'ID')
    def parameter_type(self, p):
        return p[0]

    @_('id_list "," ID', 'ID')
    def id_list(self, p):
        return p[0] + [p[2]] if len(p) == 3 else [p[0]]

    @_('basic_type id_list ";"')
    def variable_declaration(self, p):
        return self.node("variable_declaration", p)

    @_('ID id_list ";"')
    def object_declaration(self, p):
        return self.node("object_declaration", p)

    @_('COMPTIME basic_type id_list ";"')
    def comptime_declaration(self, p):
        return self.node("comptime_declaration", p)

    @_('basic_type FUNCTION ID "(" parameters ")" declarations BEGIN function_statements END ";"')
    def function_declaration(self, p):
        return self.node("function_declaration", p)

    @_('parameters "," parameter', 'parameter')
    def parameters(self, p):
        return p[0] + [p[2]] if len(p) == 3 else [p[0]]

    @_('parameter_type ID')
    def parameter(self, p):
        return self.node("parameter", p)

    # Clases: IMPORT en cabecera, EXPORT en miembros, EXTENDS en el cuerpo.
    @_('CLASS ID import_opt BEGIN members END ";"')
    def class_declaration(self, p):
        return self.node("class_declaration", p)

    @_('IMPORT FROM id_list', '')
    def import_opt(self, p):
        return self.node("import", p) if len(p) else None

    @_('members member', 'member')
    def members(self, p):
        return p[0] + [p[1]] if len(p) == 2 else [p[0]]

    @_('attribute_declaration', 'method_declaration', 'inheritance')
    def member(self, p):
        return p[0]

    @_('basic_type id_list export_opt ";"')
    def attribute_declaration(self, p):
        return self.node("attribute_declaration", p)

    @_('EXPORT TO id_list', '')
    def export_opt(self, p):
        return self.node("export", p) if len(p) else None

    @_('basic_type ID "(" parameters ")" declarations BEGIN function_statements END ";" method_export_opt')
    def method_declaration(self, p):
        return self.node("method_declaration", p)

    @_('EXPORT TO id_list ";"', '')
    def method_export_opt(self, p):
        return self.node("export", p) if len(p) else None

    @_('EXTENDS id_list ";"')
    def inheritance(self, p):
        return self.node("inheritance", p)

    # RET solo está en la familia function_* y se propaga a sus bloques.
    @_('global_statements global_statement', 'global_statement')
    def global_statements(self, p):
        return p[0] + [p[1]] if len(p) == 2 else [p[0]]

    @_('function_statements function_statement', 'function_statement')
    def function_statements(self, p):
        return p[0] + [p[1]] if len(p) == 2 else [p[0]]

    @_('simple_statement', 'global_if', 'global_repeat')
    def global_statement(self, p):
        return p[0]

    @_('simple_statement', 'return_statement', 'function_if', 'function_repeat')
    def function_statement(self, p):
        return p[0]

    @_('assignment ";"', 'output ";"', 'invocation ";"')
    def simple_statement(self, p):
        return self.node("call_statement", p) if p[0].kind == "invocation" else p[0]

    @_('error ";"')
    def simple_statement(self, p):
        # SLY desapila hasta aceptar error y descarta hasta el punto y coma.
        self.errok()
        return Node("invalid_statement", (), *self.last_error)

    @_('ID ASSIGN expression', 'attribute "=" expression')
    def assignment(self, p):
        return self.node("assignment", p)

    @_('POUT "(" expression ")"', 'POUT "(" STRING ")"')
    def output(self, p):
        return self.node("output", p)

    @_('RET "(" expression ")" ";"')
    def return_statement(self, p):
        return self.node("return", p)

    @_('global_statement', 'BEGIN global_statements END')
    def global_block(self, p):
        return self.node("block", p)

    @_('function_statement', 'BEGIN function_statements END')
    def function_block(self, p):
        return self.node("block", p)

    @_('IF "(" condition ")" global_block global_else END_IF ";"')
    def global_if(self, p):
        return self.node("if", p)

    @_('ELSE global_block', '')
    def global_else(self, p):
        return self.node("else", p) if len(p) else None

    @_('IF "(" condition ")" function_block function_else END_IF ";"')
    def function_if(self, p):
        return self.node("if", p)

    @_('ELSE function_block', '')
    def function_else(self, p):
        return self.node("else", p) if len(p) else None

    @_('REPEAT global_block UNTIL "(" condition ")" ";"')
    def global_repeat(self, p):
        return self.node("repeat", p)

    @_('REPEAT function_block UNTIL "(" condition ")" ";"')
    def function_repeat(self, p):
        return self.node("repeat", p)

    @_('expression comparator expression')
    def condition(self, p):
        return self.node("comparison", p)

    @_('">"', '"<"', 'GE', 'LE', 'EQ', 'NE')
    def comparator(self, p):
        return p[0]

    # Precedencia y asociatividad expresadas estructuralmente, sin %prec.
    @_('expression "+" term', 'expression "-" term', 'term')
    def expression(self, p):
        return self.node("binary", p) if len(p) == 3 else p[0]

    @_('term "*" factor', 'term "/" factor', 'factor')
    def term(self, p):
        return self.node("binary", p) if len(p) == 3 else p[0]

    @_('ID', 'number', 'attribute', 'invocation', 'inline_assignment', 'conversion')
    def factor(self, p):
        return p[0]

    @_('TOI "(" expression ")"')
    def conversion(self, p):
        return self.node("conversion", p)

    @_('ID "=" "(" plain_expression ")"')
    def inline_assignment(self, p):
        return self.node("inline_assignment", p)

    # Dentro de =(...), llamadas y conversiones conservan la restriccion.
    @_('plain_expression "+" plain_term', 'plain_expression "-" plain_term', 'plain_term')
    def plain_expression(self, p):
        return self.node("binary", p) if len(p) == 3 else p[0]

    @_('plain_term "*" plain_factor', 'plain_term "/" plain_factor', 'plain_factor')
    def plain_term(self, p):
        return self.node("binary", p) if len(p) == 3 else p[0]

    @_('ID', 'number', 'attribute', 'plain_invocation', 'plain_conversion')
    def plain_factor(self, p):
        return p[0]

    @_('TOI "(" plain_expression ")"')
    def plain_conversion(self, p):
        return self.node("conversion", p)

    @_('ID "[" index "]"')
    def attribute(self, p):
        return self.node("attribute", p)

    @_('ID', 'number')
    def index(self, p):
        return p[0]

    @_('ID "(" arguments ")" order', 'ID "." ID "(" arguments ")" order')
    def invocation(self, p):
        return self.node("invocation", p)

    @_('arguments "," expression', 'expression')
    def arguments(self, p):
        return p[0] + [p[2]] if len(p) == 3 else [p[0]]

    @_('ID "(" plain_arguments ")" order', 'ID "." ID "(" plain_arguments ")" order')
    def plain_invocation(self, p):
        return self.node("invocation", p)

    @_('plain_arguments "," plain_expression', 'plain_expression')
    def plain_arguments(self, p):
        return p[0] + [p[2]] if len(p) == 3 else [p[0]]

    @_('"[" order_items "]"')
    def order(self, p):
        return self.node("evaluation_order", p)

    @_('order_items "," ORDER_INDEX', 'ORDER_INDEX')
    def order_items(self, p):
        return p[0] + [p[2]] if len(p) == 3 else [p[0]]

    @_('INT', 'FLOAT', '"-" INT', '"-" FLOAT')
    def number(self, p):
        negative = len(p) == 2
        literal = p[1] if negative else p[0]
        if not negative and literal.type == "INT" and int(literal.value) > 32767:
            self.diagnostics.append(Diagnostic(
                "syntactic", "S_INTEGER_RANGE", "INTEGER positivo mayor que 32767.",
                literal.line, literal.column))
        if negative:
            # No alterar la entrada de magnitud: puede pertenecer a otros tokens.
            value = str(Decimal(literal.value).copy_negate())
            data_type = "INTEGER" if literal.type == "INT" else "SINGLEF"
            text = "-" + literal.text
            ref = self.symbols.intern("constant", text, data_type, value)
            literal = replace(literal, text=text, value=value, symbol=ref,
                              line=p[0].line, column=p[0].column)
        return make_node("constant", [literal])

    def error(self, token):
        if token is None:
            line = self.source.count("\n") + 1
            column = len(self.source) - self.source.rfind("\n")
            message = "Fin de archivo inesperado; falta completar una estructura."
            code = "S_EOF"
        else:
            line, column = token.value.line, token.value.column
            message = f"Token inesperado {token.value.text!r} ({token.type})."
            code = "S_UNEXPECTED"
        self.last_error = (line, column)
        self.diagnostics.append(Diagnostic("syntactic", code, message, line, column))


def grammar_report():
    """Reporte estable de las producciones/estados construidos por SLY 0.5."""
    grammar = GrammarParser._grammar
    table = GrammarParser._lrtable
    return {
        "productions": [str(p) for p in grammar.Productions if p is not None],
        "states": len(table.lr_action),
        "shift_reduce": table.sr_conflicts,
        "reduce_reduce": table.rr_conflicts,
    }
