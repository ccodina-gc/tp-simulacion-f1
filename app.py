import time
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from models.car_state import Monoplaza
from models.inventory import InventarioNeumaticos
from models.pit_box import PitBoxServidor, ReporteParada

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


def dibujar_grafico_telemetria(historial: list):
    """
    Renderiza el gráfico interactivo en tiempo real con Plotly.
    Muestra la curva continua de degradación del neumático vs las vueltas
    y el tiempo de vuelta en un eje secundario.
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

    fig.update_layout(
        template="plotly_dark",
        title="<b>TELEMETRÍA EN VIVO: DEGRADACIÓN CONTINUA VS TIEMPO DE VUELTA</b>",
        title_font_size=18,
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


def main():
    st.markdown('<div class="title-header">FÓRMULA 1: SIMULADOR ESTRATÉGICO HÍBRIDO</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-header">Modelado de Sistemas Dinámicos Continuos & Colas Discretas M/M/1 en Tiempo Real</div>', unsafe_allow_html=True)

    # ==========================================
    # CONFIGURACIÓN EN BARRA LATERAL (SIDEBAR)
    # ==========================================
    with st.sidebar:
        st.header("⚙️ PARÁMETROS DE SIMULACIÓN")
        
        st.subheader("🏎️ 1. Dinámica Continua")
        estilo_piloto = st.selectbox(
            "Estilo de Manejo del Piloto",
            options=[
                "Equilibrado (Ritmo constante)",
                "Conservador (Suave con los neumáticos)",
                "Agresivo (Máximo ataque)"
            ],
            index=0,
            help="Afecta el coeficiente de degradación exponencial (lambda) del neumático."
        )
        
        tiempo_base = st.slider("Tiempo Base Óptimo de Vuelta (s)", min_value=70.0, max_value=100.0, value=82.0, step=0.5)

        st.subheader("📦 2. Inventario de Garaje")
        col_s, col_m, col_h = st.columns(3)
        stock_soft = col_s.number_input("Blandos", min_value=0, max_value=5, value=2)
        stock_medium = col_m.number_input("Medios", min_value=0, max_value=5, value=2)
        stock_hard = col_h.number_input("Duros", min_value=0, max_value=5, value=2)

        st.subheader("🔧 3. Eventos Discretos y Colas")
        prob_falla = st.slider(
            "Probabilidad de Falla en Pit Box (%)", 
            min_value=0, max_value=30, value=5, step=1,
            help="Probabilidad estocástica de que la pistola neumática falle (tuerca trabada)."
        ) / 100.0

        st.subheader("📊 4. Estrategia de Carrera")
        total_vueltas = st.slider("Total de Vueltas", min_value=10, max_value=50, value=25, step=5)
        vuelta_parada = st.slider("Vuelta de Parada en Boxes", min_value=1, max_value=total_vueltas-1, value=12)
        compuesto_parada = st.selectbox("Compuesto a Colocar (Auto 1)", ["Duro", "Medio", "Blando"], index=0)

        double_stack = st.checkbox(
            "Simular Doble Parada (Double Stacking M/M/1)", 
            value=False,
            help="Simula la entrada simultánea del Auto 2 (Compañero) en la misma vuelta, obligándolo a esperar en cola."
        )
        compuesto_parada_2 = "Medio"
        if double_stack:
            compuesto_parada_2 = st.selectbox("Compuesto a Colocar (Auto 2 - Escudero)", ["Duro", "Medio", "Blando"], index=1)

        retardo_anim = st.slider("Velocidad de Animación (s)", min_value=0.1, max_value=1.5, value=0.5, step=0.1)

        iniciar_btn = st.button("🏁 INICIAR CARRERA EN VIVO", type="primary", use_container_width=True)

    # ==========================================
    # CONTENEDORES DINÁMICOS PRINCIPALES
    # ==========================================
    if "simulacion_activa" not in st.session_state:
        st.session_state["simulacion_activa"] = False

    if iniciar_btn:
        st.session_state["simulacion_activa"] = True

    if not st.session_state["simulacion_activa"]:
        # Vista inicial por defecto
        st.info("👈 Configura los parámetros en la barra lateral y presiona **'INICIAR CARRERA EN VIVO'** para comenzar la simulación animada.")
        return

    # Instanciación de Modelos
    monoplaza = Monoplaza(piloto_estilo=estilo_piloto, tiempo_base=tiempo_base)
    inventario = InventarioNeumaticos(stock_blandos=stock_soft, stock_medios=stock_medium, stock_duros=stock_hard)
    pit_box = PitBoxServidor(prob_falla=prob_falla)

    # Placeholders en UI
    progreso_barra = st.progress(0)
    grid_metricas = st.empty()
    col_grafico, col_log = st.columns([6, 4])
    
    with col_grafico:
        grafico_placeholder = st.empty()
    with col_log:
        st.markdown("<b>📜 TELEMETRÍA & TRANSMISIÓN RADIAL</b>", unsafe_allow_html=True)
        log_placeholder = st.empty()

    registro_eventos = []
    registro_eventos.append(f"🟢 [VUELTA 0] Inicio de transmisión. Neumáticos iniciales: Medio [100% Grip].")

    tiempo_total_carrera = 0.0
    tiempos_paradas = []
    reporte_final_paradas = []

    # ==========================================
    # BUCLE DE ANIMACIÓN EN VIVO (SIMULACIÓN)
    # ==========================================
    for v in range(1, total_vueltas + 1):
        # Actualización de progreso
        progreso_barra.progress(v / total_vueltas, text=f"Simulando Vuelta {v} de {total_vueltas}...")

        # 1. EVOLUCIÓN CONTINUA
        tiempo_v = monoplaza.avanzar_vuelta(v)
        tiempo_total_carrera += tiempo_v

        estado_box_clase = "box-status-libre"
        estado_box_str = "LIBRE"

        # 2. EVENTO DISCRETO Y COLA M/M/1 EN VUELTA PROGRAMADA
        if v == vuelta_parada:
            registro_eventos.append(f"🏎️ [VUELTA {v}] ¡BOX BOX! Entrando a Pit Lane para cambio de compuestos.")
            
            # Verificación de Inventario
            asignado = inventario.usar_compuesto(compuesto_parada)
            compuesto_real = compuesto_parada if asignado else "Medio"
            if not asignado:
                registro_eventos.append(f"⚠️ [INVENTARIO] No queda stock de compuesto {compuesto_parada}. Colocando {compuesto_real} por defecto.")

            if double_stack:
                estado_box_clase = "box-status-cola"
                estado_box_str = "COLA (DOUBLE STACK)"
                
                # Descontar también stock del segundo auto
                inv2 = inventario.usar_compuesto(compuesto_parada_2)
                compuesto_real_2 = compuesto_parada_2 if inv2 else "Duro"

                # Ejecutar Cola M/M/1
                rep1, rep2 = pit_box.simular_double_stack(compuesto_real, compuesto_real_2)
                
                tiempos_paradas.append(rep1.tiempo_total_box)
                tiempos_paradas.append(rep2.tiempo_total_box)
                reporte_final_paradas.extend([rep1, rep2])

                # Log de sucesos
                if rep1.falla_ocurrida:
                    estado_box_clase = "box-status-falla"
                    estado_box_str = "FALLA EN PIT"
                registro_eventos.append(f"⏱️ [BOX AUTO 1] {rep1.mensaje_alerta} (Total Box: {rep1.tiempo_total_box}s)")
                
                registro_eventos.append(f"⏳ [COLA M/M/1] Auto 2 esperó {rep2.tiempo_espera_cola}s en la cola virtual del Pit Box.")
                registro_eventos.append(f"⏱️ [BOX AUTO 2] {rep2.mensaje_alerta} (Total Box: {rep2.tiempo_total_box}s)")
            else:
                rep1 = pit_box.realizar_parada("Auto 1", compuesto_real)
                tiempos_paradas.append(rep1.tiempo_total_box)
                reporte_final_paradas.append(rep1)
                
                estado_box_clase = "box-status-falla" if rep1.falla_ocurrida else "box-status-ocupado"
                estado_box_str = "FALLA MECÁNICA" if rep1.falla_ocurrida else "OCUPADO"
                
                registro_eventos.append(f"⏱️ [BOX] {rep1.mensaje_alerta} (Total Box: {rep1.tiempo_total_box}s)")

            # Aplicar cambio al modelo continuo del Monoplaza
            obj_compuesto = inventario.obtener_compuesto(compuesto_real)
            monoplaza.colocar_neumaticos(obj_compuesto.nombre, obj_compuesto.color, obj_compuesto.lambda_deg)
            registro_eventos.append(f"🟢 [VUELTA {v}] Monoplaza en pista con {obj_compuesto.nombre} nuevos.")
            
            # Sumar tiempo de parada al tiempo de carrera
            tiempo_total_carrera += rep1.tiempo_total_box

        # Alertas de degradación continua
        if 20.0 < monoplaza.grip_actual < 35.0 and v != vuelta_parada:
            registro_eventos.append(f"⚠️ [VUELTA {v}] Neumáticos con alta degradación ({round(monoplaza.grip_actual, 1)}% Grip). Pérdida de tiempo severa.")

        # RENDERIZAR MÉTRICAS DINÁMICAS EN VIVO
        with grid_metricas.container():
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(renderizar_metrica("Vuelta", f"{v} / {total_vueltas}"), unsafe_allow_html=True)
            with col2:
                st.markdown(renderizar_metrica("Grip Neumático", f"{round(monoplaza.grip_actual, 1)}%", color_destaque=monoplaza.color_compuesto), unsafe_allow_html=True)
            with col3:
                st.markdown(renderizar_metrica("Combustible", f"{round(monoplaza.combustible, 1)} kg", color_destaque="#38BDF8"), unsafe_allow_html=True)
            with col4:
                st.markdown(renderizar_metrica("Tiempo Vuelta", f"{round(tiempo_v, 2)}s", color_destaque="#10B981"), unsafe_allow_html=True)
            with col5:
                st.markdown(renderizar_metrica("Estado Box", estado_box_str, extra_class=estado_box_clase), unsafe_allow_html=True)

        # ACTUALIZAR GRÁFICO EN VIVO
        fig_actual = dibujar_grafico_telemetria(monoplaza.historial)
        grafico_placeholder.plotly_chart(fig_actual, use_container_width=True)

        # ACTUALIZAR LOG DE TELEMETRÍA
        log_html = '<div class="telemetry-log">' + '<br>'.join(registro_eventos[::-1]) + '</div>'
        log_placeholder.markdown(log_html, unsafe_allow_html=True)

        time.sleep(retardo_anim)
        pit_box.liberar()

    progreso_barra.empty()
    st.success("🏁 **SIMULACIÓN DE CARRERA COMPLETADA**")

    # ==========================================
    # REPORTE Y RESUMEN FINAL DE CARRERA
    # ==========================================
    st.markdown("---")
    st.header("🏆 REPORTE FINAL")
    
    t1, t2, t3 = st.tabs(["📊 Resumen General de Carrera", "📦 Inventario Final", "🎓 Explicación Teórica: Variables Continuas & DES"])
    
    with t1:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Tiempo Total de Carrera", f"{round(tiempo_total_carrera / 60, 2)} min", f"{round(tiempo_total_carrera, 1)} seg")
        
        tiempo_promedio_box = round(sum(tiempos_paradas)/len(tiempos_paradas), 2) if tiempos_paradas else 0.0
        c2.metric("Tiempo Promedio en Boxes", f"{tiempo_promedio_box} s", f"{len(tiempos_paradas)} paradas simuladas")
        
        c3.metric("Estrategia Final", f"-> {monoplaza.compuesto_actual}")
        c4.metric("Grip Final en Meta", f"{round(monoplaza.grip_actual, 1)}%")

        if reporte_final_paradas:
            st.subheader("📋 Detalle de Paradas en Boxes (M/M/1)")
            df_paradas = pd.DataFrame([r.__dict__ for r in reporte_final_paradas])
            df_paradas = df_paradas.rename(columns={
                "auto_id": "Monoplaza",
                "compuesto_colocado": "Compuesto",
                "tiempo_servicio_base": "Servicio Base (s)",
                "tiempo_espera_cola": "Espera en Cola (s)",
                "tiempo_falla": "Demora por Tuerca (s)",
                "tiempo_total_box": "Tiempo Total (s)",
                "falla_ocurrida": "Falla Mecánica"
            })[["Monoplaza", "Compuesto", "Servicio Base (s)", "Espera en Cola (s)", "Demora por Tuerca (s)", "Tiempo Total (s)", "Falla Mecánica"]]
            st.dataframe(df_paradas, use_container_width=True)

    with t2:
        st.subheader("📦 Stock Restante en Garaje tras la Carrera")
        disp = inventario.obtener_disponibles()
        col_stk = st.columns(3)
        col_stk[0].metric("Juegos Blandos Restantes", disp.get("Blando", 0))
        col_stk[1].metric("Juegos Medios Restantes", disp.get("Medio", 0))
        col_stk[2].metric("Juegos Duros Restantes", disp.get("Duro", 0))

    with t3:
        st.markdown(r"""
        ### 🏎️ Modelado de Sistemas Híbridos en la Fórmula 1
        
        Esta aplicación ilustra la convergencia de paradigmas de simulación en sistemas complejos del deporte motor:

        #### 1. Simulación de Variables Continuas (Dinámica de Sistemas)
        - **Ecuaciones de Decaimiento**: El desgaste del neumático ($Grip\%$) evoluciona de manera **continua** y determinística a lo largo del tiempo siguiendo una función exponencial:
          $$G(t) = 100 \cdot e^{-\lambda \cdot K_{piloto} \cdot t}$$
          El caucho sufrirá abrasión y degradación térmica segundo a segundo.
        - **Consumo de Masa**: Paralelamente, la quema de combustible reduce continuamente la masa inercial del monoplaza, compensando parcialmente la degradación del caucho.

        #### 2. Simulación de Eventos Discretos (DES)
        - **Transiciones Instantáneas**: La decisión de llamar a un auto a boxes ("*Pit Stop*") altera bruscamente el estado del sistema en un instante de tiempo $t_{stop}$.
        - **Estocasticidad (Monte Carlo)**: La ocurrencia de una falla humana o mecánica (como una tuerca cruzada en la pistola neumática) se evalúa mediante un generador de números pseudoaleatorios con probabilidad $P_{falla}$. Su resolución introduce un tiempo de servicio distribuido uniformemente $U(4, 10)$.

        #### 3. Teoría de Colas (M/M/1) y "*Double Stacking*"
        - El Pit Box actúa como un **servidor único**.
        - Cuando un equipo llama a sus dos pilotos en la misma vuelta bajo régimen de *Safety Car* o estrategia combinada, se produce contención.
        - El Auto 2 ingresa a la cola virtual, experimentando un tiempo de espera en cola ($W_q$) exactamente igual al tiempo de servicio remanente del Auto 1 ($S_1$), lo que ilustra el costo estratégico del *Double Stack*.
        """)

if __name__ == "__main__":
    main()
