# 🌍 Descripción del Bot de Recomendación de Mercados de Exportación

Este proyecto proporciona una herramienta para recomendar mercados de exportación para productos, basada en indicadores clave de cada país. A continuación, se describe cómo el bot pondera los mercados y calcula la afinidad entre productos y países.

## 🏆 Indicadores Utilizados para Ponderar los Mercados

El bot evalúa los mercados basándose en los siguientes indicadores clave, extraídos del archivo `mercados.csv`. Cada indicador refleja un aspecto importante del potencial del mercado para la exportación de productos:

| Indicador                                | Descripción                                                                                                                                                         | Peso   |
|------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|--------|
| 📈 **Tamaño del Mercado Total (Millones USD)** | Refleja el tamaño total de la economía de un país o el mercado relevante para los productos.                                                                       | 30%    |
| 📊 **Crecimiento Anual PIB (%)**         | Mide el crecimiento económico del país. Un mayor crecimiento del PIB indica un mercado en expansión, lo que puede ser favorable para las exportaciones.             | 15%    |
| 📉 **Crecimiento de las Importaciones (%)**  | Representa el aumento en la cantidad de bienes que un país importa. Un mayor crecimiento de las importaciones indica una demanda creciente de productos extranjeros.   | 15%    |
| 🏛️ **Facilidad para Hacer Negocios (WB 2019)**  | Este indicador mide qué tan fácil es hacer negocios en un país, basado en factores como la obtención de permisos y la infraestructura.                              | 15%    |
| 🚚 **Logística (LPI 2023)**              | Evalúa la eficiencia de la infraestructura logística de un país, incluyendo el transporte, la aduana y la capacidad de envío de productos de manera eficiente.        | 15%    |
| 🌐 **Distancia a Uruguay (km)**          | Se refiere a la distancia geográfica entre Uruguay y el país en cuestión. La menor distancia suele implicar menores costos de transporte.                            | 10%    |

## ⚙️ Proceso de Cálculo de la Afinidad

El cálculo de la afinidad se realiza en varios pasos, utilizando los indicadores mencionados anteriormente:

1. **🔄 Normalización**:  
   Cada indicador se normaliza para que esté en una escala común (aproximadamente de 0 a 1), de manera que todos los indicadores sean comparables entre sí.  
   - **Distancia a Uruguay**: Se normaliza de forma inversa, donde una menor distancia recibe un puntaje más alto.

2. **⚖️ Ponderación**:  
   A cada indicador se le asigna un peso en función de su importancia relativa en la evaluación del mercado. Los pesos totales suman 100%, y se distribuyen entre los indicadores de la siguiente forma:  
   - **Tamaño del Mercado Total**: 30%
   - **Crecimiento Anual PIB**: 15%
   - **Crecimiento Importaciones**: 15%
   - **Facilidad Negocios**: 15%
   - **Logística**: 15%
   - **Distancia a Uruguay**: 10%

3. **➕ Suma Ponderada**:  
   El puntaje de cada indicador se multiplica por su peso respectivo y luego se suman para obtener un puntaje total para cada país.

4. **🎲 Variación Aleatoria**:  
   Se añade una pequeña variación aleatoria al puntaje final para simular que la afinidad no es idéntica para todos los productos hacia el mismo país. Esto refleja las diferencias en el potencial de exportación de acuerdo con las características específicas de cada producto.

5. **📏 Escalado Final**:  
   El puntaje resultante se escala a un rango de 0 a 100, asegurando que el valor final no sea menor que 0 ni mayor que 100.

## 🛠️ Uso de la Afinidad

Una vez calculado el puntaje de afinidad, se puede utilizar para recomendar mercados con mayor potencial de exportación para un producto específico. Los países con un puntaje de afinidad más alto se consideran más favorables para la exportación del producto en cuestión.

### 💡 Ejemplo de Cálculo de Afinidad

Imagina que tenemos un país con los siguientes valores para los indicadores:

| Indicador                               | Valor          |
|-----------------------------------------|----------------|
| **Tamaño del Mercado Total (Millones USD)**   | 100,000 millones USD  |
| **Crecimiento Anual PIB (%)**          | 3%             |
| **Crecimiento de Importaciones (%)**   | 5%             |
| **Facilidad de Negocios**              | 4.0 (escala 1-5) |
| **Logística**                          | 4.5 (escala 1-5) |
| **Distancia a Uruguay**                | 2,000 km       |

El cálculo de afinidad para este país seguiría estos pasos:

1. **🔄 Normalización**:  
   Todos estos valores se transforman a una escala de 0 a 1.

2. **⚖️ Ponderación**:  
   Cada valor normalizado se multiplica por su peso respectivo.

3. **➕ Suma Ponderada**:  
   Los resultados ponderados se suman para obtener un puntaje final.

Este puntaje es el que determina cuán favorable es un mercado para exportar un producto específico.

## 🎯 Conclusión

Este modelo permite calcular y comparar la afinidad de mercados potenciales para productos de exportación, facilitando la toma de decisiones sobre dónde concentrar los esfuerzos de exportación. Los mercados con mayores puntajes de afinidad son recomendados para ser explorados más a fondo.

---

### 📍**¡Prueba la Aplicación!**

Puedes interactuar con el bot y obtener recomendaciones de mercados utilizando los filtros y herramientas en la interfaz interactiva de la aplicación.

👨‍💻 **¿Tienes alguna pregunta?** ¡No dudes en contactarnos! comex@cncs.com.uy


