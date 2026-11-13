import json
from pathlib import Path
import subprocess
import sys
import unittest

from compiler_frontend import analyze, grammar_report
from compiler_frontend.model import Lexeme, walk_nodes


root = Path(__file__).resolve().parents[1]


def program(statement):
    return "demo\ninteger a,b,c;\nsinglef x;\nbegin\n" + statement + "\nend"


class GrammarTests(unittest.TestCase):
    def assert_valid(self, source, check_semantics=False):
        result = analyze(source, check_semantics=check_semantics)
        self.assertTrue(result.ok, result.diagnostics)
        return result

    def assert_invalid(self, source, check_semantics=False):
        result = analyze(source, check_semantics=check_semantics)
        self.assertFalse(result.ok)
        self.assertTrue(result.diagnostics)
        return result

    def test_zero_lalr_conflicts(self):
        report = grammar_report()
        self.assertEqual(report["shift_reduce"], [])
        self.assertEqual(report["reduce_reduce"], [])
        self.assertGreater(report["states"], 0)

    def test_full_group_example(self):
        result = self.assert_valid((root / "examples/grupo40.src").read_text(encoding="utf-8"),
                                   check_semantics=True)
        kinds = {node.kind for node in walk_nodes(result.tree)}
        self.assertTrue({"comptime_declaration", "class_declaration", "method_declaration",
                         "function_declaration", "object_declaration", "attribute",
                         "inline_assignment", "evaluation_order", "inheritance", "import",
                         "export", "conversion", "if", "repeat", "return"} <= kinds)
        self.assertTrue(result.rpn)
        self.assertIn("_err_div_cero", result.assembler)

    def test_multiplication_precedes_addition(self):
        result = self.assert_valid(program("a := 1$i + 2$i * 3$i;"))
        assignment = next(n for n in walk_nodes(result.tree) if n.kind == "assignment")
        expr = assignment.children[-1]
        self.assertEqual(expr.children[1].text, "+")
        self.assertEqual(expr.children[2].children[1].text, "*")

    def test_subtraction_and_division_are_left_associative(self):
        for operator in ("-", "/"):
            with self.subTest(operator=operator):
                result = self.assert_valid(program(f"a := 8$i {operator} 2$i {operator} 2$i;"))
                expr = next(n for n in walk_nodes(result.tree) if n.kind == "assignment").children[-1]
                self.assertEqual(expr.children[1].text, operator)
                self.assertEqual(expr.children[0].children[1].text, operator)

    def test_inline_assignment_variants(self):
        for statement in ("a := b=(2$i);", "a := b+c=(4$i);",
                          "a := b=(c+2$i)*c=(a/3$i);",
                          "a := f(b=(3.0))[1$i];", "a := b=(f(c)[1$i]+toi(x));",
                          "a := b=(f(toi(x))[1$i]);", "if(a=(2$i)==2$i) pout(a); end_if;"):
            with self.subTest(statement=statement):
                self.assert_valid(program(statement))

    def test_prohibited_nested_assignments_and_operators(self):
        for expression in ("b=(c=(1$i))", "b=(toi(c=(1.0)))",
                           "b=(f(c=(1$i))[1$i])", "b=(f(g(c=(1$i))[1$i])[1$i])",
                           "b=2$i", "b:=(2$i)"):
            with self.subTest(expression=expression):
                self.assert_invalid(program(f"a := {expression};"))
        self.assert_invalid(program("a = b=(2$i);"))

    def test_no_arithmetic_parenthesis_or_general_unary(self):
        for expression in ("(1$i+2$i)", "((1$i))", "-a", "+1$i"):
            with self.subTest(expression=expression):
                self.assert_invalid(program(f"a := {expression};"))

    def test_calls_and_mandatory_order(self):
        for call in ("f(a)[1$i]", "o.m(a)[1$i]", "f(g(a)[1$i],b)[2$i,1$i]"):
            with self.subTest(call=call):
                self.assert_valid(program(f"a := {call};"))
                self.assert_valid(program(f"{call};"))
        for call in ("f(a)", "o.m(a)", "f()[1$i]", "f(a)[]", "f(a)[1]",
                     "f(a)[-1$i]", "f(a)[1$i,]"):
            with self.subTest(call=call):
                self.assert_invalid(program(f"a := {call};"))

    def test_missing_evaluation_order_reports_specific_error(self):
        result = self.assert_invalid(program("a := f(a);"))
        codes = [d.code for d in result.diagnostics]
        self.assertIn("S_MISSING_ORDER", codes)

    def test_order_values_are_not_semantically_validated_in_syntax_only_mode(self):
        self.assert_valid(program("a := f(a)[0$i,0$i,999$i];"), check_semantics=False)

    def test_bare_integer_rejected_everywhere(self):
        for statement in ("a := 1;", "a[0] := 1$i;", "pout(2);", "a := f(a)[1];"):
            with self.subTest(statement=statement):
                self.assert_invalid(program(statement))

    def test_positional_attributes(self):
        for statement in ("a[0$i] := 1$i;", "a[b] := c[1$i];",
                          "a := b[0$i] + c[a];", "a := b[-1$i];", "a := b[1.0];"):
            with self.subTest(statement=statement):
                self.assert_valid(program(statement))
        for statement in ("a[1$i+2$i] := 1$i;", "a.x := 1$i;", "a[0$i] = 1$i;"):
            with self.subTest(statement=statement):
                self.assert_invalid(program(statement))

    def test_conditions_and_blocks(self):
        for operator in (">", "<", ">=", "<=", "==", "!="):
            with self.subTest(operator=operator):
                self.assert_valid(program(f"if(a {operator} b) a := 1$i; else pout(b); end_if;"))
        self.assert_valid(program("repeat begin if(a<b) a := a+1$i; end_if; "
                                  "end until(a>=b);"))
        self.assert_valid(program("if(a<b) if(b<c) pout(a); else pout(b); end_if; end_if;"))
        for statement in ("if(a<b<c) pout(a); end_if;", "if(a) pout(a); end_if;",
                          "repeat pout(a); while(a<b);", "if(a<b) begin end end_if;"):
            with self.subTest(statement=statement):
                self.assert_invalid(program(statement))

    def test_control_structures_reported_in_completion_order(self):
        source = (
            "demo\n"
            "integer a, b;\n"
            "begin\n"
            "  repeat\n"
            "  begin\n"
            "    if (a < b)\n"
            "      a := a + 1$i;\n"
            "    end_if;\n"
            "  end\n"
            "  until (a >= b);\n"
            "end"
        )
        result = self.assert_valid(source, check_semantics=True)
        control = [(n.kind, n.line) for n in result.structures if n.kind in {"if", "repeat"}]
        self.assertEqual(control, [("if", 6), ("repeat", 4)])

    def test_return_contexts_and_nested_functions(self):
        self.assert_valid("""demo
integer function f(integer a)
    integer function g(integer b)
    begin ret(b); end;
begin
    repeat begin if(a>0$i) ret(g(a)[1$i]); else ret(0$i); end_if;
    end until(a==0$i);
end;
begin pout(f(1$i)[1$i]); end""", check_semantics=True)
        for statement in ("ret(1$i);", "if(a<b) ret(1$i); end_if;",
                          "repeat begin ret(1$i); end until(a<b);"):
            with self.subTest(statement=statement):
                self.assert_invalid(program(statement))

    def test_function_without_return_and_object_parameter(self):
        self.assert_valid(
            "demo class ca begin integer v; end; "
            "integer function f(ca obj) begin pout(obj[0$i]); end; "
            "begin pout(1$i); end",
            check_semantics=True,
        )

    def test_empty_bodies_and_lists_rejected(self):
        for source in ("demo begin end", "demo class ca begin end; begin pout(1$i); end",
                       "demo integer function f() begin ret(1$i); end; begin pout(1$i); end",
                       "demo integer function f(integer x) begin end; begin pout(1$i); end",
                       "demo integer ; begin pout(1$i); end", "demo integer a,; begin pout(a); end"):
            with self.subTest(source=source):
                self.assert_invalid(source)
        self.assert_valid("demo begin pout(1$i); end", check_semantics=True)

    def test_classes_import_export_extends(self):
        prefix = "demo class cb begin integer x; end; class cc begin integer y; end; class ca import from cb,cc begin "
        suffix = " end; ca obj; begin obj[0$i] := 1$i; end"
        self.assert_valid(prefix + "integer a,b export to cb; extends cb,cc; "
                          "integer m(integer p) begin ret(p); end; export to cc;" + suffix,
                          check_semantics=True)
        for body in ("integer a; export to cb;", "extend cb;", "friend cb;",
                     "integer function m(integer p) begin ret(p); end;"):
            with self.subTest(body=body):
                self.assert_invalid(prefix + body + suffix)
        self.assert_invalid("demo class ca integer a; end; begin pout(1$i); end")

    def test_comptime_declarative_only(self):
        self.assert_valid("demo comptime integer a; begin a := 1$i; end", check_semantics=True)
        self.assert_invalid(program("comptime integer a;"))

    def test_no_trailing_input_or_program_semicolon(self):
        for trailing in (";", "otro begin pout(1$i); end", "pout(1$i);"):
            with self.subTest(trailing=trailing):
                self.assert_invalid(program("pout(a);") + trailing)

    def test_recovery_keeps_later_statements_and_reports_multiple_errors(self):
        result = self.assert_invalid((root / "examples/errores.src").read_text(encoding="utf-8"))
        self.assertEqual(len([d for d in result.diagnostics if d.phase == "syntactic"]), 2)
        self.assertEqual([n.line for n in result.structures if n.kind == "output"], [5, 7])

    def test_missing_comma_in_declaration_recovers(self):
        source = (
            "demo\n"
            "integer a b;\n"
            "singlef x, y;\n"
            "begin\n"
            "  x := 1.5;\n"
            "  pout(x);\n"
            "end"
        )
        result = self.assert_invalid(source)
        syntactic = [d for d in result.diagnostics if d.phase == "syntactic"]
        self.assertEqual(len(syntactic), 1)
        self.assertEqual(syntactic[0].code, "S_MISSING_COMMA")
        kinds = [n.kind for n in result.structures]
        self.assertIn("variable_declaration", kinds)
        self.assertIn("assignment", kinds)
        self.assertIn("output", kinds)

    def test_eof_diagnostic(self):
        for source in ("", "demo begin pout(1$i);", "demo begin pout("):
            with self.subTest(source=source):
                result = self.assert_invalid(source)
                self.assertTrue(any(d.code in {"S_EOF", "S_MISSING_END_IF"} for d in result.diagnostics))

    def test_ast_and_token_attributes_are_serializable(self):
        result = self.assert_valid(program("a := 1$i;"), check_semantics=True)
        data = json.loads(json.dumps(result.to_dict()))
        self.assertTrue(data["ok"])
        self.assertEqual(data["tree"]["kind"], "program")


