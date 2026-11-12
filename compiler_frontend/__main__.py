"""Uso: python -m compiler_frontend archivo.src [--json] [--tokens]."""

import argparse
import json
import sys
from pathlib import Path

from . import analyze, grammar_report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Prototipo de gramática del grupo 40")
    parser.add_argument("source", nargs="?", type=Path)
    parser.add_argument("--json", action="store_true", help="Árbol, tokens, TS y diagnósticos JSON")
    parser.add_argument("--tokens", action="store_true", help="Mostrar listado de tokens")
    parser.add_argument("--grammar-report", action="store_true", help="Producciones y conflictos")
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
    else:
        print("Análisis válido" if result.ok else "Análisis con errores")
        for diagnostic in result.diagnostics:
            print(f"{diagnostic.line}:{diagnostic.column} {diagnostic.severity} "
                  f"{diagnostic.code}: {diagnostic.message}")
        for node in result.structures:
            print(f"{node.line}:{node.column} {node.kind}")
        if args.tokens:
            print("\nTokens:")
            for token in result.tokens:
                print(f"{token.line}:{token.column} {token.type} {token.text!r} TS={token.symbol}")
        print("\nTabla de símbolos:")
        for symbol in result.symbols.entries:
            print(f"S{symbol.reference} {symbol.category} {symbol.data_type} "
                  f"{symbol.text!r} valor={symbol.value!r}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())