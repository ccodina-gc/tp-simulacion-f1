from dataclasses import dataclass
from typing import Dict


@dataclass
class Circuito:
    """
    COMPONENTE DE CIRCUITO (Parámetros compartidos de la carrera):
    Define las constantes físicas de la pista que afectan a AMBAS estrategias por igual:
    - vuelta_base: tiempo óptimo de vuelta (s) usado como base del modelo continuo.
    - fuel_por_vuelta: consumo de combustible por vuelta (kg). El combustible de largada
      se calcula como total_vueltas * fuel_por_vuelta.
    - lambdas: coeficiente de degradación continua (1/vuelta) por compuesto, según el nivel
      de abrasividad del asfalto del circuito.
    """
    nombre: str
    categoria_deg: str          # "Alta", "Media", "Baja"
    vuelta_base: float          # segundos
    vuelta_base_label: str      # formato mm:ss.mmm (ej. "1:36.527")
    fuel_por_vuelta: float      # kg por vuelta
    lambdas: Dict[str, float]   # {"Blando", "Medio", "Duro"}


# Catálogo de circuitos disponibles en el simulador.
CIRCUITOS: Dict[str, Circuito] = {
    "Suzuka": Circuito(
        nombre="Suzuka",
        categoria_deg="Alta",
        vuelta_base=96.527,
        vuelta_base_label="1:36.527",
        fuel_por_vuelta=1.92,
        lambdas={"Blando": 0.110, "Medio": 0.065, "Duro": 0.025},
    ),
    "Brasil (Interlagos)": Circuito(
        nombre="Brasil (Interlagos)",
        categoria_deg="Media",
        vuelta_base=74.020,
        vuelta_base_label="1:14.020",
        fuel_por_vuelta=1.38,
        lambdas={"Blando": 0.075, "Medio": 0.040, "Duro": 0.015},
    ),
    "Mónaco": Circuito(
        nombre="Mónaco",
        categoria_deg="Baja",
        vuelta_base=79.713,
        vuelta_base_label="1:19.713",
        fuel_por_vuelta=1.15,
        lambdas={"Blando": 0.020, "Medio": 0.008, "Duro": 0.002},
    ),
}
