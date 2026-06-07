import altair as alt
import pandas as pd
import streamlit as st

# Icon library
salesIcon = "/workspaces/OnionDataset/public/assets/sales-report.svg"
workDB = "data/BD_EVALUACION.csv" 

MXNcurrency = "(MXN)" 

tool_tiptxt = " Pase el cursor (hover) sobre las barras de los gráficos " \
"de abajo para ver los montos exactos y detalles del contenido FILTRADO."

filter_tool_tiptxt = "Utilice estos filtros para cambiar el contenido dinámicamente. " \
"Las categorías funcionan en cascada: al elegir una, se filtran las subcategorías."

custompage_description = "Esta página le permitirá observar " \
"el rendimiento individual de los productos, descubrir los más vendidos inspirado en Leaderboard " \
"y analizar la participación de ventas y piezas por categoría."

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

st.set_page_config(page_title="Análisis de Productos", page_icon=salesIcon, layout="wide")

st.title(" Análisis de Productos y Categorías")
st.sidebar.markdown(custompage_description)

@st.cache_data
def load_data():
    df = pd.read_csv(workDB, low_memory=False)

    df = df.rename(columns={
        'Denominacion 2 del gr.articulos': 'Categoria',
        'Grupo art.': 'Grupo_Articulo'
    })
    
    # -------------------------------------------------------------
    # Hierarchical sort, get big category , then smaller ones in order, not all categories have 2 smaller ones 
    split_cats = df[FieldCategory].str.split(r'\s*-\s*', n=2, expand=True)
    df['Cat_L1'] = split_cats[0].fillna('Sin Categoría') # Main Category
    df['Cat_L2'] = split_cats[1].fillna('')              # Subcategory 1
    df['Cat_L3'] = split_cats[2].fillna('')              # Subcategory 2
    
    # Convert Dates
    df[FieldDateOFSale]= pd.to_datetime(df[FieldDateOFSale], dayfirst=True, errors='coerce')
    
    # Clean money formats
    if df[FieldSale].dtype == 'object':
        df[FieldSale] = df[FieldSale].astype(str).str.replace('$', '', regex=False)
        df[FieldSale] = df[FieldSale].astype(str).str.replace(',', '', regex=False)
    
    df[FieldSale] = pd.to_numeric(df[FieldSale], errors='coerce')
    df[FieldAmount] = pd.to_numeric(df[FieldAmount], errors='coerce')

    df = df.dropna(subset=[FieldDateOFSale])
    return df

df = load_data()

# -------------------------------------------------------------
# CASCADING FILTERS SECTION
# -------------------------------------------------------------
st.subheader("Filtros de Búsqueda", help=filter_tool_tiptxt, divider="red")
st.write("Dejar estos o todos en blanco, mostrara todos por sucursal")
col_cat_1, col_cat_2, col_cat_3 = st.columns(3)

with col_cat_1:

    l1_options = sorted(df['Cat_L1'].unique().tolist())
    selected_l1 = st.multiselect("Categoría Principal", l1_options, default=l1_options[:3])
    # Filter DF for next levels (If empty, show all) and doesnt die
    df_l1 = df[df['Cat_L1'].isin(selected_l1)] if selected_l1 else df

with col_cat_2:
    l2_options = sorted([c for c in df_l1['Cat_L2'].unique().tolist() if c != ''])
    selected_l2 = st.multiselect("Subcategoría 1", l2_options, default=l2_options)
    df_l2 = df_l1[df_l1['Cat_L2'].isin(selected_l2)] if selected_l2 else df_l1

with col_cat_3:

    l3_options = sorted([c for c in df_l2['Cat_L3'].unique().tolist() if c != ''])
    if l3_options:
        selected_l3 = st.multiselect("Subcategoría 2", l3_options, default=l3_options)
        df_l3 = df_l2[df_l2['Cat_L3'].isin(selected_l3)] if selected_l3 else df_l2
    else:
        st.write("No hay Subcategoría 2 para esta selección.")
        df_l3 = df_l2

col_filt_1, col_filt_2 = st.columns(2)
min_date, max_date = df[FieldDateOFSale].min().date(), df[FieldDateOFSale].max().date()

with col_filt_1:
    date_slider = st.slider("Rango de Fechas", min_value=min_date, max_value=max_date, value=(min_date, max_date))

