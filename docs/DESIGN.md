# 🎨 DESIGN SYSTEM SPECIFICATION (DESIGN.md)
**Versión:** 10.0 (Fintech Micro-Grid, Focus Mode & Viewport Containment Edition)  
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

## 3. Estructura de Vistas SPA (3 Vistas Canónicas)
1. **Hub de Ligas (`view-leagues-hub`):** Selector de competencia con tarjetas interactivas y emblemas oficiales de torneos (Liga MX).
2. **Jornada y Tabla de Posiciones (`view-matchday-selection`):** Split-View con la tabla general de 18 clubes (pestañas General, Forma y xG Opta con refresco aislado) y Cartelera en 4 Niveles con selección de apuestas.
3. **Cartera Cuantitativa (`tab-portfolio`):** Dashboard Ejecutivo unificado con Macro KPIs duales, Cascada de Resiliencia a Reveses, Tabla Resumen de Asignación, Boletos Split en Detalle con metas de CashOut, Botón de Exportación PDF A4 integrado y Radar de Descartes (`QBE-00`).

---

### [DES-QBE-030] Barra de Navegación Cockpit y Dual-Core Layout [UX-MANDATE]

* **Barra Superior Global (`#main-navbar`):**
  - Fondo: Slate 950 (`#0B132B`), borde inferior `1px solid #1C2541`, padding `10px 24px`.
  - Elementos de navegación:
    - `[ 🏛️ Q-BE QUANT ]` (Branding Institucional).
    - `[ ⚽ CENTRO SOBERANO ]` (Pantalla Core 1 — Consulta Deportiva Pura).
    - `[ 💼 ESTACIÓN DE MERCADOS ]` (Pantalla Core 2 — Asignación y Monetización).
    - `[ ⚙️ BÓVEDA & TELEMETRÍA ]` (Admin / Estado de Daemons / Ledger LLM).

### [DES-QBE-031] Pantalla Core 1: El Centro Soberano de Inteligencia Deportiva
* **Propósito:** Inspección científica de la verdad fáctica antes de cualquier consideración de precios.
* **Componentes:**
  1. **Selector de Ligas (`#sovereign-league-selector`):** Píldoras deslizantes con bandera (`🇲🇽 Liga MX`, `🏴 Premier League`, `🇪🇸 LaLiga`).
  2. **Split-View Coordinado:**
     - *Panel Izquierdo:* Clasificación general de 18 clubes con pestañas General, Forma 5P y Métricas Opta (xG/xGA).
     - *Panel Derecho:* Carrusel cronológico de encuentros agrupados por fecha (partidos de hoy/próximos en foco; conmutador de fechas pasadas concluidas y futuras).
  3. **Franja de Distribución Soberana (Tri-Color Probabilistic Strip):**  
     Cada tarjeta de partido despliega una barra horizontal de 6px de alto dividida proporcionalmente:
     - Cian / Verde Neón (`#00E676` / `#38BDF8`): Probabilidad Victoria Local ($p_1$).
     - Gris Pizarra (`#64748B`): Probabilidad Empate ($p_X$).
     - Rojo Coral (`#EF4444`): Probabilidad Victoria Visitante ($p_2$).
     - Debajo de la barra: `λ_Local vs μ_Visita` y la probabilidad de ventaja `Φ_Lead2`.
  4. **RESTRICCIÓN ABSOLUTA:** Cero cuotas de casino, cero momios decimales, cero casillas de selección para apostar. Botón único: `[ 🔬 Inspeccionar Radiografía Estocástica ]` (abre modal con matriz 6x6 de Poisson limpia).

### [DES-QBE-032] Pantalla Core 2: Estación de Mercados Financieros y Asignación
* **Selector de Vehículo de Inversión (`#market-vehicle-tabs`):**
  - `[ 🏦 1. CASINO DEPORTES 1X2 (Caliente.mx) ]`
  - `[ 📋 2. PRONÓSTICOS DEPORTIVOS (Progol) ]`
  - `[ ⚡ 3. ARBITRAJE INTER-CASAS ]` (En radar)
* **Sub-Vista Casino Deportes 1X2:**
  - Despliega únicamente los partidos que el operador tiene abiertos con cuotas en ventanilla.
  - Cada tarjeta contrasta: Probabilidad Soberana vs. Momio Casino $\rightarrow$ **Cálculo de GAP (+EV)** destacado en verde esmeralda si hay valor o gris si es candidato a Veto (`QBE-00`).
  - Checkboxes de selección de partidos activos para el portafolio.
  - Panel inferior: Input de Bankroll, Slider de Certeza ($75\% \leftrightarrow 85\%$) y botón `[ 🚀 Generar Cartera Cuantitativa ]`.
  - Despliegue de boletos split con piso de $\$2.00\text{ MXN}$ y las Tres Píldoras de Certeza ($3^K$).
* **Sub-Vista Pronósticos Deportivos (Progol):**
  - Selector de Concurso activo (ej. `Progol 2245`).
  - Despliega los 14 partidos del boleto (admitiendo cruces multitorneo).
  - Contrasta la Venta Pública Nacional (%) vs. Probabilidad Real Q-BE (%) alertando sesgos populares.
  - Optimizador de dobles y triples maximizando el valor esperado de la bolsa acumulada.

### [DES-QBE-033] Geometría DOM Obligatoria para la Interfaz Dual-Core [UX-MANDATE]

1. **Navegación Superior Cockpit (`#main-navbar`):**
   - Botón Pantalla 1: `#nav-btn-sovereign` (Texto: "⚽ Centro Soberano")
   - Botón Pantalla 2: `#nav-btn-markets` (Texto: "💼 Estación de Mercados")
   - Botón Admin/Bóveda: `#nav-btn-admin` (Texto: "⚙️ Bóveda & Telemetría")

2. **Contenedor Pantalla Core 1 (`#view-sovereign-hub`):**
   - Selector de Ligas: `#sovereign-league-selector`
   - Tabla General: `#sovereign-standings-container`
   - Carrusel Cronológico de Encuentros: `#sovereign-matches-carousel`
   - Franja Tricolor de Probabilidad: `.prob-strip` con subelementos `.prob-strip-local`, `.prob-strip-draw`, `.prob-strip-away`.
   - RESTRICCIÓN: Cero inputs `<input type="checkbox">` para apuestas en esta vista.

3. **Contenedor Pantalla Core 2 (`#view-markets-hub`):**
   - Pestañas de Vehículo: `#market-vehicle-tabs` con botones `#tab-btn-casino` y `#tab-btn-progol`.
   - Sub-Vista Casino: `#market-view-casino` (con `#casino-matches-list`, checkboxes `.casino-match-checkbox`, `#input-bankroll`, `#slider-risk-certainty`, `#btn-generate-portfolio`).
   - Sub-Vista Progol: `#market-view-progol` (con `#progol-slate-container`, badges `.badge-bias-alert`, tabla de 14 partidos).

---


