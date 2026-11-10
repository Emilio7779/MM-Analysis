import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de la página
st.set_page_config(page_title="Dashboard Ventas - Región South", layout="wide")

@st.cache_data
def load_data(file_path):
    xls = pd.ExcelFile(file_path)
    all_south_data = []
    
    for sheet in xls.sheet_names:
        try:
            df = pd.read_excel(file_path, sheet_name=sheet)
            df.columns = [str(c).strip() for c in df.columns]
            
            if 'Region' in df.columns:
                south_df = df[df['Region'].astype(str).str.strip().str.upper() == 'SOUTH'].copy()
                if not south_df.empty:
                    category = "Tablets" if "Tablet" in sheet else "General"
                    south_df['Categoría'] = category
                    all_south_data.append(south_df)
        except Exception:
            pass
            
    combined = pd.concat(all_south_data, ignore_index=True)
    
    # Normalización de columnas
    combined['Año'] = pd.to_numeric(combined['Year'], errors='coerce')
    combined['Semana'] = pd.to_numeric(combined['Week'], errors='coerce')
    combined['Centro'] = combined['Store Name'].fillna(combined.get('Daily Store Name', 'Desconocido'))
    
    # Métricas principales
    combined['Sell-Out'] = pd.to_numeric(combined['SO'], errors='coerce').fillna(0)
    combined['Store Capa'] = pd.to_numeric(combined['SC'], errors='coerce').fillna(0)
    combined['Revenue'] = pd.to_numeric(combined.get('RV', 0), errors='coerce').fillna(0)
    combined['Value Store Capa'] = pd.to_numeric(combined.get('SC RV', 0), errors='coerce').fillna(0)
    
    # Porcentajes en base 100
    combined['In-Store Share'] = combined.apply(
        lambda r: ((r['Sell-Out'] / r['Store Capa']) * 100) if r['Store Capa'] > 0 else 0, axis=1
    )
    combined['Value In-Store Share'] = combined.apply(
        lambda r: ((r['Revenue'] / r['Value Store Capa']) * 100) if r['Value Store Capa'] > 0 else 0, axis=1
    )
    
    return combined.dropna(subset=['Año', 'Semana'])

# Cargar datos desde el archivo Excel
data = load_data("MM_Analysis_2.xlsx")

# --- BARRA LATERAL: FILTROS DESPLEGABLES ---
st.sidebar.header("🎯 Filtros de Selección (Región Sur)")

anos_disponibles = sorted([int(y) for y in data['Año'].unique()])
selected_year = st.sidebar.selectbox("📅 Seleccionar Año:", options=anos_disponibles, index=len(anos_disponibles) - 1)

tiendas_disponibles = ["Todos los Centros"] + sorted(data['Centro'].unique().tolist())
selected_store = st.sidebar.selectbox("🏪 Seleccionar Centro:", options=tiendas_disponibles, index=0)

semanas_disponibles = ["Todas las Semanas"] + sorted([int(w) for w in data['Semana'].unique()])
selected_week = st.sidebar.selectbox("📆 Seleccionar Semana:", options=semanas_disponibles, index=0)

# --- APLICACIÓN DE FILTROS ---
filtered_df = data[data['Año'] == selected_year].copy()

if selected_store != "Todos los Centros":
    filtered_df = filtered_df[filtered_df['Centro'] == selected_store]

if selected_week != "Todas las Semanas":
    filtered_df = filtered_df[filtered_df['Semana'] == selected_week]

# --- CONTENIDO PRINCIPAL ---
st.title("📊 Análisis de Ventas - Región Sur")
st.markdown(f"Mostrando datos para **Año {selected_year}** | **{selected_store}** | **{selected_week}**")

# KPIs superiores
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
total_rv = filtered_df['Revenue'].sum()
total_so = filtered_df['Sell-Out'].sum()
total_sc = filtered_df['Store Capa'].sum()
ticket_medio = total_rv / total_so if total_so > 0 else 0

kpi1.metric("💰 Revenue (Ingresos)", f"{total_rv:,.2f} €")
kpi2.metric("📦 Sell-Out (Unidades)", f"{total_so:,.0f}")
kpi3.metric("🏪 Store Capa", f"{total_sc:,.0f}")
kpi4.metric("🏷️ Ticket Medio", f"{ticket_medio:,.2f} €")

st.divider()

# Gráficos interactivos
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Evolución Semanal de Revenue")
    weekly_trend = filtered_df.groupby(['Semana', 'Año'])['Revenue'].sum().reset_index()
    weekly_trend['Año'] = weekly_trend['Año'].astype(str)
    fig_line = px.line(weekly_trend, x='Semana', y='Revenue', color='Año', markers=True,
                       labels={'Semana': 'Semana del Año', 'Revenue': 'Revenue (€)', 'Año': 'Año'},
                       title="Revenue por Semana")
    st.plotly_chart(fig_line, use_container_width=True)

with col2:
    st.subheader("🏪 Revenue por Centro")
    store_trend_df = filtered_df.groupby('Centro')['Revenue'].sum().reset_index().sort_values(by='Revenue', ascending=True)
    fig_bar = px.bar(store_trend_df, x='Revenue', y='Centro', orientation='h',
                     labels={'Revenue': 'Revenue (€)', 'Centro': 'Centro'},
                     title="Ranking de Tiendas en Región Sur", color='Revenue', color_continuous_scale='Blues')
    st.plotly_chart(fig_bar, use_container_width=True)

# --- TABLA DE DATOS ---
st.subheader("📋 Tabla de Datos Filtrados")

table_display = filtered_df[[
    'Año', 'Semana', 'Centro', 'Categoría', 
    'Sell-Out', 'Store Capa', 'Revenue', 
    'Value Store Capa', 'In-Store Share', 'Value In-Store Share'
]].copy()

st.dataframe(
    table_display,
    use_container_width=True,
    column_config={
        "Año": st.column_config.NumberColumn("Año", format="%d"),
        "Semana": st.column_config.NumberColumn("Semana", format="%d"),
        "Sell-Out": st.column_config.NumberColumn("Sell-Out", format="%','.0f"),
        "Store Capa": st.column_config.NumberColumn("Store Capa", format="%','.0f"),
        "Revenue": st.column_config.NumberColumn("Revenue (€)", format="%.2f €"),
        "Value Store Capa": st.column_config.NumberColumn("Value Store Capa (€)", format="%.2f €"),
        "In-Store Share": st.column_config.NumberColumn("In-Store Share", format="%.0f %%"),
        "Value In-Store Share": st.column_config.NumberColumn("Value In-Store Share", format="%.0f %%")
    }
)

# Botón de descarga CSV
csv_data = table_display.to_csv(index=False).encode('utf-8')
st.download_button("📥 Descargar Datos Filtrados (CSV)", data=csv_data, file_name="Ventas_Region_South.csv", mime="text/csv")