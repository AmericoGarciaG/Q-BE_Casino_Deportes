from tests.shield.abstract_test_LN_QBE_040_poisson import AbstractTestPoisson
from src.core.poisson import PoissonBivariateEngine
from src.models.analytics import PoissonModulationResult

class TestLN_QBE_040_Concrete(AbstractTestPoisson):
    def run_poisson(self, h2h_res, metrics_res, **kwargs) -> PoissonModulationResult:
        return PoissonBivariateEngine.compute_modulations(h2h=h2h_res, metrics=metrics_res, **kwargs)
