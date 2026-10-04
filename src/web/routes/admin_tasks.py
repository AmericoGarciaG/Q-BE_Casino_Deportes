# -*- coding: utf-8 -*-
"""
Kybern Industrial — [ARCH-1.4.12] Centro de Control: Despacho Gobernado de Tareas Administrativas
[ARCH-1.4.28] Adaptador de Despacho Web y Telemetría del Centro de Control.
Controlador REST del cockpit `POST /api/admin/tasks/run`.

[AISLAMIENTO DE PRODUCCIÓN]: ninguna tarea se compone con texto libre del cliente. El
identificador solicitado se resuelve contra `TAREAS_PERMITIDAS` (whitelist estricta) y el
comando resultante se materializa SIEMPRE con `sys.executable` + rutas internas del repositorio
(cero evaluación de shell, cero inyección de argumentos).

[ARCH-1.4.28] DOS MODOS DE DESPACHO sobre la MISMA whitelist:
  * `subprocess` (defecto histórico): secuencia de scripts canónicos del repositorio.
  * `integrado`: puente in-process hacia la Capa 5 (Data Nexus Bus) vía
    `IngestionCoordinator`, sin subprocesos externos frágiles. La evidencia fáctica entra por
    puerto (`concurso_num`) y su ausencia es FAIL-LOUD ([GOVERNANCE-01], `[LN-QBE-096]`):
    JAMÁS se fabrica un concurso, un emparejamiento ni una probabilidad.
"""

import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

# [ARCH-1.4.28] Capa 5 (Data Nexus Bus): el compositor orquestador es el ÚNICO motor de
# backend del modo integrado. `ESTADO_EXITOSO` se importa de su plano canónico: cero
# duplicación de constantes ([GOVERNANCE-01]).
from src.services.ingestion_coordinator import ESTADO_EXITOSO, IngestionCoordinator

router = APIRouter(prefix="/api/admin/tasks", tags=["Admin Control Center"])

# Raíz del proyecto: el despacho se materializa con paths internos absolutos.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

# [GOVERNANCE-01] Techo de reloj de la tarea despachada: la ingesta masiva (FotMob + casinos +
# Progol) es un lote batch. El límite evita hilos colgados y declarará la tarea como fallida
# sin fabricar salida alguna.
TIMEOUT_TAREA_SEGUNDOS = 900

# ── [ARCH-1.4.12] WHITELIST ESTRICTA DE SEGURIDAD ────────────────────────────
# Cada identificador certificado mapea a una secuencia de scripts canónicos del repositorio.
TAREAS_PERMITIDAS: Dict[str, Dict[str, Any]] = {
    "centinela_deportivo": {
        "descripcion": "Daemon de ingesta deportiva FotMob (J1-J17)",
        "comandos": [["scripts", "daemons", "centinela_deportivo.py"]],
    },
    "centinela_mercado": {
        "descripcion": "Daemon de cuotas Caliente + Betway (jornada activa dinámica [ARCH-1.6.15])",
        "comandos": [["scripts", "daemons", "centinela_mercado.py"]],
    },
    "centinela_progol": {
        "descripcion": "Daemon del concurso Progol #2352 (miloteria.mx)",
        "comandos": [["scripts", "daemons", "centinela_progol.py"]],
    },
    "sincronizar_activos": {
        "descripcion": "Sincronización de escudos y logos locales",
        "comandos": [["scripts", "utilidades", "sincronizar_boveda_activos.py"]],
    },
    "cadena_ingesta_total": {
        "descripcion": "Secuencia encadenada: Deportivo ➔ Mercado ➔ Progol",
        "comandos": [
            ["scripts", "daemons", "centinela_deportivo.py"],
            ["scripts", "daemons", "centinela_mercado.py"],
            ["scripts", "daemons", "centinela_progol.py"],
        ],
    },
    "auditar_pureza_vol1": {
        "descripcion": "Auditoría de pureza matemática del Tratado I (7/7 tests)",
        "comandos": [["scripts", "auditar_pureza_matematica_vol1.py"]],
    },
    "auditar_cartera_shield": {
        "descripcion": "Auditoría de las invarianzas de cartera sobre la bóveda SQLite",
        "comandos": [["scripts", "auditoria", "1_auditar_cartera_shield.py"]],
    },
    "consultar_uso_llm": {
        "descripcion": "Salud de llaves Gemini y consumo de tokens",
        "comandos": [["scripts", "utilidades", "consultar_uso_llm.py"]],
    },
    "purgar_base_datos": {
        "descripcion": "Reset selectivo de snapshots volátiles (preserva catálogo)",
        "comandos": [["scripts", "utilidades", "purgar_base_datos.py"]],
    },
}

