import folium
import pandas as pd
import plotly.express as px
import streamlit as st
from utils import apply_listings_filters, load_listings_data, render_app_sidebar

try:
    import pydeck as pdk
except ImportError:  # pragma: no cover
    pdk = None

try:
    from streamlit_folium import folium_static
except ImportError:  # pragma: no cover
    folium_static = None

st.title("Alojamientos en Madrid")
render_app_sidebar("listings")

df = load_listings_data()
if df is None:
    st.stop()

df = apply_listings_filters(df)
if df is None:
    st.stop()

st.caption(f"{len(df)} filas filtradas")

if df.empty:
    st.info("No hay filas que cumplan los filtros actuales.")
    st.stop()

st.subheader("1. Vista rápida")
st.caption("Responde a: ¿dónde se concentran los alojamientos en Madrid?")
map_df = df[["latitude", "longitude", "neighbourhood", "room_type", "price"]].copy()
if len(map_df) > 3000:
    map_df = map_df.sample(n=3000, random_state=42)
st.map(map_df[["latitude", "longitude"]], zoom=11, use_container_width=True)

st.subheader("2. Mapa con PyDeck")
st.caption("Responde a: ¿cómo se distribuyen los alojamientos por densidad espacial?")
if pdk is None:
    st.info("PyDeck no está disponible en este entorno; se muestra la vista rápida como alternativa.")
    st.map(map_df[["latitude", "longitude"]], zoom=11, use_container_width=True)
else:
    deck_df = df if len(df) <= 3000 else df.sample(n=3000, random_state=42)
    layer = pdk.Layer(
        "HexagonLayer",
        data=deck_df[["longitude", "latitude"]],
        get_position="[longitude, latitude]",
        radius=200,
        elevation_scale=4,
        elevation_range=[0, 1000],
        pickable=True,
        extruded=True,
    )
    view_state = pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=11, pitch=45)
    try:
        pydeck_map = pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            map_provider="mapbox",
            map_style=pdk.map_styles.MAPBOX_LIGHT,
            tooltip={"text": "{elevationValue}"},
        )
        st.pydeck_chart(pydeck_map, use_container_width=True)
    except Exception as exc:
        st.warning(f"No se pudo renderizar PyDeck: {exc}")
        st.map(map_df[["latitude", "longitude"]], zoom=11, use_container_width=True)

st.subheader("3. Mapa con Folium")
st.caption("Responde a: ¿cómo se agrupan los alojamientos por barrio y precio?")
if folium_static is None:
    st.info("streamlit-folium no está disponible en este entorno.")
else:
    folium_map = folium.Map(location=[40.4168, -3.7038], zoom_start=11, tiles="CartoDB positron")
    marker_cluster = folium.plugins.MarkerCluster()
    for _, row in df.head(3000).iterrows():
        popup_html = (
            f"Barrio: {row['neighbourhood']}<br>"
            f"Tipo: {row['room_type']}<br>"
            f"Precio: {row['price']}"
        )
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=250),
        ).add_to(marker_cluster)
    marker_cluster.add_to(folium_map)
    try:
        folium_static(folium_map, width=700, height=450)
    except Exception as exc:
        st.warning(f"No se pudo renderizar Folium: {exc}")
        st.map(df[["latitude", "longitude"]], zoom=11, use_container_width=True)

st.subheader("4. Precio vs disponibilidad")
st.caption("Responde a: ¿existe relación entre precio y disponibilidad?")
scatter = px.scatter(
    df,
    x="availability_365",
    y="price",
    color="room_type",
    hover_data=["neighbourhood", "room_type", "price"],
    title="Precio vs disponibilidad",
)
scatter.update_layout(height=400)
st.plotly_chart(scatter, use_container_width=True)

st.subheader("5. Tendencia por barrio")
st.caption("Responde a: ¿cómo cambia la disponibilidad media por barrio?")
agg = (
    df.groupby("neighbourhood", as_index=False)["availability_365"]
    .mean()
    .sort_values("availability_365", ascending=False)
)
line_chart = px.line(
    agg,
    x="neighbourhood",
    y="availability_365",
    title="Disponibilidad media por barrio",
)
line_chart.update_layout(height=400)
st.plotly_chart(line_chart, use_container_width=True)

st.subheader("Vista filtrada")
st.dataframe(
    df[["neighbourhood", "room_type", "price", "minimum_nights", "availability_365"]].head(50),
    use_container_width=True,
)
