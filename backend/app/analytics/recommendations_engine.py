"""
Generates actionable, data-driven business recommendations by combining
outputs from the sales / restaurant / delivery / time / churn modules.
Every recommendation is derived from an actual computed metric threshold,
never fabricated, and labelled "Data-Driven Recommendation".
"""
from typing import Dict, List


def generate_recommendations(
    sales: Dict, customer: Dict, restaurant: Dict, delivery: Dict, time_a: Dict, churn_summary: Dict = None
) -> List[Dict]:
    recs = []

    # Regional demand vs revenue imbalance
    if sales.get("revenue_by_city"):
        city_rows = sales["revenue_by_city"]
        if len(city_rows) >= 2:
            by_orders = sorted(city_rows, key=lambda x: x.get("orders", 0), reverse=True)
            by_revenue = sorted(city_rows, key=lambda x: x.get("revenue", 0))
            high_demand_low_rev = [c for c in by_orders[:3] if c["group"] in [r["group"] for r in by_revenue[:3]]]
            for c in high_demand_low_rev:
                recs.append({
                    "type": "Data-Driven Recommendation",
                    "category": "Regional Strategy",
                    "text": f"{c['group']} shows high order demand ({int(c['orders'])} orders) but comparatively low revenue "
                            f"(₹{c['revenue']:.0f}) — increase restaurant availability and run promotional campaigns "
                            f"in this region to lift average order value."
                })

    # Restaurant: high revenue + poor rating + long delivery time
    if restaurant.get("available") and restaurant.get("high_revenue_low_rating"):
        for rrow in restaurant["high_revenue_low_rating"][:3]:
            slow_note = ""
            if rrow.get("avg_delivery_time", 0) > 0 and delivery.get("avg_delivery_time"):
                if rrow["avg_delivery_time"] > delivery["avg_delivery_time"]:
                    slow_note = " combined with above-average delivery times"
            recs.append({
                "type": "Data-Driven Recommendation",
                "category": "Restaurant Operations",
                "text": f"{rrow['restaurant']} generates strong revenue (₹{rrow.get('revenue', 0):.0f}) but has a "
                        f"below-median customer rating ({rrow.get('avg_rating', 0):.1f}/5){slow_note} — "
                        f"investigate food preparation quality and delivery operations before it affects retention."
            })

    # High-value + high-churn customers
    if churn_summary and churn_summary.get("high_value_high_risk_count", 0) > 0:
        recs.append({
            "type": "Data-Driven Recommendation",
            "category": "Customer Retention",
            "text": f"{churn_summary['high_value_high_risk_count']} high-monetary-value customers currently show "
                    f"high churn probability — target these customers with loyalty rewards or personalized offers "
                    f"before they lapse."
        })

    # Peak hour delivery-partner allocation
    if time_a.get("available") and time_a.get("peak_hour") is not None:
        peak_hour = time_a["peak_hour"]
        recs.append({
            "type": "Data-Driven Recommendation",
            "category": "Delivery Operations",
            "text": f"Order volume peaks around {peak_hour:02d}:00 — increase delivery-partner allocation during "
                    f"this window to reduce delays and improve customer satisfaction."
        })

    # Cancellation rate
    if sales.get("kpis", {}).get("cancellation_rate", 0) and sales["kpis"]["cancellation_rate"] > 8:
        recs.append({
            "type": "Data-Driven Recommendation",
            "category": "Order Fulfilment",
            "text": f"Cancellation rate is {sales['kpis']['cancellation_rate']:.1f}%, above the healthy 5-8% benchmark — "
                    f"review restaurant preparation SLAs and delivery-partner assignment logic."
        })

    # Late delivery
    if delivery.get("available") and delivery.get("late_delivery_pct", 0) > 25:
        recs.append({
            "type": "Data-Driven Recommendation",
            "category": "Delivery Operations",
            "text": f"{delivery['late_delivery_pct']:.1f}% of deliveries arrive later than estimated — "
                    f"re-calibrate ETA estimation and consider dynamic partner routing during peak periods."
        })

    if not recs:
        recs.append({
            "type": "Data-Driven Recommendation",
            "category": "General",
            "text": "No strong actionable signals were detected in the current filtered view — "
                    "broaden the date range or remove filters for a fuller picture."
        })

    return recs
