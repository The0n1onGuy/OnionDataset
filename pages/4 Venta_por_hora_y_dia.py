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

st.set_page_config(page_title="Ventas por Hora y Día", page_icon=salesIcon)

st.title("Ventas por Hora y Día")
st.markdown("Análisis de ingresos económicos a través del tiempo y rendimiento por hora.")
st.sidebar.markdown(custompage_description)

# Load and clean data function
@st.cache_data
def load_data():
    df = pd.read_csv(workDB, low_memory=False)

    # Rename problematic columns to safe variable names
    df = df.rename(columns={
        'Denominacion 2 del gr.articulos': 'Categoria',
        'Grupo art.': 'Grupo_Articulo'
    })
    
    # Format dates
    df[FieldDateOFSale] = pd.to_datetime(df[FieldDateOFSale], dayfirst=True, errors='coerce')
        
    # Extract the hour for the peak hours chart
    df['Hora_Solo'] = pd.to_datetime(df[FieldTimeOFSale], format='%H:%M:%S', errors='coerce').dt.hour
        
    # Clean currency symbols and convert to numeric
    if df[FieldSale].dtype == 'object':
        df[FieldSale] = df[FieldSale].astype(str).str.replace('$', '', regex=False)
        df[FieldSale] = df[FieldSale].astype(str).str.replace(',', '', regex=False)
    
    df[FieldSale] = pd.to_numeric(df[FieldSale], errors='coerce')
    df[FieldAmount] = pd.to_numeric(df[FieldAmount], errors='coerce')

    # Drop rows with invalid dates
    df = df.dropna(subset=[FieldDateOFSale])
    return df

df = load_data()

# -------------------------------------------------------------
# Filters Section
# -------------------------------------------------------------
st.subheader("Filtros de Búsqueda", help=filter_tool_tiptxt, divider="red")

categorySelect = st.multiselect(
    "Seleccione por Categoría",
    options=df[FieldCategory].dropna().unique().tolist(),
    default=df[FieldCategory].dropna().unique().tolist()[:5] # Select first 5 by default
)

max_date = df[FieldDateOFSale].max().date()
min_date = df[FieldDateOFSale].min().date()

col_filt_1, col_filt_2 = st.columns(2)

with col_filt_1:
    date_slider = st.slider(
        "Seleccione un rango de fechas",
        min_value=min_date, 
        max_value=max_date, 
        value=(min_date, max_date)
    )

with col_filt_2:
    sucursales = df[FieldStore].dropna().unique().tolist()
    suc_seleccionada = st.multiselect("Filtrar por Sucursal", options=sucursales, default=sucursales)

# Apply filters to the DataFrame
df_filtered = df[
    (df[FieldCategory].isin(categorySelect)) & 
    (df[FieldStore].isin(suc_seleccionada)) & 
    (df[FieldDateOFSale].dt.date >= date_slider[0]) & 
    (df[FieldDateOFSale].dt.date <= date_slider[1])
]

st.divider() 

# -------------------------------------------------------------
# Metrics Section (KPIs)
# -------------------------------------------------------------
# Calculate total money (Revenue) instead of counting tickets
total_revenue = df_filtered[FieldSale].sum()
total_units = df_filtered[FieldAmount].sum()

col1, col2 = st.columns(2)
col1.metric(label="Ingresos Totales (Revenue)", value=f"${total_revenue:,.2f}")
col2.metric(label="Unidades Vendidas", value=f"{total_units:,}")

st.divider()

# -------------------------------------------------------------
# Graphs

st.subheader("Ingresos por Día", help=tool_tiptxt, divider="red")

# Group by Date and SUM the sales to see revenue trends over days
revenue_by_day = df_filtered.groupby(FieldDateOFSale)[FieldSale].sum()
st.line_chart(revenue_by_day)

st.divider()

st.subheader("Rendimiento por Hora ", help=tool_tiptxt, divider="red")

option_best= "A Mayor Ingreso (Horas Pico)"
option_24h= "Orden Cronológico (23h a 0h)"
y_sort = '-x' #Default in case something fails 

sort_option = st.radio(
    "Ordenar vista por:",
    options=[option_best, option_24h],
    horizontal=True
)

revenue_by_hour = df_filtered.groupby('Hora_Solo', as_index=False)[FieldSale].sum()
revenue_by_hour = revenue_by_hour.dropna(subset=['Hora_Solo'])
if sort_option == option_best:
    y_sort = '-x'  # Peak Hours
else:
    y_sort = '-y'  # Use 24H format
    
# Create Altair Bar Chart
hour_revenue_graph = alt.Chart(revenue_by_hour).mark_bar(
    color='#1f77b4', # Green color to represent money/revenue
    cornerRadiusEnd=3
).encode(
    x=alt.X(f'{FieldSale}:Q', title='Ingresos Totales ($)'),
    y=alt.Y('Hora_Solo:O', title='Hora del Día (24h)', sort= y_sort), 
    tooltip=[
        alt.Tooltip('Hora_Solo:O', title='Hora'), 
        # Format tooltip as currency ($,.2f)
        alt.Tooltip(f'{FieldSale}:Q', title='Ingresos', format='$,.2f')
    ]
)

# Render the chart in Streamlit
st.altair_chart(hour_revenue_graph, use_container_width=True)
