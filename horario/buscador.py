"""Búsqueda del mejor horario: backtracking con poda (ramificación y poda).

Idea:
  1. Se elige un grupo de la primera materia, luego uno de la segunda, etc.
  2. Si un grupo se cruza con lo ya elegido, se descarta y se prueba otro.
  3. Si lo elegido hasta ahora ya no puede superar a los mejores horarios
     encontrados (costo mínimo >= el peor de los mejores), se poda.
  4. Al completar todas las materias, se guarda el horario si está entre
     los 'top' mejores.
"""

from .costo import costo, cota_inferior, grupo_choca, horas_lunes


def buscar(cursos: dict, top: int = 3):
    """Devuelve (lista de los mejores horarios, nodos revisados).

    Cada horario es una tupla (costo, [Grupo, Grupo, ...]).
    """
    # Materias con menos grupos primero: se equivoca menos y poda antes
    materias = sorted(cursos, key=lambda m: len(cursos[m]))

    # lunes_pendiente[i] = máximo de horas de lunes que pueden aportar las
    # materias i, i+1, ... (para que la cota tenga en cuenta el premio del lunes)
    lunes_pendiente = [0.0] * (len(materias) + 1)
    for i in range(len(materias) - 1, -1, -1):
        mejor_lunes = max(horas_lunes(g) for g in cursos[materias[i]])
        lunes_pendiente[i] = lunes_pendiente[i + 1] + mejor_lunes

    mejores = []          # lista de (costo, grupos), ordenada de menor a mayor
    nodos = 0

    def peor_aceptado():
        return mejores[-1][0] if len(mejores) == top else float("inf")

    def recorrer(i, elegidos):
        nonlocal nodos
        nodos += 1

        if i == len(materias):                      # horario completo
            c = costo(elegidos)
            if c < peor_aceptado():
                mejores.append((c, list(elegidos)))
                mejores.sort(key=lambda x: x[0])
                del mejores[top:]
            return

        for grupo in cursos[materias[i]]:
            if grupo_choca(grupo, elegidos):        # regla dura: sin cruces
                continue
            elegidos.append(grupo)
            if cota_inferior(elegidos, lunes_pendiente[i + 1]) < peor_aceptado():   # poda
                recorrer(i + 1, elegidos)
            elegidos.pop()                          # backtracking: se devuelve

    recorrer(0, [])
    return mejores, nodos


def total_combinaciones(cursos: dict) -> int:
    """Cuántos horarios habría que revisar a la fuerza (sin poda)."""
    total = 1
    for grupos in cursos.values():
        total *= len(grupos)
    return total
