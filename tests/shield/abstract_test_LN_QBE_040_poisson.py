import abc
from src.models.analytics import PoissonModulationResult

class AbstractTestPoisson(abc.ABC):
    @abc.abstractmethod
    def run_poisson(self, h2h_res, metrics_res, **kwargs) -> PoissonModulationResult:
        pass

    def test_poisson_simplex_and_advanced_variables(self, sample_match_input):
        """[SHIELD-INVARIANTE #1] Suma de probabilidades híbridas == 1.0000 y variables avanzadas válidas."""
        from src.core.temporal import TemporalDecayEngine
        from src.core.metrics import SyntheticMetricsEngine

        h2h = TemporalDecayEngine.compute_decay(sample_match_input.h2h_matches, "FC Juárez", "Club Pachuca", "Club Pachuca")
        m = SyntheticMetricsEngine.compute_all(55.0, 5.0, 3.5, 1.6, 45.0, 3.5, 5.0, 1.0)
        
        res = self.run_poisson(
            h2h_res=h2h, metrics_res=m, gf_local_10p=1.6, gf_vis_10p=1.0,
            pts_pj_local=1.63, pts_pj_vis=0.50, jornada_tabla=7,
            q_mod_local=0.98, q_mod_vis=0.94, is_fav_local=True,
            odd_fav=1.99, odd_emp=3.50, odd_und=3.65, pago_anticipado_activo=True
        )
        assert abs((res.prob_hibrida_fav + res.prob_hibrida_empate + res.prob_hibrida_und) - 1.0) <= 0.001
        assert 0.0 <= res.phi_lead2 <= 1.0
        assert 0.0 <= res.psi_ruina <= 1.0
