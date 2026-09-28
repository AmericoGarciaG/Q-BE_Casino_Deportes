# -*- coding: utf-8 -*-
"""
🏆 Q-BE CD WEB — SENSOR DE MERCADO PROGOL (src/ingestion/progol_scraper.py)
[LN-QBE-075] Ingesta Fáctica de Concursos Progol Regular y Revancha desde miloteria.mx.
Régimen: [DBBD-FUNGIBLE] (Ingesta / Normalización — CERO matemática protegida).

Contratos rectores:
- [ARCH-1.6.6] Aislamiento de red: Playwright se invoca EXCLUSIVAMENTE en extraer_concurso_activo();
  parse_progol_text() es pura sobre texto (testeable sin red — [GOV-TEST-01]).
- [GOVERNANCE-01] Cero equipos sintéticos: los clubes no resueltos se preservan crudos.
- [LN-QBE-075] El Prior de Ignorancia Fiduciaria (1/3, 1/3, 1/3) vive aquí como FUENTE ÚNICA.

Nota de diseño [VARIANCE-04 ratificada]: el sitio emite cada casilla en TRES líneas con una línea
de tabulador intercalada como separador de celdas del DOM:
    "1." / "MEXICO" / "\t" / "COLOMBIA" / "" / ""
El terminador fáctico de casilla es el DOBLE salto en blanco; la línea "\t" NUNCA es terminador.
Se tolera además el layout compacto heredado de una línea ("1. MEXICO COLOMBIA").
El corte (local, visitante) se decide por scoring determinista contra el catálogo canónico:
  1) mayor peso de resolución (0 = crudo, 1 = resuelto por normalizer),
  2) menor penalización por abreviatura colgante en el local (token final terminado en "."),
  3) menor índice de corte (k mínimo).
Evidencia de validación: 21/21 casillas del concurso 2352 contra el DOM real capturado
(`data/output/diag_progol_dom.txt`), sin ningún par local/visitante incompleto.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple

from src.ingestion.normalizer import canonicalize_team_name

logger = logging.getLogger("ProgolScraper")

URL_PROGOL_DEFAULT = "https://miloteria.mx/progol"

# [LN-QBE-075] Prior de Ignorancia Fiduciaria — Fuente ÚNICA de verdad (1-X-2).
PRIOR_IGNORANCIA_FIDUCIARIA = (0.3333, 0.3333, 0.3334)

CASILLAS_REGULAR = 14
CASILLAS_REVANCHA = 7

# ── [LN-QBE-075 / VARIANCE-05] JERGA COMERCIAL DEL SITIO (miloteria.mx) ──────
# El DOM oficial publica sobrenombres que el catálogo canónico NO resuelve ('AGUILAS' => 'AGUILAS').
# Estrato de TRADUCCIÓN previo al normalizador difuso: no decide cortes ni probabilidades;
# sólo restituye la identidad del club tal como la publica el operador.
PROGOL_JARGON_MAP: Dict[str, str] = {
    "AGUILAS":     "Club America",
    "C. AZUL":     "Cruz Azul",
    "S. LAGUNA":   "Santos Laguna",
    "GUADALAJARA": "Chivas Guadalajara",
    "PUMAS":       "Pumas UNAM",
    "TIGRES":      "Tigres UANL",
    "ROSARIO CEN": "Rosario Central",
    "PAISES BAJO": "Paises Bajos",
    "ATL. GO":     "Atletico Goianiense",
    "REP. COREA":  "Corea del Sur",
}

_PATRON_CASILLA = re.compile(r"^\s*(\d{1,2})\s*[\.\)]\s*(.+?)\s*$")
_PATRON_TITULO_CASILLA = re.compile(r"^\s*(\d{1,2})\s*[\.\)]\s*$")
_PATRON_SECCION_REVANCHA = re.compile(r"^\s*revancha\b", re.IGNORECASE)
_PATRON_ENCABEZADO_COLUMNAS = re.compile(r"^\s*local\b.*\bempate\b", re.IGNORECASE)
_PATRON_RUIDO_CRONOMETRO = re.compile(r"^\s*\d{1,3}\s*[dDhHmMsS]\b")


def _canonizar_seguro(nombre: str) -> str:
    """
    Normaliza a identidad canónica sin congelar la ingesta [LN-QBE-075].
    Estrato 1 — traducción de jerga comercial del sitio (PROGOL_JARGON_MAP).
    Estrato 2 — normalizador difuso contra el catálogo canónico.
    Ante excepción se preserva el nombre limpio fáctico (cero identidades sintéticas).
    """
    limpio = (nombre or "").strip()
    if not limpio:
        return ""
    traducido = PROGOL_JARGON_MAP.get(limpio.upper(), limpio)
    try:
        return canonicalize_team_name(traducido)
    except Exception as e:
        logger.warning("⚠️ Normalización fallida para '%s' (%s). Se preserva el nombre limpio.", limpio, type(e).__name__)
        return limpio


def _peso_resolucion(nombre: str) -> int:
    """Peso determinista de resolución contra el catálogo canónico (0 = crudo, 1 = resuelto)."""
    limpio = re.sub(r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]", "", nombre or "")
    if len(limpio) < 2:
        return 0
    return 1 if _canonizar_seguro(nombre).strip().lower() != (nombre or "").strip().lower() else 0


def dividir_encuentro(texto_casilla: str) -> Tuple[str, str]:
    """
    Divide una casilla Progol ("LOCAL VISITANTE") en su par local/visitante.
    Regla ratificada [VARIANCE-02]: scoring canónico + penalización de abreviatura colgante + k mínimo.
    """
    tokens = (texto_casilla or "").split()
    if not tokens:
        return "", ""
    if len(tokens) == 1:
        return tokens[0], ""

    candidatos = []
    for k in range(1, len(tokens)):
        local = " ".join(tokens[:k])
        visitante = " ".join(tokens[k:])
        candidatos.append((
            -(_peso_resolucion(local) + _peso_resolucion(visitante)),
            1 if local.endswith(".") else 0,
            k,
            local,
            visitante,
        ))
    candidatos.sort(key=lambda c: (c[0], c[1], c[2]))
    mejor = candidatos[0]
    return mejor[3], mejor[4]


class ProgolMarketScraper:
    """Sensor de Ingesta para Pronósticos Deportivos (Progol & Revancha)."""

    @staticmethod
    def _registrar_casilla(
        seccion: str,
        pos_txt: str,
        local_raw: str,
        visitante_raw: str,
        reg: List[Dict[str, Any]],
        rev: List[Dict[str, Any]],
    ) -> None:
        """Clasifica y acumula una casilla en su bloque (REGULAR / REVANCHA) sin duplicados."""
        try:
            pos = int(pos_txt)
        except (TypeError, ValueError):
            return

        if seccion == "REVANCHA":
            if pos > CASILLAS_REVANCHA:
                pos -= CASILLAS_REGULAR  # Numeración continua del sitio 15..21 -> 1..7
            if not 1 <= pos <= CASILLAS_REVANCHA:
                return
            destino, tipo = rev, "REVANCHA"
        else:
            if not 1 <= pos <= CASILLAS_REGULAR:
                return
            destino, tipo = reg, "REGULAR"

        if any(p["posicion"] == pos for p in destino):
            return

        local_raw = (local_raw or "").strip()
        visitante_raw = (visitante_raw or "").strip()
        destino.append({
            "posicion": pos,
            "local_raw": local_raw,
            "visitante_raw": visitante_raw,
            "local_canonico": _canonizar_seguro(local_raw),
            "visitante_canonico": _canonizar_seguro(visitante_raw),
            "tipo": tipo,
        })

    @classmethod
    def parse_progol_text(cls, body_text: str) -> Dict[str, Any]:
        """Extrae el número de concurso, bolsa y los 21 partidos a partir del texto del DOM."""
        texto = body_text or ""

        # 1. Concurso ID
        m_concurso = re.search(r"concurso\s*#?\s*(\d{4})", texto, re.IGNORECASE)
        concurso_num = m_concurso.group(1) if m_concurso else "ACTIVO"
        concurso_id = f"PROGOL-{concurso_num}"

        # 2. Bolsa
        m_bolsa = re.search(r"Bolsa[^\$\d]{0,40}(\$[\d,]+(?:\.\d{2})?)", texto, re.IGNORECASE)
        bolsa_str = m_bolsa.group(1) if m_bolsa else "Bolsa por Definir"

        # 3. Fecha Cierre
        m_cierre = re.search(r"para\s+concurso\s+\d+\s+del\s+d[ií]a\s+([^\n\r]+)", texto, re.IGNORECASE)
        cierre_str = m_cierre.group(1).strip() if m_cierre else "Viernes 19:00 hr"

        # 4. Segmentación Progol Regular vs Revancha
        partidos_regular: List[Dict[str, Any]] = []
        partidos_revancha: List[Dict[str, Any]] = []

        lineas = re.split(r"[\r\n]+", texto)
        seccion = "REGULAR"
        i = 0

        while i < len(lineas):
            linea = lineas[i].strip()

            if not linea:
                i += 1
                continue

            if _PATRON_SECCION_REVANCHA.match(linea):
                seccion = "REVANCHA"
                i += 1
                continue

            if _PATRON_ENCABEZADO_COLUMNAS.match(linea) or _PATRON_RUIDO_CRONOMETRO.match(linea):
                i += 1
                continue

            m = _PATRON_CASILLA.match(linea)
            if m:
                local_raw, visitante_raw = dividir_encuentro(m.group(2))
                cls._registrar_casilla(seccion, m.group(1), local_raw, visitante_raw, partidos_regular, partidos_revancha)
                i += 1
                continue

            m_titulo = _PATRON_TITULO_CASILLA.match(linea)
            if m_titulo:
                # [VARIANCE-04] Layout fáctico de miloteria.mx: "N." / "LOCAL" / "\t" / "VISITANTE" / "" / "".
                # La línea de tabulador es el separador de celdas del DOM y NO termina la casilla:
                # el terminador fáctico es el doble salto en blanco. Se tolera también el layout sin separador.
                crudos: List[str] = []
                j = i + 1
                blancos_seguidos = 0
                while j < len(lineas) and len(crudos) < 2:
                    cand = lineas[j].strip()
                    if (_PATRON_CASILLA.match(cand)
                            or _PATRON_TITULO_CASILLA.match(cand)
                            or _PATRON_SECCION_REVANCHA.match(cand)
                            or _PATRON_ENCABEZADO_COLUMNAS.match(cand)):
                        break
                    if not cand:
                        blancos_seguidos += 1
                        if blancos_seguidos >= 2:
                            break
                        j += 1
                        continue
                    blancos_seguidos = 0
                    crudos.append(cand)
                    j += 1

                if len(crudos) == 2:
                    cls._registrar_casilla(seccion, m_titulo.group(1), crudos[0], crudos[1], partidos_regular, partidos_revancha)
                    i = j
                elif len(crudos) == 1:
                    local_raw, visitante_raw = dividir_encuentro(crudos[0])
                    cls._registrar_casilla(seccion, m_titulo.group(1), local_raw, visitante_raw, partidos_regular, partidos_revancha)
                    i = j
                else:
                    i += 1
                continue

            i += 1

        partidos_regular.sort(key=lambda x: x["posicion"])
        partidos_revancha.sort(key=lambda x: x["posicion"])

        return {
            "concurso_id": concurso_id,
            "concurso_num": concurso_num,
            "bolsa": bolsa_str,
            "fecha_cierre": cierre_str,
            "partidos_regular": partidos_regular,
            "partidos_revancha": partidos_revancha,
        }

    @classmethod
    def extraer_concurso_activo(cls, url: Optional[str] = None) -> Dict[str, Any]:
        """Navega a miloteria.mx con Playwright Stealth y retorna el payload estructurado."""
        target_url = url or URL_PROGOL_DEFAULT

        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            logger.error("⚠️ Playwright no está instalado. Instala con: pip install playwright && playwright install chromium")
            return cls.parse_progol_text("")

        body_text = ""
        try:
            with sync_playwright() as pw:
                args = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--window-position=0,0",
                    "--ignore-certificate-errors",
                ]
                browser = pw.chromium.launch(headless=True, args=args)
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1366, "height": 900},
                    locale="es-MX",
                    timezone_id="America/Mexico_City",
                )
                page = context.new_page()
                page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                try:
                    page.goto(target_url, timeout=30_000, wait_until="domcontentloaded")
                    page.wait_for_timeout(3500)
                    body_text = page.inner_text("body")
                finally:
                    context.close()
                    browser.close()
        except Exception as e:
            logger.error("🚨 Ingesta Progol fallida (%s): %s. Se devuelve payload degradado.", type(e).__name__, e)
            return cls.parse_progol_text("")

        payload = cls.parse_progol_text(body_text)
        logger.info(
            "✅ [LN-QBE-075] Concurso %s ingestado: %d Regular + %d Revancha (bolsa=%s).",
            payload["concurso_id"],
            len(payload["partidos_regular"]),
            len(payload["partidos_revancha"]),
            payload["bolsa"],
        )
        return payload
