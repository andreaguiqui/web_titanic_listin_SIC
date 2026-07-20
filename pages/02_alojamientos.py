import streamlit as st
from utils import apply_listings_filters, load_listings_data, render_app_sidebar

st.title("Alojamientos de Madrid")
render_app_sidebar("listings")

df = load_listings_data()
if df is None:
    st.stop()

df = apply_listings_filters(df)
if df is None:
    st.stop()

st.caption(f"{len(df)} filas filtradas")

col1, col2, col3 = st.columns(3)
col1.metric("Filas", len(df))
col2.metric("Precio medio", round(float(df["price"].mean()), 2) if not df.empty else 0.0)
col3.metric("Disponibilidad media", round(float(df["availability_365"].mean()), 2) if not df.empty else 0.0)

if df.empty:
    st.info("No hay filas que cumplan los filtros actuales.")
else:
    st.subheader("Vista filtrada")
    st.dataframe(
        df[["id", "name", "neighbourhood", "room_type", "price", "availability_365"]].head(50),
        use_container_width=True,
    )
