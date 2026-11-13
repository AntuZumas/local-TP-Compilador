"""TP3: Chequeos semánticos, Tabla de Símbolos con ámbitos (name mangling) y Polaca Inversa."""

from dataclasses import dataclass, field
from decimal import Decimal

from .model import Diagnostic, Lexeme, Node, SymbolTable


@dataclass
class RpnStep:
    index: int
    op: str
    label: str
    symbol_ref: int | None = None
    data_type: str | None = None
    line: int = 1
    column: int = 1


@dataclass
class ClassAttributeInfo:
    name: str
    mangled_name: str
    data_type: str
    origin_class: str
    exported_to: set[str] = field(default_factory=set)


@dataclass
class ClassMethodInfo:
    name: str
    mangled_name: str
    return_type: str
    params: list[tuple[str, str, str]]  # (type, raw_name, mangled_name)
    origin_class: str
    exported_to: set[str] = field(default_factory=set)
    node: Node | None = None


@dataclass
class ClassInfo:
    name: str
    mangled_name: str
    imports_from: list[str] = field(default_factory=list)
    extends: list[str] = field(default_factory=list)
    own_attributes: list[ClassAttributeInfo] = field(default_factory=list)
    own_methods: dict[str, ClassMethodInfo] = field(default_factory=dict)
    line: int = 1
    column: int = 1