with col_filt_2:
    stores_list = df[FieldStore].dropna().unique().tolist()
    selected_store = st.multiselect("Sucursal", options=stores_list, default=stores_list)

# Filter implemented
df_filtered = df_l3[
    (df_l3[FieldStore].isin(selected_store)) &
    (df_l3[FieldDateOFSale].dt.date >= date_slider[0]) & 
    (df_l3[FieldDateOFSale].dt.date <= date_slider[1])
]

st.divider() 

# -------------------------------------------------------------
# GRAPHS
col_graphs_1, col_graphs_2 = st.columns(2)

with col_graphs_1:
    st.subheader(f"Venta por Producto {MXNcurrency}", help=tool_tiptxt, divider="red")
    
    # Slider for max top N
    top_n = st.slider("Maximo productos a mostrar", min_value=50, max_value=100, value=50, step=5)
    sales_by_product = df_filtered.groupby(FieldProduct, as_index=False)[FieldSale].sum()
    sales_by_product = sales_by_product.nlargest(top_n, FieldSale) 
    
    bar_sales_product = alt.Chart(sales_by_product).mark_bar(orient="horizontal", color='#1f77b4', cornerRadiusEnd=3).encode(
        x=alt.X(f'{FieldSale}:Q', title='Ingresos ($)'),
        y=alt.Y(f'{FieldProduct}:N', sort='-x', title='', axis=alt.Axis(labelLimit=300)),
        tooltip=[FieldProduct, alt.Tooltip(f'{FieldSale}:Q', format='$,.2f', title='Ventas')]
    )
    st.altair_chart(bar_sales_product, use_container_width=True)

with col_graphs_2:
    st.subheader("Top Productos (Unidades)", help=tool_tiptxt, divider="orange")
    
    # Slider for max top N
    top_n = st.slider("Mostrar Top N Productos", min_value=5, max_value=50, value=15, step=5)
    
    units_by_product = df_filtered.groupby(FieldProduct, as_index=False)[FieldAmount].sum()
    units_by_product = units_by_product.nlargest(top_n, FieldAmount)
    
    bar_units_product = alt.Chart(units_by_product).mark_bar(orient="horizontal", color='#ff7f0e', cornerRadiusEnd=3).encode(
        x=alt.X(f'{FieldAmount}:Q', title='Unidades/Piezas'),
        y=alt.Y(f'{FieldProduct}:N', sort='-x', title='', axis=alt.Axis(labelLimit=300)),
        tooltip=[FieldProduct, alt.Tooltip(f'{FieldAmount}:Q', title='Piezas Totales')]
    )
    st.altair_chart(bar_units_product, use_container_width=True)


# -------------------------------------------------------------
# GRAPHS

st.subheader("Participación General (Categoría Completa)", divider="red")
col_part_1, col_part_2 = st.columns(2)

# We group by the original full FieldCategory to show the exact breakdown
grouped_cat = df_filtered.groupby(FieldCategory, as_index=False)[['Venta', 'Cantidad']].sum()

with col_part_1:
    #st.markdown("**Participación por Ingresos ($)**")
    st.subheader("Top Productos (Unidades)", help=tool_tiptxt, divider="red")
    part_sales = alt.Chart(grouped_cat).mark_bar(orient="horizontal", color='#1f77b4', cornerRadiusEnd=3).encode(
        x=alt.X(f'{FieldSale}:Q', title='Ingresos ($)'),
        y=alt.Y(f'{FieldCategory}:N', sort='-x', title='', axis=alt.Axis(labelLimit=350)),
        tooltip=[FieldCategory, alt.Tooltip(f'{FieldSale}:Q', format='$,.2f')]
    )
    st.altair_chart(part_sales, use_container_width=True)

with col_part_2:
    #st.markdown("**Participación por Piezas (Uds)**")
    st.subheader("Top Productos (Unidades)", help=tool_tiptxt, divider="orange")
    part_units = alt.Chart(grouped_cat).mark_bar(orient="horizontal", color='#ff7f0e', cornerRadiusEnd=3).encode(
        x=alt.X(f'{FieldAmount}:Q', title='Unidades'),
        y=alt.Y(f'{FieldCategory}:N', sort='-x', title='', axis=alt.Axis(labelLimit=350)),
        tooltip=[FieldCategory, alt.Tooltip(f'{FieldAmount}:Q')]
    )
    st.altair_chart(part_units, use_container_width=True)