# ── [ARCH-1.4.28] MODOS DE DESPACHO Y PUENTE INTEGRADO (CAPA 5) ───────────────
# La whitelist de [ARCH-1.4.12] permanece INTACTA (9 tareas). `TAREAS_PIPELINE_INTEGRADO`
# sólo certifica qué identificadores YA AUTORIZADOS publican además una ruta in-process
# hacia el Data Nexus Bus; cualquier otra combinación se rechaza de forma explícita.
MODO_DESPACHO_SUBPROCESS = "subprocess"
MODO_DESPACHO_INTEGRADO = "integrado"
MODOS_DESPACHO: tuple = (MODO_DESPACHO_SUBPROCESS, MODO_DESPACHO_INTEGRADO)

TAREAS_PIPELINE_INTEGRADO: Dict[str, str] = {
    "cadena_ingesta_total": "PROGOL_FULL",
}


class AdminTaskRequest(BaseModel):
    """[ARCH-1.4.12] [ARCH-1.4.28] Contrato de entrada del cockpit administrativo."""
    task_id: str = Field(..., description="Identificador certificado de la whitelist de tareas")
    modo: str = Field(
        MODO_DESPACHO_SUBPROCESS,
        description="Modo de despacho gobernado: 'subprocess' (scripts canónicos) o 'integrado' (Capa 5 in-process)",
    )
    concurso_num: Optional[int] = Field(
        None,
        description="Puerto de evidencia del modo integrado: número de concurso Progol a sincronizar",
    )


class AdminTaskResponse(BaseModel):
    """[ARCH-1.4.12] Contrato de salida: salida estándar íntegra + veredicto de proceso."""
    task_id: str
    exit_code: int
    output: str
    duration_s: float


def validar_tarea_solicitada(task_id: str) -> Dict[str, Any]:
    """
    [ARCH-1.4.12] Valida la tarea contra la whitelist estricta de seguridad.

    Retorna la especificación certificada (descripción + comandos canónicos) o levanta
    `ValueError` ante cualquier identificador arbitrario, inyectado o no autorizado.
    """
    identificador = str(task_id or "").strip()
    especificacion = TAREAS_PERMITIDAS.get(identificador)

    if especificacion is None:
        raise ValueError(
            f"Tarea '{identificador}' fuera de la whitelist certificada [ARCH-1.4.12]. "
            f"Identificadores autorizados: {', '.join(sorted(TAREAS_PERMITIDAS))}."
        )

    return especificacion


def _comando_absoluto(ruta_relativa: List[str]) -> List[str]:
    """[GOVERNANCE-01] Materializa el comando con rutas absolutas internas y el intérprete activo."""
    return [sys.executable] + [os.path.join(PROJECT_ROOT, *ruta_relativa)]