### [DES-QBE-015] Hub de Ligas (Vista 1) — Voz Institucional [UX-MANDATE]
* **Título de Sección:** `🏆 Ligas y Torneos de Alta Liquidez`.
* **Badge de Estado:** `⚡ Datos Oficiales en Vivo (Opta Engine)`.
* **Etiqueta en Tarjeta:** `• 18 Clubes`.
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

### [DES-QBE-012] Isotipo Institucional y Favicon Dark Fintech [UX-MANDATE]

* **Identidad Vectorial:** El favicon institucional se sirve como SVG vectorial puro en `/static/img/favicon.svg` (Fondo Slate 900 `#0B132B`, anillo exterior Cian `#38BDF8` y monograma `Q` geométrico en blanco puro).
* **Política de Cache-Buster:** En el HTML, el tag `<link rel="icon">` debe invocar obligatoriamente el parámetro de versión `?v=2026QBE` para forzar a Chromium a invalidar cachés residuales y garantizar que ningún escudo de club aparezca en la pestaña del navegador.

---

### [DES-QBE-016] Cartelera Activa — Selector Único y Limpio [UX-MANDATE] *(Enmienda v2.0)*

* **Inviolabilidad de Controles:** Cada tarjeta de partido (`.fixture-card`) debe contener **exactamente un solo control de selección** (un checkbox nativo estilizado en cian `#38BDF8`).
* **Prohibición de Redundancias:** Queda estrictamente prohibido colocar emojis de verificación (`✅`) o textos estáticos como `"Seleccionado"` junto al checkbox. La indicación de selección se refleja limpiamente por el estado del propio checkbox y el borde sutil de la tarjeta.
* **Indicador de selección:** El estado activo se comunica únicamente mediante `border: 1px solid #38BDF8` en la `.fixture-card` y el atributo `checked` del `<input type="checkbox">`.
* **[Binding Rationale]:** La duplicidad de controles de selección genera confusión UX y viola el principio de selector único enunciado en DES-QBE-016 v1.0.

### [DES-QBE-016-B] Geometría y Renderizado de Próximo Rival [UX-MANDATE]

* **Estructura DOM:** La celda `td.col-rival` debe contener:
  ```html
  <div style="display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;">
    <img src="/static/img/crests/{slug}.png" width="14" height="14" style="object-fit: contain;" alt="{Rival}">
    <span>vs {Nombre Canónico}</span>
  </div>
  ```
* **Inviolabilidad Geométrica:** Prohibido el salto de línea entre la miniatura y el texto.

---

### [DES-QBE-016-C] Jerarquía de Cartelera en 4 Niveles y Clicabilidad Total de Tarjeta [UX-MANDATE]

* **Topología de 4 Niveles Visuales:**
  1. **Nivel 1 (🔴 En Juego):** Tarjetas con borde sutil rojo (`#EF4444` al 40%), badge pulsante `🔴 EN CURSO (Minuto)` y marcador en tiempo real destacado en tipografía monospaciada (`14pt`, peso 700).
  2. **Nivel 2 (📅 Ventana Activa):** Tarjetas operables agrupadas cronológicamente. Solo llevan el prefijo `"HOY — "` si `es_hoy == True`.
  3. **Nivel 3 (⏳ Reprogramados / Fecha Lejana):** Agrupados bajo encabezado atenuado, checkboxes deshabilitados y badge `⏳ Fecha Lejana`.
  4. **Nivel 4 (🏁 Finalizados al Fondo):** Ubicados obligatoriamente al final de la vista de cartelera. Opacidad general al 65%, badge neutro `FINALIZADO`, marcador definitivo en color Gris Pizarra (`#94A3B8`) y controles deshabilitados.
* **Inviolabilidad de Interacción (Card-Level Clickability):**
  - Todo el contenedor rectangular `.fixture-card` debe poseer `cursor: pointer;` (cuando no esté deshabilitado).
  - Un clic en cualquier punto del rectángulo de la tarjeta debe alternar el estado del checkbox nativo (`checked = !checked`) y disparar el recálculo reactivo de partidos seleccionados.
  - Las tarjetas en estado `FINALIZADO` o `REPROGRAMADO` deben poseer `cursor: not-allowed;` y bloquear cualquier intento de selección.

---

### [DES-QBE-016-D] Erradicación de Prefijos Redundantes en Columna Próximo Rival [UX-MANDATE]

* **Axioma de Pulcritud Visual:** Queda terminantemente prohibido anteponer el prefijo `"vs "` o `"contra "` al nombre del club rival en la tabla de posiciones.
* **Composición Geométrica:** La celda `td.col-rival` se estructura exclusivamente como:
  `[Escudo miniatura 14x14px] [Nombre Canónico del Club]`
  *(Ejemplo: `<img src="/static/img/crests/cruz-azul.png" width="14" height="14"> Cruz Azul`)*.
* **Binding Rationale:** Al existir la identidad gráfica del escudo y el encabezado explícito **PRÓX. RIVAL**, la palabra *"vs"* constituía ruido semántico redundante que sobrecargaba la línea visual.

---

### [DES-QBE-018] Panel Administrativo de Curación HITL (Catálogos y Bóveda) [UX-MANDATE]

* **Propósito:** Interfaz de control y auditoría donde el Director visualiza la prospección de clubes antes de incorporarlos a la base de datos definitiva.
* **Componentes de Interfaz:**
  1. **Barra Superior de Control:** Selector de Liga, Botón `[ 🔍 Prospección Agéntica con Gemini ]` y Botón Maestro `[ 🔒 Sellar Catálogo en Base de Datos ]`.
  2. **Cuadrícula de Tarjetas de Club (Grid de 18 tarjetas):**
     - Pre-visualización del Escudo oficial (`48x48px`).
     - Nombre Oficial y Nombre Corto.
     - Píldoras de Aliases reconocidos (`"Águilas"`, `"América"`, etc.).
     - Estadio y Sede.
     - Botón de Estado Dual: `[ ✅ Aprobado ]` (verde) / `[ 🔄 Cambiar Fuente ]` (azul).

### [DES-QBE-019] Vista 5: Radiografía Forense Interactiva en UI (Backlog / PM-FACE) [UX-MANDATE]

* **Propósito:** Vista modal interactiva orientada a la auditoría estocástica profunda.
* **Componentes Previstos:**
  1. Mapa de calor interactivo de la matriz Poisson 6x6.
  2. Gráfico de dispersión: Momios Implícitos del Casino vs. Momio Justo Q-BE (Edge Visual).
  3. Desglose analítico de los 4 umbrales de Breakeven ($\theta^*$).
  4. Curva de liquidación en vivo y disparadores de CashOut al minuto 85'.

### [DES-QBE-028] Badge de Inconsistencia Auditada en Tesis [UX-MANDATE]
* **Supervisión Activa con IA:** Si el LLM detecta una contradicción fáctica entre los datos y la estrategia, antepondrá un recuadro de advertencia en color ámbar/rojo tenue:
  `<div class="alerta-inconsistencia" style="background: rgba(239,68,68,0.15); border-left: 3px solid #EF4444; padding: 8px 12px; margin-bottom: 8px; color: #F8FAFC; font-size: 8pt;">⚠️ <strong>Alerta de Inconsistencia Auditada:</strong> [Explicación]</div>`

