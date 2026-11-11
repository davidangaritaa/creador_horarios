"""Creador de horarios — punto de entrada.

Uso:
    python main.py ejemplos/cursos.csv
    python main.py ejemplos/cursos.csv --top 5 --imagen mi_horario.png
    python main.py ejemplos/cursos.csv --bloquear "Mar 14:00-18:00" --bloquear "Jue 14:00-18:00"
"""

import argparse
import time

from horario.datos import leer_cursos, leer_bloqueo, a_hora
from horario.buscador import buscar, total_combinaciones, quitar_bloqueados
from horario.mostrar import imprimir, guardar_imagen


def main():
    parser = argparse.ArgumentParser(description="Arma el mejor horario sin cruces ni huecos.")
    parser.add_argument("csv", help="archivo CSV con los cursos disponibles")
    parser.add_argument("--top", type=int, default=3, help="cuántos horarios mostrar (por defecto 3)")
    parser.add_argument("--imagen", default="horario.png", help="dónde guardar la imagen del mejor horario")
    parser.add_argument("--bloquear", action="append", default=[], metavar='"Mar 14:00-18:00"',
                        help="hora ocupada (trabajo, deporte...); se puede repetir")
    args = parser.parse_args()

    try:
        bloqueos = [leer_bloqueo(b) for b in args.bloquear]
    except ValueError as e:
        parser.error(str(e))

    cursos = leer_cursos(args.csv)
    print(f"Materias: {len(cursos)}")
    for materia, grupos in cursos.items():
        print(f"  - {materia}: {len(grupos)} grupo(s)")
    print(f"Combinaciones posibles: {total_combinaciones(cursos)}")
    if bloqueos:
        print("Horas ocupadas: " + ", ".join(f"{b.dia} {a_hora(b.inicio)}-{a_hora(b.fin)}" for b in bloqueos))
        _, sin_grupo = quitar_bloqueados(cursos, bloqueos)
        if sin_grupo:
            print(f"\nTodos los grupos de {', '.join(sin_grupo)} caen en tus horas ocupadas: no hay horario posible.")
            return

    t0 = time.perf_counter()
    mejores, nodos = buscar(cursos, top=args.top, bloqueos=bloqueos)
    t = time.perf_counter() - t0

    if not mejores:
        print("\nNo existe ningún horario sin cruces con estos grupos.")
        return

    print(f"Nodos revisados: {nodos} | tiempo: {t * 1000:.1f} ms")
    for i, (c, grupos) in enumerate(mejores, start=1):
        imprimir(grupos, titulo=f"Opción {i} (puntaje {c:.2f})", bloqueos=bloqueos)

    guardar_imagen(mejores[0][1], args.imagen, titulo="Mejor horario", bloqueos=bloqueos)
    print(f"\nImagen del mejor horario guardada en: {args.imagen}")


if __name__ == "__main__":
    main()
