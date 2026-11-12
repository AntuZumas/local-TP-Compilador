# Documentación de diseño — Grupo 40

Estado al 14 de septiembre de 2026: prototipo ejecutable Python + SLY 0.5,
verificado con 30 pruebas y tablas LALR sin conflictos. Las interpretaciones del
prototipo siguen pendientes de ratificación por el grupo/cátedra.

- [Cómo ejecutarlo](../README.md).
- [Decisiones implementadas y límites](gramatica/implementacion.md).
- [BNF exportada del parser](gramatica/gramatica.bnf).
- [Registro de uso de IA](ia.md).

- [Decisiones del analizador léxico](analizador-lexico/decisiones.md): requisitos,
  alternativas, recomendaciones, contrato con el parser y pruebas necesarias.
- [Propuesta de gramática](gramatica/propuesta.md): notación, reglas ejecutables y cobertura
  de los temas asignados.
- [Decisiones de gramática](gramatica/decisiones.md): preguntas que resolver,
  ejemplos y criterios para cerrar el diseño.

## Fuentes

Los PDF son material de referencia y no se copian al repositorio con estos
documentos. Las páginas citadas son páginas del PDF, contadas desde 1.

| Código | Material |
|---|---|
| T | `03.Análisis Léxico.pdf`, 77 páginas: teoría de la cátedra. |
| TP1 | `Tp01-2026.pdf`, 3 páginas: requisitos léxicos de 2026. |
| TP2 | `Tp02-2026.pdf`, 9 páginas: sintaxis y temas particulares de 2026. |
| P | `Presentacion TP1- Compiladores 2026.pdf`, 40 páginas. |
| G | [Informe del grupo 40](https://docs.google.com/document/d/1BkzEz_rgfqBG1hilX8VvjYJVZF7BAFCQrXNVjToD9vk/edit): temas 3, 7, 10, 12, 15, 17, 19, 22, 26, 29, 32 y 34. |

La teoría enseña mecanismos con ejemplos de otros lenguajes. Para determinar
qué acepta nuestro compilador se usan las consignas de 2026 y los temas del
grupo; las contradicciones se registran para consultar al docente.

El prototipo usa Python + SLY; queda confirmar con la cátedra la exigencia de
matrices para el léxico. TP2 indica entrega el 18/09/2026; confirmar cualquier
actualización con la cátedra. Las opciones iniciales están conservadas en los
catálogos de decisiones; las efectivamente implementadas están en el documento
de implementación.

## Convenciones de estado

- **Requisito:** está expresado en la consigna.
- **Propuesta:** recomendación técnica que el grupo puede aceptar o cambiar.
- **Consulta:** falta aclarar una contradicción o un punto no especificado.
- **Pendiente:** falta tomar o verificar una decisión.

Los ejemplos conceptuales de los catálogos siguen siendo ilustrativos. Los
archivos de `examples/` y las pruebas ejercitan la API del prototipo. Ninguna
salida sintáctica demuestra que el programa sea semánticamente válido.