### [DES-QBE-020] Dashboard Ejecutivo de Cartera y Métricas Duales [UX-MANDATE]

* **Macro KPIs con Distinción Financiera Estricta:**
  1. *Capital en Juego:* Total comprometido en pesos ($) y porcentaje del bankroll base (`font-size: 1.15rem`, blanco puro).
  2. *Ganancia Neta Potencial:* Premio neto máximo sumado bajo el escenario de pleno acierto en ventanilla (`+$XX.XX MXN`, verde esmeralda `#00E676`), con subtexto `Techo Máximo Pleno`.
  3. *Ganancia Neta Esperada:* La Esperanza Matemática estadística ponderada ($+EV$) derivada de las probabilidades Poisson y ruina (`+$XX.XX MXN`, cian `#38BDF8`), con subtexto `Esperanza Matemática (+EV)`.
  4. *Blindaje de Capital:* Porcentaje de preservación global (`99.9%`, cian `#38BDF8`) y probabilidad de ruina conjunta en decimales pequeños.
  5. *Posiciones Core:* Ratio de activos operables aprobados sobre total evaluado.
* **Tabla Resumen de Asignación (`#tabla-resumen-asignacion`):**
  - Columna 4: Encabezado rotulado obligatoriamente como **`GANANCIA NETA`** (cifras netas reales, prohibidas cifras brutas).
  - Renglón TOTAL CARTERA: Muestra la suma del capital invertido, la Ganancia Neta Potencial acumulada, y la **celda de Escenario Cobertura permanece strictly en blanco / vacía** para evitar redundancias.

---

### [DES-QBE-027] Banner de Resiliencia Tripartito (Las Tres Píldoras de Certeza) [UX-MANDATE]

* **Geometría y Estilo:** Contenedor `#pildoras-cascada` con `display: flex; gap: 10px; align-items: center; flex-wrap: wrap;`.
* **Estructura de las Tres Píldoras:**
  1. **Píldora 1 (Pleno Éxito):** Borde y texto Verde Esmeralda (`#00E676`), fondo `rgba(0, 230, 118, 0.15)`. Formato: `🎯 Pleno Éxito: +$XX.XX MXN (XX.X%)`.
  2. **Píldora 2 (Tablas o Ganancia — Destacada):** Borde y texto Azul Cian (`#38BDF8`), fondo `rgba(56, 189, 248, 0.20)`, sombra suave `box-shadow: 0 0 10px rgba(56, 189, 248, 0.3)`. Formato: `🛡️ Tablas o Ganancia: ≥ $0.00 MXN (XX.X%) ⭐`.
  3. **Píldora 3 (Ruina Total):** Borde y texto Rojo Muted (`#EF4444`), fondo `rgba(239, 68, 68, 0.12)`. Formato: `💀 Ruina Total: -$XX.XX MXN (0.002%)`.

---

### [DES-QBE-017-B] Jerarquía de Resolución de Emblemas por Variantes de Disco y SVG Fallback [UX-MANDATE]

* **Búsqueda Proactiva de Variantes:** Si el archivo primario `{slug}.png` no existe o pesa $\le 3,000$ bytes, el resolutor inspecciona en disco variantes físicas reconocidas (`club-{slug}.png`, `{slug}-fc.png`, `deportivo-{slug}.png`) antes de invocar la red.
* **Componente SVG Fallback Autocontenido:** Ante ausencia total de activo físico, se genera un Data URI SVG determinista (`data:image/svg+xml;utf8,...`) con gradiente Dark Fintech (`#1C2541` a `#0B132B`), anillo Cian `#38BDF8` y monograma de 2 a 3 iniciales, garantizando renderizado perfecto sin peticiones de red.

---

### [DES-QBE-021] Bloqueo Semántico en DOM y Cronometría Dinámica [UX-MANDATE]

* **Inviolabilidad de Selección en DOM:** Los controladores de eventos en `app.js` bloquean cualquier interacción de selección si la tarjeta porta `dataset.estado === 'FINALIZADO'`, `dataset.estado === 'REPROGRAMADO'` o la clase CSS `.fixture-disabled`.
* **Función `_esHoyDinamico()`:** Compara de forma estricta año, mes y día de la cadena ISO 8601 contra `new Date()` del sistema cliente para gobernar el prefijo `"HOY — "`, prohibiendo agrupamientos erróneos.

---

### [UX-CFG-01] Orden Configurable de Boletos en Tarjeta [UX-MANDATE] [BACKLOG]

* **Criterio Vigente por Defecto (Prioridad Financiera):** Boleto 1 de Ganancia (Ataque) a la izquierda en verde, Boleto 2 de Seguro (Recuperación) a la derecha en azul.
* **Criterio Opcional Futuro (Posición Canónica):** Vista conmutables por el usuario para alinear boletos por posición Local a la izquierda y Visitante a la derecha para facilitar la carga en interfaces de casas de apuestas que no admitan ordenamiento libre.

---

### [DES-QBE-023] Modal HUD de Procesamiento Cuantitativo en Vivo [UX-MANDATE] (H7)

* **Geometría y Estilo:** Ventana modal emergente Dark Fintech (`background: #1C2541`, borde cian `#38BDF8`, radio `10px`, ancho `500px`) sobre backdrop difuminado (`rgba(11, 19, 43, 0.88)` y `backdrop-filter: blur(5px)`).
* **Cinética de Progresión:**
  - Barra de progreso superior continua con gradiente `#38BDF8` a `#00E676`.
  - Lista checklist reactiva de 6 pasos secuenciales (cambian de estado `⏳` en azul a `✅` en verde conforme avanza la computación estocástica).
  - Botón de cancelación accesible que aborta la llamada HTTP mediante `AbortController`.
  - Cierre automático fluido al recibir la respuesta y transición a la Vista de Cartera.

### [DES-QBE-024] Ergonomía de Boletos Split con Prioridad Financiera [UX-MANDATE] (H9)

* **Jerarquía Visual de Izquierda a Derecha:**
  - **Boleto 1: Ganancia (Ataque) a la IZQUIERDA en Verde:** Cuadro con borde `#00E676` al 40%. Despliega la selección principal y el monto de asignación en **letra grande (`font-size: 1.35rem; font-weight: 900; color: #00E676;`)** para agilidad inmediata al teclear en ventanilla de apuestas.
  - **Boleto 2: Seguro (Recuperación) a la DERECHA en Azul:** Cuadro con borde `#38BDF8` al 30%. Despliega el empate/cobertura con su momio real y el monto de asignación en letra grande (`1.35rem`, peso 900).
