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
import re
import unicodedata
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


def normalizar_dia(texto: str):
    """'miércoles', 'Mié' o 'MIE' -> 'Mie'. Devuelve None si no es un día válido."""
    t = unicodedata.normalize("NFD", (texto or "").strip())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn").lower()
    dia = t[:1].upper() + t[1:3]
    return dia if dia in DIAS else None


def leer_dias(texto: str) -> list:
    """'Lun' -> ['Lun'];  'Lun-Vie' -> ['Lun', ..., 'Vie'];  'Lun,Mie' -> ['Lun', 'Mie'].

    Devuelve una lista vacía si algo no es un día válido.
    """
    dias = []
    for parte in (texto or "").split(","):
        if "-" in parte:
            desde, hasta = (normalizar_dia(x) for x in parte.split("-", 1))
            if not desde or not hasta or DIAS.index(desde) > DIAS.index(hasta):
                return []
            dias += DIAS[DIAS.index(desde):DIAS.index(hasta) + 1]
        else:
            dia = normalizar_dia(parte)
            if not dia:
                return []
            dias.append(dia)
    return [d for d in DIAS if d in dias]          # sin repetidos y en orden


def leer_bloqueos(texto: str) -> list:
    """Convierte una hora ocupada en una Sesion por cada día.

    'Mar 14:00-18:00'      -> el martes
    'Lun-Vie 07:00-12:00'  -> de lunes a viernes
    'Lun,Mie 14:00-16:00'  -> lunes y miércoles
    """
    ejemplo = 'Escríbela así: "Mar 14:00-18:00" o "Lun-Vie 07:00-12:00"'
    m = re.match(r"^\s*(\S+)\s+(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})\s*$", texto or "")
    dias = leer_dias(m.group(1)) if m else []
    if not dias:
        raise ValueError(f"No entiendo la hora ocupada '{texto}'. {ejemplo}")
    inicio, fin = a_minutos(m.group(2)), a_minutos(m.group(3))
    if fin <= inicio:
        raise ValueError(f"En '{texto}' la hora de fin debe ser mayor que la de inicio")
    return [Sesion(d, inicio, fin) for d in dias]


def leer_cursos(ruta: str) -> dict:
    """Lee el CSV y devuelve {materia: [Grupo, Grupo, ...]}."""
    grupos = {}  # (materia, grupo) -> Grupo
    with open(ruta, newline="", encoding="utf-8") as f:
        for n, fila in enumerate(csv.DictReader(f), start=2):
            materia = fila["materia"].strip()
            nombre = fila["grupo"].strip()
            dia = normalizar_dia(fila["dia"])
            if not dia:
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
