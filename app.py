import os
from datetime import date

import pandas as pd
import psycopg2
import streamlit as st
from dotenv import load_dotenv

# ============================
# Configuration générale
# ============================
st.set_page_config(
    page_title="EJP Analytics",
    page_icon="✨",
    layout="wide",
)

# Charge .env
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "ejp_db"),
    "user": os.getenv("DB_USER", "ejp_user"),
    "password": os.getenv("DB_PASSWORD", "ejp_password"),
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# ============================
# Data loaders (cache)
# ============================
@st.cache_data
def load_cultes():
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM cultes_ejp ORDER BY date_culte", conn)
    if not df.empty:
        df["date_culte"] = pd.to_datetime(df["date_culte"]).dt.date
    return df

@st.cache_data
def load_prieres():
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM prieres_ejp ORDER BY date_priere", conn)
    if not df.empty:
        df["date_priere"] = pd.to_datetime(df["date_priere"]).dt.date
    return df

# ============================
# Header (simple, propre)
# ============================
st.markdown(
    """
    <style>
      .title {font-size: 36px; font-weight: 800; margin-bottom: 0.2rem;}
      .subtitle {font-size: 16px; color: #666; margin-top: 0;}
      .section {margin-top: 1.2rem;}
    </style>
    """,
    unsafe_allow_html=True,
)
st.markdown('<div class="title">✨ EJP Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Suivi des cultes & temps de prière — saisie, contrôle, analyse.</div>', unsafe_allow_html=True)
st.divider()

# ============================
# Navigation
# ============================
st.sidebar.title("EJP Analytics")
menu = st.sidebar.radio(
    "Navigation",
    [
        "🏠 Dashboard",
        "✍🏽 Saisie Culte",
        "🙏🏽 Saisie Prière",
        "📊 Analyse Cultes",
        "📊 Analyse Prières",
    ],
)
st.sidebar.divider()
st.sidebar.caption("EJP • 2026")

# ============================
# Helpers UI
# ============================
def date_range_picker(df: pd.DataFrame, colname: str, label: str):
    """Retourne (start_date, end_date) en datetime.date."""
    min_date = df[colname].min()
    max_date = df[colname].max()
    picked = st.date_input(label, value=(min_date, max_date))
    if isinstance(picked, tuple):
        return picked[0], picked[1]
    return min_date, max_date

def kpis_row(items):
    cols = st.columns(len(items))
    for col, (label, value) in zip(cols, items):
        col.metric(label, value)

# ============================
# Page: Dashboard
# ============================
if menu == "🏠 Dashboard":
    st.subheader("Vue d’ensemble")

    dfc = load_cultes()
    dfp = load_prieres()

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Cultes")
        if dfc.empty:
            st.info("Aucun culte enregistré pour le moment.")
        else:
            total_cultes = int(dfc["date_culte"].nunique())
            total_part = int(dfc["nb_total_culte"].sum())
            total_nouv = int(dfc["nb_nouveaux"].sum())
            total_salut = int(dfc["nb_appels_salut"].sum())

            kpis_row([
                ("🗓️ Cultes", total_cultes),
                ("🙌 Présents", total_part),
                ("✨ Nouveaux", total_nouv),
                ("✝️ Appels", total_salut),
            ])

            st.markdown("#### Évolution des présences")
            chart = dfc.set_index("date_culte").sort_index()["nb_total_culte"]
            st.line_chart(chart)

    with c2:
        st.markdown("### Prières")
        if dfp.empty:
            st.info("Aucun temps de prière enregistré pour le moment.")
        else:
            total_prieres = int(dfp[["date_priere", "mode"]].drop_duplicates().shape[0])
            total_part = int(dfp["nb_total"].sum())
            total_zoom = int(dfp[dfp["mode"] == "ZOOM"]["nb_total"].sum())
            total_pres = int(dfp[dfp["mode"] == "PRESENTIEL"]["nb_total"].sum())

            kpis_row([
                ("🗓️ Réunions", total_prieres),
                ("🙏 Participants", total_part),
                ("💻 Zoom", total_zoom),
                ("📍 Présentiel", total_pres),
            ])

            st.markdown("#### Présentiel vs Zoom")
            mode_sum = dfp.groupby("mode")["nb_total"].sum()
            st.bar_chart(mode_sum)

