import pandas as pd
import streamlit as st

salesIcon = "/workspaces/OnionDataset/public/assets/sales-report.svg"
workDB = "data/BD_EVALUACION.csv" 

custompage_description = "Esta página proporciona conclusiones estratégicas " \
"basadas en los datos actuales, y un explorador de datos crudos (Catálogo) " \
"para auditoría y búsqueda de SKUs específicos."

FieldStore = 'Tienda'
FieldTicket = 'Ticket'
FieldMaterial = 'Material'
FieldCategory = 'Categoria'
FieldProduct = 'Producto'
FieldSale = 'Venta'
FieldDateOFSale = 'Fecha Vta'
FieldTimeOFSale = 'Hora Vta'
FieldAmount = 'Cantidad'

st.set_page_config(page_title="Insights y Explorador", page_icon=salesIcon, layout="wide")

st.title("Insights y Catálogo de Datos")
st.sidebar.markdown(custompage_description)

@st.cache_data
def load_data():
    df = pd.read_csv(workDB, low_memory=False) #Read it without limit, even if its everything but dont crash my app
    df = df.rename(columns={'Denominacion 2 del gr.articulos': 'Categoria'})
    df[FieldDateOFSale] = pd.to_datetime(df[FieldDateOFSale], dayfirst=True, errors='coerce')
    df['Hora_Solo'] = pd.to_datetime(df[FieldTimeOFSale], format='%H:%M:%S', errors='coerce').dt.hour
    
    if df[FieldSale].dtype == 'object':
        df[FieldSale] = df[FieldSale].astype(str).str.replace('$', '', regex=False)
        df[FieldSale] = df[FieldSale].astype(str).str.replace(',', '', regex=False)
    
    df[FieldSale] = pd.to_numeric(df[FieldSale], errors='coerce')
    df[FieldAmount] = pd.to_numeric(df[FieldAmount], errors='coerce')
    df = df.dropna(subset=[FieldDateOFSale])
    return df
with st.spinner('Cargando la base de datos, por favor espere...'):
    df = load_data()

# -------------------------------------------------------------
# INSIGHTS
st.subheader("Resumen Ejecutivo y Recomendaciones")
st.divider()

top_store = df.groupby(FieldStore)[FieldSale].sum().idxmax()
top_hour = df.groupby('Hora_Solo')[FieldSale].sum().idxmax()
top_category = df.groupby(FieldCategory)[FieldSale].sum().idxmax()

col_cat_1, col_cat_2, col_cat_3 = st.columns(3)

with col_cat_1:
    st.subheader("Rendimiento de Tienda")
    st.info(f"La sucursal **{top_store}** lidera las ventas generales. Podría ser valioso analizar sus prácticas operativas para replicarlas en las demás tiendas.")

with col_cat_2:
    st.subheader("Optimización de Personal")
    st.info(f"La hora pico de ingresos es alrededor de las **{int(top_hour)}:00 hrs**. Se sugiere programar los descansos del personal de caja fuera de este horario para evitar cuellos de botella.")

with col_cat_3:
    st.subheader("Estrategia de Inventario")
    st.info(f"La categoría más rentable actualmente es **{top_category}**. Se recomienda asegurar el abastecimiento de estos productos para la próxima semana.")
st.divider()

# -------------------------------------------------------------
# DATA EXPLORER & CATALOG (The Table)
# -------------------------------------------------------------
st.subheader("Catálogo de Productos y Explorador", divider="red")
st.markdown("Utilice el buscador para auditar productos específicos o exportar los datos crudos.")

all_columns = [FieldDateOFSale, FieldTimeOFSale, FieldStore, FieldTicket, FieldCategory, FieldProduct, FieldAmount, FieldSale]

# Column Selector (Multiselect)
selected_columns = st.multiselect(
    "Seleccione los campos (columnas) a mostrar en la tabla:",
    options=all_columns,
    default=[ FieldTimeOFSale, FieldStore, FieldTicket, FieldCategory,] # Empty by default means "Show All"
)

# Search Bar for the catalog
search_query = st.text_input("🔍 Buscar por Nombre de Producto, Categoría o Tienda...", "")
with st.spinner('Actualizando el catálogo, procesando datos...'):
    # apply filters logic
    df_display = df.copy()

# If user typed something in the search bar, filter the remaining dataframe
if search_query:
    mask = (
        df_display[FieldProduct].astype(str).str.contains(search_query, case=False, na=False) |
        df_display[FieldCategory].astype(str).str.contains(search_query, case=False, na=False) |
        df_display[FieldMaterial].astype(str).str.contains(search_query, case=False, na=False)
    )
    df_display = df_display[mask]

if len(selected_columns) > 0:
    columns_to_show = selected_columns
else:
    columns_to_show = all_columns # Fallback to show everything
# Display the interactive dataframe
st.dataframe(
    df_display[columns_to_show],
    use_container_width=True,
    height=400,
    hide_index=True # Hides the ugly pandas row numbers
)