def ejecutar_tarea_autorizada(task_id: str) -> AdminTaskResponse:
    """
    [ARCH-1.4.12] Despacha la tarea certificada y devuelve su salida estándar sin fabricar datos.
    """
    especificacion = validar_tarea_solicitada(task_id)
    identificador = str(task_id).strip()
    total_comandos = len(especificacion["comandos"])

    bloques: List[str] = []
    exit_code_final = 0
    t0 = time.perf_counter()

    for indice, ruta_relativa in enumerate(especificacion["comandos"], 1):
        comando = _comando_absoluto(ruta_relativa)
        etiqueta = os.path.basename(ruta_relativa[-1])
        bloques.append(f"$ [{indice}/{total_comandos}] {etiqueta}")

        try:
            proceso = subprocess.run(
                comando,
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=TIMEOUT_TAREA_SEGUNDOS,
            )
            bloques.append(((proceso.stdout or "") + (proceso.stderr or "")).rstrip())
            exit_code_final = proceso.returncode
        except subprocess.TimeoutExpired:
            bloques.append(
                f"[TIMEOUT] La tarea excedió el techo de reloj de {TIMEOUT_TAREA_SEGUNDOS}s."
            )
            exit_code_final = 1
        except OSError as error:
            bloques.append(f"[ERROR] No fue posible materializar el comando: {error}")
            exit_code_final = 1

        bloques.append(f"── exit_code = {exit_code_final} ──")

        if exit_code_final != 0:
            break

    return AdminTaskResponse(
        task_id=identificador,
        exit_code=exit_code_final,
        output="\n".join(bloques),
        duration_s=round(time.perf_counter() - t0, 3),
    )


def ejecutar_tarea_integrada(
    task_id: str,
    concurso_num: Optional[int] = None,
) -> AdminTaskResponse:
    """
    [ARCH-1.4.28] [LN-QBE-097] Despacho in-process hacia la Capa 5 (Data Nexus Bus).

    Instancia `IngestionCoordinator` como motor de backend y delega la composición pura
    (Sensor ➔ Identity Brain ➔ Desambiguación JIT ➔ Motor Soberano ➔ Persistencia 3NF). El
    compositor JAMÁS calcula: su reporte se transcribe íntegro en `output` para el cockpit.
    Sin evidencia fáctica la Capa 5 responde FAIL-LOUD ([GOVERNANCE-01]): el despacho se
    reporta fallido (exit_code = 1) y no se fabrica dato alguno (`[LN-QBE-096]`).
    """
    identificador = str(task_id or "").strip()
    validar_tarea_solicitada(identificador)

    if identificador not in TAREAS_PIPELINE_INTEGRADO:
        raise ValueError(
            f"La tarea '{identificador}' no publica puente in-process hacia la Capa 5. "
            f"Tareas integradas certificadas: {', '.join(sorted(TAREAS_PIPELINE_INTEGRADO))}."
        )

    t0 = time.perf_counter()
    reporte = IngestionCoordinator().sincronizar_progol_pipeline_completo(
        concurso_num=concurso_num
    )
    exit_code_final = 0 if reporte.status == ESTADO_EXITOSO else 1
    bloques: List[str] = [
        f"$ [integrado 1/1] {TAREAS_PIPELINE_INTEGRADO[identificador]} → IngestionCoordinator (Capa 5)",
        reporte.model_dump_json(indent=2),
        f"── exit_code = {exit_code_final} ──",
    ]

    return AdminTaskResponse(
        task_id=identificador,
        exit_code=exit_code_final,
        output="\n".join(bloques),
        duration_s=round(time.perf_counter() - t0, 3),
    )


@router.post("/run", response_model=AdminTaskResponse)
def ejecutar_tarea_administrativa(req: AdminTaskRequest) -> AdminTaskResponse:
    """[ARCH-1.4.12] [ARCH-1.4.28] Despacho gobernado de tareas administrativas bajo whitelist estricta."""
    modo = str(req.modo or MODO_DESPACHO_SUBPROCESS).strip().lower()

    if modo not in MODOS_DESPACHO:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Modo de despacho '{req.modo}' fuera de la lista gobernada "
                f"{list(MODOS_DESPACHO)}."
            ),
        )

    try:
        if modo == MODO_DESPACHO_INTEGRADO:
            return ejecutar_tarea_integrada(req.task_id, concurso_num=req.concurso_num)
        return ejecutar_tarea_autorizada(req.task_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))
