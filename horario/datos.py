"""Lectura de los cursos disponibles desde un archivo CSV.

Formato del CSV (una fila por cada sesión de clase):

    materia,grupo,dia,inicio,fin,profesor,salon
    Calculo III,A,Lun,08:00,10:00,Perez,A-201
    Calculo III,A,Mie,08:00,10:00,Perez,A-201

- Un mismo grupo puede tener varias filas (una por cada día que ve clase).
- dia: Lun, Mar, Mie, Jue, Vie, Sab
- inicio / fin: hora en formato 24 h (HH:MM)
- profesor y salon son opcionales.
"""

import csv
from dataclasses import dataclass, field

DIAS = ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab"]


@dataclass
class Sesion:
    """Una clase de un día: por ejemplo, lunes de 8:00 a 10:00."""
    dia: str
    inicio: int  # minutos desde las 00:00 (8:00 -> 480)
    fin: int


@dataclass
class Grupo:
    """Un grupo (NRC) de una materia, con todas sus sesiones de la semana."""
    materia: str
    nombre: str
    sesiones: list = field(default_factory=list)
    profesor: str = ""
    salon: str = ""


def a_minutos(hora: str) -> int:
    """Convierte '08:30' en 510 (minutos desde la medianoche)."""
    h, m = hora.strip().split(":")
    return int(h) * 60 + int(m)


def a_hora(minutos: int) -> str:
    """Convierte 510 en '08:30'."""
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def leer_cursos(ruta: str) -> dict:
    """Lee el CSV y devuelve {materia: [Grupo, Grupo, ...]}."""
    grupos = {}  # (materia, grupo) -> Grupo
    with open(ruta, newline="", encoding="utf-8") as f:
        for n, fila in enumerate(csv.DictReader(f), start=2):
            materia = fila["materia"].strip()
            nombre = fila["grupo"].strip()
            dia = fila["dia"].strip().capitalize()[:3]
            if dia not in DIAS:
                raise ValueError(f"Línea {n}: día '{fila['dia']}' no válido. Usa {DIAS}")
            inicio, fin = a_minutos(fila["inicio"]), a_minutos(fila["fin"])
            if fin <= inicio:
                raise ValueError(f"Línea {n}: la hora de fin debe ser mayor que la de inicio")

            clave = (materia, nombre)
            if clave not in grupos:
                grupos[clave] = Grupo(materia, nombre,
                                      profesor=(fila.get("profesor") or "").strip(),
                                      salon=(fila.get("salon") or "").strip())
            grupos[clave].sesiones.append(Sesion(dia, inicio, fin))

    cursos = {}
    for g in grupos.values():
        cursos.setdefault(g.materia, []).append(g)
    return cursos
