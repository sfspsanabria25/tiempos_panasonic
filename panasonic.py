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
# ESTILOS GENERALES
# -------------------------------------------------

st.markdown("""
<style>

.block-container {
    padding-top: 2rem;
}

h1 {
    font-weight: 700;
}

div[data-testid="stMetric"] {
    border: 1px solid rgba(128,128,128,0.2);
    padding: 15px;
    border-radius: 12px;
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
# ACCIÓN RECOMENDADA
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
# COLORES TABLA
# -------------------------------------------------

def colorear_estado(valor):

    if valor == "GESTIÓN PRIORITARIA":

        return (
            "background-color: #ffcccc;"
            "color: black;"
            "font-weight: bold;"
        )

    elif valor == "PRÓXIMO A VENCER":

        return (
            "background-color: #ffe5b4;"
            "color: black;"
            "font-weight: bold;"
        )

    elif valor == "DENTRO DEL TIEMPO":

        return (
            "background-color: #d4edda;"
            "color: black;"
            "font-weight: bold;"
        )

    elif valor == "SIN FECHA":

        return (
            "background-color: #e2e3e5;"
            "color: black;"
            "font-weight: bold;"
        )

    return ""

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

            st.error(
                f"No se encontró la columna: {columna_fecha}"
            )

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

        fecha_actual = pd.Timestamp.now()

        # -------------------------------------------------
        # CALCULAR DÍAS HÁBILES
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
        # CLASIFICACIÓN
        # -------------------------------------------------

        df["Clasificación"] = df[
            "Días hábiles"
        ].apply(clasificar_caso)

        # -------------------------------------------------
        # ACCIÓN RECOMENDADA
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
            "⚠️ Próximos a vencimiento",
            proximos
        )

        col4.metric(
            "✅ Dentro del tiempo",
            normales
        )

        # -------------------------------------------------
        # GRÁFICO
        # -------------------------------------------------

        conteo = (
            df["Clasificación"]
            .value_counts()
            .reset_index()
        )

        conteo.columns = [
            "Clasificación",
            "Cantidad"
        ]

        fig = px.pie(
            conteo,
            names="Clasificación",
            values="Cantidad",
            title="Distribución de Casos",
            hole=0.45,
            color="Clasificación",
            color_discrete_map={
                "GESTIÓN PRIORITARIA": "#ff6b6b",
                "PRÓXIMO A VENCER": "#f4a261",
                "DENTRO DEL TIEMPO": "#52b788",
                "SIN FECHA": "#adb5bd"
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

        tabla_estilizada = (
            df_filtrado[columnas_existentes]
            .style
            .map(
                colorear_estado,
                subset=["Clasificación"]
            )
        )

        st.dataframe(
            tabla_estilizada,
            use_container_width=True,
            height=650
        )

        # -------------------------------------------------
        # RESUMEN
        # -------------------------------------------------

        st.subheader("📊 Resumen General")

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
