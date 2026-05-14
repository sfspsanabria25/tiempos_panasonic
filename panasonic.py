import streamlit as st
import pandas as pd
import holidays
import plotly.express as px
from io import BytesIO

# -------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -------------------------------------------------

st.set_page_config(
    page_title="Control de Tiempos Panasonic",
    layout="wide"
)

# -------------------------------------------------
# ESTILO VISUAL
# -------------------------------------------------

st.markdown("""
<style>

.main {
    background-color: #f5f7fb;
}

h1 {
    color: #003366;
    font-weight: bold;
}

.stMetric {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    box-shadow: 0px 2px 8px rgba(0,0,0,0.08);
}

div[data-testid="stDataFrame"] {
    background-color: white;
    border-radius: 12px;
    padding: 10px;
}

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# TÍTULO
# -------------------------------------------------

st.title("📦 Control de Tiempos de Atención")

st.markdown("""
Sistema de seguimiento para identificación de casos:

- ✅ Dentro del tiempo esperado
- ⚠️ Próximos a vencimiento
- 🚨 Requieren gestión prioritaria
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
# CLASIFICACIÓN
# -------------------------------------------------

def clasificar_caso(dias):

    if pd.isnull(dias):
        return "SIN FECHA"

    elif dias >= 15:
        return "GESTIÓN PRIORITARIA"

    elif dias >= 12:
        return "PRÓXIMO A VENCER"

    else:
        return "DENTRO DEL TIEMPO"

# -------------------------------------------------
# ACCIONES RECOMENDADAS
# -------------------------------------------------

def accion_recomendada(estado):

    if estado == "GESTIÓN PRIORITARIA":

        return (
            "Validar inmediatamente el estado "
            "del caso y gestionar escalamiento."
        )

    elif estado == "PRÓXIMO A VENCER":

        return (
            "Realizar seguimiento preventivo "
            "y validar disponibilidad."
        )

    elif estado == "DENTRO DEL TIEMPO":

        return (
            "Continuar proceso operativo normal."
        )

    return "Validar información."

# -------------------------------------------------
# CARGA ARCHIVO
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

        # LEER ARCHIVO
        df = pd.read_excel(archivo)

        st.success("✅ Archivo cargado correctamente")

        # -------------------------------------------------
        # VALIDAR COLUMNA
        # -------------------------------------------------

        columna_fecha = "Fecha/Hora de apertura"

        if columna_fecha not in df.columns:

            st.error(
                f"No se encontró la columna: {columna_fecha}"
            )

            st.write(df.columns.tolist())

            st.stop()

        # -------------------------------------------------
        # CONVERTIR FECHA
        # -------------------------------------------------

        df[columna_fecha] = pd.to_datetime(
            df[columna_fecha],
            errors='coerce'
        )

        fecha_actual = pd.Timestamp.now()

        # -------------------------------------------------
        # CÁLCULO DÍAS
        # -------------------------------------------------

        df["Días hábiles"] = df[columna_fecha].apply(
            lambda x: calcular_dias_habiles(
                x,
                fecha_actual
            )
            if pd.notnull(x)
            else None
        )

        # -------------------------------------------------
        # ESTADO
        # -------------------------------------------------

        df["Clasificación"] = df[
            "Días hábiles"
        ].apply(clasificar_caso)

        # -------------------------------------------------
        # ACCIÓN
        # -------------------------------------------------

        df["Acción recomendada"] = df[
            "Clasificación"
        ].apply(accion_recomendada)

        # -------------------------------------------------
        # MÉTRICAS
        # -------------------------------------------------

        total_casos = len(df)

        gestion_prioritaria = len(
            df[
                df["Clasificación"]
                == "GESTIÓN PRIORITARIA"
            ]
        )

        proximos = len(
            df[
                df["Clasificación"]
                == "PRÓXIMO A VENCER"
            ]
        )

        normales = len(
            df[
                df["Clasificación"]
                == "DENTRO DEL TIEMPO"
            ]
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Casos",
            total_casos
        )

        col2.metric(
            "🚨 Gestión prioritaria",
            gestion_prioritaria
        )

        col3.metric(
            "⚠️ Próximos",
            proximos
        )

        col4.metric(
            "✅ Dentro del tiempo",
            normales
        )

        # -------------------------------------------------
        # GRÁFICA
        # -------------------------------------------------

        conteo = (
            df["Clasificación"]
            .value_counts()
            .reset_index()
        )

        conteo.columns = [
            "Estado",
            "Cantidad"
        ]

        fig = px.pie(
            conteo,
            names="Estado",
            values="Cantidad",
            title="Distribución de casos",
            hole=0.45,
            color="Estado",
            color_discrete_map={
                "DENTRO DEL TIEMPO": "green",
                "PRÓXIMO A VENCER": "orange",
                "GESTIÓN PRIORITARIA": "red",
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
            "Filtrar clasificación",
            [
                "TODOS",
                "GESTIÓN PRIORITARIA",
                "PRÓXIMO A VENCER",
                "DENTRO DEL TIEMPO",
                "SIN FECHA"
            ]
        )

        if filtro != "TODOS":

            df_filtrado = df[
                df["Clasificación"] == filtro
            ]

        else:

            df_filtrado = df

        # -------------------------------------------------
        # COLORES
        # -------------------------------------------------

        def colorear_estado(valor):

            if valor == "GESTIÓN PRIORITARIA":

                return (
                    "background-color:#d62828;"
                    "color:white;"
                    "font-weight:bold"
                )

            elif valor == "PRÓXIMO A VENCER":

                return (
                    "background-color:#f77f00;"
                    "color:white;"
                    "font-weight:bold"
                )

            elif valor == "DENTRO DEL TIEMPO":

                return (
                    "background-color:#2a9d8f;"
                    "color:white;"
                )

            elif valor == "SIN FECHA":

                return (
                    "background-color:gray;"
                    "color:white;"
                )

            return ""

        # -------------------------------------------------
        # TABLA PRINCIPAL
        # -------------------------------------------------

        st.subheader(
            "📋 Clasificación Operativa de Casos"
        )

        columnas_mostrar = [
            "Número del caso",
            "Modelo",
            "Centro de servicio solicitante",
            "Descripcion del producto",
            "Fecha/Hora de apertura",
            "Días hábiles",
            "Clasificación",
            "Acción recomendada"
        ]

        columnas_existentes = [
            col for col in columnas_mostrar
            if col in df_filtrado.columns
        ]

        st.dataframe(
            df_filtrado[columnas_existentes]
            .style
            .applymap(
                colorear_estado,
                subset=["Clasificación"]
            ),
            use_container_width=True,
            height=650
        )

        # -------------------------------------------------
        # TABLA RESUMEN
        # -------------------------------------------------

        st.subheader(
            "📊 Resumen de gestión"
        )

        resumen = (
            df.groupby("Clasificación")
            .size()
            .reset_index(name="Cantidad")
        )

        st.table(resumen)

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

        excel_descarga = convertir_excel(
            df_filtrado
        )

        st.download_button(
            label="📥 Descargar reporte Excel",
            data=excel_descarga,
            file_name="control_tiempos_panasonic.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Error procesando archivo: {e}"
        )