* **Momios 1X2 Completos:** El encabezado de la tarjeta muestra el resumen tripartito del mercado (`L @... | E @... | V @...`) para contexto completo de precios.
* **Sobriedad de Escenarios:** La descripción de desenlaces (Ganancia Principal, Doble Cobro PA y Cobertura Tablas) se formatea en tipografía sobria limpia (`font-size: 7.8pt; color: #94A3B8`), erradicando insignias o balazos fluorescentes invasivos.

---

### [DES-QBE-026] Selector de Jornadas en Píldoras Continuas (Pill-Tabs) [UX-MANDATE]

* **Geometría y Ubicación:** Montado en la cabecera superior de la Cartelera (`.cartelera-header`), sustituyendo el título plano anterior.
* **Estructura DOM:**
  ```html
  <div class="matchday-pill-selector" style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px;">
    <!-- Píldoras generadas dinámicamente -->
    <button class="pill-tab" data-jornada="8">Jornada 8 <span class="badge-status">🏁 Concluida</span></button>
    <button class="pill-tab active" data-jornada="9">Jornada 9 <span class="badge-status">🟢 Mercado Abierto ⭐</span></button>
  </div>
  ```
* **Paleta y Estados Visuales:**
  - **Píldora Inactiva:** Fondo Slate 800 (`#1E293B`), borde `1px solid #334155`, texto Gris Pizarra (`#94A3B8`). Al hover: borde cian tenue.
  - **Píldora Activa (Seleccionada):** Fondo Azul Profundo (`#0284C7`), borde `1px solid #38BDF8`, texto Blanco Puro (`#FFFFFF`), tipografía peso 700.
* **Invarianza de Selección Reactiva en Memoria (`state.selectedMatches`):**
  - El usuario puede marcar un partido en la Jornada 8 y luego hacer clic en la píldora de la Jornada 9.
  - **REGLA ABSOLUTA:** Conmutar entre píldoras **NO vacía** el set de partidos seleccionados.
  - El contador de selección superior debe totalizar dinámicamente:
    `"3 partidos seleccionados (1 de Jornada 8, 2 de Jornada 9)"`.
  - Al regresar a una jornada visitada, las tarjetas previamente seleccionadas deben conservar su checkbox activo (`checked = true`) y el borde iluminado en `#38BDF8`.

---

### [DES-QBE-035] Vista Equipos y Partidos Soberana (Limpieza de Controles Comerciales) [UX-MANDATE]

* **Axioma de Desconexión Comercial:** La vista "Equipos y Partidos" es un espacio de inteligencia y consulta deportiva pura. Queda estrictamente prohibido incluir en esta vista casillas de selección de apuestas (`checkbox`), contadores de partidos seleccionados o botones de generación de portafolios comerciales.
* **Geometría del Panel de Cartelera (`.cartelera-panel`):**
  1. **Selector de Jornadas:** Contenedor `#matchday-pill-selector` con píldoras de navegación continua:
     - Fechas Concluidas: `Jornada N 🏁 Concluida` (fondo `#1E293B`, texto `#94A3B8`).
     - Fecha Activa / En Curso: `Jornada N ⚡ Activa` (fondo `#0284C7`, borde `#38BDF8`, brillo cian).
     - Fechas Programadas: `Jornada N 📅 Programada` (fondo `#1C2541`, borde `#334155`).
     *(Queda prohibido el término "Mercado Abierto" en esta pantalla).*
  2. **Tarjetas de Partidos (`.match-card-sovereign`):**
     - Fecha, hora y distintivo de estado (`FINALIZADO` con marcador real, o `PROGRAMADO`).
     - Escudos locales oficiales y nombres canónicos de ambos clubes.
     - Franja de probabilidad o datos físicos de gol (sin cuotas de casino).
     - CERO inputs de tipo checkbox.

---

### [DES-QBE-037] El Carrusel Horizontal Continuo y la Tarjeta Clicable Limpia [UX-MANDATE]

* **Geometría del Carrusel (`.carousel-track`):**
  - Contenedor de una sola fila: `display: flex; flex-wrap: nowrap; overflow-x: auto; scroll-behavior: smooth;`.
  - Queda estrictamente prohibido que las píldoras se apilen en múltiples filas verticales (`flex-wrap: wrap` prohibido).
  - Flechas de navegación: `#btn-carousel-prev` (`◄`) y `#btn-carousel-next` (`►`).
  - Auto-centrado: La píldora de la jornada activa o seleccionada se desplaza automáticamente al centro visible del track.
* **Geometría de la Tarjeta Soberana (`.match-card-clean`):**
  - La tarjeta completa es el disparador de interacción (`cursor: pointer; transition: border-color 0.2s;`).
  - Queda prohibido añadir botones internos de ancho completo o textos con jerga técnica ("Radiografía Estocástica" prohibido).
  - Encabezado con fecha y badge de estado (`FINALIZADO` con marcador, o `PROGRAMADO`), escudos locales y nombres canónicos.

### [DES-QBE-037-A] Ventanizado de 3 Píldoras en Carrusel de Jornadas [UX-MANDATE]
* **Mecanismo:** Algoritmo determinista de renderizado de píldoras de navegación en el carrusel para limitar el Viewport y prevenir desbordamientos:
  - Para Jornada 1: Visualizar píldoras `[1, 2, 3]`.
  - Para Jornada 17: Visualizar píldoras `[15, 16, 17]`.
  - Para Jornadas intermedias $j$: Visualizar el trío dinámico `[j-1, j, j+1]`.

---

### [DES-QBE-039] Configuración de Cartera con Selector de Operador y Despacho Único [UX-MANDATE]

* **Componentes de la Tarjeta `#configuracion-cartera` (Mesa de Apuestas):**
  1. **Selector de Casino:** Dropdown `#casino-operator-select` con estilo Dark Fintech:
     - Opción activa única: `<option value="caliente" selected>Caliente_Deportes.MX</option>`.
  2. **Campo Bankroll:** Input numérico `#input-bankroll` (default: `$200.00 MXN`).
  3. **Control Deslizante de Certeza:** Slider `#slider-risk-certainty` ($70\% \leftrightarrow 90\%$, default $80\%$).
  4. **Botón Principal:** Texto unívoco ` ⚡ Calcular Cartera ` (ID: `#btn-calcular-cartera`).
* **Erradicación de Casillas:** Se eliminan los checkboxes individuales de selección de partidos. Al hacer clic en ` ⚡ Calcular Cartera `, el sistema procesa toda la jornada, descarta lo no rentable y despliega el Dashboard con los boletos split protegidos.

---

