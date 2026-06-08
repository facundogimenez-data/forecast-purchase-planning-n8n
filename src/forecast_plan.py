"""
Forecast & Purchase Planning - Core Logic (reconstruction)
==========================================================
Python reconstruction of the calculation logic that runs in production
inside the n8n "Forecast Calculation Engine" sub-workflow (Code / JavaScript
nodes). Reproduced here in Python for portfolio/demo purposes — the
production pipeline runs natively in n8n, not as a standalone script.

Logic: short-horizon moving average forecast + purchase plan that covers
the planning horizon plus the supplier lead time, netted against on-hand
stock.
"""

import json
from statistics import mean


def calculate_forecast(sales_history, forecast_weeks=1):
    """
    Forecast next week's demand as the average of the last `forecast_weeks`
    weekly sales records (sorted chronologically).

    sales_history: list of {"week_start": "YYYY-MM-DD", "qty_sold": float}
    """
    if not sales_history:
        return 0

    sorted_history = sorted(sales_history, key=lambda h: h["week_start"])
    recent_sales = [h["qty_sold"] for h in sorted_history[-forecast_weeks:]]

    if not recent_sales:
        return 0

    return round(mean(recent_sales), 2)


def generate_purchase_plan(forecast_qty, on_hand, lead_time_days, plan_weeks=2):
    """
    Determine the purchase quantity needed to cover demand for the
    planning horizon plus the supplier lead time, net of current stock.

    Parameters:
        forecast_qty:    weekly demand forecast
        on_hand:         current inventory level
        lead_time_days:  supplier lead time in days
        plan_weeks:      weeks of demand the purchase should cover
    """
    weeks_to_cover = plan_weeks + (lead_time_days // 7)
    planned_demand = forecast_qty * weeks_to_cover
    return max(0, round(planned_demand - on_hand))


def build_purchase_recommendation_context(product):
    """
    Assemble the structured context passed to the AI Agent node, which
    turns the raw numbers into a natural-language purchase recommendation
    (sent to Telegram and WhatsApp via Evolution API).
    """
    return {
        "name": product["name"],
        "sku": product["sku"],
        "on_hand": product["on_hand"],
        "forecast_qty": product["forecast_qty"],
        "purchase_plan": product["purchase_plan"],
        "unit_cost": product["unit_cost"],
        "lead_time_days": product["lead_time_days"],
    }


# --- Example usage ---
if __name__ == "__main__":
    sales_history = [
        {"week_start": "2026-05-11", "qty_sold": 120},
        {"week_start": "2026-05-18", "qty_sold": 135},
        {"week_start": "2026-05-25", "qty_sold": 128},
    ]

    forecast = calculate_forecast(sales_history, forecast_weeks=1)
    print(f"Forecast: {forecast} units/week")

    purchase_plan = generate_purchase_plan(
        forecast_qty=forecast,
        on_hand=180,
        lead_time_days=10,
        plan_weeks=2,
    )
    print(f"Purchase plan: {purchase_plan} units")

    context = build_purchase_recommendation_context(
        {
            "name": "Producto A",
            "sku": "SKU-001",
            "on_hand": 180,
            "forecast_qty": forecast,
            "purchase_plan": purchase_plan,
            "unit_cost": 15.50,
            "lead_time_days": 10,
        }
    )
    print("\nContexto enviado al AI Agent:")
    print(json.dumps(context, indent=2, ensure_ascii=False))