class LexicalIntegrationTests(unittest.TestCase):
    def test_signed_integer_limits(self):
        for literal in ("0$i", "32767$i", "-32768$i", "-0$i"):
            with self.subTest(literal=literal):
                result = analyze(program(f"a := {literal};"))
                self.assertTrue(result.ok, result.diagnostics)
        for literal, code in (("32768$i", "S_INTEGER_RANGE"), ("32769$i", "L_INTEGER_RANGE"),
                              ("-32769$i", "L_INTEGER_RANGE")):
            with self.subTest(literal=literal):
                result = analyze(program(f"a := {literal};"))
                self.assertFalse(result.ok)
                self.assertIn(code, [d.code for d in result.diagnostics])

    def test_negative_only_constant_does_not_insert_positive_in_ts(self):
        result = analyze(program("a := -1$i; x := -1.2;"))
        self.assertTrue(result.ok, result.diagnostics)
        constants = {s.text: s.value for s in result.symbols.entries if s.category == "constant"}
        self.assertIn("-1$i", constants)
        self.assertNotIn("1$i", constants)
        self.assertIn("-1.2", constants)
        self.assertNotIn("1.2", constants)

    def test_negative_constant_does_not_mutate_shared_positive_symbol(self):
        result = analyze(program("a := 7$i; b := -7$i; c := 7$i;"))
        self.assertTrue(result.ok)
        values = {s.text: s.value for s in result.symbols.entries if s.category == "constant"}
        self.assertEqual(values["7$i"], "7")
        self.assertEqual(values["-7$i"], "-7")
        pos_refs = [t.symbol for idx, t in enumerate(result.tokens)
                    if t.text == "7$i" and (idx == 0 or result.tokens[idx - 1].text != "-")]
        self.assertEqual(len(set(pos_refs)), 1)

    def test_singlef_format_range_and_exponent_sign(self):
        for literal in ("0.0", ".6", "1.0s+2", "1.0s-2", "-1.2s-3",
                        "1.17549436s-38", "3.40282346s+38"):
            with self.subTest(literal=literal):
                result = analyze(program(f"x := {literal};"))
                self.assertTrue(result.ok, result.diagnostics)
        for literal in ("1.", "1.0s", "1.0s+", "1.0d2", "7$ix", "3$ui",
                        "1.17549435s-38", "3.40282347s+38", "1.0s-40", "1.0s40"):
            with self.subTest(literal=literal):
                self.assertFalse(analyze(program(f"x := {literal};")).ok)

    def test_case_keywords_identifiers_and_truncation(self):
        result = analyze("demo InTeGeR ifvariable; BeGiN ifvariable:=1$i; EnD")
        self.assertTrue(result.ok, result.diagnostics)
        for name in ("Price", "_price", "ñombre"):
            with self.subTest(name=name):
                self.assertFalse(analyze(program(f"{name} := 1$i;")).ok)
        long_id = "a" * 23
        truncated = "a" * 22
        result = analyze(f"demo integer {long_id}; begin {long_id} := 1$i; end")
        self.assertTrue(result.ok, result.diagnostics)
        self.assertIn("L_TRUNCATED_ID", [d.code for d in result.diagnostics])
        self.assertIn(f"{truncated}:demo", [s.text for s in result.symbols.entries])

    def test_strings_comments_and_line_numbers(self):
        result = analyze('\ufeffdemo\r\nbegin\r\npout("hola //\r\nmundo");\r\n'
                         'pout(1$i); // comentario con "\r\nend // EOF')
        self.assertTrue(result.ok, result.diagnostics)
        string = next(t for t in result.tokens if t.type == "STRING")
        self.assertEqual(string.value, "hola //mundo")
        self.assertEqual(string.line, 3)
        self.assertEqual([n.line for n in result.structures if n.kind == "output"], [3, 5])
        self.assertTrue(analyze('demo begin pout(""); end').ok)
        result = analyze('demo begin pout("sin cierre')
        self.assertFalse(result.ok)
        self.assertIn("L_UNCLOSED_STRING", [d.code for d in result.diagnostics])

    def test_invalid_character_recovery_and_isolation(self):
        first = analyze(program("a := 1$i; @ pout(a);"))
        self.assertFalse(first.ok)
        self.assertIn("output", [n.kind for n in first.structures])
        second = analyze("otra begin pout(2$i); end")
        self.assertTrue(second.ok)
        self.assertNotIn("a:demo", [s.text for s in second.symbols.entries])

    def test_extreme_input_numbers_fail_without_crashing(self):
        for literal in ("9" * 5000 + "$i", "1.0s" + "9" * 100):
            with self.subTest(size=len(literal)):
                self.assertFalse(analyze(program(f"a := {literal};")).ok)


