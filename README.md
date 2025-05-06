# 🌍 Bot de Recomendación de Mercados de Exportación

Este proyecto te ayuda a descubrir **cuáles países tienen mayor potencial para que exportes tu producto**, basándose en datos confiables y criterios estratégicos. ¿Cómo lo hace? Te lo explicamos paso a paso:

---

## 📊 ¿Qué analiza el bot para recomendar un país?

Cada país es evaluado según seis indicadores clave que influyen directamente en su atractivo como destino de exportación:

| Indicador | ¿Qué mide? | Peso en el cálculo |
|----------|-------------|-------------------|
| 💵 **Tamaño del Mercado (USD)** | Qué tan grande es el mercado total del país. | 30% |
| 📈 **Crecimiento del PIB (%)** | Qué tan rápido está creciendo la economía. | 15% |
| 📦 **Crecimiento de Importaciones (%)** | Cuánto están aumentando sus compras al exterior. | 15% |
| 🏛️ **Facilidad para Hacer Negocios (WB 2019)** | Qué tan sencillo es operar comercialmente allí. | 15% |
| 🚚 **Infraestructura Logística (LPI 2023)** | Calidad del transporte, aduanas y distribución. | 15% |
| 🌐 **Distancia a Uruguay (km)** | Qué tan lejos está el país (menos distancia = mejor). | 10% |

---

## 🧠 ¿Cómo calcula el bot la “afinidad” entre un producto y un país?

El sistema sigue este proceso:

1. **🔄 Normalización**: Todos los datos se ajustan a una misma escala (de 0 a 1) para poder compararlos de forma justa. En el caso de la distancia, mientras más corta, mejor puntaje.
2. **⚖️ Ponderación**: Cada indicador se multiplica por su peso correspondiente según la tabla anterior.
3. **➕ Suma Ponderada**: Se suman los valores ponderados para obtener un puntaje base por país.
4. **🎲 Toque personalizado**: Se agrega una ligera variación aleatoria para reflejar que no todos los productos tienen el mismo comportamiento, incluso en el mismo país.
5. **📏 Escalado Final**: El puntaje se ajusta a una escala de 0 a 100, donde 100 representa la máxima afinidad.

---

## 🎯 ¿Qué hace con ese puntaje?

El bot te muestra un **ranking de países ordenados por afinidad** con el producto que elegiste. Cuanto mayor sea el puntaje, más atractivo es ese país como posible mercado para tu exportación.

También podés ver mapas interactivos, ajustar filtros según el nivel de afinidad que te interese y explorar los datos detallados de cada mercado.

---

## 💡 ¿Por qué es útil?

Esta herramienta te permite tomar decisiones más informadas sobre **dónde enfocar tus esfuerzos comerciales**, combinando datos económicos, logísticos y estratégicos en una sola vista.
