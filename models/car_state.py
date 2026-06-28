import math
from typing import List, Dict, Any

class Monoplaza:
    """
    COMPONENTE CONTINUO (Dinámica de Sistemas):
    Simula las variables continuas del monoplaza en pista:
    1. Desgaste del Neumático (Grip %): Cae exponencialmente en función del tiempo/vueltas del stint.
    2. Combustible (kg): Disminuye de forma lineal/continua, aligerando el peso del vehículo.
    3. Tiempo de Vuelta (s): Depende continuamente de la interacción entre la caída del Grip (empeora el tiempo)
       y el aligeramiento del combustible (mejora el tiempo).
    """
    def __init__(self, piloto_estilo: str = "Equilibrado", combustible_inicial: float = 100.0,
                 tiempo_base: float = 82.0, consumo_por_vuelta: float = 1.85):
        self.piloto_estilo = piloto_estilo
        self.combustible = combustible_inicial
        self.combustible_inicial = combustible_inicial
        self.tiempo_base = tiempo_base
        self.consumo_por_vuelta = consumo_por_vuelta
        
        # Multiplicador de degradación según la agresividad del piloto
        self.estilos_multiplicador = {
            "Conservador (Suave con los neumáticos)": 0.75,
            "Equilibrado (Ritmo constante)": 1.0,
            "Agresivo (Máximo ataque)": 1.35
        }
        self.k_manejo = self.estilos_multiplicador.get(piloto_estilo, 1.0)
        
        # Estado actual del neumático
        self.compuesto_actual = "Medio"
        self.color_compuesto = "#FFD700"
        self.lambda_deg = 0.035
        self.factor_ritmo = 1.0   # Ritmo del compuesto en nuevo (Blando<Medio<Duro en tiempo)
        self.vueltas_en_stint = 0
        self.grip_actual = 100.0
        
        # Historial de telemetría continua para graficación
        self.historial: List[Dict[str, Any]] = []

    def colocar_neumaticos(self, compuesto_nombre: str, color: str, lambda_deg: float, factor_ritmo: float = 1.0):
        """Reinicia el estado del neumático al cambiar en boxes."""
        self.compuesto_actual = compuesto_nombre
        self.color_compuesto = color
        self.lambda_deg = lambda_deg
        self.factor_ritmo = factor_ritmo
        self.vueltas_en_stint = 0
        self.grip_actual = 100.0

    def registrar_perdida_box(self, segundos: float):
        """Suma la pérdida de tiempo en boxes a la última vuelta registrada (la del pit stop),
        para que el gráfico de telemetría refleje el pico de tiempo en esa vuelta."""
        if self.historial:
            self.historial[-1]["Tiempo Vuelta (s)"] = round(self.historial[-1]["Tiempo Vuelta (s)"] + segundos, 3)

    def avanzar_vuelta(self, num_vuelta: int) -> float:
        """
        Evoluciona las ecuaciones diferenciales/continuas durante una vuelta:
        - Grip: G(t) = 100 * exp(-lambda * k * t)
        - Combustible: Disminuye continuamente
        - Tiempo de Vuelta: T(t) = T_base + alfa * perdida_grip - beta * perdida_peso
        """
        self.vueltas_en_stint += 1
        
        # 1. Componente Continuo Exponencial de Grip
        tasa_efectiva = self.lambda_deg * self.k_manejo
        self.grip_actual = 100.0 * math.exp(-tasa_efectiva * self.vueltas_en_stint)
        self.grip_actual = max(10.0, self.grip_actual) # Límite inferior físico de caucho
        
        # 2. Componente Continuo Lineal de Combustible (consumo por vuelta según el circuito)
        consumo = self.consumo_por_vuelta
        self.combustible = max(1.0, self.combustible - consumo)
        
        # 3. Interacción en el Tiempo de Vuelta
        perdida_grip = 100.0 - self.grip_actual
        combustible_quemado = self.combustible_inicial - self.combustible
        
        # El ritmo base se escala por el compuesto (Blando más rápido, Duro más lento en nuevo).
        # +0.14s por cada 1% de grip perdido, -0.038s por cada kg de combustible aligerado
        tiempo_vuelta = (self.tiempo_base * self.factor_ritmo) + (0.14 * perdida_grip) - (0.038 * combustible_quemado)
        
        # Guardar en telemetría
        self.historial.append({
            "Vuelta": num_vuelta,
            "Grip (%)": round(self.grip_actual, 1),
            "Combustible (kg)": round(self.combustible, 1),
            "Tiempo Vuelta (s)": round(tiempo_vuelta, 3),
            "Compuesto": self.compuesto_actual,
            "Color": self.color_compuesto
        })
        
        return tiempo_vuelta

    def obtener_estimacion(self) -> float:
        """Calcula el tiempo estimado para la vuelta en curso."""
        perdida_grip = 100.0 - self.grip_actual
        combustible_quemado = self.combustible_inicial - self.combustible
        return (self.tiempo_base * self.factor_ritmo) + (0.14 * perdida_grip) - (0.038 * combustible_quemado)
