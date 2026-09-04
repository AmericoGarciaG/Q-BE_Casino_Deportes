from src.ingestion.normalizer import canonicalize_team_name

def test_normalizer_canonical_aliases():
    """[LN-QBE-012] Normalización canónica de variantes ortográficas y aliases."""
    assert canonicalize_team_name("fe juarez") == "FC Juárez"
    assert canonicalize_team_name("tijuana xolos de caliente") == "Club Tijuana"
    assert canonicalize_team_name("club america") == "Club América"
    assert canonicalize_team_name("deportivo toluca") == "Deportivo Toluca"
    assert canonicalize_team_name("rayados") == "Rayados de Monterrey"
