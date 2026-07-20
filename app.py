import streamlit as st
from utils import render_app_sidebar

st.set_page_config(page_title="Explorador Titanic y Madrid", page_icon="🧭", layout="wide")

st.title("Explorador de datos")
st.caption("Selecciona una sección para inspeccionar Titanic o alojamientos de Madrid.")

render_app_sidebar("home")

st.info("Los filtros de la barra lateral se comparten entre páginas y se pueden restablecer con un clic.")
st.write("Usa la navegación lateral para pasar a la vista de Titanic o de alojamientos.")
