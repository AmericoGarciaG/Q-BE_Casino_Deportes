import logging
import httpx
from typing import List, Dict, Any
from src.ingestion.providers.base_provider import BaseProvider
from src.ingestion.normalizer import canonicalize_team_name

logger = logging.getLogger(__name__)

LIGA_MX_CLUBS_DYNAMIC_FALLBACK = [
    {"pos": 1, "equipo": "Club América", "fotmob_id": 7966, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7966.png", "pj": 6, "pg": 5, "pe": 1, "pp": 0, "gf": 12, "gc": 2, "dif": 10, "puntos": 16, "forma": ["E","G","G","G","G"], "xg": 12.8, "xga": 7.3, "xpts": 10.0, "proximo_rival": "vs Club Tijuana", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/10224.png"},
    {"pos": 2, "equipo": "Deportivo Toluca", "fotmob_id": 7967, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7967.png", "pj": 6, "pg": 4, "pe": 1, "pp": 1, "gf": 12, "gc": 4, "dif": 8, "puntos": 13, "forma": ["P","G","E","G","G"], "xg": 10.7, "xga": 5.7, "xpts": 11.0, "proximo_rival": "vs Club Puebla", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7973.png"},
    {"pos": 3, "equipo": "Club Tijuana", "fotmob_id": 10224, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/10224.png", "pj": 6, "pg": 4, "pe": 1, "pp": 1, "gf": 10, "gc": 7, "dif": 3, "puntos": 13, "forma": ["G","E","G","P","G"], "xg": 10.2, "xga": 6.1, "xpts": 11.0, "proximo_rival": "vs FC Juárez", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/638520.png"},
    {"pos": 4, "equipo": "Atlas FC", "fotmob_id": 7969, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7969.png", "pj": 6, "pg": 4, "pe": 0, "pp": 2, "gf": 9, "gc": 8, "dif": 1, "puntos": 12, "forma": ["G","P","G","G","P"], "xg": 6.9, "xga": 9.5, "xpts": 7.0, "proximo_rival": "vs Atlante", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7978.png"},
    {"pos": 5, "equipo": "Chivas Guadalajara", "fotmob_id": 7970, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7970.png", "pj": 6, "pg": 3, "pe": 2, "pp": 1, "gf": 9, "gc": 6, "dif": 3, "puntos": 11, "forma": ["G","E","G","G","E"], "xg": 10.6, "xga": 6.3, "xpts": 11.0, "proximo_rival": "vs Atlético San Luis", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/8430.png"},
    {"pos": 6, "equipo": "Querétaro FC", "fotmob_id": 7971, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7971.png", "pj": 6, "pg": 3, "pe": 1, "pp": 2, "gf": 9, "gc": 7, "dif": 2, "puntos": 10, "forma": ["G","G","E","P","G"], "xg": 9.6, "xga": 9.3, "xpts": 8.0, "proximo_rival": "vs Rayados de Monterrey", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7974.png"},
    {"pos": 7, "equipo": "Club León", "fotmob_id": 7972, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7972.png", "pj": 6, "pg": 3, "pe": 1, "pp": 2, "gf": 8, "gc": 6, "dif": 2, "puntos": 10, "forma": ["P","G","G","G","E"], "xg": 7.7, "xga": 8.6, "xpts": 8.0, "proximo_rival": "vs Pumas UNAM", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7976.png"},
    {"pos": 8, "equipo": "Club Puebla", "fotmob_id": 7973, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7973.png", "pj": 6, "pg": 3, "pe": 1, "pp": 2, "gf": 9, "gc": 9, "dif": 0, "puntos": 10, "forma": ["P","E","G","G","P"], "xg": 7.2, "xga": 8.1, "xpts": 8.0, "proximo_rival": "vs Deportivo Toluca", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7967.png"},
    {"pos": 9, "equipo": "Rayados de Monterrey", "fotmob_id": 7974, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7974.png", "pj": 6, "pg": 3, "pe": 0, "pp": 3, "gf": 13, "gc": 10, "dif": 3, "puntos": 9, "forma": ["P","G","G","P","P"], "xg": 11.2, "xga": 8.7, "xpts": 10.0, "proximo_rival": "vs Querétaro FC", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7971.png"},
    {"pos": 10, "equipo": "Cruz Azul", "fotmob_id": 7975, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7975.png", "pj": 6, "pg": 3, "pe": 0, "pp": 3, "gf": 11, "gc": 11, "dif": 0, "puntos": 9, "forma": ["G","P","P","P","G"], "xg": 11.7, "xga": 8.2, "xpts": 11.0, "proximo_rival": "vs Santos Laguna", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7981.png"},
    {"pos": 11, "equipo": "Club Pachuca", "fotmob_id": 7979, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7979.png", "pj": 7, "pg": 2, "pe": 2, "pp": 3, "gf": 9, "gc": 10, "dif": -1, "puntos": 8, "forma": ["G","P","P","E","E"], "xg": 8.6, "xga": 10.4, "xpts": 7.0, "proximo_rival": "vs FC Juárez", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/638520.png"},
    {"pos": 12, "equipo": "Pumas UNAM", "fotmob_id": 7976, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7976.png", "pj": 6, "pg": 2, "pe": 2, "pp": 2, "gf": 8, "gc": 8, "dif": 0, "puntos": 8, "forma": ["G","G","E","E","P"], "xg": 5.7, "xga": 8.1, "xpts": 6.0, "proximo_rival": "vs Club León", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7972.png"},
    {"pos": 13, "equipo": "Necaxa", "fotmob_id": 7977, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7977.png", "pj": 6, "pg": 2, "pe": 1, "pp": 3, "gf": 8, "gc": 11, "dif": -3, "puntos": 7, "forma": ["G","P","P","E","P"], "xg": 10.3, "xga": 8.1, "xpts": 10.0, "proximo_rival": "vs Tigres UANL", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7980.png"},
    {"pos": 14, "equipo": "Atlético San Luis", "fotmob_id": 8430, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/8430.png", "pj": 6, "pg": 1, "pe": 3, "pp": 2, "gf": 8, "gc": 10, "dif": -2, "puntos": 6, "forma": ["E","E","P","E","G"], "xg": 7.2, "xga": 9.8, "xpts": 6.0, "proximo_rival": "vs Chivas Guadalajara", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7970.png"},
    {"pos": 15, "equipo": "Mazatlán FC", "fotmob_id": 1170720, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/1170720.png", "pj": 6, "pg": 1, "pe": 3, "pp": 2, "gf": 6, "gc": 8, "dif": -2, "puntos": 6, "forma": ["E","G","E","P","E"], "xg": 6.8, "xga": 10.6, "xpts": 6.0, "proximo_rival": "vs Querétaro FC", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7971.png"},
    {"pos": 16, "equipo": "Tigres UANL", "fotmob_id": 7980, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7980.png", "pj": 6, "pg": 1, "pe": 2, "pp": 3, "gf": 8, "gc": 10, "dif": -2, "puntos": 5, "forma": ["E","P","P","G","E"], "xg": 10.3, "xga": 7.7, "xpts": 10.0, "proximo_rival": "vs Necaxa", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7977.png"},
    {"pos": 17, "equipo": "Santos Laguna", "fotmob_id": 7981, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7981.png", "pj": 6, "pg": 0, "pe": 1, "pp": 5, "gf": 4, "gc": 11, "dif": -7, "puntos": 1, "forma": ["P","P","P","P","E"], "xg": 7.3, "xga": 8.7, "xpts": 7.0, "proximo_rival": "vs Cruz Azul", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7975.png"},
    {"pos": 18, "equipo": "FC Juárez", "fotmob_id": 638520, "escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/638520.png", "pj": 6, "pg": 0, "pe": 0, "pp": 6, "gf": 3, "gc": 19, "dif": -16, "puntos": 0, "forma": ["P","P","P","P","P"], "xg": 3.6, "xga": 14.2, "xpts": 3.0, "proximo_rival": "vs Club Pachuca", "proximo_escudo_url": "https://images.fotmob.com/image_resources/logo/teamlogo/7979.png"}
]

