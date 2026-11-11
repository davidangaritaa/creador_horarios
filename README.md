# Creador de horarios 🗓️

Arma automáticamente el **mejor horario del semestre** a partir de los grupos disponibles de cada materia:
**sin cruces**, con las clases **seguidas (sin huecos)** y, de preferencia, **entre las 8:00 a. m. y las 6:00 p. m.**
Además premia tener el **viernes libre** y las clases de los **lunes**, que en Colombia suelen ser festivo.

**Úsalo en el navegador, sin instalar nada:** https://davidangaritaa.github.io/creador-horarios/

![La versión web: el mejor horario dibujado en un cuaderno cuadriculado](docs/web.png)

## ¿Qué hace?

Le das un archivo con las materias que quieres ver y los grupos (NRC) de cada una con sus días y horas.
El programa escoge **un grupo por materia** y te muestra los mejores horarios posibles.

Cada horario recibe un **puntaje** (menos es mejor; puede ser negativo):

| Situación | Puntos |
|---|---|
| Dos clases se cruzan | ❌ descartado |
| Cada hora de **hueco** entre clases del mismo día | +1 |
| Cada hora de clase **antes de las 8:00** | +2 |
| Cada hora de clase **después de las 18:00** | +2 |
| Cada **día** que hay que ir a la universidad | +0,5 |
| Tener que ir el **viernes** (se premia el viernes libre) | +1,5 |
| Cada hora de clase el **lunes** 🎉 | −0,5 |

**¿Por qué premiar los lunes?** En Colombia casi todos los festivos caen lunes (Ley Emiliani),
así que las clases del lunes se pierden seguido y el semestre queda más liviano.

