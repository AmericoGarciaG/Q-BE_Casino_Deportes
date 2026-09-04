from tests.shield.abstract_test_LN_QBE_080_compiler import AbstractTestCompiler
from src.reporting.compiler import PDFCompilerEngine

class TestLN_QBE_080_Concrete(AbstractTestCompiler):
    def render_html(self, payload: dict) -> str:
        template = PDFCompilerEngine.get_template()
        return template.render(**payload)
