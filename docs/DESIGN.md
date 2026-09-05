# 🎨 DESIGN SYSTEM SPECIFICATION (DESIGN.md)
**DARK MODE FINTECH — `Q_BE_CD_WEB`**

## 1. Paleta de Colores Canónica
- **Background Principal:** `#0F172A` (Slate 900)
- **Superficie / Cards:** `#1E293B` (Slate 800)
- **Bordes & Divisores:** `#334155` (Slate 700)
- **Acento Primario (Gold/Amber):** `#F59E0B` (Amber 500)
- **Éxito / Valor Positivo:** `#10B981` (Emerald 500)
- **Peligro / Riesgo:** `#EF4444` (Red 500)
- **Texto Principal:** `#F8FAFC` (Slate 50)
- **Texto Secundario:** `#94A3B8` (Slate 400)

## 2. Tipografía
- **Fuente Principal:** Inter / Outfit / System Sans-Serif.
- **Fuente Monospaciada:** JetBrains Mono / Fira Code (para números, probabilidades y cuotas).

## 3. Estructura de Vistas SPA (4 Vistas)
1. **Live Board (Dashboard principal):** Selector de liga, cartelera activa, tabla de posiciones.
2. **Ingesta & Captura:** Carga de cuotas e inputs de mercado.
3. **Motor Cuantitativo & Cartera:** Matriz de valor, Kelly y sugerencias de Dutching.
4. **Reporte & Tesis:** Vista previa del reporte A4 y botón de exportación PDF.

---

### [DES-QBE-016] Split-View de Selección y Triaje (Vista 2) [UX-MANDATE]

* **Layout:** Distribución 50% / 50% (`.table-panel-left` y `.fixture-panel-right`).
* **Panel Izquierdo (Tabla Interactiva con 3 Pestañas):**
  - Barra de sub-navegación: `[📋 General]`, `[📈 Forma]`, `[🎯 xG Opta]`.
  - Conmutación en tiempo real de columnas:
    * **General:** `POS | EQUIPO | PTS | PJ | G | E | P | GF:GC | DIF`.
    * **Forma:** `POS | EQUIPO | PTS | FORMA (5 Círculos: 🟢 G, ⚪ E, 🔴 P) | PRÓX. RIVAL`.
    * **xG Opta:** `POS | EQUIPO | PTS | xG | xGA | xPTS | DIF xG`.
  - Invariablemente renderiza los 18 clubes de la competencia.
* **Panel Derecho (Cartelera Dinámica y Checkboxes):**
  - Renderiza tarjetas de partidos agrupadas por fecha con momios 1X2 reales y badge `🏷️ PA Activo`.
  - Checkboxes interactivos `[✓]` vinculados al contador en vivo: `"N partidos seleccionados"`.
  - Botón Maestro: `[ 🚀 Generar Portafolio Q-BE ]` (`#btn-dispatch-portfolio`), almacena los IDs de los partidos seleccionados para el cálculo cuantitativo.

