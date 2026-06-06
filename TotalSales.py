import altair as alt
import pandas as pd
import streamlit as st

salesIcon = "/workspaces/OnionDataset/public/assets/sales-report.svg"
workDB = "data/BD_EVALUACION.csv" #My datasource (Database)
#My own sheet fields from database to reuse in other pages 

FieldStore = 'Tienda'
FieldTicket = 'Ticket'
FieldMaterial = 'Material'
FieldGroup = 'Grupo art.'
FieldCategory = 'Denominacion 2 del gr.articulos'
FieldProduct = 'Producto'
FieldSale = 'Venta'
FieldDateOFSale = 'Fecha Vta'
FieldTimeOFSale = 'Hora Vta'
FieldAmount = 'Cantidad'
FieldUMB = 'UMB'

st.set_page_config(
    page_title="Ventas Totales",
    page_icon=salesIcon,
)


st.title("Resumen de Ventas Totales")

st.sidebar.success("Una descripcion breve de la pagina:")
st.sidebar.markdown("")

#$st.write("# Welcome to Streamlit!")
st.markdown("My page content")

@st.cache_data
def load_data():
    df = pd.read_csv(workDB)

    # Ejemplo: Convertir la columna de fecha a formato datetime de Pandas
    #df[FieldDateOFSale] = pd.to_datetime(df[FieldDateOFSale]) 
    if df[FieldSale].dtype == 'object':
        df[FieldSale] = df[FieldSale].astype(str).str.replace('$', '', regex=False)
        df[FieldSale] = df[FieldSale].astype(str).str.replace(',', '', regex=False)
    
    
    df[FieldSale] = pd.to_numeric(df[FieldSale], errors='coerce')
    df[FieldAmount] = pd.to_numeric(df[FieldAmount], errors='coerce')
    return df

df = load_data()

# -------------------------------------------------------------
# SECCIÓN DE FILTROS (Filtros horizontales tipo "Top Bar")
# -------------------------------------------------------------
st.subheader("Filtros de Búsqueda")
categorySelect = st.multiselect(
    "Seleccione por Categoria",
    #df.categorySelect.unique(),
    df[FieldCategory].unique().tolist(),
    #options = df[FieldCategory].unique().tolist()[1],
    default = df[FieldCategory].unique().tolist()[9],
)
col_filt_1, col_filt_2= st.columns(2)

with col_filt_1:
    #Empty intencional field 
    date_list = df[FieldDateOFSale].unique().tolist()
    date_slider = st.slider("Dia", 1986, 2006, (2000, 2016))




with col_filt_2:
    # Ejemplo de filtro por año o sucursal
    sucursales = df[FieldStore].unique().tolist()
    suc_seleccionada = st.multiselect("Filtrar por Sucursal", options=sucursales, default=sucursales)


# Aplicar los filtros al DataFrame
df_filtrado = df[(df[FieldCategory].isin(categorySelect)) & (df[FieldStore].isin(suc_seleccionada))]

st.divider() 

# -------------------------------------------------------------
# SECCIÓN DE MÉTRICAS (KPIs)
# -------------------------------------------------------------
# Calculamos los totales basados en los datos filtrados
ingreso_total = df_filtrado[FieldSale].sum()
unidades_totales = df_filtrado[FieldAmount].sum()
ticket_promedio = df_filtrado[FieldSale].mean()

col1, col2, col3 = st.columns(3)
col1.metric(label="Ingreso Total", value=f"${ingreso_total:,.2f}")
col2.metric(label="Unidades Vendidas", value=f"{unidades_totales:,}")
col3.metric(label="Venta Promedio", value=f"${ticket_promedio:,.2f}")

st.divider()

# -------------------------------------------------------------
# SECCIÓN DE GRÁFICOS
# -------------------------------------------------------------
col_graf_1, col_graf_2 = st.columns(2)

with col_graf_1:
    st.markdown("**Ventas en el Tiempo**")
    # Agrupamos por fecha y sumamos las ventas
    ventas_tiempo = df_filtrado.groupby(FieldDateOFSale)[FieldSale].sum()
    st.line_chart(ventas_tiempo)

with col_graf_2:
    st.markdown("**Top Ventas por Categoría**")
    ventas_categoria = df_filtrado.groupby(FieldCategory)[FieldSale].sum()
    st.bar_chart(ventas_categoria)
