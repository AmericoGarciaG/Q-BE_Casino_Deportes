# 📜 REGISTRO MAESTRO DE IDENTIFICADORES CANÓNICOS (KYBERN ID LEDGER)

> **Naturaleza:** Tablero canónico de control del registro legislativo. Fuente única de verdad
> para la asignación de nuevos identificadores (`max + 1` sobre el último ID **libre**), eliminando
> el muestreo parcial del corpus que provocó las colisiones históricas.
> **Axioma:** Cero reutilización. Un identificador sellado es **inmutable y no reasignable**.
> **Auditoría computable:** `tests/shield/test_shield_legislative_registry.py` (Paso 0, pre-vuelo).
> **Ratificación:** Decreto Arquitectónico de Saneamiento Integral (Tríada Director + Arquitecto).

| ID | Familia | Archivo:Línea | Nombre del Nodo / Título | Estado |
|---|:---:|:---:|---|:---:|
| `[LN-QBE-090]` | LOGIC | `docs/LOGIC.md:566` | Escudo Forense de Invarianzas (Shield Release Gate) | SELLADO |
| `[LN-QBE-090-B]` | LOGIC | `docs/LOGIC.md:961` | Heurística de Vinculación y Emparejamiento en Slates | SELLADO |
| `[LN-QBE-091]` | LOGIC | `docs/LOGIC.md:966` | Parámetros Macro de Competiciones Descubiertas JIT | SELLADO |
| `[LN-QBE-092]` | LOGIC | `docs/LOGIC.md` | *(Reservado - Conciliación de Mercados Derivados)* | LIBRE |
| `[LN-QBE-093]` | LOGIC | `docs/LOGIC.md:971` | Arquitectura Hexagonal de Ingesta Pura (Cero DB) | SELLADO |
| `[LN-QBE-094]` | LOGIC | `docs/LOGIC.md` | Algoritmo de Desambiguación Temporal [t_cierre ± 72h] | EN FORJA |
| `[LN-QBE-095]` | LOGIC | `docs/LOGIC.md` | Guardas Léxicas de Género y Categoría (Femenil/Filial) | EN FORJA |
| `[ARCH-1.3.4]` | ARCH | `docs/ARCH.md:95` | GeminiCognitiveGateway y Ledger Contable de Inferencia | SELLADO |
| `[ARCH-1.3.5]` | ARCH | `docs/ARCH.md:1090` | Retiro y Deprecación Definitiva de Rutas Legacy | SELLADO |
| `[ARCH-1.4.23]` | ARCH | `docs/ARCH.md:1172`| Sensor de Ingesta Oficial de Liga Premier FMF | SELLADO |
| `[ARCH-1.4.24]` | ARCH | `docs/ARCH.md:1181`| Contrato Hexagonal de Proveedores de Ingesta Pura | SELLADO |
| `[ARCH-1.4.25]` | ARCH | `docs/ARCH.md` | Módulo de Normalización, Jerga y Desambiguación | EN FORJA |
| `[ARCH-1.5.11]` | ARCH | `docs/ARCH.md:1204`| Aliases Globales de Jerga Quinielera en Progol | SELLADO |
| `[ARCH-1.5.12]` | ARCH | `docs/ARCH.md` | Aprovisionador JIT de Ligas y Bóveda Soberana | EN FORJA |

---

## 📋 FICHAS DE VARIANZA HISTÓRICAS RATIFICADAS (`docs/DIRGEN_VARIANCE_REQUEST_*.md`)

| Ficha | Colisión / Hallazgo | Resolución | Estado |
|---|---|:---:|:---:|
| `docs/DIRGEN_VARIANCE_REQUEST_LN-QBE-080_COLLISION.md` | `[LN-QBE-080]` ocupado por Compilador de Reportes | Remapeo a `[LN-QBE-081]` / `[LN-QBE-082]` | RATIFICADO |
| `docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.6.19-B_ENDPOINT.md` | Endpoint REST `/api/leagues?id=` → HTTP 404 | Extracción gobernada `__NEXT_DATA__` | RATIFICADO |
| `docs/DIRGEN_VARIANCE_REQUEST_ARCH-1.5.11_COLLISION.md` | `[ARCH-1.5.11]` ocupado por PROGOL_GLOBAL_ALIASES | Remapeo a `[ARCH-1.5.12]` | RATIFICADO |
| `docs/DIRGEN_VARIANCE_REQUEST_LN-QBE-070-073.md` | Contrato `approved_matches` para Kelly atenuado (familia 070–073) | Nodo de seguimiento declarado, abierto | ABIERTO |

---

## 🔎 DEUDA DETECTADA EN EL PASO 0 (FUERA DEL ALCANCE DEL JUEZ VIGENTE)

* **Ficción documental adicional:** el Juez `tests/shield/test_shield_novibet_ingestion.py` (L17) cita la ficha
  `DIRGEN_VARIANCE_REQUEST_NOVIBET_FASE1_PASO2` (reconciliación de literales canónicos `Club Puebla`,
  `Deportivo Toluca`, `Club Pachuca` frente al contrato sellado de `normalizer.py` / `[LN-QBE-012]`).
  Dicha ficha **no existe en disco** y **no es auditada** por el Juez de Registro vigente (cuyo barrido
  normativo cubre exclusivamente `LOGIC.md` + `ARCH.md`, según mandato verbatim del Decreto).
  **Acción requerida:** autorización del Director para materializarla por transcripción (contenido ya
  íntegramente descrito en el docstring del Juez citante) y/o para **ampliar el barrido del Juez de
  Registro** a `docs/**` y `tests/**`. No se ejecuta sin autorización expresa (evita sobre-alcance del mandato).


---

## 🧭 PROTOCOLO DE ASIGNACIÓN (OBLIGATORIO PARA TODO PROMPT ARQUITECTÓNICO)

1. **Paso 0 (Pre-vuelo ineludible):** consultar este registro y ejecutar
   `pytest tests/shield/test_shield_legislative_registry.py -v`. Si el ID propuesto ya figura como
   `SELLADO` o la suite estalla, **ALTO AL FUEGO** y emisión de Ficha de Varianza.
2. **Asignación:** el nuevo ID es `max(familia) + 1` **sobre el registro completo**, nunca sobre la
   vista parcial del documento citado (trampa de muestreo documentada).
3. **Sellado:** al pasar a verde (`EXIT CODE 0`), la fila migra de `EN FORJA` a `SELLADO` con
   `archivo:línea` verificable.