**Horas ocupadas.** Si trabajas o tienes algo fijo (por ejemplo, "los martes de 2 a 6" o "de lunes
a viernes de 6 a 8 a. m."), lo marcas como hora ocupada, para uno o varios días a la vez: ningún grupo que se cruce con ella entra en el horario, y si queda entre dos
clases **no cuenta como hueco**.

Los pesos se cambian en [`horario/costo.py`](horario/costo.py) (`PESOS`, `HORA_INICIO`, `HORA_FIN`).

## Cómo usarlo

### En el navegador (sin instalar nada)

Abre [`index.html`](index.html) con doble clic, o entra a la versión publicada en
**https://davidangaritaa.github.io/creador-horarios/**.

- **Arriba ves el resultado**: un titular que describe el mejor horario (por ejemplo, *"Clases lunes,
  martes y miércoles. Viernes libre."*) y el horario dibujado en un cuaderno cuadriculado, con un color
  de resaltador por materia. Puedes comparar las mejores opciones e imprimirlo o guardarlo en PDF.
- **En "Tus materias"** escribes los grupos en la tabla o cargas tu CSV (también acepta el CSV con `;`
  que guarda Excel en español). El horario se recalcula solo con cada cambio.
- **En "Tus horas ocupadas"** marcas el trabajo, el deporte o lo que no puedas mover. Cada una
  puede valer para varios días: eliges los días con botones o con el atajo **Lun a Vie**.
- **En "Cómo se califica"** ajustas las reglas, escritas como frases: cuánto pesan los huecos,
  el rango de horas, el viernes libre y el premio del lunes.
- **"Pasar este horario a tu calendario"** descarga un archivo `.ics` con las clases de todo el
  semestre para Google Calendar, Outlook o el celular: se repiten cada semana, **se saltan los
  festivos de Colombia** (calculados con la Ley Emiliani y la Semana Santa) y te avisan 15 minutos antes.

Todo se calcula en tu navegador: los datos no se envían a ningún lado, y la página recuerda tus
materias si la cierras.

#### Pasar capturas del portal con una IA

Si tienes capturas de la oferta de grupos, no tienes que escribirlas a mano:

1. En la página, abre **"¿Tienes capturas del portal?"** y copia las instrucciones.
2. Pégalas en una IA que acepte imágenes (Claude, ChatGPT, Gemini…) junto con tus capturas.
3. Copia la respuesta, pégala en la página y elige **Agregar a mi tabla** o **Reemplazar mi tabla**.

Para probarlo, en [`ejemplos/`](ejemplos) hay tres capturas de muestra, una por materia y con tres
grupos cada una: un portal en computador ([`foto-calculo-iii.png`](ejemplos/foto-calculo-iii.png)),
una pantalla de celular ([`foto-redes.png`](ejemplos/foto-redes.png)) y una foto inclinada y con
reflejo tomada a un monitor ([`foto-bases-de-datos.png`](ejemplos/foto-bases-de-datos.png)).

### En la consola (Python)

Necesitas **Python 3.9 o más reciente**. En Windows, si `python` abre la Microsoft Store,
usa `py` en su lugar (por ejemplo, `py main.py ejemplos/cursos.csv`).

```bash
# 1. Instalar la librería para dibujar el horario
pip install -r requirements.txt

# 2. Correr con el ejemplo
python main.py ejemplos/cursos.csv

# 3. Ver los 5 mejores y guardar la imagen con otro nombre
python main.py ejemplos/cursos.csv --top 5 --imagen mi_horario.png

# 4. Marcar horas ocupadas: un día, un rango de días o varios días (se puede repetir)
python main.py ejemplos/cursos.csv --bloquear "Lun-Vie 06:00-08:00" --bloquear "Mar,Jue 14:00-18:00"
```

Salida en la consola:

```
Materias: 5
Combinaciones posibles: 162
Nodos revisados: 24 | tiempo: 0.5 ms

Opción 1 (puntaje -1.50)
Hora   Lun             Mar             Mie             Jue             Vie
08:00  Calculo III (A)                 Calculo III (A)
10:00  Bases de Da (A)                 Bases de Da (A)
12:00  Ingles IV (C)   Etica (A)       Ingles IV (C)
14:00  Redes (B)                       Redes (B)
...
Huecos: 1.0 h | Antes de las 8: 0.0 h | Después de las 6 p. m.: 0.0 h | Días: 3 | Lunes: 8.0 h | Viernes: libre | Puntaje: -1.50
```

Además guarda el mejor horario como imagen:

![Imagen generada por la versión de Python](docs/ejemplo.png)

## Formato de los cursos (CSV)

Una fila por **cada sesión** de clase. Si un grupo ve clase lunes y miércoles, son dos filas:

```csv
materia,grupo,dia,inicio,fin,profesor,salon
Calculo III,A,Lun,08:00,10:00,Perez,A-201
Calculo III,A,Mie,08:00,10:00,Perez,A-201
Calculo III,B,Mar,10:00,12:00,Gomez,A-305
```

- `dia`: `Lun`, `Mar`, `Mie`, `Jue`, `Vie` o `Sab`
- `inicio` y `fin`: hora en formato 24 h (`14:00` = 2 p. m.)
- `profesor` y `salon` son opcionales

Puedes armar el archivo en Excel y guardarlo como **CSV UTF-8**.

## ¿Cómo funciona por dentro?

Usa **backtracking con poda** (ramificación y poda):

1. Ordena las materias de la que tiene menos grupos a la que tiene más.
2. Escoge un grupo de la primera materia, luego uno de la segunda, y así sucesivamente.
3. Si un grupo **se cruza** con lo que ya escogió, lo descarta y prueba otro (*backtracking*).
4. Si lo escogido hasta ahora **ya no puede superar** a los mejores horarios encontrados, deja de explorar ese camino (*poda*).
5. Al completar todas las materias, guarda el horario si está entre los mejores.

Antes de empezar quita los grupos que caen en **horas ocupadas**; si alguna materia se queda sin
grupos, avisa que no hay horario posible.

**Detalle de la poda:** la cota usa solo las horas fuera de rango y los días usados, porque esos
puntos solo pueden **subir** al agregar materias. Los huecos **no** entran en la cota: una materia
nueva puede caer en medio de un hueco y taparlo, así que los huecos pueden **bajar**.
El premio del lunes también hace **bajar** el puntaje, así que la cota resta de una vez el máximo
premio de lunes que todavía podrían dar las materias que faltan.

Sin poda habría que revisar el producto de los grupos de todas las materias
(por ejemplo, 6 materias con 4 grupos = 4⁶ = 4.096 horarios). La poda revisa muchos menos.

## Estructura del proyecto

```
creador-horarios/
├── index.html           # versión web (mismo algoritmo en JavaScript, festivos y calendario .ics)
├── main.py              # punto de entrada (línea de comandos)
├── horario/
│   ├── datos.py         # lee el CSV y las horas ocupadas
│   ├── costo.py         # puntaje: huecos, horas fuera de rango, días, viernes y lunes
│   ├── buscador.py      # backtracking con poda (sin los grupos que caen en horas ocupadas)
│   └── mostrar.py       # tabla en consola e imagen PNG
├── ejemplos/
│   ├── cursos.csv       # datos de ejemplo
│   └── foto-*.png       # capturas de muestra para probar la lectura con IA
├── tests/               # pruebas: poda = fuerza bruta, y la web = Python
└── docs/                # imágenes del README
```

## Pruebas

```bash
python tests/test_buscador.py   # la poda encuentra el mismo óptimo que probar todo
python tests/test_web.py        # la página web da lo mismo que Python (necesita Node.js)
```

- `test_buscador.py` comprueba, con cientos de casos al azar (con y sin horas ocupadas), que la
  búsqueda con poda encuentra el mismo óptimo que probar todas las combinaciones.
- `test_web.py` corre el JavaScript de `index.html` con Node.js y comprueba que da los mismos
  puntajes que Python en 300 casos al azar. También revisa los festivos de 2026 contra la lista
  oficial y el archivo de calendario. Si Node.js no está instalado, se salta.

## Próximas ideas

- [x] Interfaz web que no necesita instalar nada.
- [x] Pasar **capturas de pantalla** a la tabla (con cualquier IA, copiando y pegando).
- [ ] Hacerlo en un solo clic (subir la foto directo a la página, con un servidor que llame a la API).
- [x] Bloquear horas (por ejemplo, "los martes trabajo de 2 a 6").
- [x] Exportar el horario al calendario (`.ics`), sin los festivos de Colombia.
- [ ] Preferir o evitar profesores.

## Origen

Nació a partir del proyecto de **Matemáticas Computacionales (UNAB)**, donde se resolvió el reparto
de prácticas de un laboratorio con backtracking, poda y gradiente descendente.

## Licencia

[MIT](LICENSE) — David Angarita Avendaño
