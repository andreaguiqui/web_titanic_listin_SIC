from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).resolve().parent / "data"


@st.cache_data(show_spinner=False)
def load_titanic_data():
    path = DATA_DIR / "Titanic-Dataset.csv"
    if not path.exists():
        st.error(f"No se encontró el archivo: {path.name}")
        return None

    df = pd.read_csv(path)
    required_columns = ["PassengerId", "Survived", "Pclass", "Name", "Sex", "Age", "SibSp", "Parch", "Ticket", "Fare", "Embarked"]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        st.error(
            "El CSV Titanic-Dataset.csv no tiene las columnas obligatorias: "
            + ", ".join(missing)
        )
        return None

    return df.copy()


@st.cache_data(show_spinner=False)
def load_listings_data():
    path = DATA_DIR / "listings.csv"
    if not path.exists():
        st.error(f"No se encontró el archivo: {path.name}")
        return None

    df = pd.read_csv(path)
    required_columns = ["id", "name", "host_id", "host_name", "neighbourhood", "latitude", "longitude", "room_type", "price", "minimum_nights", "number_of_reviews", "availability_365"]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        st.error(
            "El CSV listings.csv no tiene las columnas obligatorias: "
            + ", ".join(missing)
        )
        return None

    return df.copy()


def render_app_sidebar(active_page: str):
    st.sidebar.page_link("app.py", label="Inicio")
    st.sidebar.page_link("pages/01_titanic.py", label="Titanic")
    st.sidebar.page_link("pages/03_madrid.py", label="Madrid")
    st.sidebar.header("Filtros globales")

    st.session_state.setdefault("global_search", "")
    st.session_state.setdefault("show_only_complete_rows", False)

    search_text = st.sidebar.text_input(
        "Texto de búsqueda",
        value=st.session_state.get("global_search", ""),
        key="global_search",
    )
    show_complete_rows = st.sidebar.checkbox(
        "Mostrar solo filas completas",
        value=st.session_state.get("show_only_complete_rows", False),
        key="show_only_complete_rows",
    )

    if active_page == "titanic":
        st.session_state.setdefault("titanic_sex", "Todos")
        st.session_state.setdefault("titanic_pclass", "Todos")
        st.session_state.setdefault("titanic_embarked", "Todos")
        st.session_state.setdefault("titanic_age_min", "")
        st.session_state.setdefault("titanic_age_max", "")
        st.sidebar.selectbox("Sexo", ["Todos", "male", "female"], key="titanic_sex")
        st.sidebar.selectbox("Clase", ["Todos", 1, 2, 3], key="titanic_pclass")
        st.sidebar.selectbox("Embarque", ["Todos", "C", "Q", "S"], key="titanic_embarked")
        st.sidebar.text_input("Edad mínima", value=st.session_state.get("titanic_age_min", ""), key="titanic_age_min")
        st.sidebar.text_input("Edad máxima", value=st.session_state.get("titanic_age_max", ""), key="titanic_age_max")
    elif active_page == "listings":
        st.session_state.setdefault("listing_room_type", "Todos")
        st.session_state.setdefault("listing_neighbourhood", "Todos")
        st.session_state.setdefault("listing_min_price", "")
        st.session_state.setdefault("listing_max_price", "")

        df = load_listings_data()
        if df is not None:
            room_types = ["Todos"] + sorted(df["room_type"].dropna().astype(str).unique().tolist())
            neighbourhoods = ["Todos"] + sorted(df["neighbourhood"].dropna().astype(str).unique().tolist())
            st.sidebar.selectbox("Tipo de habitación", room_types, key="listing_room_type")
            st.sidebar.selectbox("Barrio", neighbourhoods, key="listing_neighbourhood")

        st.sidebar.text_input("Precio mínimo", value=st.session_state.get("listing_min_price", ""), key="listing_min_price")
        st.sidebar.text_input("Precio máximo", value=st.session_state.get("listing_max_price", ""), key="listing_max_price")

    if st.sidebar.button("Restablecer filtros", key=f"{active_page}_reset"):
        for key in [
            "global_search",
            "show_only_complete_rows",
            "titanic_sex",
            "titanic_pclass",
            "titanic_embarked",
            "titanic_age_min",
            "titanic_age_max",
            "listing_room_type",
            "listing_neighbourhood",
            "listing_min_price",
            "listing_max_price",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    return {
        "search_text": search_text,
        "show_complete_rows": show_complete_rows,
    }


def apply_common_filters(df, active_page: str):
    if df is None:
        return None

    filtered = df.copy()

    search_text = str(st.session_state.get("global_search", "")).strip()
    if search_text:
        searchable_columns = []
        if active_page == "titanic":
            searchable_columns = ["Name", "Sex", "Embarked", "Ticket"]
        else:
            searchable_columns = ["name", "neighbourhood", "room_type", "host_name"]

        mask = pd.Series(False, index=filtered.index)
        for column in searchable_columns:
            if column in filtered.columns:
                mask = mask | filtered[column].fillna("").astype(str).str.contains(search_text, case=False, na=False)
        filtered = filtered[mask]

    if st.session_state.get("show_only_complete_rows", False):
        filtered = filtered.dropna()

    return filtered


def apply_titanic_filters(df):
    filtered = apply_common_filters(df, "titanic")
    if filtered is None:
        return None

    sex = st.session_state.get("titanic_sex", "Todos")
    pclass = st.session_state.get("titanic_pclass", "Todos")
    embarked = st.session_state.get("titanic_embarked", "Todos")
    min_age_raw = str(st.session_state.get("titanic_age_min", "")).strip()
    max_age_raw = str(st.session_state.get("titanic_age_max", "")).strip()

    if sex != "Todos":
        filtered = filtered[filtered["Sex"] == sex]
    if pclass != "Todos":
        filtered = filtered[filtered["Pclass"] == int(pclass)]
    if embarked != "Todos":
        filtered = filtered[filtered["Embarked"] == embarked]

    if "Age" in filtered.columns:
        if min_age_raw:
            try:
                min_age = float(min_age_raw)
                filtered = filtered[filtered["Age"] >= min_age]
            except ValueError:
                pass
        if max_age_raw:
            try:
                max_age = float(max_age_raw)
                filtered = filtered[filtered["Age"] <= max_age]
            except ValueError:
                pass

    return filtered


def apply_listings_filters(df):
    filtered = apply_common_filters(df, "listings")
    if filtered is None:
        return None

    room_type = st.session_state.get("listing_room_type", "Todos")
    neighbourhood = st.session_state.get("listing_neighbourhood", "Todos")
    min_price_raw = str(st.session_state.get("listing_min_price", "")).strip()
    max_price_raw = str(st.session_state.get("listing_max_price", "")).strip()

    if room_type != "Todos":
        filtered = filtered[filtered["room_type"] == room_type]
    if neighbourhood != "Todos":
        filtered = filtered[filtered["neighbourhood"] == neighbourhood]

    if min_price_raw:
        try:
            min_price = float(min_price_raw)
            filtered = filtered[filtered["price"] >= min_price]
        except ValueError:
            pass
    if max_price_raw:
        try:
            max_price = float(max_price_raw)
            filtered = filtered[filtered["price"] <= max_price]
        except ValueError:
            pass

    return filtered
