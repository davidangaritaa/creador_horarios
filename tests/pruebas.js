/*
 * Pruebas del creador de horarios.
 *
 * Toma la lógica de index.html (entre las marcas "inicio de la lógica" y
 * "fin de la lógica") y la prueba con Node.js, sin navegador:
 *   - la búsqueda con poda encuentra el mismo óptimo que probar todas las
 *     combinaciones (fuerza bruta), en cientos de casos al azar con horas
 *     ocupadas y profesores evitados;
 *   - huecos, horas ocupadas, premio del lunes, viernes y profesores;
 *   - grupos fijos y el enlace para compartir;
 *   - lectura de CSV y de respuestas de una IA;
 *   - festivos de Colombia y el archivo de calendario (.ics).
 *
 * Correr con:  node tests/pruebas.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const vm = require("vm");
const assert = require("assert");

// ---------- Cargar la lógica de la página ----------
const html = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const inicio = html.indexOf("// ---8<--- inicio de la lógica");
const fin = html.indexOf("// ---8<--- fin de la lógica");
assert(inicio >= 0 && fin > inicio, "No encontré las marcas de la lógica en index.html");
const L = vm.runInNewContext(html.slice(inicio, fin) + `
;({ DIAS, PESOS_INICIALES, aMinutos, seCruzan, grupoChoca, chocaConBloqueos, horasDeHueco,
    detalleCosto, buscar, construirCursos, parsearCSV, extraerCSVDeRespuesta, EJEMPLO_CSV,
    tieneProfeEvitado, festivosColombia, generarICS, empacarEstado, desempacarEstado });`, {});

const CFG = (extra = {}) => ({ pesos: { ...L.PESOS_INICIALES }, horaInicio: 480, horaFin: 1080, top: 5, bloqueos: [], evitar: [], ...extra });
const casi = (a, b) => Math.abs(a - b) < 1e-9;
// La lógica corre en otro contexto: se compara por contenido, no por tipo de objeto
const igual = (a, b) => assert.deepStrictEqual(JSON.parse(JSON.stringify(a)), b);
const S = (dia, desde, hasta) => ({ dia, inicio: L.aMinutos(desde), fin: L.aMinutos(hasta) });

// ---------- Mini corredor de pruebas ----------
const pruebas = [];
const prueba = (nombre, fn) => pruebas.push({ nombre, fn });

// ---------- Fuerza bruta: prueba TODAS las combinaciones ----------
function fuerzaBruta(cursos, cfg) {
  // Un grupo fijo deja a su materia con solo ese grupo (si existe)
  const fijos = cfg.fijos || {};
  cursos = Object.fromEntries(Object.entries(cursos).map(([m, gs]) => {
    const f = fijos[m.toLowerCase()], solo = gs.filter(g => f && g.nombre.toLowerCase() === f.toLowerCase());
    return [m, solo.length ? solo : gs];
  }));
  const materias = Object.keys(cursos);
  let mejor = Infinity;
  (function recorrer(i, elegidos) {
    if (i === materias.length) { mejor = Math.min(mejor, L.detalleCosto(elegidos, cfg).total); return; }
    for (const g of cursos[materias[i]]) {
      if (L.grupoChoca(g, elegidos) || L.chocaConBloqueos(g, cfg.bloqueos)) continue;
      recorrer(i + 1, elegidos.concat([g]));
    }
  })(0, []);
  return mejor;
}

// Generador de números al azar con semilla (para que las pruebas den siempre lo mismo)
function azar(semilla) {
  let x = semilla >>> 0;
  const r = () => ((x = (x * 1664525 + 1013904223) >>> 0) / 2 ** 32);
  return { entero: (a, b) => a + Math.floor(r() * (b - a + 1)), elegir: arr => arr[Math.floor(r() * arr.length)] };
}

// ---------- Pruebas ----------
prueba("el ejemplo da el horario esperado", () => {
  const { cursos, errores } = L.construirCursos(L.parsearCSV(L.EJEMPLO_CSV));
  assert.strictEqual(errores.length, 0);
  assert.strictEqual(Object.keys(cursos).length, 5);
  const r = L.buscar(cursos, CFG());
  assert(casi(r.mejores[0].costo, 0), `costo ${r.mejores[0].costo}`);
  assert(casi(r.mejores[0].costo, fuerzaBruta(cursos, CFG())));
});

prueba("la poda da el mismo óptimo que la fuerza bruta (500 casos al azar)", () => {
  const rnd = azar(42);
  for (let caso = 0; caso < 500; caso++) {
    const cursos = {};
    for (let m = 0, nm = rnd.entero(2, 6); m < nm; m++) {
      const grupos = [];
      for (let g = 0, ng = rnd.entero(1, 4); g < ng; g++) {
        const sesiones = [];
        for (let k = 0, nk = rnd.entero(1, 3); k < nk; k++) {
          const ini = rnd.entero(6, 19) * 60 + rnd.elegir([0, 30]);
          const s = { dia: rnd.elegir(L.DIAS), inicio: ini, fin: ini + rnd.elegir([60, 90, 120, 180]) };
          if (!sesiones.some(o => L.seCruzan(s, o))) sesiones.push(s);   // un grupo real no se pisa a sí mismo
        }
        grupos.push({ materia: `M${m}`, nombre: `G${g}`, sesiones, profesor: rnd.elegir(["Carlos Rojas", "Andrés Pérez", "Díaz", ""]) });
      }
      cursos[`M${m}`] = grupos;
    }
    const bloqueos = [];
    for (let k = 0, nb = rnd.elegir([0, 0, 1, 2, 3]); k < nb; k++) {
      const ini = rnd.entero(7, 18) * 60 + rnd.elegir([0, 30]);
      bloqueos.push({ dia: rnd.elegir(L.DIAS.slice(0, 5)), inicio: ini, fin: ini + rnd.elegir([60, 120, 240]) });
    }
    const cfg = CFG({ top: rnd.elegir([1, 3]), bloqueos, evitar: rnd.elegir([[], [], ["rojas"], ["PEREZ", "Díaz"]]),
                      fijos: rnd.elegir([{}, {}, { m0: "g1" }, { m1: "G0", m2: "G2" }, { m0: "no existe" }]) });
    // Pesos al azar: así cada regla pesa lo suficiente para notar si la poda se equivoca
    cfg.pesos = { hueco: rnd.elegir([1, 0.2, 0]), temprano: rnd.elegir([2, 0.5]), tarde: rnd.elegir([2, 0.5]),
                  dia: rnd.elegir([0.5, 0, 3]), viernes: rnd.elegir([1.5, 0, 4]), lunes: rnd.elegir([0.5, 3, 6]),
                  profesor: rnd.elegir([5, 1, 0]) };
    const r = L.buscar(cursos, cfg);
    const esperado = fuerzaBruta(cursos, cfg);
    if (esperado === Infinity) assert.strictEqual(r.mejores.length, 0, `caso ${caso}`);
    else assert(r.mejores.length && casi(r.mejores[0].costo, esperado), `caso ${caso}: poda ${r.mejores[0] && r.mejores[0].costo}, fuerza bruta ${esperado}`);
  }
});

prueba("huecos y horas ocupadas", () => {
  const clases = [S("Lun", "08:00", "10:00"), S("Lun", "14:00", "16:00")];
  assert.strictEqual(L.horasDeHueco(clases, []), 4);
  assert.strictEqual(L.horasDeHueco(clases, [S("Lun", "10:00", "14:00")]), 0);              // trabajo en medio: no es hueco
  assert.strictEqual(L.horasDeHueco(clases, [S("Lun", "11:00", "12:00")]), 3);
  assert.strictEqual(L.horasDeHueco(clases, [S("Lun", "10:00", "12:00"), S("Lun", "11:00", "13:00")]), 1); // no cuenta doble
  assert.strictEqual(L.horasDeHueco(clases, [S("Lun", "17:00", "19:00")]), 4);              // fuera de las clases
});

prueba("una materia sin grupos libres se reporta", () => {
  const { cursos } = L.construirCursos(L.parsearCSV(L.EJEMPLO_CSV));
  const lunAVie = ["Lun", "Mar", "Mie", "Jue", "Vie"].map(d => S(d, "06:00", "12:00"));
  const r = L.buscar(cursos, CFG({ bloqueos: lunAVie }));
  igual(r.sinGrupo, ["Cálculo III"]);
  assert.strictEqual(r.mejores.length, 0);
});

prueba("premio del lunes y castigo del viernes", () => {
  const cfg = CFG();
  const lunes = L.detalleCosto([{ materia: "X", nombre: "A", sesiones: [S("Lun", "08:00", "10:00")] }], cfg);
  const viernes = L.detalleCosto([{ materia: "X", nombre: "B", sesiones: [S("Vie", "08:00", "10:00")] }], cfg);
  assert.strictEqual(lunes.horasLunes, 2);
  assert.strictEqual(viernes.viernes, 1);
  assert(casi(viernes.total - lunes.total, cfg.pesos.viernes + 2 * cfg.pesos.lunes));
});

prueba("profesores que se quieren evitar", () => {
  const g = { profesor: "Carlos Rojas", sesiones: [] };
  assert(L.tieneProfeEvitado(g, ["rojas"]));
  assert(L.tieneProfeEvitado(g, ["  CARLOS  rojas "]));
  assert(!L.tieneProfeEvitado(g, ["Pérez"]));
  assert(!L.tieneProfeEvitado({ profesor: "", sesiones: [] }, ["Rojas"]));
  assert(L.tieneProfeEvitado({ profesor: "Andrés Pérez", sesiones: [] }, ["perez"]));
  // En el ejemplo, evitando a Pérez y Smith se escogen otros grupos
  const { cursos } = L.construirCursos(L.parsearCSV(L.EJEMPLO_CSV));
  const r = L.buscar(cursos, CFG({ evitar: ["Perez", "Smith"] }));
  assert(r.mejores[0].grupos.every(g => !L.tieneProfeEvitado(g, ["Perez", "Smith"])));
  // Si el único grupo es con ese profesor, la materia se queda
  const solo = { Etica: [{ materia: "Etica", nombre: "A", profesor: "Mora", sesiones: [S("Mar", "12:00", "14:00")] }] };
  assert.strictEqual(L.buscar(solo, CFG({ evitar: ["Mora"] })).mejores[0].grupos[0].profesor, "Mora");
});

prueba("grupos fijos", () => {
  const { cursos } = L.construirCursos(L.parsearCSV(L.EJEMPLO_CSV));
  const libre = L.buscar(cursos, CFG()).mejores[0].grupos.find(g => g.materia === "Cálculo III");
  const otro = cursos["Cálculo III"].find(g => g.nombre !== libre.nombre);
  const cfg = CFG({ fijos: { "cálculo iii": otro.nombre.toLowerCase() } });   // sin importar mayúsculas
  const r = L.buscar(cursos, cfg);
  assert.strictEqual(r.mejores[0].grupos.find(g => g.materia === "Cálculo III").nombre, otro.nombre);
  assert(r.mejores.every(o => o.grupos.find(g => g.materia === "Cálculo III").nombre === otro.nombre));
  igual(r.fijados, ["Cálculo III"]);
  assert(casi(r.mejores[0].costo, fuerzaBruta(cursos, cfg)));
  // Un grupo fijo que ya no existe no se aplica
  igual(L.buscar(cursos, CFG({ fijos: { "cálculo iii": "zzz" } })).fijados, []);
  // Si el grupo fijo cae en una hora ocupada, la materia no cabe
  const s = otro.sesiones[0];
  const r2 = L.buscar(cursos, CFG({ fijos: cfg.fijos, bloqueos: [{ dia: s.dia, inicio: s.inicio, fin: s.fin }] }));
  igual(r2.sinGrupo, ["Cálculo III"]);
});

prueba("enlace para compartir: ida y vuelta", () => {
  const estado = {
    filas: L.parsearCSV(L.EJEMPLO_CSV), pesos: { ...L.PESOS_INICIALES, hueco: 3 }, horaInicio: "07:00", horaFin: "17:30", top: 3,
    bloqueos: [{ nombre: "Trabajo, turno", dias: ["Lun", "Mar"], inicio: "06:00", fin: "12:00" }],
    evitar: ["Pérez"], fijos: { "cálculo iii": "B" },
  };
  const paquete = JSON.parse(JSON.stringify(L.empacarEstado(estado, 2)));   // como viaja en el enlace
  const { estado: vuelta, seleccion } = L.desempacarEstado(paquete);
  igual(vuelta, JSON.parse(JSON.stringify(estado)));
  assert.strictEqual(seleccion, 2);
  assert.throws(() => L.desempacarEstado({ v: 9 }));
  assert.throws(() => L.desempacarEstado(null));
});

prueba("lectura de CSV (coma, punto y coma, tildes, a. m. / p. m.)", () => {
  const f = L.parsearCSV("﻿Materia;Grupo;Día;Inicio;Fin\nÉtica;A;miércoles;2:00 p. m.;4:00 PM\n");
  igual(f[0], { materia: "Ética", grupo: "A", dia: "Mie", inicio: "14:00", fin: "16:00", profesor: "", salon: "" });
  const { errores } = L.construirCursos([{ materia: "X", grupo: "A", dia: "Lun", inicio: "10:00", fin: "09:00" }]);
  assert.strictEqual(errores.length, 1);
});

prueba("respuestas pegadas desde una IA", () => {
  const conBloque = "Aquí tienes:\n```csv\nmateria,grupo,dia,inicio,fin,profesor,salon\nCálculo III,1234,Lun,07:00,09:00,\"Pérez, Juan\",A-201\n```\nNo pude leer el NRC 5678.";
  assert.strictEqual(L.extraerCSVDeRespuesta(conBloque)[0].profesor, "Pérez, Juan");
  assert.strictEqual(L.extraerCSVDeRespuesta("Etica;B;Vie;11:00;13:00;Mora;E-001").length, 1);   // sin encabezado
  assert.strictEqual(L.extraerCSVDeRespuesta("materia\tgrupo\tdia\tinicio\tfin\nRedes\tA\tMar\t8:00\t10:00")[0].inicio, "08:00");
  assert.throws(() => L.extraerCSVDeRespuesta("Lo siento, no veo ninguna imagen."));
});

prueba("festivos de Colombia 2026 (lista oficial)", () => {
  igual(L.festivosColombia(2026), [
    "2026-01-01", "2026-01-12", "2026-03-23", "2026-04-02", "2026-04-03", "2026-05-01",
    "2026-05-18", "2026-06-08", "2026-06-15", "2026-06-29", "2026-07-20", "2026-08-07",
    "2026-08-17", "2026-10-12", "2026-11-02", "2026-11-16", "2026-12-08", "2026-12-25"]);
});

prueba("archivo de calendario (.ics)", () => {
  const grupos = [{ materia: "Cálculo III, avanzado", nombre: "A", profesor: "Pérez",
    sesiones: [{ dia: "Lun", inicio: 480, fin: 600, salon: "A-201" }, { dia: "Mie", inicio: 480, fin: 600, salon: "A-201" }] }];
  const r = L.generarICS(grupos, { inicio: "2026-08-03", fin: "2026-11-27", saltarFestivos: true, alarma: true, ahora: new Date(Date.UTC(2026, 6, 1)) });
  const t = r.texto;
  assert(t.startsWith("BEGIN:VCALENDAR\r\n") && t.endsWith("END:VCALENDAR\r\n"));
  assert.strictEqual(t.split("BEGIN:VEVENT").length - 1, 2);
  assert(t.includes("DTSTART;TZID=America/Bogota:20260803T080000"));      // primer lunes
  assert(t.includes("DTSTART;TZID=America/Bogota:20260805T080000"));      // primer miércoles
  assert(t.includes("RRULE:FREQ=WEEKLY;UNTIL=20261128T045959Z"));
  for (const f of ["20260817", "20261012", "20261102", "20261116"])        // lunes festivos de ago. a nov.
    assert(t.includes(`EXDATE;TZID=America/Bogota:${f}T080000`), f);
  assert.strictEqual(r.omitidos, 4);
  assert(t.includes("SUMMARY:Cálculo III\\, avanzado (grupo A)"));        // comas escapadas
  assert(t.includes("TRIGGER:-PT15M"));
});

// ---------- Correr ----------
let fallas = 0;
for (const { nombre, fn } of pruebas) {
  try { fn(); console.log(`  ✓ ${nombre}`); }
  catch (e) { fallas++; console.log(`  ✗ ${nombre}\n      ${e.message}`); }
}
console.log(fallas ? `\n${fallas} prueba(s) fallaron.` : `\nLas ${pruebas.length} pruebas pasaron.`);
process.exit(fallas ? 1 : 0);
