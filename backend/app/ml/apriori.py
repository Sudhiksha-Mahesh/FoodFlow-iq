"""Market-basket / association-rule mining for product recommendations."""
import pandas as pd
from typing import Dict

MIN_ORDERS_REQUIRED = 50


def run_apriori(df: pd.DataFrame, role_map: Dict[str, str], min_support=0.01, min_confidence=0.2, min_lift=1.0) -> Dict:
    if "order_id" not in role_map or "food_item" not in role_map:
        return {"available": False, "reason": "Insufficient product-level transaction data: order identifier and food-item columns are both required."}

    order_col, item_col = role_map["order_id"], role_map["food_item"]
    basket = df.groupby(order_col)[item_col].apply(lambda items: list(set(items.dropna().astype(str))))
    basket = basket[basket.apply(len) > 1]

    if len(basket) < MIN_ORDERS_REQUIRED:
        return {"available": False, "reason": f"Only {len(basket)} multi-item orders found — at least {MIN_ORDERS_REQUIRED} are recommended for meaningful association rules."}

    try:
        from mlxtend.frequent_patterns import apriori, association_rules
        from mlxtend.preprocessing import TransactionEncoder

        te = TransactionEncoder()
        te_data = te.fit(basket.tolist()).transform(basket.tolist())
        onehot = pd.DataFrame(te_data, columns=te.columns_)

        frequent_itemsets = apriori(onehot, min_support=min_support, use_colnames=True)
        if frequent_itemsets.empty:
            return {"available": False, "reason": "No frequent itemsets found at the given minimum support — try lowering the support threshold."}

        rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_confidence)
        rules = rules[rules["lift"] >= min_lift]
        rules = rules.sort_values("lift", ascending=False).head(30)

        rules_out = []
        for _, r in rules.iterrows():
            rules_out.append({
                "antecedents": list(r["antecedents"]),
                "consequents": list(r["consequents"]),
                "support": round(float(r["support"]), 4),
                "confidence": round(float(r["confidence"]), 4),
                "lift": round(float(r["lift"]), 4),
            })

        return {"available": True, "rules": rules_out, "orders_analyzed": int(len(basket))}
    except Exception as e:
        return {"available": False, "reason": f"Association-rule mining failed: {e}"}
