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

