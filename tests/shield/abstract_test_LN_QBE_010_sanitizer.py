import abc
import pytest
from src.models.raw_input import RawMatchInput, MasterTableSnapshot

class AbstractTestSanitizer(abc.ABC):
    @abc.abstractmethod
    def run_sanitizer(self, match_input: RawMatchInput, master_table: MasterTableSnapshot) -> bool:
        pass

    def test_anchor_validation_success(self, sample_match_input, sample_master_table):
        """[SHIELD-INVARIANTE] Datos consistentes con la tabla maestra deben pasar."""
        assert self.run_sanitizer(sample_match_input, sample_master_table) is True

    def test_quarantine_rejection(self, sample_match_input, sample_master_table):
        """[SHIELD-SAD-PATH] Estado CUARENTENA debe ser rechazado inmediatamente."""
        sample_match_input.trazabilidad_consenso.estado_extraccion = "CUARENTENA"
        with pytest.raises(ValueError, match="CUARENTENA"):
            self.run_sanitizer(sample_match_input, sample_master_table)

    def test_h2h_duplicate_dates_rejection(self, sample_match_input, sample_master_table):
        """[GOVERNANCE-01 / INVARIANZA #8] Fechas H2H duplicadas/mockeadas deben ser vetadas."""
        for m in sample_match_input.h2h_matches:
            m.fecha = "01-01-2024"
        with pytest.raises(ValueError, match="Linaje H2H corrupto"):
            self.run_sanitizer(sample_match_input, sample_master_table)
