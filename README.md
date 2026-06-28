# 🏁 F1 Strategy Simulator - Simulación de Sistemas
### Trabajo Práctico Grupal - ININF UCEMA

Simulador interactivo en tiempo real desarrollado en Python con **Streamlit** y gráficos
interactivos con **Plotly**. Modela y **compara dos estrategias de carrera de Fórmula 1 en
paralelo (A vs B)** sobre el mismo circuito, combinando simulación continua (dinámica de
sistemas), eventos discretos (Monte Carlo), teoría de colas (M/M/1) e inventario.

---

## 🏛️ Componentes de la Simulación

La F1 es un sistema híbrido: coexisten procesos de cambio continuo y eventos abruptos.

### 1. Componente Continuo (Dinámica de Sistemas) — `models/car_state.py`
* **Degradación del Neumático ($Grip\,\%$)**: el agarre cae de forma continua según un decaimiento
  exponencial:
  $$G(t) = 100 \cdot e^{-\lambda \cdot K_{piloto} \cdot t}$$
  La tasa $\lambda$ depende del **compuesto** (Blando/Medio/Duro) y del **circuito**; $K_{piloto}$
  del estilo de manejo (Conservador 0.75 / Equilibrado 1.0 / Agresivo 1.35).
* **Consumo de Combustible**: lineal, a `fuel_por_vuelta` kg/vuelta (depende del circuito). El
  **combustible de largada = total de vueltas × consumo por vuelta**, aligerando el auto a medida
  que se quema.
* **Tiempo de Vuelta**: equilibra la pérdida de agarre (penaliza) y el aligeramiento de
  combustible (mejora), escalado por el ritmo del compuesto:
  $$T_{vuelta} = T_{base}\cdot f_{compuesto} + 0.14\cdot\Delta grip - 0.038\cdot kg_{quemados}$$
* **Ritmo por compuesto ($f_{compuesto}$)**: en neumático nuevo el Blando es más rápido que el
  Medio, y el Duro más lento (**±0.5 % por escalón**: Blando 0.995 / Medio 1.000 / Duro 1.005).

### 2. Componente de Eventos Discretos / Monte Carlo — `models/pit_box.py`
* **Servicio de boxes (auto detenido)**: tiempo distribuido $U(2.2, 2.8)$ s.
* **Falla estocástica**: con probabilidad $P_{falla}$ ajustable, la pistola neumática se traba y
  agrega una demora $U(4.0, 10.0)$ s.
* **Pérdida en Pit Lane**: cada parada pierde además el tiempo de recorrer el pit lane a velocidad
  limitada, $U(18, 22)$ s — el verdadero costo estratégico de parar.

### 3. Componente de Colas (M/M/1 — Double Stacking) — `models/pit_box.py`
* El **Pit Box** es un servidor de canal único. Cada parada puede activar el *Double Stacking*: el
  segundo auto del equipo entra en la misma vuelta y espera en cola virtual el tiempo de servicio
  del primero (el pit lane lo recorre cada auto por separado, no es ocupación del box).

### 4. Componente de Inventario — `models/inventory.py`
* Stock limitado de juegos por compuesto (Blando/Medio/Duro). **El compuesto de largada y cada
  parada descuentan un juego**; si se agota el solicitado se usa un compuesto por defecto.

### 5. Circuitos (parámetros compartidos) — `models/circuito.py`
Selector de pista que fija el tiempo base de vuelta, el consumo de combustible y la degradación
$\lambda$ por compuesto (igual para ambas estrategias):

| Circuito | Degradación | Vuelta base | Combustible | λ Blando / Medio / Duro |
|---|---|---|---|---|
| Suzuka | Alta | 1:36.527 | 1.92 kg/v | 0.110 / 0.065 / 0.025 |
| Brasil (Interlagos) | Media | 1:14.020 | 1.38 kg/v | 0.075 / 0.040 / 0.015 |
| Mónaco | Baja | 1:19.713 | 1.15 kg/v | 0.020 / 0.008 / 0.002 |

---

## ⚔️ Comparación A vs B
Ambas estrategias corren la **misma carrera** (mismo circuito y cantidad de vueltas) animadas en
paralelo, panel a panel. Por estrategia se configura: estilo de piloto, stock de neumáticos,
probabilidad de falla, **compuesto de largada** y una **tabla editable de paradas** (vuelta +
compuesto + double-stack opcional, 0..N paradas). El reporte final muestra el cara a cara
(tiempo total, ganador), el detalle de cada parada y el stock restante.

### Telemetría
El gráfico muestra la curva continua de **Grip (%)** y la de **Tiempo de Vuelta (s)**. En la vuelta
de cada parada, el tiempo perdido en boxes se **suma a esa vuelta**, generando un pico visible en
la curva (y en la métrica), tanto en el gráfico como en el total de carrera.

### 🎬 Demos (presets)
Al pie de la barra lateral hay botones de demo (2 por circuito) que cargan escenarios A-vs-B
típicos (undercut vs overcut, 1 vs 2 paradas, sin parada vs 1, largada Blanda vs Dura, etc.).
Cargan la configuración; luego se presiona **INICIAR COMPARACIÓN**.

---

## 📁 Estructura del Proyecto

```text
tp-simulacion-f1/
├── app.py                # Interfaz Streamlit, comparación A/B, presets y bucle de animación
├── models/
│   ├── __init__.py
│   ├── car_state.py      # Dinámica continua: grip, combustible, tiempo de vuelta, ritmo por compuesto
│   ├── pit_box.py        # Servidor M/M/1, pérdida de pit lane y fallas estocásticas
│   ├── inventory.py      # Stock e inventario de compuestos (λ y ritmo por compuesto)
│   └── circuito.py       # Catálogo de circuitos (vuelta base, consumo, degradación)
├── requirements.txt      # Dependencias
└── README.md             # Documentación del Trabajo Práctico (UCEMA)
```

---

## 🚀 Instalación y Ejecución

```bash
# 1. (opcional) entorno virtual
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate

# 2. dependencias
pip install -r requirements.txt

# 3. ejecutar
streamlit run app.py
```

La aplicación se abre en `http://localhost:8501`.

**Uso rápido:** elegí un **Circuito** y la cantidad de vueltas arriba en la barra lateral,
configurá las Estrategias A y B (o usá un botón de **🎬 Demos**), y presioná
**🏁 INICIAR COMPARACIÓN**.

---

## 🛠️ Tecnologías Utilizadas
* **Python 3.10+**
* **Streamlit** — interfaz web interactiva en vivo
* **Plotly** — telemetría dinámica (grip y tiempo de vuelta)
* **Pandas & NumPy** — manejo de datos de series temporales