### [DES-QBE-039-B] Cluster Central de Tarjeta: Triple Nivel Probabilístico (Soberano vs. Consenso) & Micro-Malla [UX-MANDATE]
* **Geometría del Núcleo Central (`.card-center` / `.match-center-cluster`):**
  El bloque central de cada tarjeta en la Jornada Activa se estructura verticalmente en 4 micro-estaciones:
  1. **Horario:** Texto pequeño monospaciado (`0.72rem`, `#94A3B8`).
  2. **Nivel 1 (Distribución Soberana Q-BE — HÉROE):**
     - Formato: `p1% · pX% · p2%` en tipografía destacada (`font-size: 0.88rem; font-weight: 800;`).
     - Franja horizontal tricolor (`.prob-strip`) de 4px de alto (Verde/Cian, Pizarra, Coral).
  3. **Nivel 2 (Consenso de Mercado Sin Comisión — COMPARATIVO SOBRIO):**
     - Formato: `Mkt: qL% · qE% · qV%`
     - Estilo: Color Gris Pizarra (`#94A3B8`), `font-size: 0.70rem`, `font-weight: 500`, fuente monospaciada (`font-family: monospace;`).
     - Prohibición: Queda strictly prohibido utilizar colores fluorescentes o fuentes en negrita en este renglón.
  4. **Nivel 3 (Diferencial Aritmético Q-BE vs. Mercado — ALPHA EDGE):**
     - Formato: `Δ: ±dL% · ±dE% · ±dV%`
     - Estilo: Color Gris Atenuado (`#64748B`), `font-size: 0.67rem`, `font-weight: 400`, fuente monospaciada.
     - Representación: Signo explícito `+` o `-` con 1 decimal (ej. `Δ: -7.2% · -1.3% · +8.5%`).
* **Geometría de Micro-Malla Fija (4 Columnas):**
  ```css
  grid-template-columns: 26px 42px 42px 42px;
  background: rgba(15, 23, 42, 0.45);
  border: 1px solid rgba(51, 65, 85, 0.5);
  ```

---

### [DES-QBE-040] Modo Enfoque: Alternador de Tabla General y Cartelera Centrada [UX-MANDATE]
* **Control de Alternancia (`#btn-toggle-standings`):**
  - Ubicado en la cabecera `.cartelera-header`, adyacente al título de la Jornada.
  - Estados:
    - Tabla Visible: Texto `◨ Ocultar Tabla`, fondo Slate 800 (`#1E293B`), texto Gris Pizarra (`#94A3B8`).
    - Tabla Oculta: Texto `◧ Ver Tabla`, fondo Azul Tenue (`#0284C7` al 25%), borde Cian (`#38BDF8`), texto Blanco Puro.
* **Geometría de Estado Oculto (`.standings-hidden`):**
  - El panel izquierdo de posiciones (`#sovereign-standings-container` o `.standings-panel`) adopta `display: none !important;`.
  - El contenedor principal de la vista elimina la cuadrícula bipartita (`grid-template-columns: 1fr !important;`).
  - El panel de la cartelera adopta:
    `max-width: 880px !important; width: 100% !important; margin: 0 auto !important;`
  - Transición fluida sin parpadeos de interfaz.

### [DES-QBE-040-A] Modo Enfoque de Cartelera y Persistencia Local [UX-MANDATE]
* **Mecanismo de Persistencia y Centrado Áureo:**
  - El botón `#btn-toggle-standings` conmuta la visibilidad de la tabla general y persiste el estado en `localStorage.setItem('qbe_standings_hidden', status)`.
  - Al activar el Modo Enfoque (tabla oculta), la cartelera adopta el centrado áureo mediante `max-width: 880px !important; margin: 0 auto !important;`.

### [DES-QBE-041] Header Fino de Un Solo Piso (45px Fijo) [UX-MANDATE]
* **Geometría:** La cabecera principal `header.app-header` restringe su altura a `height: 45px; max-height: 45px;` para maximizar el área vertical visible del Live Board en pantallas estándar.

### [DES-QBE-042] Contención Maestra Split-View con Columna minmax(0, 1fr) [UX-MANDATE]
* **Regla Antidesbordamiento Horizontal:** La vista `.split-view` debe forzar el uso de la regla CSS `grid-template-columns: minmax(0, 1fr) minmax(0, 1fr)` para impedir desbordamientos horizontales en Viewports de 1380px.

### [DES-QBE-043] Respaldo Narrativo Local de 4 Puntos Focales [UX-MANDATE]
* **Resiliencia Frontend:** El controlador de la SPA en `app.js` inyecta un bloque narrativo de respaldo determinista estructurado en 4 puntos focales ante cualquier fallo de red o tiempo de espera al consultar `/api/portfolio/match-thesis`.
* **Geometría de Estado Oculto (`.standings-hidden`):**
  - El panel izquierdo de posiciones (`#sovereign-standings-container` o `.standings-panel`) adopta `display: none !important;`.
  - El contenedor principal de la vista elimina la cuadrícula bipartita (`grid-template-columns: 1fr !important;`).
  - El panel de la cartelera adopta:
    `max-width: 880px !important; width: 100% !important; margin: 0 auto !important;`
  - Transición fluida sin parpadeos de interfaz.

---

### [DES-QBE-045] Contrato de Claves Frontend y Soporte de las 9 Estrategias Canónicas [UX-MANDATE]
* **Sincronización de Contratos JSON (3NF):**  
  La función cliente `renderizarResultadosPortafolio(data)` debe consumir obligatoriamente las claves canónicas emitidas por el backend 3NF:
  - `data.ordenes_ejecucion_partidos` (con fallback de retrocompatibilidad a `data.ordenes`).
  - `data.control_portafolio` (con fallback a `data.control`).
  - `data.balance_global_portafolio` (con fallback a `data.balance`).
* **Insignias Visuales de las 9 Estrategias:**  
  La interfaz debe soportar formalmente la paleta y semántica de las 9 estrategias canónicas:
  - `QBE-D1` y `QBE-D2` (Directas): Azul Cian `#38BDF8` (Ataque Puro).
  - `QBE-H1` y `QBE-H2` (Híbridas V=0): Verde Neón `#00E676` (Preservación en Tablas).
  - `QBE-R1` y `QBE-R2` (Reversas Underdog): Ámbar `#F59E0B` (Alto Retorno Asimétrico).
  - `QBE-C1` (DNB) y `QBE-C2` (Totales): Violeta `#A855F7` (Derivados).
  - `QBE-00` (Cuarentena / Veto): Rojo Coral `#EF4444` (Veto Total de Capital).
* **Desacoplamiento de Pago Anticipado:**  
  El distintivo `🏷️ Pago Anticipado (+PA)` se gobierna mediante la bandera booleana `ord.pa_activo` o `ord.estrategia_seleccionada.linea_promocional`, suprimiendo los códigos heredados con signo `+` (`D1+`, `H1+`).
* **Independencia de la Radiografía Forense:**  
  El clic sobre las tarjetas de la Cartelera (`abrirRadiografiaForense(matchId)`) debe operar de forma autónoma con los datos soberanos del Live Board (`f.p_local`, `f.lambda_home`, etc.) sin requerir la preexistencia de un cálculo de cartera.

