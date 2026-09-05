# 🎨 DESIGN SYSTEM SPECIFICATION (DESIGN.md)
**DARK MODE FINTECH — `Q_BE_CD_WEB`**

## 1. Paleta de Colores Canónica
- **Background Principal:** `#0F172A` (Slate 900)
- **Superficie / Cards:** `#1E293B` (Slate 800)
- **Bordes & Divisores:** `#334155` (Slate 700)
- **Acento Primario (Gold/Amber):** ~~`#F59E0B` (Amber 500)~~ **[DEROGADO por DES-QBE-005]** → Ver Acento Primario canónico: Azul Cian `#38BDF8` / `#0284C7`
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

### [DES-QBE-015] Hub de Ligas (Vista 1) — Voz Institucional [UX-MANDATE]
* **Título de Sección:** `🏆 Ligas y Torneos de Alta Liquidez`.
* **Badge de Estado:** `⚡ Datos Oficiales en Vivo (Opta Engine)`.
* **Etiqueta en Tarjeta:** `• 18 Clubes • Tabla y Métricas al Día`.
* **Pestaña de Navegación:** `🌐 Hub de Ligas`.

### [DES-QBE-016] Jornada y Tabla de Posiciones (Vista 2) [UX-MANDATE]
* **Pestaña de Navegación:** `📊 Jornada y Tabla de Posiciones`.
* **Encabezado de Tabla:** Nombre de la competencia activa (ej. `Liga MX`).
* **Encabezado de Cartelera:** Jornada en disputa activa (ej. `Jornada 7`).
* **Columna Próximo Rival (Pestaña Forma):** Debe renderizar el escudo miniatura del rival (`14x14px`) y su nombre canónico (ej. `vs Cruz Azul`). Prohibido el texto estático `vs Rival`.

### [DES-QBE-036] Inviolabilidad Geométrica de la Columna Forma [UX-MANDATE] [ARCH-PILLAR]
* **Regla Anti-Descuadre:** La celda `td.col-forma` debe forzar `white-space: nowrap !important;`.
* **Contenedor de Círculos:** Los 5 círculos de forma deben montarse en un contenedor con `display: inline-flex; align-items: center; gap: 3px; flex-wrap: nowrap;`, garantizando una sola línea horizontal perfecta y prohibiendo estrictamente que el 5º círculo se apile verticalmente formando una figura en "T".

---

### [DES-QBE-005] Paleta Cromática Disciplinada (Erradicación de Amarillo Saturado) [UX-MANDATE]

* **Axioma:** Queda estrictamente prohibido utilizar colores amarillos, anaranjados o dorados chillones en títulos de marca, cabeceras de sección, botones principales o pestañas de navegación activas.
* **Paleta Canónica de Interfaz:**
  - **Títulos y Textos Principales:** Blanco puro (`#FFFFFF`).
  - **Acento Primario e Interacción (Foco / Pestaña Activa):** Azul Cian (`#38BDF8` / `#0284C7`).
  - **Acento Positivo (+EV / Éxito):** Verde Esmeralda sutil (`#00E676` / `#16A34A`), reservado exclusivamente para métricas de ganancia confirmada y saldo a favor.
  - **Fondos y Elevaciones:** Slate 900 (`#0B132B`), Slate 800 (`#1C2541`) y Slate 700 (`#334155`).
* **Tokens prohibidos en marca/botones primarios:** `#ff9800`, `#f59e0b`, `#fbbf24`, `color: orange`, `color: yellow`, `color: gold`.
* **[Binding Rationale]:** Paleta disciplinada Fintech-grade. El amarillo/ámbar saturado reduce la percepción de seriedad institucional y genera ruido visual en contextos de análisis cuantitativo.

---

### [DES-QBE-010] Barra Superior de Identidad Discreta (Silent Branding) [UX-MANDATE]

* **Filosofía:** La identidad del software (`Q-BE Casino Deportes`) debe ser una firma sutil y no invasiva. El valor central es la funcionalidad del usuario, no el logotipo del software.
* **Estilo:**
  - Nombre de marca en tipografía neutra y sobria: color Gris Pizarra (`#94A3B8` o `#CBD5E1`), tamaño `8.5pt` a `9pt`, peso 600.
  - El botón `SYSTEM ONLINE` se mantiene discreto con borde cian tenue (`#38BDF8` a 40% opacidad).
  - Prohibido aplicar `color: #f59e0b`, `color: #fbbf24` o cualquier variante ámbar al nombre de la marca.
* **[Binding Rationale]:** La identidad invasiva compite cognitivamente con los datos de análisis. Un branding discreto refuerza la autoridad profesional de la plataforma.

---

### [DES-QBE-016] Cartelera Activa — Selector Único y Limpio [UX-MANDATE] *(Enmienda v2.0)*

* **Inviolabilidad de Controles:** Cada tarjeta de partido (`.fixture-card`) debe contener **exactamente un solo control de selección** (un checkbox nativo estilizado en cian `#38BDF8`).
* **Prohibición de Redundancias:** Queda estrictamente prohibido colocar emojis de verificación (`✅`) o textos estáticos como `"Seleccionado"` junto al checkbox. La indicación de selección se refleja limpiamente por el estado del propio checkbox y el borde sutil de la tarjeta.
* **Indicador de selección:** El estado activo se comunica únicamente mediante `border: 1px solid #38BDF8` en la `.fixture-card` y el atributo `checked` del `<input type="checkbox">`.
* **[Binding Rationale]:** La duplicidad de controles de selección genera confusión UX y viola el principio de selector único enunciado en DES-QBE-016 v1.0.