# ============================
# Page: Saisie Culte
# ============================
elif menu == "✍🏽 Saisie Culte":
    st.subheader("Saisie — Culte EJP")

    st.info("Saisis les données du culte. Si la date existe déjà, elle sera mise à jour (pas de doublons).")

    col1, col2 = st.columns(2)

    with st.form("form_culte"):
        with col1:
            date_culte = st.date_input("📅 Date du culte", value=date.today())
            nb_total_site = st.number_input("👥 Total sur site (adultes)", min_value=0, step=1)
            nb_total_culte = st.number_input("Total au culte", min_value=0, step=1)

        with col2:
            nb_hommes = st.number_input("🧑 Hommes", min_value=0, step=1)
            nb_femmes = st.number_input("👩 Femmes", min_value=0, step=1)
            nb_appels_salut = st.number_input("✝️ Appels au salut", min_value=0, step=1)
            nb_nouveaux = st.number_input("✨ Nouveaux", min_value=0, step=1)

        submitted = st.form_submit_button("✅ Enregistrer")

    if submitted:
        if nb_hommes + nb_femmes != nb_total_culte:
            st.error("❌ Vérifie : Hommes + Femmes doit être égal au Total au culte.")
        else:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO cultes_ejp (
                                date_culte,
                                nb_total_site, nb_total_culte,
                                nb_hommes, nb_femmes,
                                nb_appels_salut, nb_nouveaux
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT (date_culte) DO UPDATE SET
                                nb_total_site = EXCLUDED.nb_total_site,
                                nb_total_culte = EXCLUDED.nb_total_culte,
                                nb_hommes = EXCLUDED.nb_hommes,
                                nb_femmes = EXCLUDED.nb_femmes,
                                nb_appels_salut = EXCLUDED.nb_appels_salut,
                                nb_nouveaux = EXCLUDED.nb_nouveaux;
                            """,
                            (
                                date_culte,
                                nb_total_site, nb_total_culte,
                                nb_hommes, nb_femmes,
                                nb_appels_salut, nb_nouveaux,
                            ),
                        )
                st.success("✅ Culte enregistré (création / mise à jour) !")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ Erreur lors de l'enregistrement : {e}")

# ============================
# Page: Saisie Prière
# ============================
elif menu == "🙏🏽 Saisie Prière":
    st.subheader("Saisie — EJP en Prière")

    st.info("Saisis les données du temps de prière. Une entrée par date + mode (Présentiel/Zoom).")

    with st.form("form_priere"):
        col1, col2 = st.columns(2)

        with col1:
            date_priere = st.date_input("📅 Date", value=date.today())
            mode = st.selectbox("📍 Mode", ["PRESENTIEL", "ZOOM"])

        with col2:
            nb_total = st.number_input("👥 Total", min_value=0, step=1)
            nb_hommes = st.number_input("🧑 Hommes", min_value=0, step=1)
            nb_femmes = st.number_input("👩 Femmes", min_value=0, step=1)

        submitted = st.form_submit_button("✅ Enregistrer")

    if submitted:
        if nb_hommes + nb_femmes != nb_total:
            st.error("❌ Vérifie : Hommes + Femmes doit être égal au Total.")
        else:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO prieres_ejp (date_priere, mode, nb_total, nb_hommes, nb_femmes)
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (date_priere, mode) DO UPDATE SET
                                nb_total = EXCLUDED.nb_total,
                                nb_hommes = EXCLUDED.nb_hommes,
                                nb_femmes = EXCLUDED.nb_femmes;
                            """,
                            (date_priere, mode, nb_total, nb_hommes, nb_femmes),
                        )
                st.success("✅ Prière enregistrée (création / mise à jour) !")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"❌ Erreur lors de l'enregistrement : {e}")

