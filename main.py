"""Creador de horarios — punto de entrada.

Uso:
    python main.py ejemplos/cursos.csv
    python main.py ejemplos/cursos.csv --top 5 --imagen mi_horario.png
"""

import argparse
import time

from horario.datos import leer_cursos
from horario.buscador import buscar, total_combinaciones
from horario.mostrar import imprimir, guardar_imagen


def main():
    parser = argparse.ArgumentParser(description="Arma el mejor horario sin cruces ni huecos.")
    parser.add_argument("csv", help="archivo CSV con los cursos disponibles")
    parser.add_argument("--top", type=int, default=3, help="cuántos horarios mostrar (por defecto 3)")
    parser.add_argument("--imagen", default="horario.png", help="dónde guardar la imagen del mejor horario")
    args = parser.parse_args()

    cursos = leer_cursos(args.csv)
    print(f"Materias: {len(cursos)}")
    for materia, grupos in cursos.items():
        print(f"  - {materia}: {len(grupos)} grupo(s)")
    print(f"Combinaciones posibles: {total_combinaciones(cursos)}")

    t0 = time.perf_counter()
    mejores, nodos = buscar(cursos, top=args.top)
    t = time.perf_counter() - t0

    if not mejores:
        print("\nNo existe ningún horario sin cruces con estos grupos.")
        return

    print(f"Nodos revisados: {nodos} | tiempo: {t * 1000:.1f} ms")
    for i, (c, grupos) in enumerate(mejores, start=1):
        imprimir(grupos, titulo=f"Opción {i} (puntaje {c:.2f})")

    guardar_imagen(mejores[0][1], args.imagen, titulo="Mejor horario")
    print(f"\nImagen del mejor horario guardada en: {args.imagen}")


if __name__ == "__main__":
    main()
