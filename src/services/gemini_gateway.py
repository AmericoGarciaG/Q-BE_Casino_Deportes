# -*- coding: utf-8 -*-
"""
🏆 Q-BE CD WEB — GATEWAY COGNITIVO UNIFICADO (GEMINI 3.6 FLASH)
[ARCH-1.3.1 / ARCH-1.3.4] Pool Circular de Llaves, Circuit Breaker y Contabilidad de Tokens.
Base de Gobierno: Kybern Framework v8.0 / v12.0
"""

import os
import sys
import time
import json
import logging
import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from src.storage.database import SessionLocal
from src.storage.models import LLMTokenLedger

logger = logging.getLogger("GeminiGateway")


def _safe_print(msg: str):
    try:
        print(msg, flush=True)
    except Exception:
        try:
            print(msg.encode("ascii", errors="replace").decode("ascii"), flush=True)
        except Exception:
            logger.info(msg)


class GeminiCognitiveGateway:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiCognitiveGateway, cls).__new__(cls)
            cls._instance._init_gateway()
        return cls._instance

    def _init_gateway(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.keys = []
        self.key_states = {}  # key: {"status": "OK", "cooldown_until": 0}
        self.current_idx = 0

        PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        # Carga física forzada de .env desde la raíz del proyecto
        env_path = os.path.join(PROJECT_ROOT, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'").strip('"')
                    if k.startswith("Gemini_API_4_QBE_") or k.startswith("GEMINI_API_KEY"):
                        if v and v not in self.keys:
                            self.keys.append(v)
                            self.key_states[v] = {"alias": k, "status": "OK", "cooldown_until": 0}

        # Auto-descubrimiento dinámico de llaves en entorno
        for k, v in os.environ.items():
            if (k.startswith("Gemini_API_4_QBE_") or k.startswith("GEMINI_API_KEY")) and v.strip():
                val = v.strip().strip("'").strip('"')
                if val and val not in self.keys:
                    self.keys.append(val)
                    self.key_states[val] = {"alias": k, "status": "OK", "cooldown_until": 0}

        # Fallback si no hay llaves
        if not self.keys:
            dummy = "DUMMY_KEY_NO_ENV"
            self.keys.append(dummy)
            self.key_states[dummy] = {"alias": "DUMMY", "status": "COOLDOWN", "cooldown_until": 9999999999}

        logger.info(f"🧠 [GATEWAY INITIALIZED] {len(self.keys)} llaves registradas. Modelo: {self.model_name}")

    def get_registered_keys(self) -> List[str]:
        return self.keys

    def get_current_key_index(self) -> int:
        return self.current_idx

    def _obtener_llave_activa(self) -> Optional[str]:
        """Selecciona la siguiente llave disponible respetando cooldowns."""
        ahora = time.time()
        for _ in range(len(self.keys)):
            k = self.keys[self.current_idx]
            st = self.key_states[k]
            if st["status"] == "COOLDOWN" and ahora > st["cooldown_until"]:
                st["status"] = "OK"
                logger.info(f"🔄 [GATEWAY] Llave {st['alias']} reactivada (cooldown expirado).")

            if st["status"] == "OK":
                return k
            self.current_idx = (self.current_idx + 1) % len(self.keys)
        return None

    def _registrar_telemetria(self, key_alias: str, task: str, prompt_tok: int, cand_tok: int, lat_ms: float, status: str):
        """Registra el consumo en el Ledger SQLite de forma atómica."""
        try:
            # Precios Gemini 3.6 Flash: $0.075 / 1M prompt, $0.30 / 1M output
            cost = (prompt_tok * 0.075 / 1e6) + (cand_tok * 0.30 / 1e6)
            db: Session = SessionLocal()
            rec = LLMTokenLedger(
                key_alias=key_alias,
                task_type=task,
                model_name=self.model_name,
                prompt_tokens=prompt_tok,
                candidates_tokens=cand_tok,
                latency_ms=lat_ms,
                cost_usd=round(cost, 6),
                status=status
            )
            db.add(rec)
            db.commit()
            db.close()
        except Exception as e:
            logger.warning(f"No se pudo registrar telemetría LLM: {e}")

    def generate_thesis(self, partido_data: Dict[str, Any]) -> str:
        """
        [LN-QBE-014] Genera la Tesis Didáctica en 4 viñetas expandidas.
        Aplica rotación de llaves, registro de tokens y fallback a Mad-Libs ante fallo.
        """
        if partido_data.get("simular_fallback"):
            from src.reporting.narrative import generar_tesis_madlibs_fallback
            return generar_tesis_madlibs_fallback(partido_data)

        fav = partido_data.get("fav_name", "Local")
        und = partido_data.get("und_name", "Visitante")
        cod = partido_data.get("codigo_estrategia", "QBE-D1")
        p_fav_raw = partido_data.get("prob_fav", 0.70)
        p_fav = (p_fav_raw * 100) if isinstance(p_fav_raw, (int, float)) and p_fav_raw <= 1.0 else (float(p_fav_raw) if isinstance(p_fav_raw, (int, float)) else 70.0)
        edge_raw = partido_data.get("edge_fav", 0.05)
        edge = (edge_raw * 100) if isinstance(edge_raw, (int, float)) and edge_raw <= 1.0 else (float(edge_raw) if isinstance(edge_raw, (int, float)) else 5.0)
        edge_und_raw = partido_data.get("edge_und", 0.0)
        edge_und = (edge_und_raw * 100) if isinstance(edge_und_raw, (int, float)) and abs(edge_und_raw) <= 1.0 else (float(edge_und_raw) if isinstance(edge_und_raw, (int, float)) else 0.0)
        # Extraer puestos reales desde tabla_10p si existen
        t10p = partido_data.get("tabla_10p", [])
        fav_pos = partido_data.get("fav_puesto") or (t10p[0].get("puesto") if len(t10p) > 0 else 1)
        und_pos = partido_data.get("und_puesto") or (t10p[1].get("puesto") if len(t10p) > 1 else 18)
        fav_pts = partido_data.get("fav_pts") or (t10p[0].get("pts") if len(t10p) > 0 else 0)
        und_pts = partido_data.get("und_pts") or (t10p[1].get("pts") if len(t10p) > 1 else 0)

        # Extraer montos reales de inversión y ganancia
        boletos = partido_data.get("boletos", {})
        inv = float(partido_data.get("inversion_total") or boletos.get("inversion_partido_A_i") or 16.0)
        proy = partido_data.get("proyecciones", {})
        gan = float(partido_data.get("ganancia_neta") or proy.get("ganancia_neta_principal_mxn") or 4.0)

        prompt = f"""
Actúa como un Socio Cuantitativo Senior de un Fondo de Inversión Deportivo.
Tu objetivo es redactar la Tesis Didáctica de Inversión en exactamente 4 viñetas HTML en ESPAÑOL.

DATOS FÁCTICOS CERTIFICADOS DEL ENCUENTRO:
• Partido: {fav} (#{fav_pos}, {fav_pts} pts) vs {und} (#{und_pos}, {und_pts} pts)
• Estrategia Seleccionada: {cod}
• Probabilidad Modelo Q-BE: {p_fav:.1f}% para {fav} | Edge (+EV): {edge:+.2f}%
• Asignación de Capital: ${inv:.2f} MXN | Ganancia Neta Esperada: ${gan:.2f} MXN

REGLAS DE ORO DE GENERACIÓN:
1. IDIOMA: 100% ESPAÑOL. Queda estrictamente prohibido emitir palabras, notas o pensamientos en inglés.
2. CERO PREÁMBULOS: Comienza tu respuesta DIRECTAMENTE con '<div>• <strong>Momento y Tabla:</strong>'. Prohibido incluir introducciones, saludos o explicaciones previas.
3. EXTENSIÓN: Cada viñeta debe ser un párrafo rico y analítico de al menos 35 palabras.

ESTRUCTURA EXACTA REQUERIDA (4 VIÑETAS):
<div>• <strong>Momento y Tabla:</strong> [Analiza el contraste real de puntos, puestos y regularidad de ambos clubes en el torneo]</div>
<div style='margin-top:6px;'>• <strong>Dominio de Cancha:</strong> [Analiza el peligro proyectado en xG Opta, volumen de disparos y control territorial]</div>
<div style='margin-top:6px;'>• <strong>Historial y Bajas:</strong> [Explica la solidez de la plantilla y estabilidad del favorito para este duelo]</div>
<div style='margin-top:6px;'>• <strong>Estrategia y Protección Financiera:</strong> [Explica por qué {cod} es la jugada matemáticamente óptima, destacando la ventaja sobre el casino y el blindaje del capital]</div>

Devuelve ÚNICAMENTE el bloque HTML. Cero bloques de código markdown (```html).
"""

        payload = {
            "system_instruction": {"parts": [{"text": "Eres un generador de HTML en español sin preámbulos ni monólogos de razonamiento."}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 2000,
                "thinkingConfig": {"thinkingBudget": 0}
            }
        }

        t0 = time.perf_counter()
        intentos = len(self.keys)

        for _ in range(intentos):
            api_key = self._obtener_llave_activa()
            if not api_key:
                break

            st = self.key_states[api_key]
            url = f"{self.base_url}/{self.model_name}:generateContent?key={api_key}"
            _safe_print(f"🧠 [GEMINI ROTATOR LOG] Invocando llave '{st['alias']}' (Modelo: {self.model_name}) para {fav} vs {und}...")

            try:
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, json=payload)

                lat = (time.perf_counter() - t0) * 1000.0

                if resp.status_code == 200:
                    r_json = resp.json()
                    usage = r_json.get("usageMetadata", {})
                    p_tok = usage.get("promptTokenCount", 350)
                    c_tok = usage.get("candidatesTokenCount", 400)

                    texto = r_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    self._registrar_telemetria(st["alias"], "TESIS", p_tok, c_tok, lat, "SUCCESS")
                    _safe_print(f"✅ [GEMINI ROTATOR LOG] Tesis generada con éxito ({lat:.1f} ms) | Llave: {st['alias']} | Tokens: {p_tok} prompt, {c_tok} candidates")
                    return texto

                elif resp.status_code in (429, 503):
                    st["status"] = "COOLDOWN"
                    st["cooldown_until"] = time.time() + 60.0  # 60s cooldown
                    _safe_print(f"⚠️ [GEMINI ROTATOR LOG] Llave '{st['alias']}' en COOLDOWN 429 ({lat:.1f} ms). Rotando a siguiente llave en pool...")
                    logger.warning(f"⚠️ [GATEWAY 429] Llave {st['alias']} en pausa. Rotando...")
                    self._registrar_telemetria(st["alias"], "TESIS", 0, 0, lat, "COOLDOWN_429")
                    self.current_idx = (self.current_idx + 1) % len(self.keys)
                else:
                    _safe_print(f"⚠️ [GEMINI ROTATOR LOG] Llave '{st['alias']}' retornó HTTP {resp.status_code}. Rotando...")
                    logger.warning(f"⚠️ [GATEWAY HTTP {resp.status_code}] Llave {st['alias']}. Rotando...")
                    self.current_idx = (self.current_idx + 1) % len(self.keys)

            except Exception as ex:
                lat = (time.perf_counter() - t0) * 1000.0
                _safe_print(f"❌ [GEMINI ROTATOR LOG] Excepción con llave '{st['alias']}': {ex}. Rotando...")
                logger.warning(f"Error invocando Gemini con {st['alias']}: {ex}")
                self.current_idx = (self.current_idx + 1) % len(self.keys)

        # Fallback Seguro Mad-Libs si todas fallan
        logger.info("🛡️ [GATEWAY] Activando fallback determinista Mad-Libs.")
        from src.reporting.narrative import generar_tesis_madlibs_fallback
        return generar_tesis_madlibs_fallback(partido_data)
