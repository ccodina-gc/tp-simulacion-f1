import random
from typing import Tuple
from dataclasses import dataclass

@dataclass
class ReporteParada:
    auto_id: str
    compuesto_colocado: str
    tiempo_servicio_base: float
    tiempo_pit_lane: float
    tiempo_espera_cola: float
    tiempo_falla: float
    tiempo_total_box: float
    falla_ocurrida: bool
    mensaje_alerta: str


class PitBoxServidor:
    """
    COMPONENTE DE COLAS (M/M/1) Y EVENTOS DISCRETOS (Fallas Estocásticas):
    - M/M/1: El Pit Box es un servidor único. Si llegan dos autos del mismo equipo
      (Double Stacking), el segundo experimenta una espera en cola virtual.
    - Fallas: En cada parada se evalúa mediante Monte Carlo si ocurre una traba
      en la tuerca (pistola neumática), añadiendo un tiempo distribuido Uniforme(4, 10)s.
    """
    def __init__(self, prob_falla: float = 0.05):
        self.prob_falla = prob_falla # Probabilidad estocástica de falla (0.0 a 1.0)
        self.ocupado = False
        self.estado_box = "Libre"    # Libre, Ocupado, Doble Parada (Cola), Falla Mecánica

    def realizar_parada(self, auto_id: str, compuesto_nombre: str, tiempo_espera_previo: float = 0.0) -> ReporteParada:
        """
        Ejecuta el evento discreto de servicio de Pit Stop para un monoplaza.
        """
        self.ocupado = True
        self.estado_box = "Ocupado"
        
        tiempo_base = round(random.uniform(2.2, 2.8), 2) # Servicio óptimo normal de F1 (auto detenido)

        # Pérdida en pit lane: tiempo perdido recorriendo el pit lane a velocidad limitada
        # (vs. seguir en pista). Generado por Monte Carlo igual que el cambio de neumáticos.
        tiempo_pit_lane = round(random.uniform(18.0, 22.0), 2) # Distribución Uniforme(18, 22)

        falla = False
        tiempo_falla = 0.0
        mensaje = f"Parada de {tiempo_base}s en boxes (+{tiempo_pit_lane}s de pit lane) para colocar {compuesto_nombre}."

        # Tirada estocástica (Monte Carlo) para falla de pistola neumática
        if random.random() < self.prob_falla:
            falla = True
            self.estado_box = "Falla Mecánica"
            # Distribución Uniforme entre 4 y 10 segundos adicionales de demora
            tiempo_falla = round(random.uniform(4.0, 10.0), 2)
            mensaje = f"¡ALERTA! Tuerca trabada en pistola neumática. Demora extra de +{tiempo_falla}s."

        tiempo_total = round(tiempo_base + tiempo_pit_lane + tiempo_espera_previo + tiempo_falla, 2)

        return ReporteParada(
            auto_id=auto_id,
            compuesto_colocado=compuesto_nombre,
            tiempo_servicio_base=tiempo_base,
            tiempo_pit_lane=tiempo_pit_lane,
            tiempo_espera_cola=tiempo_espera_previo,
            tiempo_falla=tiempo_falla,
            tiempo_total_box=tiempo_total,
            falla_ocurrida=falla,
            mensaje_alerta=mensaje
        )

    def simular_double_stack(self, compuesto_auto1: str, compuesto_auto2: str) -> Tuple[ReporteParada, ReporteParada]: # type: ignore
        """
        Simula el ingreso simultáneo de dos autos del equipo (Cola M/M/1).
        El Auto 2 debe esperar a que finalice el servicio del Auto 1.
        """
        self.estado_box = "Doble Parada (Cola)"
        
        # Atendemos primero al Auto 1 (Líder en pista)
        rep1 = self.realizar_parada("Auto 1 (Líder)", compuesto_auto1, tiempo_espera_previo=0.0)
        
        # El Auto 2 sólo espera a que se libere el servidor (el box físico): servicio + falla.
        # NO incluye el pit lane, que cada auto recorre por su cuenta (no es ocupación del box).
        espera_auto2 = round(rep1.tiempo_servicio_base + rep1.tiempo_falla, 2)
        
        # Atendemos al Auto 2
        rep2 = self.realizar_parada("Auto 2 (Escudero)", compuesto_auto2, tiempo_espera_previo=espera_auto2)
        
        self.ocupado = False
        self.estado_box = "Libre"
        return rep1, rep2

    def liberar(self):
        self.ocupado = False
        self.estado_box = "Libre"
