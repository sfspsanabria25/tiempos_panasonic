import streamlit as st
import pandas as pd
import holidays
import plotly.express as px
from io import BytesIO

# -------------------------------------------------
# PAGE CONFIGURATION
# -------------------------------------------------

st.set_page_config(
    page_title="Panasonic Case Monitoring",
    layout="wide"
)

# -------------------------------------------------
# VISUAL STYLE
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
# TITLE
# -------------------------------------------------

st.title("📦 Case Lead Time Monitoring")

st.markdown("""
Monitoring system for operational case tracking:

- ✅ Within target
- ⚠️ Near due date
- 🚨 Priority management required
""")

# -------------------------------------------------
# CLASSIFICATION RULES
# -------------------------------------------------

st.info("""
📌 Classification Criteria (Colombian Business Days)

✅ WITHIN TARGET
Cases between 0 and 11 business days.

⚠️ NEAR DUE DATE
Cases between 12 and 14 business days.

🚨 PRIORITY MANAGEMENT
Cases with 15 business days or more.

Business day calculation excludes:
• Saturdays
• Sundays
• Official Colombian holidays

The opening date and current date ARE included in the calculation.
""")

# -------------------------------------------------
# COLOMBIAN HOLIDAYS
# -------------------------------------------------

festivos_colombia = holidays.Colombia()

# -------------------------------------------------
# BUSINESS DAYS CALCULATION
# -------------------------------------------------

def calcular_dias_habiles(fecha_inicio, fecha_fin):

    fecha_inicio = fecha_inicio.normalize()
    fecha_fin = fecha_fin.normalize()

    dias = pd.date_range(
        start=fecha_inicio,
        end=fecha_fin,
        freq='D'
    )

    dias_habiles = [
        dia for dia in dias
        if dia.weekday() < 5
        and dia.date() not in festivos_colombia
    ]

    return len(dias_habiles)

# -------------------------------------------------
# SALESFORCE DATE TRANSFORMATION
# -------------------------------------------------

def transformar_fecha_salesforce(valor):

    if pd.isnull(valor):
        return pd.NaT

    try:

        valor = str(valor)

        valor = (
            valor
            .replace("\xa0", " ")
            .replace("\u202f", " ")
            .replace("\u2009", " ")
            .strip()
        )

        valor = (
            valor
            .replace("a. m.", "AM")
            .replace("p. m.", "PM")
            .replace("a.m.", "AM")
            .replace("p.m.", "PM")
            .replace("a. m", "AM")
            .replace("p. m", "PM")
        )

        valor = " ".join(valor.split())

        fecha = pd.to_datetime(
            valor,
            format="%d/%m/%Y, %I:%M %p",
            errors="coerce"
        )

        return fecha

    except Exception:
        return pd.NaT

# -------------------------------------------------
# CASE CLASSIFICATION
# -------------------------------------------------

def clasificar_caso(dias):

    if pd.isnull(dias):
        return "NO DATE"

    elif dias >= 15:
        return "PRIORITY MANAGEMENT"

    elif dias >= 12:
        return "NEAR DUE DATE"

    else:
        return "WITHIN TARGET"

# -------------------------------------------------
# RECOMMENDED ACTION
# -------------------------------------------------

def accion_recomendada(estado):

    if estado == "PRIORITY MANAGEMENT":

        return (
            "Immediate validation and escalation required."
        )

    elif estado == "NEAR DUE DATE":

        return (
            "Preventive follow-up recommended."
        )

    elif estado == "WITHIN TARGET":

        return (
            "Normal operational flow."
        )

    return "Review information."

# -------------------------------------------------
# TABLE COLORS
# -------------------------------------------------

def colorear_estado(valor):

    if valor == "PRIORITY MANAGEMENT":

        return (
            "background-color: #ffcccc;"
            "color: black;"
            "font-weight: bold;"
        )

    elif valor == "NEAR DUE DATE":

        return (
            "background-color: #ffe5b4;"
            "color: black;"
            "font-weight: bold;"
        )

    elif valor == "WITHIN TARGET":

        return (
            "background-color: #d4edda;"
            "color: black;"
            "font-weight: bold;"
        )

    elif valor == "NO DATE":

        return (
            "background-color: #e2e3e5;"
            "color: black;"
            "font-weight: bold;"
        )

    return ""

# -------------------------------------------------
# FILE UPLOAD
# -------------------------------------------------

archivo = st.file_uploader(
    "📂 Upload Excel File",
    type=["xlsx"]
)

# -------------------------------------------------
# PROCESSING
# -------------------------------------------------

