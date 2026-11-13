"""TP4: Chequeo de tipos sobre Polaca Inversa y generación de Assembler 80x86/80x87 (Grupo 40)."""

from dataclasses import dataclass
from decimal import Decimal

from .intermediate import RpnStep
from .model import Diagnostic, SymbolTable


@dataclass
class StackOperand:
    name: str
    data_type: str
    line: int
    column: int


class AssemblerGenerator:
    """Traduce la Polaca Inversa a Assembler MASM32 de 32 bits con chequeos de runtime a, c, d, g."""

    def __init__(self, symbols: SymbolTable, diagnostics: list[Diagnostic]):
        self.symbols = symbols
        self.diagnostics = diagnostics
        self.aux_counter = 0

    def error(self, code: str, message: str, line: int, column: int):
        self.diagnostics.append(Diagnostic("semantic", code, message, line, column))

    def new_aux(self, data_type: str) -> str:
        self.aux_counter += 1
        name = f"@aux{self.aux_counter}"
        self.symbols.intern("identifier", name, data_type=data_type, value=name, usage="auxiliar")
        return name

    def asm_id(self, text: str) -> str:
        """Normaliza un nombre de la TS a un identificador válido en MASM32."""
        cleaned = (
            text.replace(":", "_")
            .replace("$", "_")
            .replace(".", "_")
            .replace("+", "p")
            .replace("-", "m")
            .replace("[", "_")
            .replace("]", "")
            .replace("@", "_aux_")
        )
        return f"v_{cleaned}"

    def format_masm_float(self, val_str: str) -> str:
        """Asegura formato punto flotante compatible con MASM32 (ej. 0.5, 1.25e-2)."""
        d = Decimal(val_str)
        s = format(d, "f") if abs(d) >= Decimal("1e-4") and abs(d) < Decimal("1e6") else format(d, "e")
        if "." not in s:
            if "e" in s:
                base, exp = s.split("e", 1)
                s = f"{base}.0e{exp}"
            else:
                s = f"{s}.0"
        return s

    def translate(self, steps: list[RpnStep]) -> str:
        stack: list[StackOperand] = []
        main_lines: list[str] = []
        proc_blocks: list[list[str]] = []
        active_proc_stack: list[list[str]] = []
        jump_targets: set[int] = set()

        def emit_asm(*lines: str):
            target_list = active_proc_stack[-1] if active_proc_stack else main_lines
            target_list.extend(lines)

        # Pre-escaneo de pasos destino de saltos para insertar etiquetas L_step_N
        for step in steps:
            if step.op == "JUMP_TARGET" and step.label.startswith("[") and step.label.endswith("]"):
                inner = step.label[1:-1]
                if inner.isdigit():
                    jump_targets.add(int(inner))

        last_comparison_op: str | None = None
        last_comparison_type: str | None = None

        for step in steps:
            if step.index in jump_targets:
                emit_asm(f"L_step_{step.index}:")

            op = step.op

            if op in {"ID", "CONST", "STRING", "PARAM_TARGET"}:
                stack.append(StackOperand(step.label, step.data_type or "INTEGER", step.line, step.column))

            elif op == "JUMP_TARGET":
                stack.append(StackOperand(step.label, "TARGET", step.line, step.column))

            elif op == "LABEL":
                if step.label.startswith("REPEAT_START"):
                    emit_asm(f"L_step_{step.index}: ; {step.label}")
                else:
                    emit_asm(f"; --- {step.label} ---")

            elif op == "FUNC_BEGIN":
                fn_name = step.label.removeprefix("FUNC_BEGIN ").strip()
                new_block = [f"{self.asm_id(fn_name)} PROC"]
                active_proc_stack.append(new_block)

            elif op == "FUNC_END":
                fn_name = step.label.removeprefix("FUNC_END ").strip()
                emit_asm("    RET", f"{self.asm_id(fn_name)} ENDP")
                if active_proc_stack:
                    proc_blocks.append(active_proc_stack.pop())

            elif op == "TOI":
                # Tema 34 + Control Runtime (g): Pérdida de información en conversión SINGLEF -> INTEGER
                if not stack:
                    continue
                operand = stack.pop()
                if operand.data_type != "SINGLEF":
                    self.error(
                        "M_TYPE_MISMATCH",
                        f"La conversión explícita 'toi' requiere un operando SINGLEF, pero recibió {operand.data_type}.",
                        step.line,
                        step.column,
                    )
                aux = self.new_aux("INTEGER")
                src_asm = self.asm_id(operand.name)
                dst_asm = self.asm_id(aux)
                emit_asm(
                    f"    ; toi({operand.name}) -> {aux} con control (g) de pérdida de información",
                    f"    FLD {src_asm}",
                    "    FCOM _flt_max_int",
                    "    FSTSW AX",
                    "    SAHF",
                    "    JA _err_perdida_info_toi",
                    "    FCOM _flt_min_int",
                    "    FSTSW AX",
                    "    SAHF",
                    "    JB _err_perdida_info_toi",
                    f"    FISTP {dst_asm}",
                    f"    FILD {dst_asm}",
                    f"    FLD {src_asm}",
                    "    FCOMPP",
                    "    FSTSW AX",
                    "    SAHF",
                    "    JNE _err_perdida_info_toi",
                )
                stack.append(StackOperand(aux, "INTEGER", step.line, step.column))

            elif op in {"+", "-", "*", "/"}:
                if len(stack) < 2:
                    continue
                right = stack.pop()
                left = stack.pop()
                if left.data_type != right.data_type:
                    self.error(
                        "M_TYPE_MISMATCH",
                        f"Incompatibilidad de tipos en operación '{op}': no se puede operar {left.data_type} con {right.data_type}.",
                        step.line,
                        step.column,
                    )
                res_type = left.data_type
                aux = self.new_aux(res_type)
                l_asm, r_asm, dst_asm = self.asm_id(left.name), self.asm_id(right.name), self.asm_id(aux)

                if res_type == "INTEGER":
                    if op == "+":
                        emit_asm(
                            f"    MOV AX, {l_asm}",
                            f"    ADD AX, {r_asm}",
                            f"    MOV {dst_asm}, AX",
                        )
                    elif op == "-":
                        emit_asm(
                            f"    MOV AX, {l_asm}",
                            f"    SUB AX, {r_asm}",
                            f"    MOV {dst_asm}, AX",
                        )
                    elif op == "*":
                        # Control Runtime (d): Overflow en producto de enteros
                        emit_asm(
                            f"    MOV AX, {l_asm}",
                            f"    IMUL {r_asm}",
                            "    JO _err_overflow_prod_int",
                            f"    MOV {dst_asm}, AX",
                        )
                    elif op == "/":
                        # Control Runtime (a): División por cero entera
                        emit_asm(
                            f"    MOV BX, {r_asm}",
                            "    CMP BX, 0",
                            "    JE _err_div_cero",
                            f"    MOV AX, {l_asm}",
                            "    CWD",
                            "    IDIV BX",
                            f"    MOV {dst_asm}, AX",
                        )
                else:
                    # Operaciones SINGLEF en coprocesador 80x87
                    if op == "+":
                        # Control Runtime (c): Overflow en suma de punto flotante
                        emit_asm(
                            f"    FLD {l_asm}",
                            f"    FADD {r_asm}",
                            f"    FSTP {dst_asm}",
                            f"    FLD {dst_asm}",
                            "    FABS",
                            "    FCOMP _flt_max_single",
                            "    FSTSW AX",
                            "    SAHF",
                            "    JA _err_overflow_suma_flt",
                        )
                    elif op == "-":
                        emit_asm(
                            f"    FLD {l_asm}",
                            f"    FSUB {r_asm}",
                            f"    FSTP {dst_asm}",
                        )
                    elif op == "*":
                        emit_asm(
                            f"    FLD {l_asm}",
                            f"    FMUL {r_asm}",
                            f"    FSTP {dst_asm}",
                        )
                    elif op == "/":
                        # Control Runtime (a): División por cero en punto flotante
                        emit_asm(
                            f"    FLD {r_asm}",
                            "    FTST",
                            "    FSTSW AX",
                            "    SAHF",
                            "    FSTP ST(0)",
                            "    JE _err_div_cero",
                            f"    FLD {l_asm}",
                            f"    FDIV {r_asm}",
                            f"    FSTP {dst_asm}",
                        )
                stack.append(StackOperand(aux, res_type, step.line, step.column))

            elif op in {":=", "=", "PARAM_ASSIGN"}:
                if len(stack) < 2:
                    continue
                target = stack.pop()
                value = stack.pop()
                if target.data_type != value.data_type:
                    self.error(
                        "M_TYPE_MISMATCH",
                        f"Incompatibilidad de tipos en asignación '{op}' a {target.name!r}: "
                        f"no se puede asignar {value.data_type} a {target.data_type}.",
                        step.line,
                        step.column,
                    )
                val_asm, dst_asm = self.asm_id(value.name), self.asm_id(target.name)
                if target.data_type == "INTEGER":
                    emit_asm(
                        f"    MOV AX, {val_asm}",
                        f"    MOV {dst_asm}, AX",
                    )
                else:
                    emit_asm(
                        f"    FLD {val_asm}",
                        f"    FSTP {dst_asm}",
                    )
                if op == "=":
                    stack.append(StackOperand(target.name, target.data_type, step.line, step.column))

            elif op in {">", "<", ">=", "<=", "==", "!="}:
                if len(stack) < 2:
                    continue
                right = stack.pop()
                left = stack.pop()
                if left.data_type != right.data_type:
                    self.error(
                        "M_TYPE_MISMATCH",
                        f"Incompatibilidad de tipos en comparación '{op}': {left.data_type} vs {right.data_type}.",
                        step.line,
                        step.column,
                    )
                last_comparison_op = op
                last_comparison_type = left.data_type
                l_asm, r_asm = self.asm_id(left.name), self.asm_id(right.name)
                if left.data_type == "INTEGER":
                    emit_asm(
                        f"    MOV AX, {l_asm}",
                        f"    CMP AX, {r_asm}",
                    )
                else:
                    emit_asm(
                        f"    FLD {l_asm}",
                        f"    FCOMP {r_asm}",
                        "    FSTSW AX",
                        "    SAHF",
                    )

            elif op == "BF":
                if not stack:
                    continue
                target = stack.pop()
                t_num = target.name.strip("[]")
                label = f"L_step_{t_num}"
                if last_comparison_type == "SINGLEF":
                    branch_map = {">": "JBE", "<": "JAE", ">=": "JB", "<=": "JA", "==": "JNE", "!=": "JE"}
                else:
                    branch_map = {">": "JLE", "<": "JGE", ">=": "JL", "<=": "JG", "==": "JNE", "!=": "JE"}
                jmp_instr = branch_map.get(last_comparison_op or "==", "JNE")
                emit_asm(f"    {jmp_instr} {label}")

            elif op == "BI":
                if not stack:
                    continue
                target = stack.pop()
                t_num = target.name.strip("[]")
                emit_asm(f"    JMP L_step_{t_num}")

            elif op == "CALL":
                fn_name = step.label.removeprefix("CALL ").strip()
                ret_type = step.data_type or "INTEGER"
                aux = self.new_aux(ret_type)
                emit_asm(f"    CALL {self.asm_id(fn_name)}")
                if ret_type == "INTEGER":
                    emit_asm(f"    MOV {self.asm_id(aux)}, AX")
                else:
                    emit_asm(f"    FSTP {self.asm_id(aux)}")
                stack.append(StackOperand(aux, ret_type, step.line, step.column))

            elif op == "RET":
                if stack:
                    ret_val = stack.pop()
                    if ret_val.data_type == "INTEGER":
                        emit_asm(f"    MOV AX, {self.asm_id(ret_val.name)}")
                    else:
                        emit_asm(f"    FLD {self.asm_id(ret_val.name)}")
                emit_asm("    RET")

            elif op == "POUT":
                if stack:
                    item = stack.pop()
                    if item.data_type == "STRING":
                        raw_str = item.name.strip('"')
                        sym_id = self.asm_id(raw_str)
                        emit_asm(f"    invoke crt_printf, addr _fmt_str, addr {sym_id}")
                    elif item.data_type == "INTEGER":
                        sym_id = self.asm_id(item.name)
                        emit_asm(
                            f"    MOVSX EAX, {sym_id}",
                            "    invoke crt_printf, addr _fmt_int, EAX",
                        )
                    else:
                        sym_id = self.asm_id(item.name)
                        emit_asm(
                            f"    FLD {sym_id}",
                            "    FSTP _print_flt_buf",
                            "    invoke crt_printf, addr _fmt_flt, _print_flt_buf",
                        )

        end_label = len(steps) + 1
        if end_label in jump_targets:
            emit_asm(f"L_step_{end_label}:")

        # Construcción de la sección .data a partir de la Tabla de Símbolos
        data_lines = [
            ".386",
            ".model flat, stdcall",
            "option casemap :none",
            "include \\masm32\\include\\masm32rt.inc",
            "",
            ".data",
            "    _flt_max_single DD 3.40282347e38",
            "    _flt_max_int    DD 32767.0",
            "    _flt_min_int    DD -32768.0",
            "    _print_flt_buf  DQ 0.0",
            '    _fmt_int        DB "%d", 13, 10, 0',
            '    _fmt_flt        DB "%g", 13, 10, 0',
            '    _fmt_str        DB "%s", 13, 10, 0',
            '    _msg_div_cero   DB "Error en tiempo de ejecucion (a): Division por cero.", 13, 10, 0',
            '    _msg_ovf_flt    DB "Error en tiempo de ejecucion (c): Overflow en suma de punto flotante.", 13, 10, 0',
            '    _msg_ovf_int    DB "Error en tiempo de ejecucion (d): Overflow en producto de enteros.", 13, 10, 0',
            '    _msg_toi_loss   DB "Error en tiempo de ejecucion (g): Perdida de informacion en conversion toi.", 13, 10, 0',
        ]
        for sym in self.symbols.entries:
            if sym.category == "string":
                safe_str = sym.value.replace('"', "'")
                data_lines.append(f'    {self.asm_id(sym.text)} DB "{safe_str}", 0')
            elif sym.category == "constant":
                if sym.data_type == "INTEGER":
                    data_lines.append(f"    {self.asm_id(sym.text)} DW {sym.value}")
                else:
                    data_lines.append(f"    {self.asm_id(sym.text)} DD {self.format_masm_float(sym.value)}")
            elif sym.usage in {"variable", "variable_comptime", "parametro", "atributo_objeto", "auxiliar"}:
                if sym.data_type == "INTEGER":
                    data_lines.append(f"    {self.asm_id(sym.text)} DW 0")
                elif sym.data_type == "SINGLEF":
                    data_lines.append(f"    {self.asm_id(sym.text)} DD 0.0")

        flat_procs = [line for block in proc_blocks for line in block]

        runtime_handlers = [
            "    invoke ExitProcess, 0",
            "_err_div_cero:",
            "    invoke StdOut, addr _msg_div_cero",
            "    invoke ExitProcess, 1",
            "_err_overflow_suma_flt:",
            "    invoke StdOut, addr _msg_ovf_flt",
            "    invoke ExitProcess, 1",
            "_err_overflow_prod_int:",
            "    invoke StdOut, addr _msg_ovf_int",
            "    invoke ExitProcess, 1",
            "_err_perdida_info_toi:",
            "    invoke StdOut, addr _msg_toi_loss",
            "    invoke ExitProcess, 1",
            "",
            *flat_procs,
            "end start",
        ]

        return "\n".join([
            *data_lines,
            "",
            ".code",
            "start:",
            "    FINIT",
            *main_lines,
            *runtime_handlers,
            "",
        ])