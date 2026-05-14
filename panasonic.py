import streamlit as st
import pandas as pd
from datetime import datetime
from pandas.tseries.offsets import BDay
from io import BytesIO

# -------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -------------------------------------------------

st.set_page_config(
    page_title="Control de Casos - 15 Días Hábiles",
    layout="wide"
)

st.title("📦 Control de Casos por Tiempo de Atención")

st.markdown("""
Este aplicativo analiza automáticamente los casos y detecta:

- ✅ Casos normales
- ⚠️ Casos cercanos a vencerse
- 🚨 Casos que superan 15 días hábiles
""")

# -------------------------------------------------
# FUNCIÓN PARA CALCULAR DÍAS HÁBILES
# -------------------------------------------------

def calcular_dias_habiles(fecha_inicio, fecha_fin):
    return len(pd.bdate_range(fecha_inicio, fecha_fin)) - 1

# -------------------------------------------------
# CARGA DE ARCHIVO
# -------------------------------------------------

archivo = st.file_uploader(
    "Cargar archivo Excel",
    type=["xlsx"]
)

if archivo:

    try:

        # -------------------------------------------------
        # LEER EXCEL
        # -------------------------------------------------

        df = pd.read_excel(archivo)

        st.success("Archivo cargado correctamente")

        # -------------------------------------------------
        # VALIDAR COLUMNA
        # -------------------------------------------------

        columna_fecha = "Fecha/Hora de apertura"

        if columna_fecha not in df.columns:
            st.error(f"No se encontró la columna: {columna_fecha}")
            st.stop()

        # -------------------------------------------------
        # CONVERTIR FECHA
        # -------------------------------------------------

        df[columna_fecha] = pd.to_datetime(df[columna_fecha], errors='coerce')

        # -------------------------------------------------
        # FECHA ACTUAL
        # -------------------------------------------------

        fecha_actual = pd.Timestamp.now()

        # -------------------------------------------------
        st.error(f"Error procesando archivo: {e}")