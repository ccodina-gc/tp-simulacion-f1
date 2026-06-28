import time
from dataclasses import dataclass, field
from typing import List

import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from models.car_state import Monoplaza
from models.inventory import InventarioNeumaticos
from models.pit_box import PitBoxServidor, ReporteParada
from models.circuito import CIRCUITOS

# Configuración de página premium
st.set_page_config(
    page_title="F1 Live Strategy Simulator",
    page_icon="🏁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS Premium embebido para Dark Mode, Neumorfismo y Colores F1
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .title-header {
        background: linear-gradient(135deg, #E10600 0%, #FF8C00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    
    .subtitle-header {
        color: #A0AEC0;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: rgba(26, 32, 44, 0.75);
        border: 1px solid rgba(225, 6, 0, 0.2);
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: rgba(225, 6, 0, 0.8);
    }
    
    .metric-label {
        font-size: 0.9rem;
        color: #CBD5E0;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #FFFFFF;
    }
    
    .telemetry-log {
        background-color: #0F172A;
        border-left: 4px solid #E10600;
        border-radius: 8px;
        padding: 1.2rem;
        font-family: 'Courier New', monospace;
        font-size: 0.95rem;
        color: #38BDF8;
        max-height: 350px;
        overflow-y: auto;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.5);
    }
    
    .box-status-libre {
        color: #10B981;
        font-weight: 700;
    }
    .box-status-ocupado {
        color: #F59E0B;
        font-weight: 700;
    }
    .box-status-cola {
        color: #EC4899;
        font-weight: 700;
    }
    .box-status-falla {
        color: #EF4444;
        font-weight: 800;
        animation: pulse 1s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)


def dibujar_grafico_telemetria(historial: list, etiqueta: str = ""):
    """
    Renderiza el gráfico interactivo en tiempo real con Plotly.
    Muestra la curva continua de degradación del neumático vs las vueltas
    y el tiempo de vuelta en un eje secundario.
    El parámetro `etiqueta` distingue el panel (ej. "Estrategia A") en el título.
    """
    if not historial:
        return go.Figure()

    df = pd.DataFrame(historial)
    
    fig = make_subplots(
        specs=[[{"secondary_y": True}]],
    )

    # Curva Continua 1: Degradación de Adherencia (Grip %)
    fig.add_trace(
        go.Scatter(
            x=df["Vuelta"], 
            y=df["Grip (%)"],
            mode="lines+markers",
            name="Grip Neumático (%)",
            line=dict(color="#FF4500", width=3, shape="spline"),
            marker=dict(size=7, color=df["Color"].tolist()),
            fill="tozeroy",
            fillcolor="rgba(255, 69, 0, 0.1)"
        ),
        secondary_y=False,
    )

    # Curva Continua 2: Evolución del Tiempo de Vuelta (s)
    fig.add_trace(
        go.Scatter(
            x=df["Vuelta"], 
            y=df["Tiempo Vuelta (s)"],
            mode="lines",
            name="Tiempo de Vuelta (s)",
            line=dict(color="#00D2BE", width=2.5, dash="dot", shape="spline"),
        ),
        secondary_y=True,
    )

    titulo = "<b>TELEMETRÍA EN VIVO</b>"
    if etiqueta:
        titulo = f"<b>TELEMETRÍA · {etiqueta.upper()}</b>"

    fig.update_layout(
        template="plotly_dark",
        title=titulo,
        title_font_size=16,
        hovermode="x unified",
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(15, 23, 42, 0.6)",
        paper_bgcolor="rgba(15, 23, 42, 0.0)"
    )

    fig.update_xaxes(title_text="Vueltas Transcurridas", showgrid=True, gridcolor="rgba(255,255,255,0.08)")
    fig.update_yaxes(title_text="Grip del Neumático (%)", range=[0, 105], showgrid=True, gridcolor="rgba(255,255,255,0.08)", secondary_y=False)
    fig.update_yaxes(title_text="Tiempo de Vuelta (s)", showgrid=False, secondary_y=True)

    return fig


def renderizar_metrica(label: str, valor: str, color_destaque: str = "#FFFFFF", extra_class: str = ""):
    """Genera el HTML de una tarjeta de métrica con estética premium."""
    return f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value {extra_class}" style="color: {color_destaque};">{valor}</div>
    </div>
    """


@dataclass
class EstrategiaSim:
    """
    Agrupa todo el estado de UNA estrategia para poder simular dos en paralelo
    (Estrategia A vs Estrategia B) sobre la misma carrera. Contiene los tres modelos
    (continuo, inventario y cola/eventos) más sus parámetros y acumuladores de telemetría.
    """
    nombre: str
    monoplaza: Monoplaza
    inventario: InventarioNeumaticos
    pit_box: PitBoxServidor
    compuesto_inicial: str
    # Mapa vuelta -> {"compuesto", "double_stack", "compuesto_2"} con las paradas programadas
    paradas_por_vuelta: dict = field(default_factory=dict)
    # Acumuladores de la carrera
    tiempo_total_carrera: float = 0.0
    tiempos_paradas: List[float] = field(default_factory=list)
    registro_eventos: List[str] = field(default_factory=list)
    reporte_final_paradas: List[ReporteParada] = field(default_factory=list)


def procesar_vuelta(est: EstrategiaSim, v: int):
    """
    Avanza UNA vuelta de una estrategia: evolución continua del monoplaza, y si toca,
    el evento discreto de parada en boxes (inventario + cola M/M/1 + falla estocástica).
    Actualiza los acumuladores y el log de `est` in-place.
    Retorna (tiempo_vuelta, estado_box_str, estado_box_clase) para el render del panel.
    """
    # 1. EVOLUCIÓN CONTINUA
    tiempo_v = est.monoplaza.avanzar_vuelta(v)
    est.tiempo_total_carrera += tiempo_v

    estado_box_clase = "box-status-libre"
    estado_box_str = "LIBRE"

    # 2. EVENTO DISCRETO Y COLA M/M/1 EN VUELTA PROGRAMADA
    parada = est.paradas_por_vuelta.get(v)
    if parada:
        est.registro_eventos.append(f"🏎️ [VUELTA {v}] ¡BOX BOX! Entrando a Pit Lane para cambio de compuestos.")

        # Verificación de Inventario
        asignado = est.inventario.usar_compuesto(parada["compuesto"])
        compuesto_real = parada["compuesto"] if asignado else "Medio"
        if not asignado:
            est.registro_eventos.append(f"⚠️ [INVENTARIO] No queda stock de compuesto {parada['compuesto']}. Colocando {compuesto_real} por defecto.")

        if parada["double_stack"]:
            estado_box_clase = "box-status-cola"
            estado_box_str = "COLA (DOUBLE STACK)"

            # Descontar también stock del segundo auto
            inv2 = est.inventario.usar_compuesto(parada["compuesto_2"])
            compuesto_real_2 = parada["compuesto_2"] if inv2 else "Duro"

            # Ejecutar Cola M/M/1
            rep1, rep2 = est.pit_box.simular_double_stack(compuesto_real, compuesto_real_2)

            est.tiempos_paradas.append(rep1.tiempo_total_box)
            est.tiempos_paradas.append(rep2.tiempo_total_box)
            est.reporte_final_paradas.extend([rep1, rep2])

            # Log de sucesos
            if rep1.falla_ocurrida:
                estado_box_clase = "box-status-falla"
                estado_box_str = "FALLA EN PIT"
            est.registro_eventos.append(f"⏱️ [BOX AUTO 1] {rep1.mensaje_alerta} (Total Box: {rep1.tiempo_total_box}s)")

            est.registro_eventos.append(f"⏳ [COLA M/M/1] Auto 2 esperó {rep2.tiempo_espera_cola}s en la cola virtual del Pit Box.")
            est.registro_eventos.append(f"⏱️ [BOX AUTO 2] {rep2.mensaje_alerta} (Total Box: {rep2.tiempo_total_box}s)")
        else:
            rep1 = est.pit_box.realizar_parada("Auto 1", compuesto_real)
            est.tiempos_paradas.append(rep1.tiempo_total_box)
            est.reporte_final_paradas.append(rep1)

            estado_box_clase = "box-status-falla" if rep1.falla_ocurrida else "box-status-ocupado"
            estado_box_str = "FALLA MECÁNICA" if rep1.falla_ocurrida else "OCUPADO"

            est.registro_eventos.append(f"⏱️ [BOX] {rep1.mensaje_alerta} (Total Box: {rep1.tiempo_total_box}s)")

        # Aplicar cambio al modelo continuo del Monoplaza
        obj_compuesto = est.inventario.obtener_compuesto(compuesto_real)
        est.monoplaza.colocar_neumaticos(obj_compuesto.nombre, obj_compuesto.color, obj_compuesto.lambda_deg, obj_compuesto.factor_ritmo)
        est.registro_eventos.append(f"🟢 [VUELTA {v}] Monoplaza en pista con {obj_compuesto.nombre} nuevos.")

        # Sumar tiempo de parada (del auto líder) al tiempo de carrera
        est.tiempo_total_carrera += rep1.tiempo_total_box

        # Reflejar la pérdida en boxes en la vuelta del pit stop (solo visualización: el total
        # ya fue sumado arriba). Infla la métrica "Tiempo Vuelta" y el pico del gráfico.
        tiempo_v += rep1.tiempo_total_box
        est.monoplaza.registrar_perdida_box(rep1.tiempo_total_box)

    # Alertas de degradación continua
    if 20.0 < est.monoplaza.grip_actual < 35.0 and v not in est.paradas_por_vuelta:
        est.registro_eventos.append(f"⚠️ [VUELTA {v}] Neumáticos con alta degradación ({round(est.monoplaza.grip_actual, 1)}% Grip). Pérdida de tiempo severa.")

    return tiempo_v, estado_box_str, estado_box_clase


def renderizar_panel(est: EstrategiaSim, v: int, total_vueltas: int, tiempo_v: float,
                     estado_box_str: str, estado_box_clase: str,
                     metric_ph, chart_ph, log_ph):
    """Dibuja el panel de una estrategia: grilla 2x2 de métricas + gráfico + log de telemetría."""
    with metric_ph.container():
        r1c1, r1c2 = st.columns(2)
        r1c1.markdown(renderizar_metrica("Vuelta", f"{v} / {total_vueltas}"), unsafe_allow_html=True)
        r1c2.markdown(renderizar_metrica("Grip Neumático", f"{round(est.monoplaza.grip_actual, 1)}%", color_destaque=est.monoplaza.color_compuesto), unsafe_allow_html=True)
        r2c1, r2c2 = st.columns(2)
        r2c1.markdown(renderizar_metrica("Tiempo Vuelta", f"{round(tiempo_v, 2)}s", color_destaque="#10B981"), unsafe_allow_html=True)
        r2c2.markdown(renderizar_metrica("Estado Box", estado_box_str, extra_class=estado_box_clase), unsafe_allow_html=True)

    chart_ph.plotly_chart(
        dibujar_grafico_telemetria(est.monoplaza.historial, est.nombre),
        use_container_width=True,
        key=f"chart_{est.nombre}_{v}",
    )

    log_html = '<div class="telemetry-log">' + '<br>'.join(est.registro_eventos[::-1]) + '</div>'
    log_ph.markdown(log_html, unsafe_allow_html=True)


def renderizar_reporte_detalle(est: EstrategiaSim):
    """Detalle final de una estrategia: estrategia/grip, paradas en boxes y stock restante."""
    st.subheader(f"🏎️ {est.nombre}")

    c1, c2 = st.columns(2)
    c1.metric("Estrategia Final", f"{est.monoplaza.compuesto_actual}")
    c2.metric("Grip Final en Meta", f"{round(est.monoplaza.grip_actual, 1)}%")

    tiempo_promedio_box = round(sum(est.tiempos_paradas) / len(est.tiempos_paradas), 2) if est.tiempos_paradas else 0.0
    st.metric("Tiempo Promedio en Boxes", f"{tiempo_promedio_box} s", f"{len(est.tiempos_paradas)} paradas simuladas")

    if est.reporte_final_paradas:
        st.markdown("**📋 Detalle de Paradas (M/M/1)**")
        df_paradas = pd.DataFrame([r.__dict__ for r in est.reporte_final_paradas])
        df_paradas = df_paradas.rename(columns={
            "auto_id": "Monoplaza",
            "compuesto_colocado": "Compuesto",
            "tiempo_pit_lane": "Pit Lane (s)",
            "tiempo_servicio_base": "Servicio Base (s)",
            "tiempo_espera_cola": "Espera en Cola (s)",
            "tiempo_falla": "Demora por Tuerca (s)",
            "tiempo_total_box": "Tiempo Total (s)",
            "falla_ocurrida": "Falla Mecánica"
        })[["Monoplaza", "Compuesto", "Pit Lane (s)", "Servicio Base (s)", "Espera en Cola (s)", "Demora por Tuerca (s)", "Tiempo Total (s)", "Falla Mecánica"]]
        st.dataframe(df_paradas, use_container_width=True)

    st.markdown("**📦 Stock Restante**")
    disp = est.inventario.obtener_disponibles()
    col_stk = st.columns(3)
    col_stk[0].metric("Blandos", disp.get("Blando", 0))
    col_stk[1].metric("Medios", disp.get("Medio", 0))
    col_stk[2].metric("Duros", disp.get("Duro", 0))


def inputs_estrategia(prefijo: str, total_vueltas: int, defaults: dict) -> dict:
    """Renderiza los controles de UNA estrategia en la barra lateral y devuelve sus parámetros."""
    estilo = st.selectbox(
        "Estilo de Manejo del Piloto",
        options=[
            "Equilibrado (Ritmo constante)",
            "Conservador (Suave con los neumáticos)",
            "Agresivo (Máximo ataque)"
        ],
        index=defaults["estilo"],
        key=f"{prefijo}_estilo",
        help="Afecta el coeficiente de degradación exponencial (lambda) del neumático."
    )

    st.markdown("**📦 Inventario**")
    col_s, col_m, col_h = st.columns(3)
    stock_soft = col_s.number_input("Blandos", min_value=0, max_value=5, value=defaults["soft"], key=f"{prefijo}_soft")
    stock_medium = col_m.number_input("Medios", min_value=0, max_value=5, value=defaults["medium"], key=f"{prefijo}_medium")
    stock_hard = col_h.number_input("Duros", min_value=0, max_value=5, value=defaults["hard"], key=f"{prefijo}_hard")

    # Compuesto inicial de largada: restringido a compuestos con stock disponible.
    stock = {"Blando": stock_soft, "Medio": stock_medium, "Duro": stock_hard}
    en_stock = [c for c in ["Blando", "Medio", "Duro"] if stock[c] > 0]
    opciones_inicial = en_stock or ["Blando", "Medio", "Duro"]
    default_ini = defaults.get("compuesto_inicial", "Medio")
    idx_ini = opciones_inicial.index(default_ini) if default_ini in opciones_inicial else 0
    compuesto_inicial = st.selectbox(
        "Compuesto Inicial (de Largada)", opciones_inicial, index=idx_ini, key=f"{prefijo}_ini",
        help="Compuesto con el que arranca la carrera. Solo se ofrecen compuestos con stock; descuenta un juego del inventario."
    )

    prob_falla = st.slider(
        "Probabilidad de Falla en Pit Box (%)",
        min_value=0, max_value=30, value=defaults["prob"], step=1,
        key=f"{prefijo}_prob",
        help="Probabilidad estocástica de que la pistola neumática falle (tuerca trabada)."
    ) / 100.0

    # Tabla editable de paradas: cada fila es una parada (vuelta + compuesto + double stack opcional).
    st.markdown("**🔧 Paradas en Boxes** (agregá/quitá filas)")
    df_default = pd.DataFrame(defaults["paradas"], columns=["Vuelta", "Compuesto", "Double Stack", "Compuesto Auto 2"])
    edited = st.data_editor(
        df_default,
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        key=f"{prefijo}_paradas",
        column_config={
            "Vuelta": st.column_config.NumberColumn("Vuelta", min_value=1, max_value=total_vueltas - 1, step=1),
            "Compuesto": st.column_config.SelectboxColumn("Compuesto", options=["Blando", "Medio", "Duro"]),
            "Double Stack": st.column_config.CheckboxColumn("Doble Parada", default=False),
            "Compuesto Auto 2": st.column_config.SelectboxColumn("Comp. Auto 2", options=["Blando", "Medio", "Duro"]),
        },
    )

    # Limpieza: descartar filas sin vuelta válida, deduplicar por vuelta (gana la última) y ordenar.
    paradas = {}
    for _, row in edited.iterrows():
        vuelta = row.get("Vuelta")
        if pd.isna(vuelta):
            continue
        vuelta = int(vuelta)
        if vuelta < 1 or vuelta > total_vueltas - 1:
            continue
        comp = row.get("Compuesto")
        comp = "Medio" if (pd.isna(comp) or not comp) else comp
        comp2 = row.get("Compuesto Auto 2")
        comp2 = "Medio" if (pd.isna(comp2) or not comp2) else comp2
        paradas[vuelta] = {
            "vuelta": vuelta,
            "compuesto": comp,
            "double_stack": bool(row.get("Double Stack", False)),
            "compuesto_2": comp2,
        }
    paradas_lista = [paradas[v] for v in sorted(paradas)]

    return {
        "estilo": estilo,
        "soft": stock_soft, "medium": stock_medium, "hard": stock_hard,
        "prob": prob_falla,
        "compuesto_inicial": compuesto_inicial,
        "paradas": paradas_lista,
    }


def construir_estrategia(nombre: str, cfg: dict, circuito, total_vueltas: int) -> EstrategiaSim:
    """Instancia los modelos de una estrategia a partir de su configuración de sidebar y el circuito."""
    monoplaza = Monoplaza(
        piloto_estilo=cfg["estilo"],
        tiempo_base=circuito.vuelta_base,
        combustible_inicial=total_vueltas * circuito.fuel_por_vuelta,
        consumo_por_vuelta=circuito.fuel_por_vuelta,
    )
    inventario = InventarioNeumaticos(
        stock_blandos=cfg["soft"], stock_medios=cfg["medium"], stock_duros=cfg["hard"],
        lambdas=circuito.lambdas,
    )

    # Compuesto inicial: aplicar su dinámica al monoplaza y descontar el juego del inventario.
    obj_inicial = inventario.obtener_compuesto(cfg["compuesto_inicial"])
    monoplaza.colocar_neumaticos(obj_inicial.nombre, obj_inicial.color, obj_inicial.lambda_deg, obj_inicial.factor_ritmo)
    descontado = inventario.usar_compuesto(cfg["compuesto_inicial"])

    eventos = [f"🟢 [VUELTA 0] Inicio de transmisión. Neumáticos de largada: {obj_inicial.nombre} [100% Grip]."]
    if not descontado:
        eventos.append(f"⚠️ [INVENTARIO] Sin stock de {cfg['compuesto_inicial']} para la largada; se arranca igual (no descontado).")

    # Mapa vuelta -> parada para búsqueda O(1) en el bucle de simulación.
    paradas_por_vuelta = {p["vuelta"]: p for p in cfg["paradas"]}

    return EstrategiaSim(
        nombre=nombre,
        monoplaza=monoplaza,
        inventario=inventario,
        pit_box=PitBoxServidor(prob_falla=cfg["prob"]),
        compuesto_inicial=cfg["compuesto_inicial"],
        paradas_por_vuelta=paradas_por_vuelta,
        registro_eventos=eventos,
    )


def _parada(vuelta, compuesto, ds=False, comp2="Medio"):
    """Helper para definir una fila de parada en los presets/defaults."""
    return {"Vuelta": vuelta, "Compuesto": compuesto, "Double Stack": ds, "Compuesto Auto 2": comp2}


# Configuración por defecto (primera carga = comportamiento previo).
DEFAULT_CFG = {
    "track": "Suzuka", "laps": 25,
    "A": {"estilo": 2, "soft": 2, "medium": 2, "hard": 2, "prob": 5, "compuesto_inicial": "Blando",
          "paradas": [_parada(8, "Medio"), _parada(16, "Duro")]},
    "B": {"estilo": 1, "soft": 2, "medium": 2, "hard": 2, "prob": 5, "compuesto_inicial": "Duro",
          "paradas": [_parada(18, "Medio")]},
}


def _estrat(estilo, ini, paradas, soft=2, medium=2, hard=2, prob=5):
    return {"estilo": estilo, "soft": soft, "medium": medium, "hard": hard, "prob": prob,
            "compuesto_inicial": ini, "paradas": paradas}

# Índices de estilo: 0 Equilibrado · 1 Conservador · 2 Agresivo
# Presets de demo: 2 por circuito, cada uno compara 2 estrategias (A vs B).
PRESETS = [
    {"label": "2 vs 1 parada", "track": "Suzuka", "laps": 20,
     "help": "Suzuka (alta deg): A agresivo a 2 paradas (Blando→Blando→Medio) vs B conservador a 1 parada (Medio→Duro).",
     "A": _estrat(2, "Blando", [_parada(7, "Blando"), _parada(14, "Medio")]),
     "B": _estrat(1, "Medio", [_parada(12, "Duro")])},
    {"label": "Largada B vs D", "track": "Suzuka", "laps": 20,
     "help": "Suzuka: misma parada (vuelta 10 → Medio), pero A larga en Blando (rápido, se degrada) y B en Duro.",
     "A": _estrat(2, "Blando", [_parada(10, "Medio")]),
     "B": _estrat(1, "Duro", [_parada(10, "Medio")])},

    {"label": "Undercut vs Overcut", "track": "Brasil (Interlagos)", "laps": 20,
     "help": "Brasil: ambos Medio→Duro; A para antes (undercut, vuelta 8), B para después (overcut, vuelta 13).",
     "A": _estrat(0, "Medio", [_parada(8, "Duro")]),
     "B": _estrat(0, "Medio", [_parada(13, "Duro")])},
    {"label": "1 vs 2 paradas", "track": "Brasil (Interlagos)", "laps": 25,
     "help": "Brasil: A a 1 parada (Medio→Duro, vuelta 13) vs B a 2 paradas (Blando→Medio→Medio).",
     "A": _estrat(0, "Medio", [_parada(13, "Duro")]),
     "B": _estrat(2, "Blando", [_parada(9, "Medio"), _parada(17, "Medio")])},

    {"label": "Sin parada vs 1", "track": "Mónaco", "laps": 20,
     "help": "Mónaco (baja deg): A sin parar (posición en pista) vs B con 1 parada (Medio→Duro, vuelta 10).",
     "A": _estrat(1, "Medio", []),
     "B": _estrat(0, "Medio", [_parada(10, "Duro")])},
    {"label": "Blando vs Duro", "track": "Mónaco", "laps": 20,
     "help": "Mónaco: A larga en Blando y para 1 vez (vuelta 9 → Medio) vs B larga en Duro y no para.",
     "A": _estrat(0, "Blando", [_parada(9, "Medio")]),
     "B": _estrat(1, "Duro", [])},
]


def aplicar_preset(preset: dict):
    """Callback de los botones de demo: carga el escenario en los widgets (sin auto-correr).
    Bumpea la versión para forzar la reconstrucción de los widgets keyed (incl. la tabla de paradas)."""
    st.session_state["cfg"] = {
        "track": preset["track"], "laps": preset["laps"], "A": preset["A"], "B": preset["B"],
    }
    st.session_state["cfg_v"] = st.session_state.get("cfg_v", 0) + 1


def main():
    st.markdown('<div class="title-header">FÓRMULA 1: COMPARADOR ESTRATÉGICO HÍBRIDO</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-header">Dos Estrategias en Paralelo · Dinámica Continua & Colas Discretas M/M/1 en Tiempo Real</div>', unsafe_allow_html=True)

    # ==========================================
    # CONFIGURACIÓN EN BARRA LATERAL (SIDEBAR)
    # ==========================================
    # Configuración activa (editable por presets de demo mediante versionado de keys).
    st.session_state.setdefault("cfg", DEFAULT_CFG)
    st.session_state.setdefault("cfg_v", 0)
    cfg = st.session_state["cfg"]
    v = st.session_state["cfg_v"]

    with st.sidebar:
        st.header("⚙️ PARÁMETROS DE SIMULACIÓN")

        st.subheader("🌐 Parámetros Compartidos (Misma Carrera)")
        circuitos = list(CIRCUITOS.keys())
        idx_circ = circuitos.index(cfg["track"]) if cfg["track"] in circuitos else 0
        nombre_circuito = st.selectbox("🏁 Circuito", circuitos, index=idx_circ, key=f"circuito_{v}")
        circuito = CIRCUITOS[nombre_circuito]
        total_vueltas = st.slider("Total de Vueltas", min_value=10, max_value=50, value=cfg["laps"], step=5, key=f"tv_{v}")
        retardo_anim = st.slider("Velocidad de Animación (s)", min_value=0.1, max_value=1.5, value=0.5, step=0.1, key="retardo")

        # Sección de solo lectura: parámetros físicos del circuito (no editables).
        combustible_largada = round(total_vueltas * circuito.fuel_por_vuelta, 1)
        lam = circuito.lambdas
        st.markdown(f"""
| 📋 Parámetro del Circuito | Valor |
|:---|:---|
| Degradación del asfalto | **{circuito.categoria_deg}** |
| Tiempo base de vuelta | **{circuito.vuelta_base_label}** ({circuito.vuelta_base:.3f}s) |
| Consumo de combustible | **{circuito.fuel_por_vuelta} kg/vuelta** |
| Combustible de largada | **{combustible_largada} kg** ({total_vueltas} × {circuito.fuel_por_vuelta}) |
| λ Blando / Medio / Duro | **{lam['Blando']} / {lam['Medio']} / {lam['Duro']}** |
""")

        with st.expander("🅰️ ESTRATEGIA A", expanded=True):
            cfg_a = inputs_estrategia(f"a_{v}", total_vueltas, cfg["A"])

        with st.expander("🅱️ ESTRATEGIA B", expanded=True):
            cfg_b = inputs_estrategia(f"b_{v}", total_vueltas, cfg["B"])

        iniciar_btn = st.button("🏁 INICIAR COMPARACIÓN", type="primary", use_container_width=True)

        # ----- Sección de DEMOS (presets) -----
        st.markdown("---")
        st.caption("🎬 Demos · cargan un escenario A vs B (luego presioná INICIAR)")
        for i in range(0, len(PRESETS), 2):
            par = PRESETS[i:i + 2]
            st.caption(f"🏁 {par[0]['track']}")
            cols = st.columns(2)
            for col, preset in zip(cols, par):
                col.button(preset["label"], key=f"preset_{i}_{preset['label']}",
                           help=preset["help"], on_click=aplicar_preset, args=(preset,),
                           use_container_width=True)

    # ==========================================
    # CONTENEDORES DINÁMICOS PRINCIPALES
    # ==========================================
    if "simulacion_activa" not in st.session_state:
        st.session_state["simulacion_activa"] = False

    if iniciar_btn:
        st.session_state["simulacion_activa"] = True

    if not st.session_state["simulacion_activa"]:
        # Vista inicial por defecto
        st.info("👈 Configura los parámetros compartidos y cada estrategia (A / B) en la barra lateral y presiona **'INICIAR COMPARACIÓN'** para correrlas en paralelo.")
        return

    # Instanciación de Modelos (una estrategia por panel)
    est_a = construir_estrategia("Estrategia A", cfg_a, circuito, total_vueltas)
    est_b = construir_estrategia("Estrategia B", cfg_b, circuito, total_vueltas)

    # Placeholders en UI: dos paneles lado a lado
    progreso_barra = st.progress(0)
    col_a, col_b = st.columns(2)
    placeholders = {}
    for col, est in ((col_a, est_a), (col_b, est_b)):
        with col:
            st.markdown(f"<b>{'🅰️' if est is est_a else '🅱️'} {est.nombre.upper()}</b>", unsafe_allow_html=True)
            metric_ph = st.empty()
            chart_ph = st.empty()
            st.markdown("<b>📜 TELEMETRÍA & TRANSMISIÓN RADIAL</b>", unsafe_allow_html=True)
            log_ph = st.empty()
            placeholders[est.nombre] = (metric_ph, chart_ph, log_ph)

    # ==========================================
    # BUCLE DE ANIMACIÓN EN VIVO (AMBAS ESTRATEGIAS EN PARALELO)
    # ==========================================
    for v in range(1, total_vueltas + 1):
        progreso_barra.progress(v / total_vueltas, text=f"Simulando Vuelta {v} de {total_vueltas}...")

        for est in (est_a, est_b):
            tiempo_v, estado_box_str, estado_box_clase = procesar_vuelta(est, v)
            metric_ph, chart_ph, log_ph = placeholders[est.nombre]
            renderizar_panel(est, v, total_vueltas, tiempo_v, estado_box_str, estado_box_clase,
                             metric_ph, chart_ph, log_ph)

        time.sleep(retardo_anim)
        est_a.pit_box.liberar()
        est_b.pit_box.liberar()

    progreso_barra.empty()
    st.success("🏁 **SIMULACIÓN DE CARRERA COMPLETADA**")

    # ==========================================
    # REPORTE Y RESUMEN FINAL — COMPARACIÓN A vs B
    # ==========================================
    st.markdown("---")
    st.header("🏆 REPORTE FINAL — COMPARACIÓN A vs B")

    # Cara a cara: tiempo total y ganador
    ta, tb = est_a.tiempo_total_carrera, est_b.tiempo_total_carrera
    ganador = est_a if ta <= tb else est_b
    delta = round(abs(ta - tb), 1)

    h1, h2, h3 = st.columns(3)
    h1.metric(f"Tiempo {est_a.nombre}", f"{round(ta / 60, 2)} min", f"{round(ta, 1)} s")
    h2.metric(f"Tiempo {est_b.nombre}", f"{round(tb / 60, 2)} min", f"{round(tb, 1)} s")
    h3.metric("🏆 Ganador", ganador.nombre, f"{delta} s más rápido", delta_color="off")

    st.markdown("---")
    rep_col_a, rep_col_b = st.columns(2)
    with rep_col_a:
        renderizar_reporte_detalle(est_a)
    with rep_col_b:
        renderizar_reporte_detalle(est_b)

    st.markdown("---")
    with st.expander("🎓 Explicación Teórica: Variables Continuas & DES"):
        st.markdown(r"""
        ### 🏎️ Modelado de Sistemas Híbridos en la Fórmula 1
        
        Esta aplicación ilustra la convergencia de paradigmas de simulación en sistemas complejos del deporte motor:

        #### 1. Simulación de Variables Continuas (Dinámica de Sistemas)
        - **Ecuaciones de Decaimiento**: El desgaste del neumático ($Grip\%$) evoluciona de manera **continua** y determinística a lo largo del tiempo siguiendo una función exponencial:
          $$G(t) = 100 \cdot e^{-\lambda \cdot K_{piloto} \cdot t}$$
          El caucho sufrirá abrasión y degradación térmica segundo a segundo.
        - **Consumo de Masa**: Paralelamente, la quema de combustible reduce continuamente la masa inercial del monoplaza, compensando parcialmente la degradación del caucho. El consumo por vuelta y el coeficiente de degradación $\lambda$ dependen del **circuito seleccionado** (Suzuka, Brasil o Mónaco), y el combustible de largada es $\text{vueltas} \times \text{consumo}$.

        #### 2. Simulación de Eventos Discretos (DES)
        - **Transiciones Instantáneas**: La decisión de llamar a un auto a boxes ("*Pit Stop*") altera bruscamente el estado del sistema en un instante de tiempo $t_{stop}$.
        - **Estocasticidad (Monte Carlo)**: La ocurrencia de una falla humana o mecánica (como una tuerca cruzada en la pistola neumática) se evalúa mediante un generador de números pseudoaleatorios con probabilidad $P_{falla}$. Su resolución introduce un tiempo de servicio distribuido uniformemente $U(4, 10)$.
        - **Pérdida en Pit Lane**: Cada parada incurre además en el tiempo perdido al recorrer el pit lane a velocidad limitada (vs. seguir en pista), modelado como una variable aleatoria uniforme $\Delta T_{pitlane} \sim U(18, 22)$ s generada por Monte Carlo en cada parada. Este es el verdadero costo estratégico de parar en boxes.

        #### 3. Teoría de Colas (M/M/1) y "*Double Stacking*"
        - El Pit Box actúa como un **servidor único**.
        - Cuando un equipo llama a sus dos pilotos en la misma vuelta bajo régimen de *Safety Car* o estrategia combinada, se produce contención.
        - El Auto 2 ingresa a la cola virtual, experimentando un tiempo de espera en cola ($W_q$) exactamente igual al tiempo de servicio remanente del Auto 1 ($S_1$), lo que ilustra el costo estratégico del *Double Stack*.
        """)

if __name__ == "__main__":
    main()