class SemanticAndCodegenTests(unittest.TestCase):
    """Pruebas de TP3 (Semántica, Ámbitos, Polaca Inversa) y TP4 (Tipos y Assembler)."""

    def test_name_mangling_and_nested_scopes(self):
        source = """main
integer a;
integer function aa(integer x)
    integer a;
    integer function aaa(integer w)
        integer x;
    begin
        x := w + a;
        ret(x);
    end;
begin
    a := aaa(x)[1$i];
    ret(a);
end;
begin
    a := aa(1$i)[1$i];
end"""
        result = analyze(source)
        self.assertTrue(result.ok, result.diagnostics)
        names = {s.text for s in result.symbols.entries}
        self.assertIn("a:main", names)
        self.assertIn("aa:main", names)
        self.assertIn("x:main:aa", names)
        self.assertIn("a:main:aa", names)
        self.assertIn("aaa:main:aa", names)
        self.assertIn("w:main:aa:aaa", names)
        self.assertIn("x:main:aa:aaa", names)

    def test_undeclared_and_redeclared_errors(self):
        res_redecl = analyze("demo integer a, a; begin a := 1$i; end")
        self.assertFalse(res_redecl.ok)
        self.assertIn("M_REDECLARED", [d.code for d in res_redecl.diagnostics])

        res_undecl = analyze("demo integer a; begin b := 1$i; end")
        self.assertFalse(res_undecl.ok)
        self.assertIn("M_UNDECLARED", [d.code for d in res_undecl.diagnostics])

    def test_type_compatibility_and_explicit_toi_tema34(self):
        ok_res = analyze(program("a := toi(x + 1.5) + 2$i;"))
        self.assertTrue(ok_res.ok, ok_res.diagnostics)

        bad_expr = analyze(program("a := x + 2$i;"))
        self.assertFalse(bad_expr.ok)
        self.assertIn("M_TYPE_MISMATCH", [d.code for d in bad_expr.diagnostics])

        bad_assign = analyze(program("a := x;"))
        self.assertFalse(bad_assign.ok)
        self.assertIn("M_TYPE_MISMATCH", [d.code for d in bad_assign.diagnostics])

    def test_evaluation_order_tema19_and_inline_assignment_tema17(self):
        source = """demo
integer a, b, c;
integer function f(integer p1, integer p2, integer p3)
begin
    ret(p1 + p2 + p3);
end;
begin
    a := 1$i;
    b := 2$i;
    c := f(a, b=(4$i), a+b)[1$i, 3$i, 2$i];
end"""
        result = analyze(source)
        self.assertTrue(result.ok, result.diagnostics)
        param_targets = [step.label for step in result.rpn if step.op == "PARAM_TARGET"]
        # Verifica que en la invocación los parámetros se copien en el orden [1$i, 3$i, 2$i]
        self.assertEqual(param_targets, ["p1:demo:f", "p3:demo:f", "p2:demo:f"])

        bad_order = analyze(source.replace("[1$i, 3$i, 2$i]", "[1$i, 2$i]"))
        self.assertFalse(bad_order.ok)
        self.assertIn("M_ORDER_ARITY_MISMATCH", [d.code for d in bad_order.diagnostics])

    def test_comptime_replacement_and_restrictions_tema22(self):
        valid_src = """demo
comptime integer k;
integer z;
begin
    k := 3$i;
    k := k + 2$i;
    z := k;
end"""
        result = analyze(valid_src)
        self.assertTrue(result.ok, result.diagnostics)
        # Cuando z := k se traduce a Polaca Inversa, debe usarse la constante 5$i
        rpn_labels = [s.label for s in result.rpn]
        self.assertIn("5$i", rpn_labels)

        invalid_src = """demo
comptime integer k;
integer z;
begin
    z := 4$i;
    k := z;
end"""
        bad = analyze(invalid_src)
        self.assertFalse(bad.ok)
        self.assertIn("M_COMPTIME_DYNAMIC", [d.code for d in bad.diagnostics])

    def test_multiple_inheritance_ambiguity_option3_tema32(self):
        ambiguous_src = """demo
class cb begin
    integer x;
end;
class cc begin
    integer x;
end;
class ca begin
    integer propio;
    extends cb, cc;
end;
begin
    pout(1$i);
end"""
        res = analyze(ambiguous_src)
        self.assertFalse(res.ok)
        self.assertIn("M_AMBIGUOUS_INHERITANCE", [d.code for d in res.diagnostics])

    def test_runtime_checks_present_in_assembler_tp4(self):
        src = """demo
integer a, b, c;
singlef x, y;
begin
    a := 10$i * 20$i;
    b := a / 2$i;
    x := 1.5 + 2.5;
    c := toi(x);
end"""
        res = analyze(src)
        self.assertTrue(res.ok, res.diagnostics)
        self.assertIn("_err_div_cero", res.assembler)
        self.assertIn("_err_overflow_suma_flt", res.assembler)
        self.assertIn("_err_overflow_prod_int", res.assembler)
        self.assertIn("_err_perdida_info_toi", res.assembler)


