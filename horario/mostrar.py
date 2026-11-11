"""Mostrar un horario: como tabla en la consola y como imagen PNG."""

from .datos import DIAS, a_hora
from .costo import detalle_costo, HORA_INICIO, HORA_FIN


def dias_usados(grupos):
    usados = {s.dia for g in grupos for s in g.sesiones}
    return [d for d in DIAS if d in usados or d != "Sab"]


def imprimir(grupos, titulo="Horario"):
    """Tabla por horas (filas) y días (columnas)."""
    dias = dias_usados(grupos)
    inicio = min(s.inicio for g in grupos for s in g.sesiones) // 60 * 60
    fin = -(-max(s.fin for g in grupos for s in g.sesiones) // 60) * 60

    ancho = 16
    print(f"\n{titulo}")
    print("Hora   " + "".join(f"{d:<{ancho}}" for d in dias))
    for t in range(inicio, fin, 60):
        fila = f"{a_hora(t)}  "
        for d in dias:
            texto = ""
            for g in grupos:
                for s in g.sesiones:
                    if s.dia == d and s.inicio < t + 60 and t < s.fin:
                        texto = f"{g.materia[:11]} ({g.nombre})"
            fila += f"{texto:<{ancho}}"
        print(fila)

    d = detalle_costo(grupos)
    print(f"Huecos: {d['huecos']:.1f} h | Antes de las 8: {d['temprano']:.1f} h | "
          f"Después de las 6 p. m.: {d['tarde']:.1f} h | Días: {d['dias']} | "
          f"Lunes: {d['horas_lunes']:.1f} h | Viernes: {'sí' if d['viernes'] else 'libre'} | "
          f"Puntaje: {d['total']:.2f}")


def guardar_imagen(grupos, ruta, titulo="Mi horario"):
    """Dibuja el horario como un calendario semanal y lo guarda en PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch

    dias = dias_usados(grupos)
    inicio = min(min(s.inicio for g in grupos for s in g.sesiones), HORA_INICIO) // 60
    fin = -(-max(max(s.fin for g in grupos for s in g.sesiones), HORA_FIN) // 60)

    colores = ["#4C78A8", "#F58518", "#54A24B", "#B279A2", "#E45756",
               "#72B7B2", "#9D755D", "#EECA3B", "#FF9DA6", "#79706E"]
    materias = sorted({g.materia for g in grupos})
    color = {m: colores[i % len(colores)] for i, m in enumerate(materias)}

    fig, ax = plt.subplots(figsize=(1.9 * len(dias) + 1.2, 0.55 * (fin - inicio) + 1.4))
    # Zonas penalizadas (antes de las 8 y después de las 6) en gris claro
    ax.axhspan(inicio, HORA_INICIO / 60, color="#eeeeee", zorder=0)
    ax.axhspan(HORA_FIN / 60, fin, color="#eeeeee", zorder=0)

    for g in grupos:
        for s in g.sesiones:
            x = dias.index(s.dia)
            y0, y1 = s.inicio / 60, s.fin / 60
            ax.add_patch(FancyBboxPatch((x + 0.05, y0 + 0.03), 0.9, (y1 - y0) - 0.06,
                                        boxstyle="round,pad=0,rounding_size=0.08",
                                        color=color[g.materia], zorder=2))
            texto = f"{g.materia}\nGrupo {g.nombre}\n{a_hora(s.inicio)}–{a_hora(s.fin)}"
            if g.salon:
                texto += f"\n{g.salon}"
            ax.text(x + 0.5, (y0 + y1) / 2, texto, ha="center", va="center",
                    fontsize=8, color="white", zorder=3, wrap=True)

    ax.set_xlim(0, len(dias))
    ax.set_ylim(fin, inicio)                       # la mañana arriba
    ax.set_xticks([i + 0.5 for i in range(len(dias))])
    ax.set_xticklabels(dias)
    ax.xaxis.tick_top()
    ax.set_yticks(range(inicio, fin + 1))
    ax.set_yticklabels([f"{h:02d}:00" for h in range(inicio, fin + 1)])
    ax.grid(axis="y", color="#dddddd", zorder=1)
    for i in range(1, len(dias)):
        ax.axvline(i, color="#dddddd", zorder=1)
    for lado in ax.spines.values():
        lado.set_visible(False)

    d = detalle_costo(grupos)
    ax.set_title(f"{titulo} — huecos: {d['huecos']:.1f} h · días: {d['dias']} · "
                 f"puntaje: {d['total']:.2f}", pad=28, fontsize=11)
    fig.tight_layout()
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
