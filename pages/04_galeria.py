import time
from textwrap import dedent

import streamlit as st
import pandas as pd

from utils import load_listings_data, load_titanic_data

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
except Exception:  # pragma: no cover
    plt = None
    sns = None

try:
    import altair as alt
except Exception:  # pragma: no cover
    alt = None

try:
    import plotly.express as px
except Exception:  # pragma: no cover
    px = None

try:
    import pydeck as pdk
except Exception:
    pdk = None

st.title("Galería de visualizaciones")
st.markdown("Ejemplos rápidos de librerías y cuándo usarlas.")

# Load data once (cached in utils)
listings = load_listings_data()
titanic = load_titanic_data()

tabs = st.tabs(["Nativos", "Matplotlib/Seaborn", "Altair", "Vega-Lite", "Plotly", "Mapas", "Arquitectura"])

# --- Nativos ---
with tabs[0]:
    st.header("Gráficos nativos (st.line_chart / st.bar_chart)")
    st.write("Úsalo cuando: necesitas una representación rápida y responsiva sin dependencia externa.")
    st.write("Limitación: menos control estético y de interactividad fina.")

    start = time.perf_counter()
    if listings is not None:
        top = listings["neighbourhood"].value_counts().head(10)
        st.bar_chart(top)
    elif titanic is not None:
        st.line_chart(titanic["Age"].dropna().head(50))
    elapsed = time.perf_counter() - start
    st.caption(f"Render time: {elapsed:.3f} s")

    with st.expander("Código relevante"):
        st.code(dedent('''
        top = listings["neighbourhood"].value_counts().head(10)
        st.bar_chart(top)
        '''))

# --- Matplotlib / Seaborn ---
with tabs[1]:
    st.header("Matplotlib / Seaborn")
    st.write("Úsalo cuando: necesitas personalización detallada de figura o estilos estadísticos.")
    st.write("Limitación: integración less interactive; requiere conversion para web interactivity.")

    start = time.perf_counter()
    if plt is None or sns is None or listings is None:
        st.info("Matplotlib/Seaborn no disponibles o no hay datos.")
    else:
        fig, ax = plt.subplots()
        sns.histplot(listings["price"].dropna(), bins=40, ax=ax)
        ax.set_title("Distribución de precios (muestra)")
        st.pyplot(fig)
    elapsed = time.perf_counter() - start
    st.caption(f"Render time: {elapsed:.3f} s")

    with st.expander("Código relevante"):
        st.code(dedent('''
        fig, ax = plt.subplots()
        sns.histplot(listings["price"].dropna(), bins=40, ax=ax)
        st.pyplot(fig)
        '''))

# --- Altair ---
with tabs[2]:
    st.header("Altair")
    st.write("Úsalo cuando: quieres gráficos declarativos y vinculables con filtros.")
    st.write("Limitación: puede ser lento con datasets grandes sin agregación.")

    start = time.perf_counter()
    if alt is None or listings is None:
        st.info("Altair no disponible o no hay datos.")
    else:
        sample = listings[["price", "availability_365", "room_type"]].dropna()
        if len(sample) > 2000:
            sample = sample.sample(2000, random_state=1)
        chart = alt.Chart(sample).mark_circle(opacity=0.6).encode(
            x="availability_365",
            y="price",
            color="room_type",
            tooltip=["room_type", "price", "availability_365"],
        ).interactive()
        st.altair_chart(chart, use_container_width=True)
    elapsed = time.perf_counter() - start
    st.caption(f"Render time: {elapsed:.3f} s")

    with st.expander("Código relevante"):
        st.code(dedent('''
        sample = listings[["price", "availability_365", "room_type"]].dropna().sample(2000)
        chart = alt.Chart(sample).mark_circle().encode(...)
        st.altair_chart(chart)
        '''))

