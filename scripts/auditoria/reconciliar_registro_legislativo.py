# -*- coding: utf-8 -*-
"""
🏛️ Q-BE — RECONCILIADOR MECÁNICO DEL REGISTRO MAESTRO DE IDENTIFICADORES (PASO 0)
Herramienta de gobernanza (no de negocio): reconstruye la tabla del KYBERN ID LEDGER
(`docs/ID_REGISTRY.md`) a partir de los encabezados REALES publicados en los Libros sellados
(`docs/LOGIC.md` y `docs/ARCH.md`), garantizando consolidación al 100%.

Régimen: [DIRGEN-STRICT]. La herramienta NO inventa nodos, NO reasigna identificadores y NO
modifica un solo título: transcribe verbatim lo que los Libros publican (anclaje simbólico, R-2:
libro dueño + símbolo, jamás `archivo:línea` que rota con cada enmienda).

Salvaguarda anti-destrucción (DICTAMEN DEL DIRECTOR — hallazgo residual, 2026-10-04):
  * El modo POR DEFECTO es SOLO LECTURA. Ningún invocante puede mutar la Base de Gobierno por
    accidente ni por omisión de bandera.
  * La reescritura de la tabla exige la bandera explícita `--write`.
  * Al escribir, el ESTADO preexistente de cada fila (`LIBRE`, `EN FORJA`, `SELLADO` o cualquier
    otro declarado por el Director) se PRESERVA celda por celda; sólo los nodos anclados por
    primera vez reciben `SELLADO`, y se reportan en consola para su ratificación fiduciaria.

Uso:
    python scripts/auditoria/reconciliar_registro_legislativo.py            # SOLO LECTURA (audita)
    python scripts/auditoria/reconciliar_registro_legislativo.py --check    # SOLO LECTURA (explícito)
    python scripts/auditoria/reconciliar_registro_legislativo.py --write    # reconcilia (escribe)
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOGIC_PATH = PROJECT_ROOT / "docs" / "LOGIC.md"
ARCH_PATH = PROJECT_ROOT / "docs" / "ARCH.md"
REGISTRY_PATH = PROJECT_ROOT / "docs" / "ID_REGISTRY.md"

# Reservas explícitas del Director que no publican encabezado propio en los Libros.
RESERVADOS = {
    "LN-QBE-092": ("LOGIC", "*(Reservado - Conciliación de Mercados Derivados)*", "LIBRE"),
}

PATRON_LOGICO = re.compile(r'^###\s+ID:\s+\[(LN-QBE-[A-Za-z0-9_\-]+)\]\s*(.*)$')
PATRON_ARCH = re.compile(r'^###\s+\[(ARCH-[0-9A-Za-z\.\-_]+)\]\s*(.*)$')

# [DIRGEN-STRICT] Estado asignado EXCLUSIVAMENTE a las filas de nodos que aún no existían en el
# registro. Todo estado preexistente se preserva verbatim (salvaguarda anti-destrucción).
ESTADO_POR_DEFECTO = "SELLADO"
PATRON_CELDA_ID = re.compile(r'^`?\[([^\]]+)\]`?$')
PATRON_ESTADO = re.compile(r'^[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ \-]*$')


def extraer_estados_previos(registro: str) -> dict:
    """Lee la tabla vigente y devuelve {id_del_nodo: estado} SIN interpretar ni normalizar.

    El estado es una anotación fiduciaria del Director: la herramienta JAMÁS lo degrada, lo
    promueve ni lo reasigna por su cuenta.
    """
    estados = {}
    for linea in registro.splitlines():
        if not linea.strip().startswith("|"):
            continue
        # Split respetando las barras escapadas (`\\|`) que el saneado inserta en los títulos.
        celdas = [celda.strip() for celda in re.split(r'(?<!\\)\|', linea.strip())]
        if len(celdas) < 7:
            continue
        coincidencia = PATRON_CELDA_ID.match(celdas[1])
        if not coincidencia:
            continue
        estado = celdas[-2]
        if PATRON_ESTADO.match(estado or ""):
            estados[coincidencia.group(1)] = estado
    return estados


def _celda(texto: str) -> str:
    """Sanea una celda markdown: prohibido que una barra rompa la tabla."""
    return " ".join(str(texto).split()).replace("|", "\\|") or "(Sin título publicado)"


def extraer_nodos() -> list:
    """Extrae (familia, id, título) de los Libros sellados, en el orden en que se publican."""
    nodos, vistos = [], set()
    for familia, ruta, patron in (("LOGIC", LOGIC_PATH, PATRON_LOGICO), ("ARCH", ARCH_PATH, PATRON_ARCH)):
        if not ruta.exists():
            raise SystemExit(f"[ALTO AL FUEGO] Libro canónico ausente: {ruta}")
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            coincidencia = patron.match(linea.strip())
            if not coincidencia:
                continue
            nodo_id, titulo = coincidencia.group(1), coincidencia.group(2)
            if nodo_id in vistos:
                raise SystemExit(f"[ALTO AL FUEGO] Nodo duplicado en los Libros: {nodo_id}")
            vistos.add(nodo_id)
            nodos.append((familia, nodo_id, _celda(titulo)))
    for nodo_id, (familia, titulo, estado) in RESERVADOS.items():
        if nodo_id not in vistos:
            vistos.add(nodo_id)
            nodos.append((familia, nodo_id, titulo, estado))
    return nodos


def construir_tabla(nodos: list, estados_previos: dict) -> tuple:
    """Reconstruye la tabla preservando el estado preexistente de cada fila.

    Devuelve `(tabla, ids_nuevos)`: los `ids_nuevos` son los nodos anclados por PRIMERA vez y que
    por tanto reciben `ESTADO_POR_DEFECTO` (deben ser ratificados por el Director).
    """
    filas = [
        "| ID | Familia | Anclaje Simbólico | Nombre del Nodo / Título | Estado |",
        "|---|:---:|:---:|---|:---:|",
    ]
    ids_nuevos = []
    for nodo in nodos:
        familia, nodo_id, titulo = nodo[0], nodo[1], nodo[2]
        if len(nodo) > 3:
            estado = nodo[3]  # Reserva explícita del Director (`RESERVADOS`).
        else:
            estado = estados_previos.get(nodo_id)
            if estado is None:
                estado = ESTADO_POR_DEFECTO
                ids_nuevos.append(nodo_id)
        libro = "docs/LOGIC.md" if familia == "LOGIC" else "docs/ARCH.md"
        filas.append(f"| `[{nodo_id}]` | {familia} | `{libro}` | {titulo} | {estado} |")
    return "\n".join(filas), ids_nuevos


def main() -> int:
    for flujo in (sys.stdout, sys.stderr):
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8")

    modo_escritura = "--write" in sys.argv
    if modo_escritura and "--check" in sys.argv:
        raise SystemExit(
            "[ALTO AL FUEGO] Banderas contradictorias: `--write` (muta la Base de Gobierno) y "
            "`--check` (solo lectura) son mutuamente excluyentes."
        )

    nodos = extraer_nodos()
    if not REGISTRY_PATH.exists():
        raise SystemExit(f"[ALTO AL FUEGO] Registro Maestro ausente: {REGISTRY_PATH}")
    registro = REGISTRY_PATH.read_text(encoding="utf-8")
    estados_previos = extraer_estados_previos(registro)

    faltantes = [f"[{nodo[1]}]" for nodo in nodos if f"[{nodo[1]}]" not in registro]

    # ── MODO POR DEFECTO: SOLO LECTURA (auditoría). Cero mutación implícita. ──────
    if not modo_escritura:
        if faltantes:
            print(f"🚨 REGISTRO INCOMPLETO: {len(faltantes)} nodos sin anclaje: {faltantes}")
            print("   (sugerencia: `--write` para anclar los nodos faltantes preservando estados)")
            return 1
        print(f"✅ REGISTRO COMPLETO: {len(nodos)} nodos anclados simbólicamente (cobertura 100%).")
        print(f"   Modo SOLO LECTURA (por defecto). Filas con estado preservado: {len(estados_previos)}.")
        return 0

    tabla, ids_nuevos = construir_tabla(nodos, estados_previos)
    patron = re.compile(r"\| ID \| Familia \|.*?\n---", re.DOTALL)
    if not patron.search(registro):
        raise SystemExit("[ALTO AL FUEGO] No se localizó la tabla del Registro Maestro (marcador | ID | Familia |).")
    # Reemplazo LITERAL (función): los títulos contienen LaTeX (`\kappa`, `\rho`) que `re.sub`
    # interpretaría como grupos de escape. Cero corrupción de títulos.
    REGISTRY_PATH.write_text(patron.sub(lambda _: tabla + "\n\n---", registro, count=1), encoding="utf-8")

    print(f"✅ Registro Maestro reconciliado: {len(nodos)} nodos anclados (LOGIC + ARCH, cobertura 100%).")
    print(f"   Estados preexistentes PRESERVADOS: {len(estados_previos)} filas.")
    if ids_nuevos:
        print(f"⚠️  Nodos anclados por PRIMERA vez con estado `{ESTADO_POR_DEFECTO}`: {ids_nuevos}")
        print("    (ratifique su estado fiduciario si no corresponde a SELLADO)")
    if faltantes:
        print(f"   (antes: {len(faltantes)} nodos huérfanos)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
