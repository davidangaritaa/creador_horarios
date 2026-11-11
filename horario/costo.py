"""Cómo se califica un horario: entre menos puntos, mejor.

Penalizaciones (se pueden cambiar en PESOS):
  - Cada hora de hueco entre dos clases del mismo día.
  - Cada hora de clase antes de las 8:00 (por ejemplo, de 6:00 a 8:00).
  - Cada hora de clase después de las 18:00 (por ejemplo, de 18:00 a 20:00).
  - Cada día que hay que ir a la universidad (para juntar clases).
  - Ir el viernes (se premia tener el viernes libre).

Premio (resta puntos):
  - Cada hora de clase el lunes. En Colombia casi todos los festivos caen
    lunes, así que las clases del lunes se pierden seguido y el semestre
    queda más liviano.
"""

from .datos import DIAS

PESOS = {
    "hueco": 1.0,       # por hora de hueco
    "temprano": 2.0,    # por hora antes de HORA_INICIO
    "tarde": 2.0,       # por hora después de HORA_FIN
    "dia": 0.5,         # por cada día con clase
    "viernes": 1.5,     # extra si hay que ir el viernes
    "lunes": 0.5,       # PREMIO por hora de clase el lunes (se resta)
}
HORA_INICIO = 8 * 60    # 8:00
HORA_FIN = 18 * 60      # 18:00 (6 p. m.)


def se_cruzan(a, b) -> bool:
    """True si dos sesiones son el mismo día y se pisan en el tiempo."""
    return a.dia == b.dia and a.inicio < b.fin and b.inicio < a.fin


def grupo_choca(grupo, elegidos) -> bool:
    """True si alguna sesión del grupo se cruza con algún grupo ya elegido."""
    for otro in elegidos:
        for s1 in grupo.sesiones:
            for s2 in otro.sesiones:
                if se_cruzan(s1, s2):
                    return True
    return False


def horas_fuera_de_rango(sesion):
    """Horas de la sesión que caen antes de HORA_INICIO y después de HORA_FIN."""
    temprano = max(0, min(sesion.fin, HORA_INICIO) - sesion.inicio) / 60
    tarde = max(0, sesion.fin - max(sesion.inicio, HORA_FIN)) / 60
    return temprano, tarde


def horas_de_hueco(sesiones_del_dia):
    """Huecos de un día = (de la primera a la última clase) - (horas de clase)."""
    if not sesiones_del_dia:
        return 0.0
    primera = min(s.inicio for s in sesiones_del_dia)
    ultima = max(s.fin for s in sesiones_del_dia)
    en_clase = sum(s.fin - s.inicio for s in sesiones_del_dia)
    return (ultima - primera - en_clase) / 60


def detalle_costo(grupos):
    """Devuelve un diccionario con cada parte del costo y el total."""
    por_dia = {d: [] for d in DIAS}
    temprano = tarde = 0.0
    for g in grupos:
        for s in g.sesiones:
            por_dia[s.dia].append(s)
            t, l = horas_fuera_de_rango(s)
            temprano += t
            tarde += l

    huecos = sum(horas_de_hueco(ses) for ses in por_dia.values())
    dias = sum(1 for ses in por_dia.values() if ses)
    viernes = 1 if por_dia["Vie"] else 0
    horas_lunes = sum(s.fin - s.inicio for s in por_dia["Lun"]) / 60

    total = (PESOS["hueco"] * huecos + PESOS["temprano"] * temprano
             + PESOS["tarde"] * tarde + PESOS["dia"] * dias
             + PESOS["viernes"] * viernes - PESOS["lunes"] * horas_lunes)
    return {"huecos": huecos, "temprano": temprano, "tarde": tarde,
            "dias": dias, "viernes": viernes, "horas_lunes": horas_lunes,
            "total": total}


def horas_lunes(grupo) -> float:
    """Horas de clase que tiene un grupo el lunes."""
    return sum(s.fin - s.inicio for s in grupo.sesiones if s.dia == "Lun") / 60


def costo(grupos) -> float:
    return detalle_costo(grupos)["total"]


def cota_inferior(grupos, lunes_pendiente=0.0):
    """Lo MÍNIMO que costará un horario que empieza con estos grupos.

    Ojo: los huecos NO entran en la cota, porque una clase nueva puede
    caer en medio de un hueco y taparlo (el hueco puede bajar). En cambio,
    las horas fuera de rango, los días usados y el viernes solo pueden subir
    al agregar más materias, así que sí sirven como cota.

    El premio del lunes hace que el costo BAJE al agregar materias, así que
    se resta de una vez el máximo premio que aún se podría ganar
    (lunes_pendiente = horas de lunes que como mucho darían las materias
    que faltan). Así la cota sigue siendo optimista y la poda es segura.
    """
    d = detalle_costo(grupos)
    return (PESOS["temprano"] * d["temprano"] + PESOS["tarde"] * d["tarde"]
            + PESOS["dia"] * d["dias"] + PESOS["viernes"] * d["viernes"]
            - PESOS["lunes"] * (d["horas_lunes"] + lunes_pendiente))
