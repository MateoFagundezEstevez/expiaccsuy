with st.expander("📊 Sobre los datos utilizados"):
    st.markdown("""
    ### Fuentes de los indicadores y estructura de los CSV

    - **`afinidad_producto_país.csv`**  
      - 🔍 **Contenido:** Compatibilidad entre productos uruguayos y mercados internacionales.  
      - 🧠 **Metodología:** Índices generados a partir de análisis de comercio bilateral, preferencias arancelarias, acuerdos comerciales, patrones de consumo y tendencias sectoriales.  
      - 🗂️ **Columnas:**  
        - `Producto`: Nombre del producto uruguayo.  
        - `País`: Mercado de destino.  
        - `Afinidad`: Valor numérico (0 a 100) que refleja la compatibilidad.  
      - 📚 **Fuente:** Elaboración propia basada en datos de COMTRADE (ONU), Trademap (ITC), observaciones de expertos y relevamientos de mercado sectoriales.

    - **`mercados.csv`**  
      - 🔍 **Contenido:** Indicadores económicos y políticos por país.  
      - 🗂️ **Columnas:**  
        - `País`  
        - `Facilidad para hacer negocios`: Índice derivado del **ranking Doing Business** del Banco Mundial.  
        - `Demanda esperada`: Estimaciones basadas en datos de consumo sectorial y crecimiento proyectado (ITC, Euromonitor).  
        - `Beneficios arancelarios`: Relevamiento de acuerdos comerciales vigentes entre Uruguay y cada país.  
        - `Estabilidad política`: Indicador del **Worldwide Governance Indicators** (Banco Mundial).  
      - 📚 **Fuente:** Banco Mundial, ITC, Tratados de Libre Comercio vigentes, Dirección General de Asuntos de Frontera (Uruguay), informes de inteligencia comercial de Uruguay XXI.

    ✅ Los datos son de uso referencial y orientativo. La aplicación tiene fines exploratorios y de apoyo a la decisión exportadora.
    """)