class IntermediateGenerator:
    """Construye la información semántica en TS y la Polaca Inversa del Grupo 40."""

    def __init__(self, symbols: SymbolTable, diagnostics: list[Diagnostic]):
        self.symbols = symbols
        self.diagnostics = diagnostics
        self.steps: list[RpnStep] = []
        self.scope_stack: list[str] = []
        # Mapa (scope_path, raw_name) -> symbol_text_mangled
        self.scoped_declarations: dict[tuple[str, str], str] = {}
        self.classes: dict[str, ClassInfo] = {}
        self.comptime_values: dict[str, Decimal] = {}
        self.current_class: str | None = None
        self.current_function: str | None = None

    # ------------------------------------------------------------------
    # Utilidades de diagnóstico, ámbitos y Polaca Inversa
    # ------------------------------------------------------------------
    def error(self, code: str, message: str, line: int, column: int):
        self.diagnostics.append(Diagnostic("semantic", code, message, line, column))

    @property
    def current_scope_path(self) -> str:
        return ":".join(self.scope_stack)

    def mangle(self, raw_name: str, scope_path: str | None = None) -> str:
        path = self.current_scope_path if scope_path is None else scope_path
        return f"{raw_name}:{path}" if path else raw_name

    def emit(self, op: str, label: str | None = None, symbol_ref: int | None = None,
             data_type: str | None = None, line: int = 1, column: int = 1) -> int:
        idx = len(self.steps) + 1
        step = RpnStep(
            index=idx,
            op=op,
            label=op if label is None else label,
            symbol_ref=symbol_ref,
            data_type=data_type,
            line=line,
            column=column,
        )
        self.steps.append(step)
        return idx

    def patch_step(self, step_index: int, target_index: int):
        step = self.steps[step_index - 1]
        step.op = "JUMP_TARGET"
        step.label = f"[{target_index}]"

    def declare_symbol(self, raw_name: str, data_type: str, usage: str,
                       line: int, column: int, scope_path: str | None = None, **attrs) -> str | None:
        path = self.current_scope_path if scope_path is None else scope_path
        key = (path, raw_name)
        if key in self.scoped_declarations:
            self.error(
                "M_REDECLARED",
                f"Redeclaración del identificador {raw_name!r} en el ámbito {path!r}.",
                line,
                column,
            )
            return None
        mangled = self.mangle(raw_name, path)
        self.scoped_declarations[key] = mangled
        self.symbols.intern(
            "identifier",
            mangled,
            data_type=data_type,
            value=mangled,
            usage=usage,
            scope=path,
            **attrs,
        )
        return mangled

    def resolve_symbol(self, raw_name: str, line: int, column: int):
        """Busca desde el ámbito más interno hacia el global según reglas de alcance."""
        for i in range(len(self.scope_stack), 0, -1):
            prefix = ":".join(self.scope_stack[:i])
            mangled = self.scoped_declarations.get((prefix, raw_name))
            if mangled is not None:
                return self.symbols.find_by_text(mangled)
        self.error(
            "M_UNDECLARED",
            f"Identificador {raw_name!r} no declarado o fuera de alcance en el ámbito {self.current_scope_path!r}.",
            line,
            column,
        )
        return None

    # ------------------------------------------------------------------
    # Punto de entrada principal
    # ------------------------------------------------------------------
    def generate(self, tree: Node | None) -> list[RpnStep]:
        if tree is None or tree.kind != "program":
            return []
        prog_id: Lexeme = tree.children[0]
        prog_name = prog_id.value
        self.symbols.intern("identifier", prog_name, data_type="PROGRAM", value=prog_name, usage="programa")
        self.scope_stack.append(prog_name)

        # Separa declaraciones de sentencias ejecutables del programa principal
        declarations = [
            c for c in tree.children[1:]
            if isinstance(c, Node) and c.kind in {
                "variable_declaration", "object_declaration", "comptime_declaration",
                "function_declaration", "class_declaration", "invalid_declaration",
            }
        ]
        statements = [
            c for c in tree.children[1:]
            if isinstance(c, Node) and c.kind not in {
                "variable_declaration", "object_declaration", "comptime_declaration",
                "function_declaration", "class_declaration", "invalid_declaration",
            }
            and not isinstance(c, Lexeme)
        ]

        for decl in declarations:
            self.process_declaration(decl)

        self.emit("LABEL", f"BEGIN_MAIN ({prog_name})", line=tree.line, column=tree.column)
        for stmt in statements:
            self.process_statement(stmt)
        self.emit("LABEL", f"END_MAIN ({prog_name})", line=tree.line, column=tree.column)

        self.scope_stack.pop()
        self.symbols.rebuild_without_unscoped_identifiers()
        return self.steps

    # ------------------------------------------------------------------
    # Procesamiento de Declaraciones
    # ------------------------------------------------------------------
    def process_declaration(self, node: Node):
        kind = node.kind
        if kind == "variable_declaration":
            dtype = node.children[0].type  # INTEGER o SINGLEF
            for child in node.children[1:]:
                if isinstance(child, Lexeme) and child.type == "ID":
                    self.declare_symbol(child.value, dtype, "variable", child.line, child.column)

        elif kind == "comptime_declaration":
            dtype = node.children[1].type
            for child in node.children[2:]:
                if isinstance(child, Lexeme) and child.type == "ID":
                    mangled = self.declare_symbol(
                        child.value, dtype, "variable_comptime", child.line, child.column, comptime=True
                    )
                    if mangled:
                        self.comptime_values[mangled] = Decimal(0)

        elif kind == "object_declaration":
            class_lex: Lexeme = node.children[0]
            class_name = class_lex.value
            if class_name not in self.classes:
                self.error(
                    "M_UNDECLARED_CLASS",
                    f"La clase {class_name!r} no fue declarada antes de instanciar objetos.",
                    class_lex.line,
                    class_lex.column,
                )
            for child in node.children[1:]:
                if isinstance(child, Lexeme) and child.type == "ID":
                    mangled = self.declare_symbol(
                        child.value, class_name, "objeto", child.line, child.column, class_type=class_name
                    )
                    # Instancia en TS las ranuras de atributos posicionales del objeto
                    if mangled and class_name in self.classes:
                        attrs = self.resolve_class_positional_attributes(
                            class_name, child.line, child.column, report_errors=False
                        )
                        for idx, attr_info in enumerate(attrs):
                            slot_name = f"{mangled}[{idx}]"
                            self.symbols.intern(
                                "identifier",
                                slot_name,
                                data_type=attr_info.data_type,
                                value=slot_name,
                                usage="atributo_objeto",
                                owner_object=mangled,
                                attr_index=idx,
                                attr_name=attr_info.name,
                            )

        elif kind == "class_declaration":
            self.process_class_declaration(node)

        elif kind == "function_declaration":
            self.process_function_declaration(node)

    def _extract_parameters(self, children) -> list[Node]:
        return [c for c in children if isinstance(c, Node) and c.kind == "parameter"]

    def process_function_declaration(self, node: Node):
        ret_type = node.children[0].type
        func_lex: Lexeme = node.children[2]
        func_name = func_lex.value
        mangled_func = self.declare_symbol(
            func_name, ret_type, "funcion", func_lex.line, func_lex.column
        )
        func_scope = f"{self.current_scope_path}:{func_name}"
        self.scope_stack.append(func_name)

        param_nodes = self._extract_parameters(node.children)
        formal_params: list[tuple[str, str, str]] = []
        for pnode in param_nodes:
            ptype_lex: Lexeme = pnode.children[0]
            pid_lex: Lexeme = pnode.children[1]
            ptype = ptype_lex.type if ptype_lex.type in {"INTEGER", "SINGLEF"} else ptype_lex.value
            if ptype not in {"INTEGER", "SINGLEF"} and ptype not in self.classes:
                self.error(
                    "M_UNDECLARED_CLASS",
                    f"Tipo de parámetro {ptype!r} no declarado.",
                    ptype_lex.line,
                    ptype_lex.column,
                )
            pmangled = self.declare_symbol(
                pid_lex.value, ptype, "parametro", pid_lex.line, pid_lex.column
            )
            if pmangled:
                formal_params.append((ptype, pid_lex.value, pmangled))
                if ptype in self.classes:
                    attrs = self.resolve_class_positional_attributes(
                        ptype, pid_lex.line, pid_lex.column, report_errors=False
                    )
                    for idx, attr_info in enumerate(attrs):
                        slot_name = f"{pmangled}[{idx}]"
                        self.symbols.intern(
                            "identifier",
                            slot_name,
                            data_type=attr_info.data_type,
                            value=slot_name,
                            usage="atributo_objeto",
                            owner_object=pmangled,
                            attr_index=idx,
                            attr_name=attr_info.name,
                        )

        if mangled_func:
            sym = self.symbols.find_by_text(mangled_func)
            if sym:
                sym.attrs["params"] = formal_params
                sym.attrs["return_type"] = ret_type

        # Declaraciones locales y cuerpo de la función
        local_decls = [
            c for c in node.children
            if isinstance(c, Node) and c.kind in {
                "variable_declaration", "object_declaration", "comptime_declaration",
                "function_declaration", "class_declaration", "invalid_declaration",
            }
        ]
        body_stmts = [
            c for c in node.children
            if isinstance(c, Node) and c.kind not in {
                "parameter", "variable_declaration", "object_declaration",
                "comptime_declaration", "function_declaration", "class_declaration",
                "invalid_declaration",
            }
        ]

        for d in local_decls:
            self.process_declaration(d)

        prev_func = self.current_function
        self.current_function = mangled_func or func_scope
        self.emit("FUNC_BEGIN", f"FUNC_BEGIN {self.current_function}", line=func_lex.line, column=func_lex.column)
        has_return = False
        for stmt in body_stmts:
            if stmt.kind == "return":
                has_return = True
            self.process_statement(stmt)

        # Retorno por defecto si la función no tuvo sentencia ret explícita
        if not has_return:
            default_text = "0$i" if ret_type == "INTEGER" else "0.0"
            default_val = "0" if ret_type == "INTEGER" else "0.0"
            ref = self.symbols.intern("constant", default_text, ret_type, default_val)
            self.emit("CONST", default_text, symbol_ref=ref, data_type=ret_type,
                      line=func_lex.line, column=func_lex.column)
            self.emit("RET", f"RET {self.current_function}", data_type=ret_type,
                      line=func_lex.line, column=func_lex.column)

        self.emit("FUNC_END", f"FUNC_END {self.current_function}", line=func_lex.line, column=func_lex.column)
        self.current_function = prev_func
        self.scope_stack.pop()

    # ------------------------------------------------------------------
    # Clases, Import/Export (Tema 26), Atributos Posicionales (Tema 29) y Herencia Opción 3 (Tema 32)
    # ------------------------------------------------------------------
    def process_class_declaration(self, node: Node):
        class_lex: Lexeme = node.children[1]
        class_name = class_lex.value
        mangled_class = self.declare_symbol(
            class_name, "CLASS", "clase", class_lex.line, class_lex.column
        )
        if class_name in self.classes:
            return
        cinfo = ClassInfo(
            name=class_name,
            mangled_name=mangled_class or class_name,
            line=class_lex.line,
            column=class_lex.column,
        )
        self.classes[class_name] = cinfo
        self.scope_stack.append(class_name)
        prev_class = self.current_class
        self.current_class = class_name

        for child in node.children[2:]:
            if not isinstance(child, Node):
                continue
            if child.kind == "import":
                for tok in child.children:
                    if isinstance(tok, Lexeme) and tok.type == "ID":
                        if tok.value not in self.classes:
                            self.error(
                                "M_UNDECLARED_CLASS",
                                f"La clase importada {tok.value!r} no está declarada.",
                                tok.line,
                                tok.column,
                            )
                        cinfo.imports_from.append(tok.value)

            elif child.kind == "inheritance":
                for tok in child.children:
                    if isinstance(tok, Lexeme) and tok.type == "ID":
                        if tok.value not in self.classes:
                            self.error(
                                "M_UNDECLARED_CLASS",
                                f"La superclase {tok.value!r} en 'extends' no está declarada.",
                                tok.line,
                                tok.column,
                            )
                        cinfo.extends.append(tok.value)

            elif child.kind == "attribute_declaration":
                dtype = child.children[0].type
                export_node = next((x for x in child.children if isinstance(x, Node) and x.kind == "export"), None)
                exported_to = {
                    t.value for t in (export_node.children if export_node else ())
                    if isinstance(t, Lexeme) and t.type == "ID"
                }
                for tok in child.children[1:]:
                    if isinstance(tok, Lexeme) and tok.type == "ID":
                        mangled_attr = self.declare_symbol(
                            tok.value, dtype, "atributo", tok.line, tok.column,
                            exported_to=sorted(exported_to),
                        )
                        if mangled_attr:
                            cinfo.own_attributes.append(
                                ClassAttributeInfo(
                                    name=tok.value,
                                    mangled_name=mangled_attr,
                                    data_type=dtype,
                                    origin_class=class_name,
                                    exported_to=set(exported_to),
                                )
                            )

            elif child.kind == "method_declaration":
                self.process_method_declaration(child, cinfo)

        # Valida inmediatamente colisiones de herencia múltiple (Tema 32 Opción 3)
        self.validate_multiple_inheritance_ambiguity(cinfo)

        if mangled_class:
            sym = self.symbols.find_by_text(mangled_class)
            if sym:
                sym.attrs["imports_from"] = cinfo.imports_from
                sym.attrs["extends"] = cinfo.extends
                sym.attrs["attributes"] = [a.name for a in cinfo.own_attributes]
                sym.attrs["methods"] = list(cinfo.own_methods.keys())

        self.current_class = prev_class
        self.scope_stack.pop()

    def process_method_declaration(self, node: Node, cinfo: ClassInfo):
        ret_type = node.children[0].type
        meth_lex: Lexeme = node.children[1]
        meth_name = meth_lex.value
        export_node = next((x for x in node.children if isinstance(x, Node) and x.kind == "export"), None)
        exported_to = {
            t.value for t in (export_node.children if export_node else ())
            if isinstance(t, Lexeme) and t.type == "ID"
        }
        mangled_meth = self.declare_symbol(
            meth_name, ret_type, "metodo", meth_lex.line, meth_lex.column,
            exported_to=sorted(exported_to),
        )
        self.scope_stack.append(meth_name)

        # Parámetro implícito self para permitir acceso al objeto receptor dentro del método
        formal_params: list[tuple[str, str, str]] = []
        for pnode in self._extract_parameters(node.children):
            ptype_lex: Lexeme = pnode.children[0]
            pid_lex: Lexeme = pnode.children[1]
            ptype = ptype_lex.type if ptype_lex.type in {"INTEGER", "SINGLEF"} else ptype_lex.value
            if ptype not in {"INTEGER", "SINGLEF"} and ptype not in self.classes:
                self.error(
                    "M_UNDECLARED_CLASS",
                    f"Tipo de parámetro {ptype!r} no declarado.",
                    ptype_lex.line,
                    ptype_lex.column,
                )
            pmangled = self.declare_symbol(
                pid_lex.value, ptype, "parametro", pid_lex.line, pid_lex.column
            )
            if pmangled:
                formal_params.append((ptype, pid_lex.value, pmangled))
                if ptype in self.classes:
                    attrs = self.resolve_class_positional_attributes(
                        ptype, pid_lex.line, pid_lex.column, report_errors=False
                    )
                    for idx, attr_info in enumerate(attrs):
                        slot_name = f"{pmangled}[{idx}]"
                        self.symbols.intern(
                            "identifier",
                            slot_name,
                            data_type=attr_info.data_type,
                            value=slot_name,
                            usage="atributo_objeto",
                            owner_object=pmangled,
                            attr_index=idx,
                            attr_name=attr_info.name,
                        )

        if mangled_meth:
            sym = self.symbols.find_by_text(mangled_meth)
            if sym:
                sym.attrs["params"] = formal_params
                sym.attrs["return_type"] = ret_type
                sym.attrs["exported_to"] = sorted(exported_to)

        minfo = ClassMethodInfo(
            name=meth_name,
            mangled_name=mangled_meth or meth_name,
            return_type=ret_type,
            params=formal_params,
            origin_class=cinfo.name,
            exported_to=set(exported_to),
            node=node,
        )
        cinfo.own_methods[meth_name] = minfo

        local_decls = [
            c for c in node.children
            if isinstance(c, Node) and c.kind in {
                "variable_declaration", "object_declaration", "comptime_declaration",
                "function_declaration", "class_declaration", "invalid_declaration",
            }
        ]
        body_stmts = [
            c for c in node.children
            if isinstance(c, Node) and c.kind not in {
                "parameter", "variable_declaration", "object_declaration",
                "comptime_declaration", "function_declaration", "class_declaration",
                "export", "invalid_declaration",
            }
        ]
        for d in local_decls:
            self.process_declaration(d)

        prev_func = self.current_function
        self.current_function = minfo.mangled_name
        self.emit("FUNC_BEGIN", f"FUNC_BEGIN {minfo.mangled_name}", line=meth_lex.line, column=meth_lex.column)
        has_return = False
        for stmt in body_stmts:
            if stmt.kind == "return":
                has_return = True
            self.process_statement(stmt)
        if not has_return:
            default_text = "0$i" if ret_type == "INTEGER" else "0.0"
            default_val = "0" if ret_type == "INTEGER" else "0.0"
            ref = self.symbols.intern("constant", default_text, ret_type, default_val)
            self.emit("CONST", default_text, symbol_ref=ref, data_type=ret_type,
                      line=meth_lex.line, column=meth_lex.column)
            self.emit("RET", f"RET {minfo.mangled_name}", data_type=ret_type,
                      line=meth_lex.line, column=meth_lex.column)
        self.emit("FUNC_END", f"FUNC_END {minfo.mangled_name}", line=meth_lex.line, column=meth_lex.column)
        self.current_function = prev_func
        self.scope_stack.pop()

    def validate_multiple_inheritance_ambiguity(self, cinfo: ClassInfo):
        """Tema 32 (Opción 3): informa error si las clases padres poseen atributos o métodos con igual nombre."""
        own_attr_names = {a.name for a in cinfo.own_attributes}
        seen_parent_attrs: dict[str, str] = {}
        seen_parent_methods: dict[str, str] = {}

        for parent_name in cinfo.extends:
            parent = self.classes.get(parent_name)
            if not parent:
                continue
            for attr in parent.own_attributes:
                if attr.name in own_attr_names:
                    continue
                if attr.name in seen_parent_attrs and seen_parent_attrs[attr.name] != parent_name:
                    self.error(
                        "M_AMBIGUOUS_INHERITANCE",
                        f"Ambigüedad por herencia múltiple (Tema 32 Opción 3): el atributo {attr.name!r} "
                        f"está definido tanto en {seen_parent_attrs[attr.name]!r} como en {parent_name!r}.",
                        cinfo.line,
                        cinfo.column,
                    )
                else:
                    seen_parent_attrs[attr.name] = parent_name

            for mname in parent.own_methods:
                if mname in cinfo.own_methods:
                    continue
                if mname in seen_parent_methods and seen_parent_methods[mname] != parent_name:
                    self.error(
                        "M_AMBIGUOUS_INHERITANCE",
                        f"Ambigüedad por herencia múltiple (Tema 32 Opción 3): el método {mname!r} "
                        f"está definido tanto en {seen_parent_methods[mname]!r} como en {parent_name!r}.",
                        cinfo.line,
                        cinfo.column,
                    )
                else:
                    seen_parent_methods[mname] = parent_name

    def resolve_class_positional_attributes(
        self, class_name: str, line: int, column: int, report_errors: bool = True
    ) -> list[ClassAttributeInfo]:
        """Orden posicional: 1) atributos propios, 2) heredados/importados visibles."""
        cinfo = self.classes.get(class_name)
        if not cinfo:
            return []
        result = list(cinfo.own_attributes)
        seen_names = {a.name for a in result}

        # Padres e importados
        external_sources = list(dict.fromkeys(cinfo.extends + cinfo.imports_from))
        for src_name in external_sources:
            src = self.classes.get(src_name)
            if not src:
                continue
            is_imported = src_name in cinfo.imports_from
            is_extended = src_name in cinfo.extends
            for attr in src.own_attributes:
                if attr.name in seen_names:
                    continue
                # Tema 26: si proviene de import/extends con export_to definido, verificar permiso
                if attr.exported_to and class_name not in attr.exported_to:
                    continue
                if is_imported or (is_extended and (not attr.exported_to or class_name in attr.exported_to)):
                    result.append(attr)
                    seen_names.add(attr.name)
        return result

    def resolve_method(self, class_name: str, method_name: str, line: int, column: int) -> ClassMethodInfo | None:
        """Busca el método en la clase del objeto, o en sus padres/importados aplicando Temas 26 y 32."""
        cinfo = self.classes.get(class_name)
        if not cinfo:
            self.error("M_UNDECLARED_CLASS", f"Clase {class_name!r} no declarada.", line, column)
            return None

        # 1. Definido en la propia clase
        if method_name in cinfo.own_methods:
            minfo = cinfo.own_methods[method_name]
            # Si se invoca desde otra clase y el método tiene lista export_to restringida, validar
            if self.current_class and self.current_class != class_name:
                caller_cls = self.classes.get(self.current_class)
                if (
                    caller_cls
                    and class_name not in caller_cls.imports_from
                    and class_name not in caller_cls.extends
                ):
                    self.error(
                        "M_VISIBILITY",
                        f"La clase {self.current_class!r} no importa de {class_name!r} para usar el método {method_name!r}.",
                        line,
                        column,
                    )
                    return None
                if minfo.exported_to and self.current_class not in minfo.exported_to:
                    self.error(
                        "M_VISIBILITY",
                        f"El método {method_name!r} de {class_name!r} no fue exportado a {self.current_class!r}.",
                        line,
                        column,
                    )
                    return None
            return minfo

        # 2. Buscar en clases base (extends) e importadas (import from)
        candidates: list[ClassMethodInfo] = []
        sources = list(dict.fromkeys(cinfo.extends + cinfo.imports_from))
        for src_name in sources:
            src = self.classes.get(src_name)
            if not src or method_name not in src.own_methods:
                continue
            cand = src.own_methods[method_name]
            if cand.exported_to and class_name not in cand.exported_to:
                self.error(
                    "M_VISIBILITY",
                    f"El método {method_name!r} de {src_name!r} no está exportado hacia {class_name!r}.",
                    line,
                    column,
                )
                return None
            candidates.append(cand)

        if len(candidates) > 1:
            origins = ", ".join(repr(c.origin_class) for c in candidates)
            self.error(
                "M_AMBIGUOUS_INHERITANCE",
                f"Ambigüedad al invocar el método {method_name!r} sobre {class_name!r}: existe en múltiples superclases ({origins}).",
                line,
                column,
            )
            return None
        if len(candidates) == 1:
            return candidates[0]

        self.error(
            "M_UNDECLARED_METHOD",
            f"El método {method_name!r} no está declarado ni es visible en la clase {class_name!r}.",
            line,
            column,
        )
        return None

    # ------------------------------------------------------------------
    # Evaluación en Tiempo de Compilación (Tema 22 - comptime)
    # ------------------------------------------------------------------
    def evaluate_comptime_expr(self, node) -> Decimal | None:
        """Evalúa una expresión en compilación si todos sus operandos son constantes o comptime."""
        if isinstance(node, Lexeme):
            if node.type == "ID":
                sym = self.resolve_symbol(node.value, node.line, node.column)
                if sym and sym.usage == "variable_comptime" and sym.text in self.comptime_values:
                    return self.comptime_values[sym.text]
            return None

        if not isinstance(node, Node):
            return None

        if node.kind == "constant":
            lit: Lexeme = node.children[0]
            return Decimal(lit.value)

        if node.kind == "conversion":
            inner = self.evaluate_comptime_expr(node.children[2])
            return Decimal(int(inner)) if inner is not None else None

        if node.kind == "binary":
            left = self.evaluate_comptime_expr(node.children[0])
            op: Lexeme = node.children[1]
            right = self.evaluate_comptime_expr(node.children[2])
            if left is None or right is None:
                return None
            if op.text == "+":
                return left + right
            if op.text == "-":
                return left - right
            if op.text == "*":
                return left * right
            if op.text == "/":
                return (left // right if left == int(left) and right == int(right) else left / right) if right != 0 else None
        return None

    def expr_mentions_comptime(self, node) -> bool:
        if isinstance(node, Lexeme) and node.type == "ID":
            for i in range(len(self.scope_stack), 0, -1):
                prefix = ":".join(self.scope_stack[:i])
                mangled = self.scoped_declarations.get((prefix, node.value))
                if mangled:
                    sym = self.symbols.find_by_text(mangled)
                    return bool(sym and sym.usage == "variable_comptime")
            return False
        if isinstance(node, Node):
            return any(self.expr_mentions_comptime(c) for c in node.children)
        return False

    # ------------------------------------------------------------------
    # Sentencias Ejecutables y Estructuras de Control
    # ------------------------------------------------------------------
    def process_statement(self, node: Node):
        kind = node.kind
        if kind == "block":
            for child in node.children:
                if isinstance(child, Node):
                    self.process_statement(child)

        elif kind == "assignment":
            self.process_assignment(node)

        elif kind == "output":
            arg = node.children[2]
            if isinstance(arg, Lexeme) and arg.type == "STRING":
                self.emit("STRING", f'"{arg.value}"', symbol_ref=arg.symbol, data_type="STRING",
                          line=arg.line, column=arg.column)
            else:
                self.process_expression(arg)
            self.emit("POUT", "POUT", line=node.line, column=node.column)

        elif kind == "return":
            expr = node.children[2]
            dtype = self.process_expression(expr)
            if self.current_function:
                fn_sym = self.symbols.find_by_text(self.current_function)
                expected_ret = fn_sym.data_type if fn_sym else None
                if expected_ret and dtype and expected_ret != dtype:
                    self.error(
                        "M_TYPE_MISMATCH",
                        f"Tipo de retorno incompatible en {self.current_function!r}: se esperaba {expected_ret} y se retornó {dtype}.",
                        node.line,
                        node.column,
                    )
            self.emit("RET", f"RET {self.current_function or ''}".strip(), data_type=dtype,
                      line=node.line, column=node.column)

        elif kind == "call_statement":
            inv_node = node.children[0]
            self.process_invocation(inv_node, discard_result=True)

        elif kind == "if":
            self.process_if(node)

        elif kind == "repeat":
            self.process_repeat(node)

    def process_assignment(self, node: Node):
        target = node.children[0]
        expr = node.children[2]

        # Caso 1: Asignación a un identificador simple (variable o comptime)
        if isinstance(target, Lexeme) and target.type == "ID":
            sym = self.resolve_symbol(target.value, target.line, target.column)
            if sym is None:
                self.process_expression(expr)
                return
            if sym.usage not in {"variable", "variable_comptime", "parametro"}:
                self.error(
                    "M_INVALID_USAGE",
                    f"No se puede asignar a {target.value!r} porque su uso es {sym.usage!r}.",
                    target.line,
                    target.column,
                )
                return
            if sym.usage == "variable_comptime":
                val = self.evaluate_comptime_expr(expr)
                if val is None:
                    self.error(
                        "M_COMPTIME_DYNAMIC",
                        f"La variable comptime {target.value!r} sólo puede recibir expresiones evaluables en compilación.",
                        target.line,
                        target.column,
                    )
                    return
                self.comptime_values[sym.text] = val
                sym.attrs["comptime_value"] = str(val)
                # Registra la constante resultante y emite la asignación con el valor conocido
                const_text = f"{int(val)}$i" if sym.data_type == "INTEGER" else str(val)
                const_val = str(int(val)) if sym.data_type == "INTEGER" else str(val)
                cref = self.symbols.intern("constant", const_text, sym.data_type, const_val)
                self.emit("CONST", const_text, symbol_ref=cref, data_type=sym.data_type,
                          line=target.line, column=target.column)
                self.emit("ID", sym.text, symbol_ref=sym.reference, data_type=sym.data_type,
                          line=target.line, column=target.column)
                self.emit(":=", ":=", data_type=sym.data_type, line=node.line, column=node.column)
                return

            self.process_expression(expr)
            self.emit("ID", sym.text, symbol_ref=sym.reference, data_type=sym.data_type,
                      line=target.line, column=target.column)
            self.emit(":=", ":=", data_type=sym.data_type, line=node.line, column=node.column)
            return

        # Caso 2: Asignación a un atributo posicional obj[idx] := expr (Tema 29)
        if isinstance(target, Node) and target.kind == "attribute":
            self.process_expression(expr)
            slot_sym = self.resolve_positional_attribute_access(target)
            if slot_sym is not None:
                self.emit("ID", slot_sym.text, symbol_ref=slot_sym.reference,
                          data_type=slot_sym.data_type, line=target.line, column=target.column)
                self.emit(":=", ":=", data_type=slot_sym.data_type, line=node.line, column=node.column)

    def process_if(self, node: Node):
        cond_node = node.children[2]
        then_block = node.children[4]
        else_node = node.children[5] if len(node.children) > 5 and isinstance(node.children[5], Node) and node.children[5].kind == "else" else None

        self.process_condition(cond_node)
        bf_target_step = self.emit("JUMP_TARGET", "[?]", line=cond_node.line, column=cond_node.column)
        self.emit("BF", "BF", line=cond_node.line, column=cond_node.column)

        self.process_statement(then_block)

        if else_node is not None:
            # Completa el BF con #paso_actual + 2 (salta el blanco del BI y el BI)
            self.patch_step(bf_target_step, len(self.steps) + 3)
            bi_target_step = self.emit("JUMP_TARGET", "[?]", line=else_node.line, column=else_node.column)
            self.emit("BI", "BI", line=else_node.line, column=else_node.column)
            self.process_statement(else_node.children[1])
            self.patch_step(bi_target_step, len(self.steps) + 1)
        else:
            self.patch_step(bf_target_step, len(self.steps) + 1)

    def process_repeat(self, node: Node):
        """Tema 12: repeat <bloque> until (<condicion>);"""
        body_block = node.children[1]
        cond_node = node.children[4]

        # Chequeo Tema 22: si la condición usa una variable comptime, no puede compararse con una variable dinámica
        if self.expr_mentions_comptime(cond_node):
            left_val = self.evaluate_comptime_expr(cond_node.children[0])
            right_val = self.evaluate_comptime_expr(cond_node.children[2])
            if left_val is None or right_val is None:
                self.error(
                    "M_COMPTIME_DYNAMIC",
                    "Una condición de iteración con variables 'comptime' no puede depender de variables de tiempo de ejecución.",
                    cond_node.line,
                    cond_node.column,
                )

        start_step = len(self.steps) + 1
        self.emit("LABEL", f"REPEAT_START [{start_step}]", line=node.line, column=node.column)
        self.process_statement(body_block)
        self.process_condition(cond_node)
        self.emit("JUMP_TARGET", f"[{start_step}]", line=cond_node.line, column=cond_node.column)
        self.emit("BF", "BF", line=cond_node.line, column=cond_node.column)

    def process_condition(self, node: Node):
        left = node.children[0]
        comp: Lexeme = node.children[1]
        right = node.children[2]
        self.process_expression(left)
        self.process_expression(right)
        self.emit(comp.text, comp.text, line=comp.line, column=comp.column)

    # ------------------------------------------------------------------
    # Expresiones, Asignaciones Internas (Tema 17) e Invocaciones (Tema 19)
    # ------------------------------------------------------------------
    def process_expression(self, node) -> str | None:
        if isinstance(node, Lexeme) and node.type == "ID":
            sym = self.resolve_symbol(node.value, node.line, node.column)
            if sym is None:
                return None
            if sym.usage == "variable_comptime":
                val = self.comptime_values.get(sym.text, Decimal(0))
                const_text = f"{int(val)}$i" if sym.data_type == "INTEGER" else str(val)
                const_val = str(int(val)) if sym.data_type == "INTEGER" else str(val)
                cref = self.symbols.intern("constant", const_text, sym.data_type, const_val)
                self.emit("CONST", const_text, symbol_ref=cref, data_type=sym.data_type,
                          line=node.line, column=node.column)
                return sym.data_type
            if sym.usage not in {"variable", "parametro"}:
                self.error(
                    "M_INVALID_USAGE",
                    f"El identificador {node.value!r} ({sym.usage}) no puede usarse como operando en una expresión.",
                    node.line,
                    node.column,
                )
                return None
            self.emit("ID", sym.text, symbol_ref=sym.reference, data_type=sym.data_type,
                      line=node.line, column=node.column)
            return sym.data_type

        if not isinstance(node, Node):
            return None

        if node.kind == "constant":
            lit: Lexeme = node.children[0]
            dtype = "INTEGER" if lit.type == "INT" else "SINGLEF"
            self.emit("CONST", lit.text, symbol_ref=lit.symbol, data_type=dtype,
                      line=lit.line, column=lit.column)
            return dtype

        if node.kind == "binary":
            lt = self.process_expression(node.children[0])
            op: Lexeme = node.children[1]
            rt = self.process_expression(node.children[2])
            res_type = lt if lt == rt else (lt or rt)
            self.emit(op.text, op.text, data_type=res_type, line=op.line, column=op.column)
            return res_type

        if node.kind == "conversion":
            # Tema 34: toi(expresion) convierte de SINGLEF a INTEGER
            inner_type = self.process_expression(node.children[2])
            self.emit("TOI", "toi", data_type="INTEGER", line=node.line, column=node.column)
            return "INTEGER"

        if node.kind == "inline_assignment":
            # Tema 17: ID = (plain_expression)
            target_lex: Lexeme = node.children[0]
            expr = node.children[3]
            rhs_type = self.process_expression(expr)
            sym = self.resolve_symbol(target_lex.value, target_lex.line, target_lex.column)
            if sym is not None:
                if sym.usage not in {"variable", "parametro"}:
                    self.error(
                        "M_INVALID_USAGE",
                        f"No se puede realizar asignación interna sobre {target_lex.value!r} ({sym.usage}).",
                        target_lex.line,
                        target_lex.column,
                    )
                self.emit("ID", sym.text, symbol_ref=sym.reference, data_type=sym.data_type,
                          line=target_lex.line, column=target_lex.column)
                self.emit("=", "=", data_type=sym.data_type, line=node.line, column=node.column)
                return sym.data_type
            return rhs_type

        if node.kind == "attribute":
            slot_sym = self.resolve_positional_attribute_access(node)
            if slot_sym is not None:
                self.emit("ID", slot_sym.text, symbol_ref=slot_sym.reference,
                          data_type=slot_sym.data_type, line=node.line, column=node.column)
                return slot_sym.data_type
            return None

        if node.kind == "invocation":
            return self.process_invocation(node, discard_result=False)

        return None

    def resolve_positional_attribute_access(self, node: Node):
        """Tema 29: ID [ index ] -> verifica objeto, clase, visibilidad e índice."""
        obj_lex: Lexeme = node.children[0]
        idx_item = node.children[2]
        obj_sym = self.resolve_symbol(obj_lex.value, obj_lex.line, obj_lex.column)
        if obj_sym is None:
            return None
        if obj_sym.usage not in {"objeto", "parametro"} or obj_sym.data_type not in self.classes:
            self.error(
                "M_NOT_AN_OBJECT",
                f"El identificador {obj_lex.value!r} no es un objeto de una clase declarada.",
                obj_lex.line,
                obj_lex.column,
            )
            return None

        attrs = self.resolve_class_positional_attributes(obj_sym.data_type, node.line, node.column)
        if not attrs:
            self.error(
                "M_ATTRIBUTE_INDEX",
                f"La clase {obj_sym.data_type!r} no posee atributos visibles para el acceso posicional.",
                node.line,
                node.column,
            )
            return None

        # Determina el índice si es constante o variable entera
        index_val: int | None = None
        if isinstance(idx_item, Node) and idx_item.kind == "constant":
            lit: Lexeme = idx_item.children[0]
            if lit.type != "INT":
                self.error(
                    "M_ATTRIBUTE_INDEX_TYPE",
                    f"El índice de acceso posicional a atributo debe ser INTEGER, se encontró SINGLEF ({lit.text!r}).",
                    lit.line,
                    lit.column,
                )
                return None
            index_val = int(lit.value)
        elif isinstance(idx_item, Lexeme) and idx_item.type == "ID":
            idx_sym = self.resolve_symbol(idx_item.value, idx_item.line, idx_item.column)
            if idx_sym is None:
                return None
            if idx_sym.data_type != "INTEGER":
                self.error(
                    "M_ATTRIBUTE_INDEX_TYPE",
                    f"La variable de índice posicional {idx_item.value!r} debe ser de tipo INTEGER.",
                    idx_item.line,
                    idx_item.column,
                )
                return None
            if idx_sym.usage == "variable_comptime" and idx_sym.text in self.comptime_values:
                index_val = int(self.comptime_values[idx_sym.text])
            else:
                index_val = 0  # Para variables dinámicas se valida tipo y se referencia la base 0

        if index_val is not None and (index_val < 0 or index_val >= len(attrs)):
            self.error(
                "M_ATTRIBUTE_INDEX",
                f"Índice posicional {index_val} fuera de rango para la clase {obj_sym.data_type!r} "
                f"(tiene {len(attrs)} atributo(s) accesible(s)).",
                node.line,
                node.column,
            )
            return None

        chosen_idx = index_val or 0
        attr_info = attrs[chosen_idx]
        # Verifica visibilidad (Tema 26) si se accede desde otra clase
        if (
            self.current_class
            and self.current_class != attr_info.origin_class
            and attr_info.exported_to
            and self.current_class not in attr_info.exported_to
        ):
            self.error(
                "M_VISIBILITY",
                f"El atributo posicional {chosen_idx} ({attr_info.name!r}) de {attr_info.origin_class!r} "
                f"no fue exportado a {self.current_class!r}.",
                node.line,
                node.column,
            )
            return None

        slot_name = f"{obj_sym.text}[{chosen_idx}]"
        ref = self.symbols.intern(
            "identifier",
            slot_name,
            data_type=attr_info.data_type,
            value=slot_name,
            usage="atributo_objeto",
            owner_object=obj_sym.text,
            attr_index=chosen_idx,
            attr_name=attr_info.name,
        )
        return self.symbols.get(ref)

    def process_invocation(self, node: Node, discard_result: bool = False) -> str | None:
        """Tema 19: Invocación con orden de evaluación obligatorio de parámetros reales."""
        order_node = next(c for c in node.children if isinstance(c, Node) and c.kind == "evaluation_order")
        order_lexemes = [c for c in order_node.children if isinstance(c, Lexeme) and c.type == "INT"]
        order_indices = [int(lex.value) for lex in order_lexemes]

        # Distingue llamada a función f(args)[orden] vs llamada a método obj.m(args)[orden]
        is_method_call = isinstance(node.children[1], Lexeme) and node.children[1].text == "."
        if is_method_call:
            obj_lex: Lexeme = node.children[0]
            meth_lex: Lexeme = node.children[2]
            arg_nodes = [
                c for c in node.children[4:-1]
                if not (isinstance(c, Lexeme) and c.text in {"(", ")", ","})
            ]
            obj_sym = self.resolve_symbol(obj_lex.value, obj_lex.line, obj_lex.column)
            if obj_sym is None:
                return None
            if obj_sym.usage not in {"objeto", "parametro"} or obj_sym.data_type not in self.classes:
                self.error(
                    "M_NOT_AN_OBJECT",
                    f"El receptor {obj_lex.value!r} de la invocación a método no es un objeto válido.",
                    obj_lex.line,
                    obj_lex.column,
                )
                return None
            minfo = self.resolve_method(obj_sym.data_type, meth_lex.value, meth_lex.line, meth_lex.column)
            if minfo is None:
                return None
            formal_params = minfo.params
            callee_name = minfo.mangled_name
            return_type = minfo.return_type
        else:
            fn_lex: Lexeme = node.children[0]
            arg_nodes = [
                c for c in node.children[2:-1]
                if not (isinstance(c, Lexeme) and c.text in {"(", ")", ","})
            ]
            fn_sym = self.resolve_symbol(fn_lex.value, fn_lex.line, fn_lex.column)
            if fn_sym is None:
                return None
            if fn_sym.usage != "funcion":
                self.error(
                    "M_INVALID_USAGE",
                    f"El identificador {fn_lex.value!r} ({fn_sym.usage}) no es una función invocable.",
                    fn_lex.line,
                    fn_lex.column,
                )
                return None
            formal_params = fn_sym.attrs.get("params", [])
            callee_name = fn_sym.text
            return_type = fn_sym.data_type

        # Chequeo de cantidad de argumentos reales vs parámetros formales vs lista de orden
        expected_count = len(formal_params)
        if len(arg_nodes) != expected_count:
            self.error(
                "M_ARITY_MISMATCH",
                f"Cantidad de argumentos incorrecta al invocar {callee_name!r}: "
                f"se esperaban {expected_count} y se recibieron {len(arg_nodes)}.",
                node.line,
                node.column,
            )
            return return_type

        if len(order_indices) != expected_count:
            self.error(
                "M_ORDER_ARITY_MISMATCH",
                f"La lista de orden de evaluación tiene {len(order_indices)} constante(s), "
                f"pero la invocación a {callee_name!r} tiene {expected_count} parámetro(s).",
                order_node.line,
                order_node.column,
            )
            return return_type

        if sorted(order_indices) != list(range(1, expected_count + 1)):
            self.error(
                "M_INVALID_ORDER",
                f"El orden de evaluación {order_indices} debe ser una permutación válida de 1..{expected_count}.",
                order_node.line,
                order_node.column,
            )
            return return_type

        # Genera en la Polaca Inversa la evaluación y copia por valor en el orden indicado por [...]
        for pos in order_indices:
            arg_idx = pos - 1
            arg_expr = arg_nodes[arg_idx]
            ptype, pname, pmangled = formal_params[arg_idx]
            param_sym = self.symbols.find_by_text(pmangled)
            arg_type = self.process_expression(arg_expr)
            if arg_type and ptype and arg_type != ptype:
                self.error(
                    "M_TYPE_MISMATCH",
                    f"Incompatibilidad de tipos en el parámetro {pname!r} (#{pos}) al invocar {callee_name!r}: "
                    f"se esperaba {ptype} y se pasó {arg_type}.",
                    node.line,
                    node.column,
                )
            self.emit(
                "PARAM_TARGET",
                pmangled,
                symbol_ref=param_sym.reference if param_sym else None,
                data_type=ptype,
                line=node.line,
                column=node.column,
            )
            self.emit("PARAM_ASSIGN", ":=", data_type=ptype, line=node.line, column=node.column)

        self.emit("CALL", f"CALL {callee_name}", data_type=return_type, line=node.line, column=node.column)
        return return_type