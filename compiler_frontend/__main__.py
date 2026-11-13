"""Uso: python -m compiler_frontend archivo.src [--json] [--tokens] [--structures] [--asm salida.asm]."""

import argparse
import json
import sys
from pathlib import Path

from . import analyze, grammar_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Compilador Grupo 40 (TP1 a TP4)")
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--json", action="store_true", help="Salida completa en formato JSON")
    parser.add_argument("--tokens", action="store_true", help="Mostrar listado de tokens (TP1)")
    parser.add_argument("--structures", action="store_true", help="Mostrar estructuras sintácticas (TP2)")
    parser.add_argument("--asm", type=Path, help="Ruta donde guardar el código Assembler generado")
    parser.add_argument("--grammar-report", action="store_true", help="Producciones y conflictos LALR")
    args = parser.parse_args(argv)

    if args.grammar_report:
        report = grammar_report()
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 1 if report["shift_reduce"] or report["reduce_reduce"] else 0

    if args.source is None:
        parser.error("indicá un archivo fuente o --grammar-report")

    try:
        source = args.source.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as error:
        print(f"No se pudo leer {args.source}: {error}", file=sys.stderr)
        return 2

    result = analyze(source)
    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
        return 0 if result.ok else 1

    print("Análisis válido" if result.ok else "Análisis con errores")

    # 1) Errores generados en tiempo de compilación (Léxicos, Sintácticos y Semánticos)
    if result.diagnostics:
        print("\nDiagnósticos:")
        for diagnostic in result.diagnostics:
            print(f"Línea {diagnostic.line}:{diagnostic.column} [{diagnostic.phase}/{diagnostic.severity}] "
                  f"{diagnostic.code}: {diagnostic.message}")

    # Salidas opcionales de TP1/TP2 (ocultas por defecto según consigna de TP3/TP4)
    if args.structures:
        print("\nEstructuras sintácticas:")
        for node in result.structures:
            print(f"{node.line}:{node.column} {node.kind}")

    if args.tokens:
        print("\nTokens:")
        for token in result.tokens:
            print(f"{token.line}:{token.column} {token.type} {token.text!r} TS={token.symbol}")

    # 2) Representación Intermedia: Polaca Inversa numerada
    if result.rpn:
        print("\nCódigo Intermedio (Polaca Inversa):")
        for step in result.rpn:
            print(f"{step.index:03d}: {step.label}")

    # 3) Contenido de la Tabla de Símbolos
    print("\nTabla de símbolos:")
    for symbol in result.symbols.entries:
        extras = f" attrs={symbol.attrs}" if symbol.attrs else ""
        print(f"S{symbol.reference} uso={symbol.usage} tipo={symbol.data_type} "
              f"nombre={symbol.text!r} valor={symbol.value!r}{extras}")

    # 4) Archivo con el código Assembler (TP4)
    if result.ok and result.assembler:
        asm_path = args.asm if args.asm is not None else args.source.with_suffix(".asm")
        try:
            asm_path.write_text(result.assembler, encoding="utf-8")
            print(f"\nCódigo Assembler generado en: {asm_path}")
        except OSError as error:
            print(f"No se pudo escribir el archivo Assembler {asm_path}: {error}", file=sys.stderr)

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())