# --- Vega-Lite (st.vega_lite_chart) ---
with tabs[3]:
    st.header("Vega-Lite (st.vega_lite_chart)")
    st.write("Úsalo cuando: necesitas especificar un spec Vega-Lite directamente.")
    st.write("Limitación: escribir specs manualmente puede ser verboso.")

    start = time.perf_counter()
    if listings is None:
        st.info("No hay datos para Vega-Lite.")
    else:
        spec = {
            "mark": "point",
            "encoding": {
                "x": {"field": "availability_365", "type": "quantitative"},
                "y": {"field": "price", "type": "quantitative"},
                "color": {"field": "room_type", "type": "nominal"},
                "tooltip": [{"field": "neighbourhood", "type": "nominal"}, {"field": "price", "type": "quantitative"}]
            }
        }
        st.vega_lite_chart(listings.dropna(subset=["price", "availability_365"]).head(2000), spec, use_container_width=True)
    elapsed = time.perf_counter() - start
    st.caption(f"Render time: {elapsed:.3f} s")

    with st.expander("Código relevante"):
        st.code(dedent('''
        spec = {...}
        st.vega_lite_chart(df.head(2000), spec)
        '''))

# --- Plotly ---
with tabs[4]:
    st.header("Plotly")
    st.write("Úsalo cuando: necesitas interacción avanzada y controles del usuario.")
    st.write("Limitación: tamaño del bundle y carga en navegadores antiguos.")

    start = time.perf_counter()
    if px is None or listings is None:
        st.info("Plotly no disponible o no hay datos.")
    else:
        fig = px.box(listings.dropna(subset=["price", "room_type"]), x="room_type", y="price", title="Precio por tipo de habitación")
        st.plotly_chart(fig, use_container_width=True)
    elapsed = time.perf_counter() - start
    st.caption(f"Render time: {elapsed:.3f} s")

    with st.expander("Código relevante"):
        st.code(dedent('''
        fig = px.box(listings, x="room_type", y="price")
        st.plotly_chart(fig)
        '''))

# --- Mapas ---
with tabs[5]:
    st.header("Mapas")
    st.write("Úsalo cuando: necesitas ver distribución geográfica.")
    st.write("Limitación: las capas avanzadas requieren pydeck o folium y pueden necesitar tokens.")

    start = time.perf_counter()
    if listings is None:
        st.info("No hay datos geográficos.")
    else:
        coords = listings.dropna(subset=["latitude", "longitude"]).loc[:, ["latitude", "longitude"]].head(3000)
        if pdk is not None:
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=coords.rename(columns={"latitude": "lat", "longitude": "lon"}),
                get_position=["lon", "lat"],
                get_radius=100,
            )
            view_state = pdk.ViewState(latitude=40.4168, longitude=-3.7038, zoom=11)
            deck = pdk.Deck(
                layers=[layer],
                initial_view_state=view_state,
                map_provider="mapbox",
                map_style="mapbox://styles/mapbox/light-v10",
                tooltip={"text": "{latitude}, {longitude}"},
            )
            st.pydeck_chart(deck, use_container_width=True)
        else:
            st.map(coords)
    elapsed = time.perf_counter() - start
    st.caption(f"Render time: {elapsed:.3f} s")

    with st.expander("Código relevante"):
        st.code(dedent('''
        coords = listings.dropna(subset=["latitude","longitude"]).head(3000)
        st.map(coords)
        '''))

# --- Arquitectura ---
with tabs[6]:
    st.header("Arquitectura de la pipeline")
    st.write("Diagrama simple de la ruta de datos desde CSV hasta visualización.")
    dot = '''
    digraph G {
      rankdir=LR;
      CSV -> Validacion -> Cache -> Filtros -> Agregacion -> Visualizacion;
    }
    '''
    st.graphviz_chart(dot)
    st.write("No se duplica la carga: las funciones `load_*` usan cache_data y los DataFrames se usan por referencia y se muestrean o agregan.")

    with st.expander("Código relevante"):
        st.code(dedent('''
        digraph = """
        digraph G { CSV -> Validacion -> Cache -> Filtros -> Agregacion -> Visualizacion }
        """
        st.graphviz_chart(digraph)
        '''))
