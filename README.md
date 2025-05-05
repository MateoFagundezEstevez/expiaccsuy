# Recomendador de Mercados para Exportadores Uruguayos

Este proyecto está diseñado para ayudar a los exportadores uruguayos a determinar el mejor mercado para exportar sus productos, basado en criterios clave como la **facilidad para hacer negocios**, **demanda de productos**, **beneficios arancelarios**, y **estabilidad política** de los países destino. La aplicación utiliza un modelo de recomendación en Python con **Streamlit** y proporciona un análisis detallado para cada país recomendado.

## Funcionalidades

La plataforma permite:

1. **Clasificación de Producto NCM**: Clasificación de productos bajo la **Nomenclatura Común del Mercosur (NCM)** para determinar el código arancelario adecuado.
2. **Recomendación de Mercados**: Basado en los siguientes indicadores:
   - **Facilidad para hacer negocios**.
   - **Demanda esperada**.
   - **Beneficios arancelarios**.
   - **Estabilidad política**.

Los usuarios pueden ajustar los parámetros utilizando **sliders** en la interfaz y recibir recomendaciones sobre los **5 mejores países** para exportar sus productos.

## Indicadores Decisivos y Fuentes

A continuación se detallan los 4 indicadores clave utilizados para calcular las recomendaciones, junto con las fuentes donde puedes obtener la información actualizada:

### 1. **Facilidad para hacer negocios**
   La facilidad para hacer negocios mide la eficiencia de los procedimientos administrativos y legales para crear y operar una empresa en cada país. 
   - **Fuente principal**: [Doing Business Report - World Bank](https://www.doingbusiness.org/en/reports/global-reports/doing-business-2020)  
   - **Fuente alternativa**: [Business Environment Rankings - The Economist Intelligence Unit](https://www.eiu.com/topic/business-environment)

### 2. **Demanda de Productos**
   La demanda de productos se calcula mediante el análisis de comercio internacional y exportaciones. Esto ayuda a determinar qué tan solicitado está un producto en diferentes mercados internacionales.
   - **Fuente principal**: [UN Comtrade Database](https://comtrade.un.org/)
   - **Fuente alternativa**: [TradeMap - International Trade Centre](https://trademap.org/)

### 3. **Beneficios Arancelarios**
   Los beneficios arancelarios indican las preferencias que existen para los productos exportados, basadas en acuerdos comerciales, tratados y tarifas preferenciales.
   - **Fuente principal**: [Mercosur - Acuerdos Comerciales y Aranceles](https://www.mercosur.int)
   - **Fuente alternativa**: [WTO - World Trade Organization](https://www.wto.org/)

### 4. **Estabilidad Política**
   La estabilidad política evalúa la situación interna de los países, considerando factores como la seguridad, los riesgos políticos y la corrupción. Un entorno político estable es fundamental para el éxito de las exportaciones.
   - **Fuente principal**: [Political Stability Index - The Economist Intelligence Unit](https://www.eiu.com/)
   - **Fuente alternativa**: [Fragile States Index - Fund for Peace](https://fragilestatesindex.org/)

## Requisitos

Para ejecutar esta aplicación necesitas tener instalado **Python 3.x** y las siguientes bibliotecas:

- streamlit
- pandas
- numpy
- matplotlib (si quieres graficar los resultados)

Puedes instalar las dependencias utilizando pip:

```bash
pip install streamlit pandas numpy matplotlib