# ============================
# Page: Analyse Cultes
# ============================
elif menu == "📊 Analyse Cultes":
    st.subheader("Analyse — Cultes")

    df = load_cultes()

    if df.empty:
        st.warning("Aucune donnée de culte. Ajoute une entrée dans *Saisie Culte*.")
    else:
        start_date, end_date = date_range_picker(df, "date_culte", "📅 Période d’analyse")
        df_f = df[(df["date_culte"] >= start_date) & (df["date_culte"] <= end_date)]

        if df_f.empty:
            st.warning("Aucune donnée sur cette période.")
        else:
            st.markdown("### Indicateurs")
            kpis_row([
                ("🗓️ Cultes", int(df_f["date_culte"].nunique())),
                ("🙌 Présents", int(df_f["nb_total_culte"].sum())),
                ("👩 Femmes", int(df_f["nb_femmes"].sum())),
                ("🧑 Hommes", int(df_f["nb_hommes"].sum())),
            ])

            kpis_row([
                ("✝️ Appels", int(df_f["nb_appels_salut"].sum())),
                ("✨ Nouveaux", int(df_f["nb_nouveaux"].sum())),
            ])

            st.divider()

            st.download_button(
            "⬇️ Export CSV (cultes filtrés)",
            data=df_f.to_csv(index=False).encode("utf-8"),
            file_name="cultes_ejp_filtre.csv",
            mime="text/csv",
            )
            with st.expander("📋 Données détaillées"):
                st.dataframe(df_f, width="stretch")

            tab1, tab2, tab3 = st.tabs(["📈 Présences", "👥 H/F", "✝️ Salut & Nouveaux"])

            with tab1:
                series = df_f.set_index("date_culte").sort_index()["nb_total_culte"]
                st.line_chart(series)

            with tab2:
                hf = df_f.set_index("date_culte").sort_index()[["nb_hommes", "nb_femmes"]]
                st.bar_chart(hf)
            with tab3:
                an = df_f.set_index("date_culte").sort_index()[["nb_appels_salut", "nb_nouveaux"]]
                st.bar_chart(an)



# ============================
# Page: Analyse Prières
# ============================
elif menu == "📊 Analyse Prières":
    st.subheader("Analyse — Prières")

    df = load_prieres()

    if df.empty:
        st.warning("Aucune donnée de prière. Ajoute une entrée dans *Saisie Prière*.")
    else:
        start_date, end_date = date_range_picker(df, "date_priere", "📅 Période d’analyse")
        modes = st.multiselect("📍 Mode", ["PRESENTIEL", "ZOOM"], default=["PRESENTIEL", "ZOOM"])

        df_f = df[
            (df["date_priere"] >= start_date)
            & (df["date_priere"] <= end_date)
            & (df["mode"].isin(modes))
        ]

        if df_f.empty:
            st.warning("Aucune donnée sur cette période / mode.")
        else:
            st.markdown("### Indicateurs")
            total_reunions = int(df_f[["date_priere", "mode"]].drop_duplicates().shape[0])

            kpis_row([
                ("🗓️ Réunions", total_reunions),
                ("🙏 Participants", int(df_f["nb_total"].sum())),
                ("👩 Femmes", int(df_f["nb_femmes"].sum())),
                ("🧑 Hommes", int(df_f["nb_hommes"].sum())),
            ])

            st.divider()
            st.download_button(
            "⬇️ Export CSV (prières filtrées)",
            data=df_f.to_csv(index=False).encode("utf-8"),
            file_name="prieres_ejp_filtre.csv",
            mime="text/csv",
            )
            with st.expander("📋 Données détaillées"):
                st.dataframe(df_f, width="stretch")

            tab1, tab2 = st.tabs(["📈 Évolution", "📍 Présentiel vs Zoom"])

            with tab1:
                series = df_f.groupby("date_priere")["nb_total"].sum().sort_index()
                st.line_chart(series)

            with tab2:
                mode_sum = df_f.groupby("mode")["nb_total"].sum()
                st.bar_chart(mode_sum)

          
