import altair as alt
import pandas as pd
import streamlit as st

#My tiny icon library
salesIcon = "/workspaces/OnionDataset/public/assets/sales-report.svg"
hover_icon = "/workspaces/OnionDataset/public/assets/cursor-hover-20-filler white.svg"
workDB = "data/BD_EVALUACION.csv" #My datasource (Database)

MXNcurrency = "(MXN)" 
USDcurrency = "(USD)" 

tool_tiptxt = " Pase el cursor (hover) sobre las líneas, " \
"barras de los gráficos, o grafos coloreados de azul " \
"de abajo para ver los montos exactos" \
"y detalles del contenido FILTRADOS."

filter_tool_tiptxt = "Utilize estos filtros para cambiar el contenido dinamicamente de elementos " \
" como categoria que son extensos puede escribir para encontrar su contenido mas rapido"

custompage_description = "Esta pagina le permitira observar " \
"las ventas en modo de promedio vendido , totales, unidades vendidas respectivas a la categoria."
#My own sheet fields from database to reuse in other pages 

FieldStore = 'Tienda'
FieldTicket = 'Ticket'
FieldMaterial = 'Material'
#FieldGroup = 'Grupo art.'#Old denomination since Altir conflicts with . 
#FieldCategory = 'Denominacion 2 del gr.articulos' 
FieldGroup = 'Grupo_Articulo'
FieldCategory = 'Categoria'
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

#st.sidebar.success("Una descripcion breve de la pagina:")
st.sidebar.markdown(custompage_description)

#$st.write("# Welcome to Streamlit!")
#st.markdown("My page content")

@st.cache_data
def load_data():
    df = pd.read_csv(workDB)

    # Refer these column to other names due to naming 
    df = df.rename(columns={
        'Denominacion 2 del gr.articulos': 'Categoria',
        'Grupo art.': 'Grupo_Articulo'
    })
    # Convert Dates to Date Time so its DD/MM/YY
    df[FieldDateOFSale]= pd.to_datetime(
        df[FieldDateOFSale]
        ,dayfirst=True
        ,errors = 'coerce'
        )
    if df[FieldSale].dtype == 'object':
        df[FieldSale] = df[FieldSale].astype(str).str.replace('$', '', regex=False)
        df[FieldSale] = df[FieldSale].astype(str).str.replace(',', '', regex=False)
    
    
    df[FieldSale] = pd.to_numeric(df[FieldSale], errors='coerce')
    df[FieldAmount] = pd.to_numeric(df[FieldAmount], errors='coerce')

    #Drop row if it fails on dates 
    df = df.dropna(subset=[FieldDateOFSale])
    return df

df = load_data()


# -------------------------------------------------------------
# FILTERS

st.subheader("Filtros de Busqueda", help= filter_tool_tiptxt, divider="red")
categorySelect = st.multiselect(
    "Seleccione por Categoria",
    #df.categorySelect.unique(),
    df[FieldCategory].unique().tolist(),
    #options = df[FieldCategory].unique().tolist()[1],
    default = df[FieldCategory].unique().tolist()[9],
)
max_date = df[FieldDateOFSale].max().date()
min_date = df[FieldDateOFSale].min().date()
col_filt_1, col_filt_2= st.columns(2)

with col_filt_1:
    #Filter by Date
    date_list = df[FieldDateOFSale].unique().tolist()
    date_slider = st.slider("Seleccione un rango de fechas "
                            ,min_value = min_date
                            ,max_value = max_date
                            , value = (min_date, max_date))

with col_filt_2:
    # Filter by store
    stores_list = df[FieldStore].unique().tolist()
    selected_store = st.multiselect("Filtrar por Sucursal", options=stores_list, default=stores_list)


# Apply filters
#df_filtered = df[(df[FieldCategory].isin(categorySelect)) & (df[FieldStore].isin(suc_seleccionada))]

df_filtered = df[
    (df[FieldCategory].isin(categorySelect)) & 
    (df[FieldStore].isin(selected_store)) &
    (df[FieldDateOFSale].dt.date >= date_slider[0]) & 
    (df[FieldDateOFSale].dt.date <= date_slider[1])
]

st.divider() 

# All the calculations to show in the section of the page's metrics
total_income = df_filtered[FieldSale].sum()
total_units = df_filtered[FieldAmount].sum()
avg_ticket = df_filtered[FieldSale].mean()

col1, col2, col3 = st.columns(3)
col1.metric(label="Ingreso Total " + MXNcurrency, value=f"${total_income:,.2f}")
col2.metric(label="Unidades Vendidas ", value=f"{total_units:,}")
col3.metric(label="Venta Promedio " + MXNcurrency, value=f"${avg_ticket:,.2f}")

st.divider()
# -------------------------------------------------------------
# GRAPHS

#col_graf_1, col_graf_2 = st.columns(2)

st.subheader(" Ventas basadas en fecha " + MXNcurrency, help= tool_tiptxt ,divider="red")
salesby_time = df_filtered.groupby(FieldDateOFSale)[FieldSale].sum()
st.line_chart(salesby_time)


st.subheader(" Ventas por Categoría " + MXNcurrency, help= tool_tiptxt, divider="red")

salesby_category = df_filtered.groupby(FieldCategory, as_index=False)[FieldSale].sum()

salesby_category = salesby_category.dropna(subset=[FieldCategory])
salesby_category = salesby_category[salesby_category[FieldCategory].astype(str).str.strip() != '']


dynamicbar_graph = alt.Chart(salesby_category).mark_bar(
    orient="horizontal",
    color='#1f77b4',
    cornerRadiusEnd=3 
).encode(
    x=alt.X(f'{FieldSale}:Q', title='Ingresos por Ventas ($)'),
    
    # Map to the respective fields
    
    y=alt.Y(
        f'{FieldCategory}:N', 
        sort='-x', 
        title='',
        axis=alt.Axis(labelLimit=350) 
    ),
    
    tooltip=[FieldCategory, alt.Tooltip(f'{FieldSale}:Q', format='$,.2f')]
)

st.altair_chart(dynamicbar_graph, use_container_width=True)