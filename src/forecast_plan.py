"""
Forecast & Purchase Planning - Core Logic
==========================================
Calculates demand forecast using moving averages and generates
optimal purchase plans considering lead time and current stock.

This script runs inside n8n's Python node.
"""

import json
from datetime import datetime, timedelta


def calculate_forecast(sales_history, weeks=4):
    """Calculate demand forecast using simple moving average."""
    if not sales_history or len(sales_history) < weeks:
        return 0
    recent = sales_history[-weeks:]
    return round(sum(recent) / len(recent), 2)


def generate_purchase_plan(
    forecast, current_stock, lead_time_weeks, planning_horizon=4
):
    """
    Determine optimal purchase quantity.

    Parameters:
        forecast: weekly demand forecast
        current_stock: current inventory level
        lead_time_weeks: supplier lead time in weeks
        planning_horizon: weeks to cover with purchase
    """
    demand_during_lead = forecast * lead_time_weeks
    target_stock = forecast * planning_horizon
    purchase_qty = max(0, target_stock + demand_during_lead - current_stock)
    return round(purchase_qty)


def prepare_telegram_message(product_name, stock, forecast, purchase_qty, unit_cost, lead_time):
    """Format purchase plan data for Telegram notification."""
    if purchase_qty <= 0:
        return None
    return (
        f"📦 *{product_name}*\n"
        f"  Stock actual: {stock}\n"
        f"  Forecast semanal: {forecast}\n"
        f"  Cantidad a comprar: {purchase_qty}\n"
        f"  Costo unitario: ${unit_cost}\n"
        f"  Lead time: {lead_time} semanas"
    )


# --- Example usage ---
if __name__ == "__main__":
    sales = [120, 135, 110, 125, 140, 130, 145, 138]

    forecast = calculate_forecast(sales, weeks=4)
    print(f"Forecast: {forecast} units/week")

    purchase = generate_purchase_plan(
        forecast=forecast,
        current_stock=200,
        lead_time_weeks=2,
        planning_horizon=4,
    )
    print(f"Purchase plan: {purchase} units")

    msg = prepare_telegram_message(
        "Producto A", 200, forecast, purchase, 15.50, 2
    )
    if msg:
        print(f"\nTelegram message:\n{msg}")
