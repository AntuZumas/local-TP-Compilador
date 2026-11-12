"""Exporta las producciones reales de SLY; --check detecta documentación desactualizada."""

import argparse
from pathlib import Path
import sys

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from compiler_frontend import grammar_report


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("--check", action="store_true")
    args = cli.parse_args()
    report = grammar_report()
    if report["shift_reduce"] or report["reduce_reduce"]:
        raise SystemExit("No exportar: la gramática tiene conflictos pendientes.")
    text = "\n".join([
        "# Gramática generada desde compiler_frontend/parser.py con SLY 0.5.",
        "# No editar a mano. Regenerar: python scripts/export_grammar.py",
        f"# Estados LALR: {report['states']}; shift/reduce: 0; reduce/reduce: 0.",
        "# <empty> = secuencia vacía; error = símbolo especial de recuperación.",
        "# La primera producción es el inicio aumentado del generador.",
        "", *report["productions"], "",
    ])
    target = root / "docs/gramatica/gramatica.bnf"
    if args.check:
        if not target.exists() or target.read_text() != text:
            raise SystemExit("Regenerar docs/gramatica/gramatica.bnf")
        print("Gramática documentada sincronizada con el parser.")
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        print(target.relative_to(root))


if __name__ == "__main__":
    main()