### [DES-QBE-046] Sub-Pestaña de Quinielas Progol #2352 en la Mesa de Apuestas [UX-MANDATE]
* **Navegación de Segundo Piso en `#tab-portfolio`:**  
  La Mesa de Apuestas incorpora un selector de submódulo con botones de píldora:
  - `[ 🎰 Sportsbook Casino 1X2 ]` (Sub-vista activa por defecto: órdenes split, Kelly, hard-caps).
  - `[ 🎟️ Quinielas Progol #2352 ]` (Sub-vista de pronósticos deportivos).
* **Geometría de la Sub-Vista Progol (`#contenedor-progol`):**  
  - Encabezado: Número de Concurso (`#2352`), Bolsa Acumulada (`$8,800,000.00 MXN`) y Tiempo Límite.
  - Retículo de 21 Casillas (14 Progol Regular + 7 Revancha): Despliega local, visitante, probabilidades soberanas Q-BE y badge de `Prior Base (1/3)` para partidos internacionales.
  - Barra de Control de Presupuesto: Input monetario (`$360 MXN` default) y botón **`[ ⚡ Optimizar Presupuesto ]`** conectado a `/api/markets/progol/optimize`.
* **Token Tolerado de Compatibilidad:** el contenedor expone adicionalmente la clase `progol-slate-container` como alias CSS, sin sustituir jamás al ID canónico `#contenedor-progol` (desviación declarada `D-1`).

### [DES-QBE-047] Selector Multi-Operador en Mesa de Apuestas [UX-MANDATE]
* El elemento `<select id="casino-operator-select">` debe exponer formalmente los operadores certificados en backend:
  - `<option value="caliente" selected>Caliente_Deportes.MX</option>`
  - `<option value="betway">Betway.MX</option>`
* El header macro de la cartera debe actualizarse dinámicamente según la jornada activa consultada, erradicando textos fijos de jornadas anteriores (`Jornada 8` quemado).

> **Trazabilidad de registro (VARIANCE-01):** los nodos solicitados como `[DES-QBE-042]`,
> `[DES-QBE-043]` y `[DES-QBE-044]` en la Directiva Maestra Fase 6 se registran como
> `[DES-QBE-045]`, `[DES-QBE-046]` y `[DES-QBE-047]` por colisión con los nodos `042`
> (Contención Maestra Split-View) y `043` (Respaldo Narrativo de 4 Puntos Focales), ya
> sellados en `docs/DESIGN.md` (líneas 387 y 390). Referencia cruzada: `LOGIC.md [LN-QBE-060-B]`
> (9 estrategias canónicas) y `DIRGEN_VAULT.md` (`[VAULT-CORE-070-TRIAJE]`, línea 30) — sin contradicción.
> **Ajuste de dictamen Q9 (autoridad humana):** el ID canónico del contenedor Progol es
> `#contenedor-progol`; el token `progol-slate-container` sobrevive únicamente como alias de
> compatibilidad para el Juez Inmutable (desviación declarada `D-1`).

### [DES-QBE-048] Cockpit: Cuarta Pestaña [ ⚙️ Centro de Control ] y Terminal de Streaming [UX-MANDATE]
* **Navegación Superior:** Se añade la pestaña `[ ⚙️ Centro de Control ]` (`data-tab="view-control-center"`).
* **Geometría de la Vista:**
  - **Comando Maestro Superior:** Botón destacado `[ ⚡ EJECUTAR TODA LA INGESTA EN CADENA ]`.
  - **Tres Grupos de Control:**
    1. *Grupo 1: Daemons de Carga (Ingesta 3NF):* Botones individuales para Deportivo, Mercado, Progol y Escudos.
    2. *Grupo 2: Auditoría y Certificación:* Botones para Pureza Vol. 1, Cartera Shield y Llaves LLM.
    3. *Grupo 3: Mantenimiento:* Botón para Purga de Base de Datos.
  - **Consola Integrada en Vivo (`#terminal-stream-output`):**  
    Ventana monospaciada de estilo terminal (`background: #050B14; border: 1px solid #334155; font-family: monospace; color: #38BDF8; max-height: 380px; overflow-y: auto;`) que despliega la salida estándar en tiempo real de la tarea ejecutada.

### [DES-QBE-049] Saneamiento Tipográfico de Celdas de Equipo (Anti-Truncamiento Real) [UX-MANDATE]
* **Derogación de Restricción Rígida:** Se deroga formalmente el uso de `max-width: 145px;` en `.team-home-cell` y `.team-away-cell`.
* **Regla Tipográfica:** Las celdas adoptan `min-width: 0; width: 100%; font-size: 0.88rem; font-weight: 700;`. El texto largo debe fluir de forma elástica dentro del grid simétrico `1fr auto 1fr`, impidiendo que nombres como *"Chivas Guadalajara"* o *"Rayados de Monterrey"* sean truncados prematuramente.

### [DES-QBE-050] Tooltips Didácticos Fiduciarios en el Centro de Control [UX-MANDATE]
* Cada botón de tarea en `#view-control-center` debe incorporar un atributo descriptivo explícito (`title` o tarjeta hover) estructurado en tres niveles:
  1. **Qué hace:** La subrutina exacta que invoca.
  2. **Cuándo usar:** El momento operativo del ciclo de jornada.
  3. **Impacto y Restauración:** Para herramientas destructivas (purga), advierte qué tablas vacía y explica que se restaura pulsando `[ ⚡ Ejecutar Toda la Cadena de Ingesta ]`.

### [DES-QBE-051] Banner Didáctico de Base de Datos Vacía en Live Board [UX-MANDATE]
* Si el cliente consulta la cartelera y la base de datos ha sido purgada, el panel izquierdo y derecho no deben exhibir errores de red (`❌ Error al conectar`); deben desplegar un banner estilizado Dark Fintech:
  `ℹ️ Base de datos en reposo / vacía. Vaya a [ ⚙️ Centro de Control ] y presione "⚡ Ejecutar Cadena de Ingesta Total" para sincronizar la liga.`

> **Trazabilidad de registro (VARIANCE-01) — Fase 7:** los nodos `[ARCH-1.6.15]`,
> `[ARCH-1.4.12]` y `[ARCH-1.6.16]` (registrados en `docs/ARCH.md`) y `[DES-QBE-048]` /
> `[DES-QBE-049]` se sellan sin colisión con los identificadores `042`–`047` previamente
> legislados. Los identificadores `[ARCH-1.4.11]` y `[ARCH-1.6.14]` permanecen **no
> asignados** en esta ventana (sin contradicción ni reutilización). Referencia cruzada:
> `tests/shield/test_shield_admin_tasks_and_dynamic_matchday.py` (Juez Inmutable Twin-Test).
> **Derogación expresa:** `[DES-QBE-049]` deroga la restricción `max-width: 145px;` y la
> deuda abierta `O-2` declarada en `src/web/static/css/theme.css` (bloque `[DES-QBE-046]`).

