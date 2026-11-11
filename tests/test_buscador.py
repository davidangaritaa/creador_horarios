"""Pruebas: la búsqueda con poda debe dar lo mismo que probar todo a la fuerza.

Correr con:  python -m pytest   (o simplemente: python tests/test_buscador.py)
"""
import itertools
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from horario.datos import leer_cursos
from horario.buscador import buscar
from horario.costo import costo, grupo_choca, horas_de_hueco, choca_con_bloqueos
from horario.datos import Sesion

EJEMPLO = os.path.join(os.path.dirname(__file__), "..", "ejemplos", "cursos.csv")


def fuerza_bruta(cursos, bloqueos=()):
    """Prueba TODAS las combinaciones y devuelve el menor costo."""
    mejor = float("inf")
    for combo in itertools.product(*cursos.values()):
        elegidos = []
        valido = True
        for g in combo:
            if grupo_choca(g, elegidos) or choca_con_bloqueos(g, bloqueos):
                valido = False
                break
            elegidos.append(g)
        if valido:
            mejor = min(mejor, costo(elegidos, bloqueos))
    return mejor


def test_poda_encuentra_el_optimo():
    cursos = leer_cursos(EJEMPLO)
    mejores, _ = buscar(cursos, top=1)
    assert abs(mejores[0][0] - fuerza_bruta(cursos)) < 1e-9


def test_huecos():
    # Clases de 8 a 10 y de 12 a 14 el mismo día: 2 horas de hueco
    sesiones = [Sesion("Lun", 8 * 60, 10 * 60), Sesion("Lun", 12 * 60, 14 * 60)]
    assert horas_de_hueco(sesiones) == 2.0


def test_horas_ocupadas_no_son_hueco():
    # Clases de 8 a 10 y de 14 a 16; trabajo de 10 a 14 en medio: no hay hueco
    sesiones = [Sesion("Lun", 8 * 60, 10 * 60), Sesion("Lun", 14 * 60, 16 * 60)]
    assert horas_de_hueco(sesiones, [Sesion("Lun", 10 * 60, 14 * 60)]) == 0.0
    # Solo de 11 a 12 ocupado: quedan 3 h de hueco
    assert horas_de_hueco(sesiones, [Sesion("Lun", 11 * 60, 12 * 60)]) == 3.0
    # Dos bloqueos que se pisan (10-12 y 11-13) no se cuentan doble: queda 1 h
    assert horas_de_hueco(sesiones, [Sesion("Lun", 600, 720), Sesion("Lun", 660, 780)]) == 1.0
    # Un bloqueo fuera de las clases (17-19) no cambia nada
    assert horas_de_hueco(sesiones, [Sesion("Lun", 17 * 60, 19 * 60)]) == 4.0


def test_bloqueos_quitan_grupos():
    from horario.datos import leer_bloqueos
    cursos = leer_cursos(EJEMPLO)
    bloqueos = leer_bloqueos("Lun 14:00-18:00")
    mejores, _ = buscar(cursos, top=5, bloqueos=bloqueos)
    assert mejores
    for _, grupos in mejores:
        assert not any(choca_con_bloqueos(g, bloqueos) for g in grupos)
    # Si una materia queda sin grupos, no hay horario
    todo_ocupado = leer_bloqueos("Lun-Vie 06:00-22:00")
    assert buscar(cursos, top=1, bloqueos=todo_ocupado) == ([], 0)


def test_leer_horas_ocupadas_por_rangos():
    from horario.datos import leer_bloqueos
    dias = lambda texto: [s.dia for s in leer_bloqueos(texto)]
    assert dias("Mar 14:00-18:00") == ["Mar"]
    assert dias("Lun-Vie 07:00-12:00") == ["Lun", "Mar", "Mie", "Jue", "Vie"]
    assert dias("lunes-miércoles 07:00 - 12:00") == ["Lun", "Mar", "Mie"]
    assert dias("Vie,Lun,Mie 14:00-16:00") == ["Lun", "Mie", "Vie"]
    assert dias("Lun-Mar,Jue 14:00-16:00") == ["Lun", "Mar", "Jue"]
    assert all(s.inicio == 420 and s.fin == 720 for s in leer_bloqueos("Lun-Vie 07:00-12:00"))
    for malo in ["Vie-Lun 07:00-12:00", "Lun-Xyz 07:00-12:00", "Lun-Vie de 7 a 12", "Lun-Vie 12:00-07:00"]:
        try:
            leer_bloqueos(malo)
            assert False, malo
        except ValueError:
            pass


def test_viernes_y_lunes():
    from horario.datos import Grupo
    from horario.costo import detalle_costo, PESOS
    # Mismo horario, uno el lunes y otro el viernes (2 h de clase cada uno)
    lunes = Grupo("X", "A", [Sesion("Lun", 8 * 60, 10 * 60)])
    viernes = Grupo("X", "B", [Sesion("Vie", 8 * 60, 10 * 60)])
    d_lun, d_vie = detalle_costo([lunes]), detalle_costo([viernes])
    assert d_lun["horas_lunes"] == 2.0 and d_lun["viernes"] == 0
    assert d_vie["horas_lunes"] == 0.0 and d_vie["viernes"] == 1
    diferencia = d_vie["total"] - d_lun["total"]
    assert abs(diferencia - (PESOS["viernes"] + 2 * PESOS["lunes"])) < 1e-9


def test_poda_con_muchos_casos_aleatorios():
    """La poda (con el premio del lunes y horas ocupadas) da el mismo óptimo que la fuerza bruta."""
    import random
    from horario.datos import Grupo, DIAS
    from horario.costo import se_cruzan
    rnd = random.Random(42)
    for _ in range(200):
        cursos = {}
        for m in range(rnd.randint(2, 5)):
            grupos = []
            for g in range(rnd.randint(1, 4)):
                sesiones = []
                for _ in range(rnd.randint(1, 2)):
                    ini = rnd.randint(6, 19) * 60
                    nueva = Sesion(rnd.choice(DIAS[:5]), ini, ini + rnd.choice([60, 120, 180]))
                    # un grupo real no tiene dos clases que se pisen entre sí
                    if not any(se_cruzan(nueva, s) for s in sesiones):
                        sesiones.append(nueva)
                grupos.append(Grupo(f"M{m}", f"G{g}", sesiones))
            cursos[f"M{m}"] = grupos
        bloqueos = []
        for _ in range(rnd.choice([0, 0, 1, 2])):
            ini = rnd.randint(7, 18) * 60
            bloqueos.append(Sesion(rnd.choice(DIAS[:5]), ini, ini + rnd.choice([60, 120, 240])))
        mejores, _ = buscar(cursos, top=1, bloqueos=bloqueos)
        esperado = fuerza_bruta(cursos, bloqueos)
        if esperado == float("inf"):
            assert not mejores
        else:
            assert abs(mejores[0][0] - esperado) < 1e-9


if __name__ == "__main__":
    test_poda_encuentra_el_optimo()
    test_huecos()
    test_horas_ocupadas_no_son_hueco()
    test_bloqueos_quitan_grupos()
    test_leer_horas_ocupadas_por_rangos()
    test_viernes_y_lunes()
    test_poda_con_muchos_casos_aleatorios()
    print("Todas las pruebas pasaron.")
