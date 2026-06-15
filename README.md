# 🏁 F1 Live Strategy Simulator - Simulación de Sistemas Híbridos
### Trabajo Práctico Grupal - Materia: Simulación de Sistemas
#### Universidad del Centro de Estudios Macroeconómicos de Argentina (UCEMA)

Este proyecto consiste en un simulador interactivo en tiempo real desarrollado en Python utilizando la librería **Streamlit** y gráficos interactivos con **Plotly**. El objetivo principal es modelar y analizar el comportamiento dinámico de una estrategia de carrera de Fórmula 1, combinando componentes de simulación continua, eventos discretos y teoría de colas.

---

## 🏛️ Estructura de la Simulación Híbrida

En el deporte motor moderno, el rendimiento del vehículo y las operaciones en boxes son ejemplos clásicos de sistemas híbridos donde coexisten procesos de cambio constante y eventos abruptos:

### 1. Componente Continuo (Dinámica de Sistemas)
* **Degradación del Neumático ($Grip\,\%$)**: El porcentaje de agarre inyectado en pista disminuye de forma continua según una función de decaimiento exponencial:
  $$G(t) = 100 \cdot e^{-\lambda \cdot K_{piloto} \cdot t}$$
  Donde la tasa de desgaste $\lambda$ cambia según el compuesto seleccionado (Blando, Medio, Duro) y el estilo de conducción del piloto ($K_{piloto}$).
* **Consumo de Combustible**: Disminuye de forma lineal a una tasa aproximada de $1.85 \text{ kg}$ por vuelta, aligerando el peso total del auto.
* **Tiempo de Vuelta ($T_{vuelta}$)**: Se modela continuamente equilibrando la pérdida de agarre (que penaliza el tiempo) y el consumo de combustible (que mejora el tiempo por reducción de masa).

### 2. Componente de Colas (Servidor M/M/1 - Double Stacking)
* El **Pit Box** se comporta como un servidor de canal único.
* La simulación contempla la llegada concurrente del segundo auto del equipo (Double Stacking) en la misma vuelta bajo condiciones de parada. Si el Auto 1 está ocupando los boxes, el Auto 2 ingresa en una cola de espera virtual aumentando su tiempo total de parada.

### 3. Componente de Fallas (Eventos Discretos - Simulación de Monte Carlo)
* En cada parada, se genera un evento discreto con una probabilidad estocástica ajustable de falla humana/mecánica (ej. pistola neumática trabada).
* Si ocurre la falla, se calcula una demora estocástica distribuida uniformemente:
  $$\Delta T_{falla} \sim \text{Uniforme}(4.0, 10.0) \text{ segundos}$$

### 4. Componente de Inventario
* El garaje cuenta con un stock limitado de compuestos de neumáticos (Blandos, Medios, Duros). Cada parada en boxes descuenta una unidad del stock seleccionado del inventario, determinando las ecuaciones diferenciales de desgaste para las siguientes vueltas.

---

## 📁 Estructura del Proyecto

El código está estructurado de manera modular y limpia en el siguiente árbol de directorios:

```text
tp-simulacion/
├── app.py                # Interfaz principal Streamlit y bucle de animación
├── models/
│   ├── __init__.py
│   ├── car_state.py      # Ecuaciones dinámicas y continuas del monoplaza
│   ├── pit_box.py        # Servidor de cola M/M/1 y fallas estocásticas
│   └── inventory.py      # Control de stock e inventario de compuestos
├── requirements.txt      # Dependencias del entorno de simulación
└── README.md             # Documentación del Trabajo Práctico (UCEMA)
```

---

## 🚀 Instalación y Ejecución

Sigue estos pasos para levantar la simulación interactiva localmente:

### 1. Clonar o acceder al repositorio
Asegúrate de estar en el directorio del proyecto:
```bash
cd /usr/local/google/home/camilacodina/Desktop/tp-simulacion
```

### 2. Instalar dependencias
Se recomienda utilizar un entorno virtual de Python. Puedes instalar los paquetes requeridos directamente usando:
```bash
pip install -r requirements.txt
```

### 3. Ejecutar la aplicación de Streamlit
Inicia el servidor local de visualización:
```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador web (por defecto en `http://localhost:8501`).

---

## 🛠️ Tecnologías Utilizadas

* **Python 3.10+** como lenguaje de programación principal.
* **Streamlit** para la interfaz web interactiva en vivo.
* **Plotly** para el gráfico dinámico de telemetría y degradación continua en tiempo real.
* **Pandas & NumPy** para la manipulación matemática de datos de series temporales de vueltas.