> **Trazabilidad de registro (VARIANCE-01) — Fase 7.5:** los nodos `[DES-QBE-050]` y
> `[DES-QBE-051]` se sellan sin colisión con los identificadores `042`–`049` previamente
> legislados. Referencia cruzada: `docs/ARCH.md` (`[ARCH-1.6.15-B]`, `[ARCH-1.6.10-B]`,
> `[ARCH-1.4.13]`) y `tests/shield/test_shield_market_resolution_and_purge.py` (Juez
> Inmutable Twin-Test en Estado RED certificado).







### [DES-QBE-052] Selector Multi-Operador con Opción "Mejor Combinación" por Defecto [UX-MANDATE]
* El desplegable `#casino-operator-select` se estructura con:
  - `<option value="mejor_combinacion" selected>⚡ Mejor Combinación (Cross-Market)</option>`
  - `<option value="caliente">Caliente_Deportes.MX</option>`
  - `<option value="betway">Betway.MX</option>` *(con sufijo " (Sin cuotas)" y disabled si carece de datos)*.

### [DES-QBE-053] Boletos Split con Logo de Casa Patrocinadora por Boleto [UX-MANDATE]
* En cada tarjeta de orden split, el rótulo genérico `APOSTAR EN VENTANILLA:` se sustituye por:
  `APOSTAR EN: <img src="/static/img/bookmakers/{slug}.png" class="bookmaker-logo-mini"> {NOMBRE_CASINO}`
  permitiendo que el usuario identifique de inmediato en qué casa meter el Boleto 1 (Ataque) y en cuál meter el Boleto 2 (Seguro).

### [DES-QBE-054] Corrección de Macro KPI "Posiciones del Total" [UX-MANDATE]
* El elemento `#kpi-posiciones-core` debe renderizar con fidelidad:
  `${kAprobados} / ${totalJornada}` (ej. `1 / 9` o `4 / 9`), reflejando cuántos partidos de la jornada activa superaron el triaje fiduciario.

> **Trazabilidad de registro (VARIANCE-01) — Fase 7.6:** los nodos `[DES-QBE-052]`,
> `[DES-QBE-053]` y `[DES-QBE-054]` se sellan de forma consecutiva tras `[DES-QBE-051]`
> sin colisión con los identificadores `042`–`051` previamente legislados. Referencia
> cruzada: `docs/ARCH.md` (`[ARCH-1.4.14]`, `[ARCH-1.4.15]`, `[ARCH-1.5.10]` — este último
> registrado por remapeo de colisión VARIANCE-01 del `[ARCH-1.5.4]` solicitado),
> `docs/LOGIC.md` (`[LN-QBE-076]`, `[LN-QBE-077]`) y el Juez Inmutable
> `tests/shield/test_shield_cross_market_best_execution.py` (Twin-Test en Estado RED
> certificado). La Carta de Clase `bookmaker-logo-mini` (`[DES-QBE-053]`) y la opción
> `mejor_combinacion` (`[DES-QBE-052]`) quedan pendientes de materialización en
> `src/web/templates/index.html`, `src/web/static/js/app.js` y `src/web/static/css/theme.css`
> bajo autorización de la Tríada (Paso 3).

### [DES-QBE-055] Micro-Insignia de Operador en Boletos Split (Cero Texto Duplicado) [UX-MANDATE]
* En las tarjetas de órdenes de boletos split, queda estrictamente prohibido repetir el nombre textual del casino después del logo (ej. erradicar `APOSTAR EN: [LOGO] Caliente_Deportes.MX:`).
* El bloque de pie de boleto se estructura limpiamente como:
  `<span class="ticket-action-label">APOSTAR EN:</span> <img src="/static/img/bookmakers/${slug}.png" class="bookmaker-logo-inline" alt="${slug}">`
  eliminando bordes azules toscos y asegurando una altura máxima de `18px` para el logo.

### [DES-QBE-056] Apertura Dinámica del Live Board en Jornada Vigente [UX-MANDATE]
* Al ingresar a la vista `view-matchday-selection`, la cartelera debe posicionarse por defecto en la jornada con partidos activos por disputarse (Jornada 11), mostrando el selector de píldoras centrado en `[J10] [J11 Activa] [J12]`.

### [DES-QBE-057] Selector de Mercados con Tríada de Operadores y "Mejor Combinación" [UX-MANDATE]
* El selector `#casino-operator-select` se expande formalmente a:
  - `<option value="mejor_combinacion" selected>⚡ Mejor Combinación (Cross-Market)</option>`
  - `<option value="caliente">Caliente_Deportes.MX</option>`
  - `<option value="novibet">Novibet.MX</option>`
  - `<option value="betway">Betway.MX</option>`
* El logotipo oficial `/static/img/bookmakers/novibet.svg` se renderiza automáticamente en los boletos split cuando la pierna sea asignada a Novibet.

> **Trazabilidad de registro (VARIANCE-01) — Volumen III (Novibet):** el nodo `[DES-QBE-057]`
> se sella de forma consecutiva tras `[DES-QBE-056]` sin colisión con los identificadores
> `042`–`056` previamente legislados. El emblema `novibet.svg` se ancla en la bóveda local de
> activos bajo `[ARCH-1.5.10-B]` (vector oficial auditado, 5 859 B, `viewBox="0 0 164 38"`),
> consumido automáticamente por la cadena de degradación declarada de `_rotuloCasaApostar`
> (PNG → SVG → ocultar) sin hotlinking a terceros. Referencia cruzada: `docs/ARCH.md`
> (`[ARCH-1.4.6-F]`), Juez Inmutable `tests/shield/test_shield_novibet_ingestion.py`.

> **Trazabilidad de registro (VARIANCE-01) — Volumen II:** los nodos `[DES-QBE-055]` y
> `[DES-QBE-056]` se sellan de forma consecutiva tras `[DES-QBE-054]` sin colisión con los
> identificadores `042`–`054` previamente legislados. `[DES-QBE-055]` **enmienda y deroga
> parcialmente** la fórmula de `[DES-QBE-053]`: la Carta de Clase `bookmaker-logo-mini` con
> sufijo textual `{NOMBRE_CASINO}` queda sustituida por la Carta de Clase
> `bookmaker-logo-inline` (alto máximo `18px`, cero texto duplicado, cero borde azul tosco).
> `[DES-QBE-056]` es enmienda de presentación de `docs/ARCH.md` (`[ARCH-1.6.15]`,
> `[ARCH-1.6.15-C]`). Referencia cruzada: Juez Inmutable
> `tests/shield/test_shield_volume2_consolidation.py`. La materialización en
> `src/web/static/js/app.js`, `src/web/static/css/theme.css` y `src/web/templates/index.html`
> queda supeditada a la autorización de la Tríada (Paso 3).

---

### [DES-QBE-058] Desglose Cuantitativo en Tarjetas de Partidos Vetados [UX-MANDATE]
* La sección de *Partidos Vetados (QBE-00)* en la Mesa de Apuestas debe sustituir las explicaciones narrativas por un bloque de datos transparente:
  `Q-BE: {p1}% · {pX}% · {p2}% | Momios: {OL} / {OX} / {OV} | α_max = {alpha}% (EV Negativo) | θ* = {theta} vs Empate @{OX}`

