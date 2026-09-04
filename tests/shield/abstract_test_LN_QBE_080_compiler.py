import abc
from bs4 import BeautifulSoup

class AbstractTestCompiler(abc.ABC):
    @abc.abstractmethod
    def render_html(self, payload: dict) -> str:
        pass

    def test_dom_table_11_columns_geometry(self):
        """[SHIELD-INVARIANTE #8 / DES-QBE-035] La tabla 10P debe tener 11 columnas perfectamente alineadas."""
        payload = {
            "metadata": {"torneo": "Liga MX", "jornada": "Jornada 7", "fechas": "05-Sep-2026"},
            "control": {
                "partidos_core": "1 / 1",
                "total_posiciones_core_label": "1 Posición Core",
                "capital_total_core_mxn": 100.0,
                "desglose_bankroll": {"bankroll_total": 200.0, "porcentaje_total_arriesgado": 50.0},
                "blindaje_global_preservacion_porcentaje": 100.0,
                "probabilidad_ruina_total_porcentaje": 0.0
            },
            "balance": {"ganancia_neta_esperada_jornada_mxn": 10.0, "roi_global_esperado_porcentaje": 10.0},
            "ordenes": [],
            "satelite": {"autorizado": False},
            "partidos_analisis": [
                {
                    "id_partido": "OCR-01",
                    "partido": "A vs B",
                    "estrategia_codigo": "QBE-D1",
                    "estrategia_nombre": "Directo",
                    "probabilidades_3vias": [],
                    "tabla_10p": [
                        {"equipo": "A", "puesto": 1, "pts": 10, "gf_gc": "10/5", "pts_pj": 2.0, "goles_pro": "2/1", "sot": 5.0, "sota": 3.0, "posesion": 55.0, "bajas": "Ninguna", "qmod": 1.0}
                    ],
                    "h2h_filas": [],
                    "theta_fav": 0.40
                }
            ],
            "descartes": []
        }
        html = self.render_html(payload)
        soup = BeautifulSoup(html, "html.parser")
        
        tablas_10p = [t for t in soup.find_all("table") if "POSESIÓN" in t.text or "SOT" in t.text]
        assert len(tablas_10p) > 0
        for t in tablas_10p:
            ths = t.find("thead").find_all("th")
            assert len(ths) == 11
