import altair as alt
import pandas as pd
import streamlit as st

salesIcon = "/workspaces/OnionDataset/public/assets/sales-report.svg"
workDB = "data/BD_EVALUACION.csv" 

tool_tiptxt = " Pase el cursor (hover) sobre las líneas, " \
"barras de los gráficos, o grafos coloreados de azul " \
"de abajo para ver los montos exactos" \
"y detalles del contenido FILTRADOS."

filter_tool_tiptxt = "Utilize estos filtros para cambiar el contenido dinamicamente de elementos " \
" como categoria que son extensos puede escribir para encontrar su contenido mas rapido"

custompage_description = "La funcion principal de la pagina " \
"es proporcionar el flujo de clientes por medio de los tickets " \
"asi como destarcar los unicos con los repetidos (Una compra con varios elementos) " \
"y a su vez dar informacion de las horas pico filtrable"

#My own sheet fields from database to reuse in other pages 
FieldStore = 'Tienda'
FieldTicket = 'Ticket'
FieldMaterial = 'Material'
FieldGroup = 'Grupo_Articulo'
FieldCategory = 'Categoria'
FieldProduct = 'Producto'
FieldSale = 'Venta'
FieldDateOFSale = 'Fecha Vta'
FieldTimeOFSale = 'Hora Vta'
FieldAmount = 'Cantidad'
FieldUMB = 'UMB'

st.set_page_config(page_title="Análisis de Tickets", page_icon=salesIcon)

st.title("Análisis de Tráfico y Tickets")
st.markdown("Análisis del flujo de clientes, artículos por transacción y horas pico.")
st.sidebar.markdown(custompage_description)

@st.cache_data
def load_data():
    df = pd.read_csv(workDB, low_memory=False)

    df = df.rename(columns={
        'Denominacion 2 del gr.articulos': 'Categoria',
        'Grupo art.': 'Grupo_Articulo'
    })
    
    
    df[FieldDateOFSale] = pd.to_datetime(df[FieldDateOFSale], dayfirst=True, errors='coerce')
        
    # Convertion 
    df['Hora_Solo'] = pd.to_datetime(df[FieldTimeOFSale], format='%H:%M:%S', errors='coerce').dt.hour
        
    if df[FieldSale].dtype == 'object':
        df[FieldSale] = df[FieldSale].astype(str).str.replace('$', '', regex=False)
        df[FieldSale] = df[FieldSale].astype(str).str.replace(',', '', regex=False)
    
    df[FieldSale] = pd.to_numeric(df[FieldSale], errors='coerce')
    df[FieldAmount] = pd.to_numeric(df[FieldAmount], errors='coerce')

    df = df.dropna(subset=[FieldDateOFSale])
    return df

df = load_data()

# -------------------------------------------------------------
# Filters
st.subheader("Filtros de Búsqueda", help= filter_tool_tiptxt, divider="red")
categorySelect = st.multiselect(
    "Seleccione por Categoría",
    options=df[FieldCategory].dropna().unique().tolist(),
    default=df[FieldCategory].dropna().unique().tolist()[:5] # Selecciona los primeros 5 por defecto para no saturar
)

max_date = df[FieldDateOFSale].max().date()
min_date = df[FieldDateOFSale].min().date()

col_filt_1, col_filt_2 = st.columns(2)

with col_filt_1:
    date_slider = st.slider("Seleccione un rango de fechas",
                            min_value=min_date, max_value=max_date, value=(min_date, max_date))

with col_filt_2:
    sucursales = df[FieldStore].dropna().unique().tolist()
    suc_seleccionada = st.multiselect("Filtrar por Sucursal", options=sucursales, default=sucursales)

df_filtered = df[
    (df[FieldCategory].isin(categorySelect)) & 
    (df[FieldStore].isin(suc_seleccionada)) & 
    (df[FieldDateOFSale].dt.date >= date_slider[0]) & 
    (df[FieldDateOFSale].dt.date <= date_slider[1])
]

st.divider() 

# -------------------------------------------------------------
# Metrics
# Check for UNIQUE tickets 
total_tickets = df_filtered[FieldTicket].nunique()
total_units = df_filtered[FieldAmount].sum()

# avoid 0
if total_tickets > 0:
    items_per_ticket = total_units / total_tickets
else:
    items_per_ticket = 0

col1, col2 = st.columns(2)
col1.metric(label="Total de Transacciones (Tickets)", value=f"{total_tickets:,}")
col2.metric(label="Promedio de Artículos por Ticket", value=f"{items_per_ticket:,.1f} uds")

st.divider()

# -------------------------------------------------------------
# Graphs

st.subheader("Tráfico de Clientes por Día",help= tool_tiptxt, divider="red")
trafficby_time = df_filtered.groupby(FieldDateOFSale)[FieldTicket].nunique()
st.line_chart(trafficby_time)

st.divider()

st.subheader("Análisis de Horas Pico (Tráfico por Hora)",help= tool_tiptxt, divider="red")

peak_time = df_filtered.groupby('Hora_Solo', as_index=False)[FieldTicket].nunique()
peak_time = peak_time.dropna(subset=['Hora_Solo'])

hour_graph = alt.Chart(peak_time).mark_bar(
    color='#1f77b4', 
    cornerRadiusEnd=3
).encode(
    x=alt.X(f'{FieldTicket}:Q', title='Cantidad de Tickets'),
    y=alt.Y('Hora_Solo:O', title='Hora del Día (24h)', sort='-x'), 
    tooltip=[alt.Tooltip('Hora_Solo:O', title='Hora'), alt.Tooltip(f'{FieldTicket}:Q', title='Tickets')]
)

st.altair_chart(hour_graph, use_container_width=True)