from dataclasses import dataclass
from typing import Dict, Tuple

@dataclass
class Compuesto:
    nombre: str
    color: str
    lambda_deg: float          # Coeficiente de degradación continua exponencial (1/vuelta)
    factor_ritmo: float = 1.0  # Factor de ritmo en neumático nuevo (Blando más rápido que Duro)
    grip_inicial: float = 100.0


class InventarioNeumaticos:
    """
    COMPONENTE DE INVENTARIO:
    Gestiona el stock limitado de juegos de neumáticos disponibles en el garaje.
    Cada elección altera la tasa de desgaste continua (lambda) para las siguientes vueltas.
    """
    def __init__(self, stock_blandos: int = 2, stock_medios: int = 2, stock_duros: int = 2,
                 lambdas: Dict[str, float] = None):
        self.stock = {
            "Blando": stock_blandos,
            "Medio": stock_medios,
            "Duro": stock_duros
        }

        # Coeficientes de degradación: provistos por el circuito; si no, valores por defecto.
        lam = lambdas or {"Blando": 0.060, "Medio": 0.035, "Duro": 0.018}

        # Definición de las propiedades físicas y estéticas de los compuestos.
        # factor_ritmo: ritmo en neumático nuevo respecto al Medio (±0.5% por escalón).
        self.compuestos = {
            "Blando": Compuesto(
                nombre="Blando (Soft)",
                color="#FF3333",            # Rojo característico F1
                lambda_deg=lam["Blando"],   # Degradación veloz
                factor_ritmo=0.995          # 0.5% más rápido que el Medio
            ),
            "Medio": Compuesto(
                nombre="Medio (Medium)",
                color="#FFD700",            # Amarillo F1
                lambda_deg=lam["Medio"],    # Degradación moderada
                factor_ritmo=1.000          # Ritmo de referencia (tiempo base del circuito)
            ),
            "Duro": Compuesto(
                nombre="Duro (Hard)",
                color="#FFFFFF",            # Blanco F1
                lambda_deg=lam["Duro"],     # Degradación lenta
                factor_ritmo=1.005          # 0.5% más lento que el Medio
            )
        }

    def hay_stock(self, tipo: str) -> bool:
        """Verifica si queda al menos un juego del compuesto solicitado."""
        return self.stock.get(tipo, 0) > 0

    def usar_compuesto(self, tipo: str) -> bool:
        """
        Intenta asignar un juego de neumáticos del stock.
        Retorna True si fue exitoso, False si no hay stock.
        """
        if self.hay_stock(tipo):
            self.stock[tipo] -= 1
            return True
        return False

    def obtener_compuesto(self, tipo: str) -> Compuesto:
        """Retorna el objeto Compuesto con su coeficiente de degradación."""
        return self.compuestos.get(tipo, self.compuestos["Medio"])

    def obtener_disponibles(self) -> Dict[str, int]:
        """Devuelve el estado actual del stock en boxes."""
        return self.stock
