"""Creador de horarios — punto de entrada.

Uso:
    python main.py ejemplos/cursos.csv
    python main.py ejemplos/cursos.csv --top 5 --imagen mi_horario.png
    python main.py ejemplos/cursos.csv --bloquear "Mar 14:00-18:00" --bloquear "Lun-Vie 06:00-07:00"
    python main.py ejemplos/cursos.csv --evitar "Rojas" --evitar "Ortiz"
"""

import argparse
import time

from horario.datos import leer_cursos, leer_bloqueos, a_hora
from horario.buscador import buscar, total_combinaciones, quitar_bloqueados
from horario.costo import tiene_profe_evitado
from horario.mostrar import imprimir, guardar_imagen


def main():
    parser = argparse.ArgumentParser(description="Arma el mejor horario sin cruces ni huecos.")
    parser.add_argument("csv", help="archivo CSV con los cursos disponibles")
    parser.add_argument("--top", type=int, default=3, help="cuántos horarios mostrar (por defecto 3)")
    parser.add_argument("--imagen", default="horario.png", help="dónde guardar la imagen del mejor horario")
    parser.add_argument("--bloquear", action="append", default=[], metavar='"Lun-Vie 14:00-18:00"',
                        help='hora ocupada (trabajo, deporte...): un día ("Mar"), un rango ("Lun-Vie") '
                             'o varios ("Lun,Mie"); se puede repetir')
    parser.add_argument("--evitar", action="append", default=[], metavar='"Rojas"',
                        help="profesor que prefieres evitar (basta con parte del nombre); se puede repetir")
    args = parser.parse_args()

    try:
        bloqueos = [s for b in args.bloquear for s in leer_bloqueos(b)]
    except ValueError as e:
        parser.error(str(e))

    cursos = leer_cursos(args.csv)
    print(f"Materias: {len(cursos)}")
    for materia, grupos in cursos.items():
        print(f"  - {materia}: {len(grupos)} grupo(s)")
    print(f"Combinaciones posibles: {total_combinaciones(cursos)}")
    for nombre in args.evitar:
        if not any(tiene_profe_evitado(g, [nombre]) for gs in cursos.values() for g in gs):
            print(f"Aviso: ningún grupo tiene un profesor llamado '{nombre}'.")
    if args.evitar:
        print("Profesores a evitar: " + ", ".join(args.evitar))
    if bloqueos:
        print("Horas ocupadas: " + ", ".join(f"{b.dia} {a_hora(b.inicio)}-{a_hora(b.fin)}" for b in bloqueos))
        _, sin_grupo = quitar_bloqueados(cursos, bloqueos)
        if sin_grupo:
            # Esas materias no caben: se arma el mejor horario con las demás
            print(f"\nNo cabe: {', '.join(sin_grupo)} (todos sus grupos caen en tus horas ocupadas).")
            cursos = {m: gs for m, gs in cursos.items() if m not in sin_grupo}
            if not cursos:
                print("Ninguna materia cabe en tus horas libres.")
                return
            print(f"Este es el mejor horario con las otras {len(cursos)} materias.")

    t0 = time.perf_counter()
    mejores, nodos = buscar(cursos, top=args.top, bloqueos=bloqueos, evitar=args.evitar)
    t = time.perf_counter() - t0

    if not mejores:
        print("\nNo existe ningún horario sin cruces con estos grupos.")
        return

    print(f"Nodos revisados: {nodos} | tiempo: {t * 1000:.1f} ms")
    for i, (c, grupos) in enumerate(mejores, start=1):
        imprimir(grupos, titulo=f"Opción {i} (puntaje {c:.2f})", bloqueos=bloqueos, evitar=args.evitar)

    guardar_imagen(mejores[0][1], args.imagen, titulo="Mejor horario", bloqueos=bloqueos, evitar=args.evitar)
    print(f"\nImagen del mejor horario guardada en: {args.imagen}")


if __name__ == "__main__":
    main()