class CommandLineTests(unittest.TestCase):
    def test_json_success_and_error_exit_codes(self):
        for filename, code in (("minimo.src", 0), ("errores.src", 1)):
            with self.subTest(filename=filename):
                proc = subprocess.run([sys.executable, "-m", "compiler_frontend",
                                       str(root / "examples" / filename), "--json"],
                                      cwd=root, capture_output=True, text=True, timeout=15)
                self.assertEqual(proc.returncode, code, proc.stderr)
                data = json.loads(proc.stdout)
                self.assertEqual(data["ok"], code == 0)

    def test_cli_prints_rpn_and_symbol_table_by_default(self):
        proc = subprocess.run([sys.executable, "-m", "compiler_frontend",
                               str(root / "examples" / "minimo.src")],
                              cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("Código Intermedio (Polaca Inversa):", proc.stdout)
        self.assertIn("Tabla de símbolos:", proc.stdout)
        self.assertNotIn("\nTokens:", proc.stdout)
        self.assertNotIn("\nEstructuras sintácticas:", proc.stdout)

    def test_missing_file_and_report(self):
        proc = subprocess.run([sys.executable, "-m", "compiler_frontend", "no-existe.src"],
                              cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 2)
        proc = subprocess.run([sys.executable, "-m", "compiler_frontend", "--grammar-report"],
                              cwd=root, capture_output=True, text=True, timeout=15)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["reduce_reduce"], [])


class CasosPruebaFilesTests(unittest.TestCase):
    def test_casos_prueba_files(self):
        casos_dir = root / "tests" / "casos_prueba"
        if not casos_dir.exists():
            return
        for src_file in sorted(casos_dir.glob("*.src")):
            with self.subTest(file=src_file.name):
                result = analyze(src_file.read_text(encoding="utf-8"))
                if "err" in src_file.stem or "errores" in src_file.stem:
                    self.assertFalse(result.ok, f"Se esperaba fallo en {src_file.name}")
                else:
                    self.assertTrue(result.ok, f"Fallo inesperado en {src_file.name}: {result.diagnostics}")


if __name__ == "__main__":
    unittest.main()