if archivo:

    try:

        # -------------------------------------------------
        # READ EXCEL
        # -------------------------------------------------

        df = pd.read_excel(archivo)

        st.success("✅ File loaded successfully")

        # -------------------------------------------------
        # DATE COLUMN
        # -------------------------------------------------

        columna_fecha = "Fecha/Hora de apertura"

        if columna_fecha not in df.columns:

            st.error(
                f"Column not found: {columna_fecha}"
            )

            st.write(df.columns.tolist())

            st.stop()

        # -------------------------------------------------
        # TRANSFORM DATES
        # -------------------------------------------------

        df[columna_fecha] = (
            df[columna_fecha]
            .astype(str)
            .apply(transformar_fecha_salesforce)
        )

        # -------------------------------------------------
        # INVALID DATES
        # -------------------------------------------------

        fechas_invalidas = df[columna_fecha].isna().sum()

        if fechas_invalidas > 0:

            st.warning(
                f"⚠️ {fechas_invalidas} records contain invalid dates."
            )

        # -------------------------------------------------
        # CURRENT DATE
        # -------------------------------------------------

        fecha_actual = pd.Timestamp.now()

        # -------------------------------------------------
        # BUSINESS DAYS
        # -------------------------------------------------

        df["Business Days"] = df[columna_fecha].apply(
            lambda x: calcular_dias_habiles(
                x,
                fecha_actual
            )
            if pd.notnull(x)
            else None
        )

        df["Business Days"] = (
            df["Business Days"]
            .fillna(0)
            .astype(int)
        )

        # -------------------------------------------------
        # CLASSIFICATION
        # -------------------------------------------------

        df["Classification"] = df[
            "Business Days"
        ].apply(clasificar_caso)

        # -------------------------------------------------
        # RECOMMENDED ACTION
        # -------------------------------------------------

        df["Recommended Action"] = df[
            "Classification"
        ].apply(accion_recomendada)

        # -------------------------------------------------
        # SORT
        # -------------------------------------------------

        df = df.sort_values(
            by="Business Days",
            ascending=False
        )

        # -------------------------------------------------
        # METRICS
        # -------------------------------------------------

        total_casos = len(df)

        priority_cases = len(
            df[
                df["Classification"]
                == "PRIORITY MANAGEMENT"
            ]
        )

        near_due = len(
            df[
                df["Classification"]
                == "NEAR DUE DATE"
            ]
        )

        within_target = len(
            df[
                df["Classification"]
                == "WITHIN TARGET"
            ]
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Total Cases",
            total_casos
        )

        col2.metric(
            "🚨 Priority",
            priority_cases
        )

        col3.metric(
            "⚠️ Near Due",
            near_due
        )

        col4.metric(
            "✅ Within Target",
            within_target
        )

        # -------------------------------------------------
        # CHART
        # -------------------------------------------------

        conteo = (
            df["Classification"]
            .value_counts()
            .reset_index()
        )

        conteo.columns = [
            "Classification",
            "Quantity"
        ]

        fig = px.pie(
            conteo,
            names="Classification",
            values="Quantity",
            title="Case Distribution",
            hole=0.45,
            color="Classification",
            color_discrete_map={
                "PRIORITY MANAGEMENT": "#ff6b6b",
                "NEAR DUE DATE": "#f4a261",
                "WITHIN TARGET": "#52b788",
                "NO DATE": "#adb5bd"
            }
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # -------------------------------------------------
        # FILTER
        # -------------------------------------------------

        filtro = st.selectbox(
            "Filter classification",
            [
                "ALL",
                "PRIORITY MANAGEMENT",
                "NEAR DUE DATE",
                "WITHIN TARGET",
                "NO DATE"
            ]
        )

        if filtro != "ALL":

            df_filtrado = df[
                df["Classification"] == filtro
            ]

        else:

            df_filtrado = df

        # -------------------------------------------------
        # TABLE
        # -------------------------------------------------

        st.subheader(
            "📋 Operational Case Classification"
        )

        columnas_mostrar = [
            "Número del caso",
            "Modelo",
            "Centro de servicio solicitante",
            "Sublínea",
            "Descripcion del producto",
            "Cantidad solicitada",
            "Fecha de Compra",
            "Fecha/Hora de apertura",
            "Fecha de solicitud",
            "Business Days",
            "Classification",
            "Recommended Action"
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
                subset=["Classification"]
            )
        )

        st.dataframe(
            tabla_estilizada,
            use_container_width=True,
            height=650
        )

        # -------------------------------------------------
        # SUMMARY
        # -------------------------------------------------

        st.subheader("📊 General Summary")

        resumen = (
            df.groupby("Classification")
            .size()
            .reset_index(name="Quantity")
        )

        st.table(resumen)

        # -------------------------------------------------
        # EXPORT EXCEL
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
            label="📥 Download Excel Report",
            data=excel_descarga,
            file_name="panasonic_case_monitoring.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:

        st.error(
            f"Error processing file: {e}"
        )
