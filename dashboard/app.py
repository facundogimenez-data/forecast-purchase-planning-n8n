"""
Forecast & Purchase Planning — Live Dashboard
==============================================
Streamlit app that reads the output of the n8n automation
(`forecasts`, `purchase_plan`, `inventory_snapshots` tables) and
shows the current weekly planning status: demand forecast,
suggested purchase quantities, and stock coverage per product.

Closes the loop: automation → data → visualization.
"""

import os

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Forecast & Purchase Planning",
    page_icon="📦",
    layout="wide",
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "3306"),
    "user": os.getenv("DB_USER", "demo_user"),
    "password": os.getenv("DB_PASSWORD", "demo_password"),
    "database": os.getenv("DB_NAME", "supply_chain_demo"),
}


@st.cache_resource
def get_engine():
    url = (
        f"mysql+mysqlconnector://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    return create_engine(url)


@st.cache_data(ttl=300)
def load_planning_data() -> pd.DataFrame:
    query = """
        SELECT
            pp.product_id,
            pp.name           AS product_name,
            pp.on_hand        AS current_stock,
            pp.forecast_qty,
            pp.revision_date  AS forecast_date,
            pp.purchase_qty,
            p.unit_cost,
            pp.lead_time_days
        FROM purchase_plan pp
        JOIN products p
            ON p.product_id = pp.product_id
        WHERE pp.revision_date = (SELECT MAX(revision_date) FROM purchase_plan)
        ORDER BY pp.purchase_qty DESC;
    """
    return pd.read_sql(query, get_engine())


def main():
    st.title("📦 Forecast & Purchase Planning")
    st.caption(
        "Estado de la planificación semanal generada automáticamente "
        "por el workflow de n8n (forecast por moving average + AI Agent "
        "para recomendaciones de compra)."
    )

    try:
        df = load_planning_data()
    except Exception as exc:
        st.error(f"No se pudo conectar a la base de datos: {exc}")
        st.info(
            "Configura las variables DB_HOST, DB_PORT, DB_USER, DB_PASSWORD "
            "y DB_NAME en un archivo .env (ver .env.example)."
        )
        return

    if df.empty:
        st.warning("Todavía no hay datos de forecast para esta semana.")
        return

    total_purchase_value = (df["purchase_qty"].fillna(0) * df["unit_cost"].fillna(0)).sum()
    products_to_reorder = (df["purchase_qty"].fillna(0) > 0).sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Productos analizados", len(df))
    col2.metric("Productos a reponer", int(products_to_reorder))
    col3.metric("Valor estimado de compra", f"${total_purchase_value:,.2f}")

    st.divider()
    st.subheader("Plan de compra sugerido")

    display_df = df.copy()
    display_df = display_df.rename(
        columns={
            "product_name": "Producto",
            "current_stock": "Stock actual",
            "forecast_qty": "Forecast semanal",
            "purchase_qty": "Cantidad a comprar",
            "unit_cost": "Costo unitario",
            "lead_time_days": "Lead time (días)",
        }
    )[
        [
            "Producto",
            "Stock actual",
            "Forecast semanal",
            "Cantidad a comprar",
            "Costo unitario",
            "Lead time (días)",
        ]
    ]

    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Forecast vs. stock actual")
    chart_df = df.set_index("product_name")[["current_stock", "forecast_qty"]]
    chart_df = chart_df.rename(
        columns={"current_stock": "Stock actual", "forecast_qty": "Forecast semanal"}
    )
    st.bar_chart(chart_df, color=["#006D77", "#E29578"])

    st.caption(
        f"Última actualización: {df['forecast_date'].max()} · "
        "Datos generados por el workflow `Forecast & Purchase Planning` en n8n."
    )


if __name__ == "__main__":
    main()
