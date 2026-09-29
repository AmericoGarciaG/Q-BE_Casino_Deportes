# -*- coding: utf-8 -*-
"""
🛡️ THE SHIELD — TWIN-TEST: ANATOMÍA ENRIQUECIDA DE BOLETOS SPLIT EN UI
[DES-QBE-060]
Régimen: [DIRGEN-STRICT]
Axioma: Erradicación de jerga críptica, presencia de 'Momio Casino' y 'Predicción Q-BE con P':'.
"""

import os
import pytest
from abc import ABC, abstractmethod


class AbstractTestEnhancedTicketDisplay(ABC):
    """Juez Abstracto que audita los rótulos y transparencia fiduciaria en app.js."""

    def test_etiquetas_fiduciarias_en_boletos_app_js(self):
        """Verifica que app.js contenga 'Momio Casino:' y 'Predicción Q-BE con P':'.'"""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        assert os.path.exists(js_path), "app.js no encontrado"

        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Debe contener las nuevas etiquetas exigidas por la Dirección
        assert "Momio Casino:" in js, "Violación DES-QBE-060: Falta etiqueta 'Momio Casino:' en app.js"
        assert "Predicción Q-BE con P':" in js or "Prediccion Q-BE con P':" in js, \
            "Violación DES-QBE-060: Falta etiqueta 'Predicción Q-BE con P':' en app.js"
        assert "Opción No Jugada:" in js or "Opcion No Jugada:" in js, \
            "Violación DES-QBE-060: Falta bloque de 'Opción No Jugada:' en app.js"

    def test_supresion_de_jerga_criptica(self):
        """Verifica que no se inyecten términos incomprensibles como Overround o θ* en los boletos."""
        js_path = os.path.join("src", "web", "static", "js", "app.js")
        with open(js_path, "r", encoding="utf-8") as f:
            js = f.read()

        # Prohibida la jerga confusa en el renderizado de tarjetas de órdenes
        assert "CIFRAS COMPLETAS DEL ENCUENTRO" not in js, \
            "Violación DES-QBE-060: Título ruidoso no debe aparecer en app.js"
        assert "Overround" not in js, \
            "Violación DES-QBE-060: Término 'Overround' no debe aparecer en el renderizado de boletos"


class TestEnhancedTicketDisplay(AbstractTestEnhancedTicketDisplay):
    """Implementación concreta en The Shield."""
    pass
