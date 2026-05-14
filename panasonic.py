import streamlit as st
import pandas as pd
import holidays
import plotly.express as px
from io import BytesIO

# -------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -------------------------------------------------

st.set_page_config(
    page_title="Control SLA Panasonic",
    layout="wide"
)

st.title("📦 Control de Casos SLA Panasonic")

st.markdown("""
Este aplicativo analiza automáticamente los casos y detecta:

- ✅ Casos normales
- ⚠️ Casos próximos a vencerse
- 🚨 Casos que superan 15 días hábiles
""")

# -------------------------------------------------
# FESTIVOS COLOMBIA
# -------------------------------------------------

festivos_colombia = holidays.Colombia()

# -------------------------------------------------
# FUNCIÓN DÍAS HÁBILES
# -------------------------------------------------

def calcular_dias_habiles(fecha_inicio, fecha_fin):

    dias = pd.date_range(fecha_inicio, fecha_fin)

    dias_habiles = [
        dia for dia in dias
        if dia.weekday() < 5
        and dia.date() not in festivos_colombia
    ]

    return max(len(dias_habiles) - 1, 0)

# -------------------------------------------------
# CARGAR ARCHIVO
# -------------------------------------------------

archivo = st.file_uploader(
    "📂 Cargar archivo Excel",
    type=["xlsx"]
)

# -------------------------------------------------
# PROCESAMIENTO
# -------------------------------------------------

if archivo:

    try:

        # LEER EXCEL
        df = pd.read_excel(archivo)

        st.success("✅ Archivo cargado correctamente")

        # -------------------------------------------------
        # VALIDAR COLUMNA FECHA
        # -------------------------------------------------

        columna_fecha = "Fecha/Hora de apertura"

        if columna_fecha not in df.columns:

            st.error(f"No se encontró la columna: {columna_fecha}")

            st.write("Columnas encontradas:")

            st.write(df.columns.tolist())

            st.stop()

        # -------------------------------------------------
        # CONVERTIR FECHA
        # -------------------------------------------------

        df[columna_fecha] = pd.to_datetime(
            df[columna_fecha],
            errors='coerce'
        )

        # -------------------------------------------------
        # FECHA ACTUAL
        # -------------------------------------------------

        fecha_actual = pd.Timestamp.now()

        # -------------------------------------------------
        # CALCULAR DÍAS HÁBILES
        # -------------------------------------------------

        df["Días hábiles"] = df[columna_fecha].apply(
            lambda x: calcular_dias_habiles(x, fecha_actual)
            if pd.notnull(x)
            else None
        )

        # -------------------------------------------------
        # CLASIFICAR SLA
        # -------------------------------------------------

        def clasificar_caso(dias):

            if pd.isnull(dias):
                return "SIN FECHA"

            elif dias >= 15:
                return "SE VA DE CAMBIO"

            elif dias >= 12:
                return "PRÓXIMO A VENCER"

            else:
                return "NORMAL"

        df["Estado SLA"] = df["Días hábiles"].apply(clasificar_caso)

        # -------------------------------------------------
        # MÉTRICAS
        # -------------------------------------------------

        total_casos = len(df)

        casos_vencidos = len(
            df[df["Estado SLA"] == "SE VA DE CAMBIO"]
        )

        casos_proximos = len(
            df[df["Estado SLA"] == "PRÓXIMO A VENCER"]
        )

        casos_normales = len(
            df[df["Estado SLA"] == "NORMAL"]
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Casos", total_casos)

        col2.metric(
            "🚨 Se van de cambio",
            casos_vencidos
        )

        col3.metric(
            "⚠️ Próximos",
            casos_proximos
        )

        col4.metric(
            "✅ Normales",
            casos_normales
        )

        # -------------------------------------------------
        # GRÁFICO
        # -------------------------------------------------

        conteo_estados = (
            df["Estado SLA"]
            .value_counts()
            .reset_index()
        )

        conteo_estados.columns = [
            "Estado",
            "Cantidad"
        ]

        fig = px.pie(
            conteo_estados,
            names="Estado",
            values="Cantidad",
            title="Distribución SLA",
            hole=0.4,
            color="Estado",
            color_discrete_map={
                "NORMAL": "green",
                "PRÓXIMO A VENCER": "orange",
                "SE VA DE CAMBIO": "red",
                "SIN FECHA": "gray"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # -------------------------------------------------
        # FILTRO
        # -------------------------------------------------

        filtro = st.selectbox(
            "Filtrar casos",
            [
                "TODOS",
                "SE VA DE CAMBIO",
                "PRÓXIMO A VENCER",
                "NORMAL",
                "SIN FECHA"
            ]
        )

        if filtro != "TODOS":

            df_filtrado = df[
                df["Estado SLA"] == filtro
            ]

        else:

            df_filtrado = df

        # -------------------------------------------------
        # COLORES TABLA
        # -------------------------------------------------

        def colorear_estado(valor):

            if valor == "SE VA DE CAMBIO":

                return (
                    "background-color: #ff4b4b;"
                    "color: white;"
                    "font-weight: bold"
                )

            elif valor == "PRÓXIMO A VENCER":

                return (
                    "background-color: #ffa500;"
                    "color: black;"
                    "font-weight: bold"
                )

            elif valor == "NORMAL":

                return (
                    "background-color: #28a745;"
                    "color: white"
                )

            elif valor == "SIN FECHA":

                return (
                    "background-color: gray;"
                    "color: white"
                )

            return ""

        # -------------------------------------------------
        # COLUMNAS A MOSTRAR
        # -------------------------------------------------

        columnas_mostrar = [
            "Número del caso",
            "Modelo",
            "Centro de servicio solicitante",
            "Descripcion del producto",
            "Fecha/Hora de apertura",
            "Días hábiles",
            "Estado SLA"
        ]

        columnas_existentes = [
            col for col in columnas_mostrar
            if col in df_filtrado.columns
        ]

        # -------------------------------------------------
        # TABLA
        # -------------------------------------------------

        st.subheader("📋 Resultado del análisis")

        st.dataframe(
            df_filtrado[columnas_existentes]
            .style
            .applymap(
                colorear_estado,
                subset=["Estado SLA"]
            ),
            use_container_width=True,
            height=600
        )

        # -------------------------------------------------
        # EXPORTAR EXCEL
        # -------------------------------------------------

        def convertir_excel(dataframe):

            salida = BytesIO()

            with pd.ExcelWriter(
                salida,
                engine='openpyxl'
            ) as writer:

                dataframe.to_excel(
                    writer,
                    index=False
                )

            return salida.getvalue()

        excel_descarga = convertir_excel(df_filtrado)

        st.download_button(
            label="📥 Descargar Excel",
            data=excel_descarga,
            file_name="analisis_sla_panasonic.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"❌ Error procesando archivo: {e}"
        )
