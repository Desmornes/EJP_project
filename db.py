import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

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

def read_cultes() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM cultes_ejp ORDER BY date_culte", conn)
    if not df.empty:
        df["date_culte"] = pd.to_datetime(df["date_culte"]).dt.date
    return df

def read_prieres() -> pd.DataFrame:
    with get_connection() as conn:
        df = pd.read_sql("SELECT * FROM prieres_ejp ORDER BY date_priere", conn)
    if not df.empty:
        df["date_priere"] = pd.to_datetime(df["date_priere"]).dt.date
    return df

def upsert_culte(date_culte, nb_total_site, nb_total_culte, nb_hommes, nb_femmes, nb_appels_salut, nb_nouveaux):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO cultes_ejp (
                    date_culte, nb_total_site, nb_total_culte,
                    nb_hommes, nb_femmes, nb_appels_salut, nb_nouveaux
                ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (date_culte) DO UPDATE SET
                    nb_total_site = EXCLUDED.nb_total_site,
                    nb_total_culte = EXCLUDED.nb_total_culte,
                    nb_hommes = EXCLUDED.nb_hommes,
                    nb_femmes = EXCLUDED.nb_femmes,
                    nb_appels_salut = EXCLUDED.nb_appels_salut,
                    nb_nouveaux = EXCLUDED.nb_nouveaux;
                """,
                (date_culte, nb_total_site, nb_total_culte, nb_hommes, nb_femmes, nb_appels_salut, nb_nouveaux)
            )

def upsert_priere(date_priere, mode, nb_total, nb_hommes, nb_femmes):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO prieres_ejp (date_priere, mode, nb_total, nb_hommes, nb_femmes)
                VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (date_priere, mode) DO UPDATE SET
                    nb_total = EXCLUDED.nb_total,
                    nb_hommes = EXCLUDED.nb_hommes,
                    nb_femmes = EXCLUDED.nb_femmes;
                """,
                (date_priere, mode, nb_total, nb_hommes, nb_femmes)
            )