### [DES-QBE-059] Renderizado Universal de Emblema de Casino en Boletos Mono-Operador [UX-MANDATE]
* En el pie de cada boleto de apuesta, el rótulo debe renderizar siempre el logo oficial del operador:
  `APOSTAR EN: <img src="/static/img/bookmakers/${slug}.png" class="bookmaker-logo-inline">`
  tanto si la orden proviene de *Mejor Combinación* como si proviene de una selección mono-casino (*Caliente* o *Novibet*).

### [DES-QBE-060] Anatomía Enriquecida de Boletos Split con Momio Casino, P' y Opción No Jugada [UX-MANDATE]
* **Rótulos Estandarizados por Pierna (Boleto 1 y 2):**
  - Línea de Cuota: `Momio Casino: @{cuota}` (se erradica la etiqueta genérica "Momio:"). **Formato SUPERSEDED por `[DES-QBE-061]` (Fase 7.9): el vigente es `Momio Casino: {prob_implicita}% (@{momio})`.**
  - Línea de Probabilidad Fiduciaria: `Predicción Q-BE con P': {prob_efectiva}%` (exhibe el porcentaje fiduciario P' asociado a ese desenlace).
  - Línea de Casa Patrocinadora: `APOSTAR EN: <img src="/static/img/bookmakers/{slug}.png" class="bookmaker-logo-inline">` (sin texto repetido).
* **Bloque de Transparencia 360° al Pie de Tarjeta:**
  - Separado por una línea sutil (`border-top: 1px solid rgba(51,65,85,0.4)`).
  - Se erradican títulos ruidosos (prohibido `📊 CIFRAS COMPLETAS DEL ENCUENTRO`) y jerga técnica compleja (prohibido `Overround` y `θ*`).
  - Despliega exclusivamente el desenlace descartado:
    `• Opción No Jugada: {nombre_descartado} ──► Momio Casino: @{cuota} | Predicción Q-BE con P': {prob_P}%` **Formato SUPERSEDED por `[DES-QBE-061]`: `Momio Casino: {prob_implicita}% (@{momio})`.**

### [DES-QBE-061] Formato Dual de Cuotas de Casino: Probabilidad Implícita + Decimal [UX-MANDATE]
* En cada pierna de apuesta (Boleto 1, Boleto 2 y Opción No Jugada), el momio comercial debe exhibir primero la probabilidad implícita del mercado y entre paréntesis el decimal:
  `Momio Casino: {prob_implicita}% (@{momio})`
  donde $\text{prob\_implicita} = \frac{100.0}{O_{\text{casino}}}$ con 1 decimal.
* Directamente debajo se mantiene:
  `Predicción Q-BE con P': {prob_efectiva}%`
  permitiendo contrastar instantáneamente la creencia del casino contra la certeza de Q-BE.

### [DES-QBE-062] Despliegue de la Tetralogía de Escenarios en Boletos Split [UX-MANDATE]
* En el bloque de texto informativo de cada tarjeta split, se deben renderizar en orden estricto los siguientes cuatro renglones:
  1. `• Ganancia Principal: Cobro de $X.XX MXN (++$Y.YY netos, +ZZ.Z% ROI).`
  2. `• Cobertura en Empate: Recuperación de $B.BB MXN ($0.00 pérdida de capital).`
  3. `• Pago Anticipado con Empate: Cobro de AMBOS boletos por $X.XX MXN (++$Y.YY netos, +ZZ.Z% ROI) si el favorito toma ventaja de 2 goles y el juego concluye empatado.` *(Solo si pa_activo es True y existe boleto seguro).* **[Enmienda Fase 7.9 — Resolución `VARIANCE-01`: el rótulo canónico LITERAL es `Pago Anticipado con Empate:` (deroga a `Pago Anticipado + Empate:`), certificado por `tests/shield/test_shield_ticket_ux_and_cashout_refinement.py`.]**
  4. `• Salida de Emergencia: Si el rival anota primero, ejecutar CashOut al empatar en el 2T en cuanto ofrezca Tablas ($B.BB MXN) para recuperar el 100% del capital.`
* Debajo de este bloque se ubica la línea divisoria continua y la `• Opción No Jugada`.

### [DES-QBE-063] Diseño de la Radiografía Forense: Barras Duales Apiladas, Radiografía Estructural y Cero Estrellas [ARCH-PILLAR]
* **Cabecera:** Píldora de estrategia dinámica con paleta canónica (`_paletaEstrategia`) y botón simple `Cerrar`.
* **Comparador Gráfico de Barras Duales (Minimalista):**
  - **Leyenda Apilada en Cabecera:** Local en Azul Cian (`#38BDF8`) arriba, Visitante en Verde Esmeralda (`#00E676`) abajo, emulando la disposición vertical de las barras.
  - **Supresión de Redundancias:** Prohibido repetir los nombres de los clubes en cada renglón de métrica.
  - **Diferencia Relativa Plegada:** La ventaja del ganador se indica exclusivamente entre paréntesis junto a la barra mayor (ej. `1.95 xG (+0.85)`). Cero textos descriptivos repetidos a la derecha.
  - **Las 4 Métricas Fácticas:** Conectadas a `currentLiveBoard.standings` (Peligro Ofensivo xG de Partido, Producción en Temporada GF/PJ, Solidez Defensiva GC/PJ y Ritmo Competitivo PTS/PJ). Si faltan datos en un partido, degrada limpiamente a `--` (prohibido inventar números).
* **Tabla de Probabilidades (6 Columnas):**
  - Cero momios decimales (@).
  - Resaltado en Verde (`#00E676`) para Ataque y Azul (`#38BDF8`) para Cobertura.
  - Columna *Casino Seleccionado*: Muestra el nombre limpio en color sin emojis de estrella (`⭐`).
* **Tabla Inferior — Radiografía Estructural y Forma Reciente:**
  - Sustituye a la tabla de desempeño vacía por una estructura de 2 filas leyendo directamente de `currentLiveBoard.standings`.
  - Columnas: `EQUIPO | PUESTO | PTS | RÉCORD (G-E-P) | DIF GOLES | FORMA RECIENTE (5P) | xPTS OPTA | DIF xG | Q_MOD`.
  - Los 5 resultados recientes se representan con círculos de color (`🟢` victoria, `⚪` empate, `🔴` derrota).
  - El valor líder en cada columna se ilumina en Verde Esmeralda (`#00E676`). Cero estrellas.
* **Contenedor de Acciones de Tarjeta:**
  - Extremo Izquierdo: Botón `🔬 Ver Análisis Cuantitativo`.
  - Extremo Derecho: Botón `📋 Copiar Ticket` y botón destacado `🎟️ Comprar Boleto` (congelamiento de cuotas y cambio de estado a `✔ Boleto Registrado`).
  - Barra de Control: Badge dinámico `#badge-boletos-comprados` (`🎟️ Comprados: N ($XX.XX MXN)`).


---

