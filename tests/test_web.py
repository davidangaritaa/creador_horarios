"""Pruebas de la versión web (index.html): su JavaScript debe dar lo mismo que Python.

Copia la lógica de index.html (entre las marcas "inicio de la lógica" y
"fin de la lógica"), la corre con Node.js y compara los resultados con los de
horario/ en cientos de casos al azar. También revisa los festivos de Colombia y
el archivo de calendario (.ics).

Necesita Node.js; si no está instalado, la prueba se salta.
Correr con:  python tests/test_web.py   (o python -m pytest)
"""
import json
import os
import random
import shutil
import subprocess
import sys

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)

from horario import costo as costo_py
from horario.buscador import buscar
from horario.costo import se_cruzan
from horario.datos import DIAS, Grupo, Sesion, leer_cursos

NODE = shutil.which("node")


def logica_js() -> str:
    with open(os.path.join(RAIZ, "index.html"), encoding="utf-8") as f:
        html = f.read()
    inicio = html.index("// ---8<--- inicio de la lógica")
    fin = html.index("// ---8<--- fin de la lógica")
    return html[inicio:fin]


def correr_js(programa: str, datos) -> object:
    """Corre la lógica de index.html + `programa` en Node y devuelve lo que imprime (JSON)."""
    codigo = logica_js() + "\nconst DATOS = " + json.dumps(datos) + ";\n" + programa
    r = subprocess.run([NODE, "-"], input=codigo, capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)


def a_json(cursos):
    return {m: [{"materia": g.materia, "nombre": g.nombre, "profesor": g.profesor,
                 "sesiones": [{"dia": s.dia, "inicio": s.inicio, "fin": s.fin} for s in g.sesiones]}
                for g in gs] for m, gs in cursos.items()}


def casos_al_azar(n=300, semilla=7):
    rnd = random.Random(semilla)
    casos = [(leer_cursos(os.path.join(RAIZ, "ejemplos", "cursos.csv")), [], []),
             (leer_cursos(os.path.join(RAIZ, "ejemplos", "cursos.csv")), [], ["Pérez", "smith"])]
    for _ in range(n):
        cursos = {}
        for mi in range(rnd.randint(2, 6)):
            gs = []
            for gi in range(rnd.randint(1, 4)):
                ses = []
                for _ in range(rnd.randint(1, 3)):
                    ini = rnd.randint(6, 19) * 60 + rnd.choice([0, 30])
                    s = Sesion(rnd.choice(DIAS), ini, ini + rnd.choice([60, 90, 120, 180]))
                    if not any(se_cruzan(s, o) for o in ses):
                        ses.append(s)
                gs.append(Grupo(f"M{mi}", f"G{gi}", ses, profesor=rnd.choice(["Carlos Rojas", "Andrés Pérez", "Díaz", ""])))
            cursos[f"M{mi}"] = gs
        bloqueos = []
        for _ in range(rnd.choice([0, 0, 1, 2, 3])):
            ini = rnd.randint(7, 18) * 60 + rnd.choice([0, 30])
            bloqueos.append(Sesion(rnd.choice(DIAS[:5]), ini, ini + rnd.choice([60, 120, 240])))
        casos.append((cursos, bloqueos, rnd.choice([[], [], ["rojas"], ["PEREZ", "Díaz"]])))
    return casos


def test_web_da_lo_mismo_que_python():
    if not NODE:
        print("  (se salta: Node.js no está instalado)")
        return
    datos, esperado = [], []
    for cursos, bloqueos, evitar in casos_al_azar():
        mejores, _ = buscar(cursos, top=5, bloqueos=bloqueos, evitar=evitar)
        esperado.append([c for c, _ in mejores])
        datos.append({"cursos": a_json(cursos),
                      "bloqueos": [{"dia": b.dia, "inicio": b.inicio, "fin": b.fin} for b in bloqueos],
                      "evitar": evitar})
    pesos = dict(costo_py.PESOS)
    obtenido = correr_js(f"""
      const pesos = {json.dumps(pesos)};
      const salida = DATOS.map(c => buscar(c.cursos, {{
        pesos, horaInicio: {costo_py.HORA_INICIO}, horaFin: {costo_py.HORA_FIN}, top: 5, bloqueos: c.bloqueos, evitar: c.evitar,
      }}).mejores.map(x => x.costo));
      console.log(JSON.stringify(salida));
    """, datos)
    distintos = [i for i, (a, b) in enumerate(zip(esperado, obtenido))
                 if len(a) != len(b) or any(abs(x - y) > 1e-9 for x, y in zip(a, b))]
    assert not distintos, f"{len(distintos)} casos distintos, por ejemplo el {distintos[0]}"


def test_festivos_de_colombia_2026():
    if not NODE:
        return
    # Lista oficial de festivos de 2026 en Colombia
    oficiales = ["2026-01-01", "2026-01-12", "2026-03-23", "2026-04-02", "2026-04-03",
                 "2026-05-01", "2026-05-18", "2026-06-08", "2026-06-15", "2026-06-29",
                 "2026-07-20", "2026-08-07", "2026-08-17", "2026-10-12", "2026-11-02",
                 "2026-11-16", "2026-12-08", "2026-12-25"]
    assert correr_js("console.log(JSON.stringify(festivosColombia(2026)));", None) == oficiales


def test_calendario_ics():
    if not NODE:
        return
    r = correr_js("""
      const grupos = [{ materia: "Cálculo III, avanzado", nombre: "A", profesor: "Pérez",
        sesiones: [{ dia: "Lun", inicio: 480, fin: 600, salon: "A-201" }, { dia: "Mie", inicio: 480, fin: 600, salon: "A-201" }] }];
      const r = generarICS(grupos, { inicio: "2026-08-03", fin: "2026-11-27", saltarFestivos: true,
                                     alarma: true, ahora: new Date(Date.UTC(2026, 6, 1)) });
      console.log(JSON.stringify(r));
    """, None)
    texto = r["texto"]
    assert texto.startswith("BEGIN:VCALENDAR\r\n") and texto.endswith("END:VCALENDAR\r\n")
    assert texto.count("BEGIN:VEVENT") == 2 and r["clases"] == 2
    assert "DTSTART;TZID=America/Bogota:20260803T080000" in texto      # primer lunes
    assert "DTSTART;TZID=America/Bogota:20260805T080000" in texto      # primer miércoles
    assert "RRULE:FREQ=WEEKLY;UNTIL=20261128T045959Z" in texto
    # Lunes festivos entre agosto y noviembre de 2026: 17 ago, 12 oct, 2 nov y 16 nov
    for f in ["20260817", "20261012", "20261102", "20261116"]:
        assert f"EXDATE;TZID=America/Bogota:{f}T080000" in texto
    assert r["omitidos"] == 4
    assert "SUMMARY:Cálculo III\\, avanzado (grupo A)" in texto          # comas escapadas
    assert "TRIGGER:-PT15M" in texto


if __name__ == "__main__":
    if not NODE:
        print("Node.js no está instalado: se saltan las pruebas de la versión web.")
        sys.exit(0)
    test_web_da_lo_mismo_que_python()
    test_festivos_de_colombia_2026()
    test_calendario_ics()
    print("Todas las pruebas de la versión web pasaron.")
