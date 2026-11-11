"""Pruebas: la búsqueda con poda debe dar lo mismo que probar todo a la fuerza.

Correr con:  python -m pytest   (o simplemente: python tests/test_buscador.py)
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from horario.datos import leer_cursos
from horario.buscador import buscar
from horario.costo import costo, grupo_choca, horas_de_hueco
from horario.datos import Sesion

EJEMPLO = os.path.join(os.path.dirname(__file__), "..", "ejemplos", "cursos.csv")


def fuerza_bruta(cursos):
    """Prueba TODAS las combinaciones y devuelve el menor costo."""
    mejor = float("inf")
    for combo in itertools.product(*cursos.values()):
        elegidos = []
        valido = True
        for g in combo:
            if grupo_choca(g, elegidos):
                valido = False
                break
            elegidos.append(g)
        if valido:
            mejor = min(mejor, costo(elegidos))
    return mejor


def test_poda_encuentra_el_optimo():
    cursos = leer_cursos(EJEMPLO)
    mejores, _ = buscar(cursos, top=1)
    assert abs(mejores[0][0] - fuerza_bruta(cursos)) < 1e-9


def test_huecos():
    # Clases de 8 a 10 y de 12 a 14 el mismo día: 2 horas de hueco
    sesiones = [Sesion("Lun", 8 * 60, 10 * 60), Sesion("Lun", 12 * 60, 14 * 60)]
    assert horas_de_hueco(sesiones) == 2.0


if __name__ == "__main__":
    test_poda_encuentra_el_optimo()
    test_huecos()
    print("Todas las pruebas pasaron.")
