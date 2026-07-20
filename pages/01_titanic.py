import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
import streamlit as st
from utils import apply_titanic_filters, load_titanic_data, render_app_sidebar

st.title("Titanic")
render_app_sidebar("titanic")

df = load_titanic_data()
if df is None:
    st.stop()

df = apply_titanic_filters(df)
if df is None:
    st.stop()

st.caption(f"{len(df)} filas filtradas")

if df.empty:
    st.info("No hay filas que cumplan los filtros actuales.")
    st.stop()

survival_rate = float(df["Survived"].mean()) if "Survived" in df.columns else 0.0
median_age = float(df["Age"].median()) if "Age" in df.columns else 0.0
median_fare = float(df["Fare"].median()) if "Fare" in df.columns else 0.0

st.subheader("1. KPIs")
st.caption("Responden a: ¿cuántos pasajeros hay, qué proporción sobrevivió y cuáles son las tendencias centrales de edad y tarifa?")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Pasajeros", len(df))
col2.metric("Supervivencia", f"{survival_rate:.1%}")
col3.metric("Edad mediana", f"{median_age:.1f}")
col4.metric("Tarifa mediana", f"{median_fare:.2f}")

st.subheader("Vista filtrada")
st.dataframe(
    df[["PassengerId", "Name", "Sex", "Age", "Pclass", "Survived", "Embarked", "Fare"]].head(50),
    use_container_width=True,
)

st.subheader("2. Supervivencia total")
st.caption("Responde a: ¿cuál es la proporción de supervivencia en el subconjunto filtrado?")
survival_summary = pd.DataFrame({
    "Categoria": ["Sobrevivieron", "No sobrevivieron"],
    "Valor": [int(df["Survived"].eq(1).sum()), int(df["Survived"].eq(0).sum())],
})
st.plotly_chart(
    px.pie(
        survival_summary,
        values="Valor",
        names="Categoria",
        color="Categoria",
        color_discrete_map={"Sobrevivieron": "#F58518", "No sobrevivieron": "#4C78A8"},
    ),
    use_container_width=True,
)

st.subheader("3. Tasa de supervivencia por sexo y clase")
st.caption("Responde a: ¿varía la supervivencia según sexo y clase?")
survival_by_group = (
    df.groupby(["Sex", "Pclass"])["Survived"].mean().unstack().rename_axis(columns=None)
)
survival_by_group = survival_by_group.rename(columns={1: "Clase 1", 2: "Clase 2", 3: "Clase 3"})
st.bar_chart(survival_by_group)

st.subheader("3. Heatmap de correlaciones")
st.caption("Responde a: ¿qué variables numéricas se relacionan con la supervivencia, la edad o la tarifa?")
num_df = df.select_dtypes(include=["number"]).copy()
if not num_df.empty:
    corr = num_df.corr(numeric_only=True)
    fig, ax = plt.subplots(figsize=(8, 6))
    sns.heatmap(corr, annot=True, cmap="coolwarm", fmt=".2f", ax=ax)
    ax.set_title("Correlaciones")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
else:
    st.info("No hay columnas numéricas disponibles para correlacionar.")

st.subheader("4. Edad frente a tarifa")
st.caption("Responde a: ¿cómo se distribuye la edad por supervivencia y cómo se relaciona con la tarifa?")
selection = alt.selection_interval()
age_chart = (
    alt.Chart(df)
    .mark_circle(size=70, opacity=0.75)
    .encode(
        x=alt.X("Age:Q", title="Edad"),
        y=alt.Y("Fare:Q", title="Tarifa"),
        color=alt.Color("Survived:N", title="Sobrevivió", scale=alt.Scale(domain=[0, 1], range=["#4C78A8", "#F58518"])),
        tooltip=["Name:N", "Age:Q", "Fare:Q", "Survived:N"],
    )
    .add_params(selection)
    .properties(width=700, height=300)
)
st.altair_chart(age_chart, use_container_width=True)

st.subheader("5. Composición por clase")
st.caption("Responde a: ¿cómo se distribuyen los pasajeros por clase dentro del subconjunto filtrado?")
composition_chart = (
    alt.Chart(df)
    .mark_bar()
    .encode(
        x=alt.X("Pclass:N", title="Clase"),
        y=alt.Y("count()", title="Pasajeros"),
        color=alt.Color("Survived:N", title="Sobrevivió", scale=alt.Scale(domain=[0, 1], range=["#4C78A8", "#F58518"])),
    )
    .properties(width=700, height=300)
)
st.altair_chart(composition_chart, use_container_width=True)

st.subheader("6. Vista jerárquica")
st.caption("Responde a: ¿cómo se distribuyen los pasajeros por clase, sexo y supervivencia en una vista jerárquica?")
composition = (
    df.assign(
        Clase=lambda x: x["Pclass"].astype(int).astype(str).map(lambda value: f"Clase {value}"),
        Supervivencia=lambda x: x["Survived"].map({0: "No sobrevivió", 1: "Sobrevivió"}),
        Sexo=lambda x: x["Sex"],
    )
    .groupby(["Clase", "Sexo", "Supervivencia"])
    .size()
    .reset_index(name="count")
)
chart = (
    alt.Chart(composition)
    .mark_bar()
    .encode(
        x=alt.X("Clase:N", title="Clase"),
        y=alt.Y("count:Q", title="Pasajeros"),
        color=alt.Color("Supervivencia:N", title="Supervivencia", scale=alt.Scale(domain=["Sobrevivió", "No sobrevivió"], range=["#F58518", "#4C78A8"])),
        column=alt.Column("Sexo:N", title="Sexo"),
    )
    .properties(width=180, height=250)
)
st.altair_chart(chart, use_container_width=True)