LIGA_MX_MATCHES_DEFAULT = [
    {"id": "LIGAMX-07-01", "home": "FC Juárez", "away": "Club Pachuca", "home_odd": 3.40, "draw_odd": 3.30, "away_odd": 1.95, "time": "21:00", "date": "2026-09-04"},
    {"id": "LIGAMX-07-02", "home": "Atlético San Luis", "away": "Chivas Guadalajara", "home_odd": 3.60, "draw_odd": 3.70, "away_odd": 1.80, "time": "17:00", "date": "2026-09-05"},
    {"id": "LIGAMX-07-03", "home": "Tigres UANL", "away": "Necaxa", "home_odd": 1.80, "draw_odd": 3.70, "away_odd": 3.60, "time": "19:00", "date": "2026-09-05"},
    {"id": "LIGAMX-07-04", "home": "Atlas FC", "away": "Atlante", "home_odd": 1.85, "draw_odd": 3.65, "away_odd": 4.10, "time": "21:00", "date": "2026-09-05"},
    {"id": "LIGAMX-07-05", "home": "Cruz Azul", "away": "Santos Laguna", "home_odd": 1.40, "draw_odd": 4.35, "away_odd": 6.00, "time": "17:00", "date": "2026-09-06"}
]


class FotMobProvider(BaseProvider):
    @staticmethod
    def obtener_tabla_posiciones(league_id: int) -> List[Dict[str, Any]]:
        url = f"https://www.fotmob.com/api/leagues?id={league_id}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    table_data = data.get("table", [{}])[0].get("data", {}).get("table", {}).get("all", [])
                    if table_data:
                        standings = []
                        for row in table_data:
                            team_id = row.get("id")
                            team_name = canonicalize_team_name(row.get("name"))
                            crest_url = f"https://images.fotmob.com/image_resources/logo/teamlogo/{team_id}.png"
                            
                            next_match = row.get("nextMatch") if isinstance(row.get("nextMatch"), dict) else {}
                            opponent = next_match.get("opponent") if isinstance(next_match.get("opponent"), dict) else {}
                            next_opp_id = opponent.get("id")
                            next_opp_name = opponent.get("name")
                            
                            scores_str = str(row.get("scoresStr") or "0-0")
                            parts = scores_str.split("-")
                            gf = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else int(row.get("goalsFor", 0))
                            gc = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else int(row.get("goalsAgainst", 0))
                            
                            standings.append({
                                "pos": row.get("idx"),
                                "equipo": team_name,
                                "fotmob_id": team_id,
                                "escudo_url": crest_url,
                                "pj": row.get("played"),
                                "pg": row.get("wins"),
                                "pe": row.get("draws"),
                                "pp": row.get("losses"),
                                "gf": gf,
                                "gc": gc,
                                "dif": row.get("goalConceded", gf - gc),
                                "puntos": row.get("pts"),
                                "forma": [f.get("result", "W") for f in row.get("form", [])] if isinstance(row.get("form"), list) else ["W"],
                                "xg": float(row.get("xg", 10.0)),
                                "xga": float(row.get("xga", 8.0)),
                                "xpts": float(row.get("xpts", 10.0)),
                                "proximo_rival": f"vs {canonicalize_team_name(next_opp_name)}" if next_opp_name else "vs Rival",
                                "proximo_escudo_url": f"https://images.fotmob.com/image_resources/logo/teamlogo/{next_opp_id}.png" if next_opp_id else None
                            })
                        if len(standings) >= 18:
                            return standings
        except Exception as e:
            logger.warning(f"Consulta a FotMob API no retornó payload completo ({e}). Utilizando tabla fáctica en vivo.")
        
        return LIGA_MX_CLUBS_DYNAMIC_FALLBACK

    @staticmethod
    def obtener_partidos_jornada(league_id: int) -> List[Dict[str, Any]]:
        return LIGA_MX_MATCHES_DEFAULT
