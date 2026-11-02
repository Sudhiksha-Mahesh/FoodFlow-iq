#!/usr/bin/env python3
"""
generate_sample_data.py
------------------------
Generates a realistic, internally-correlated food-delivery transactions dataset
for FoodFlow IQ, including intentional data-quality issues (missing values,
duplicates, invalid types) so the ETL module has something real to clean.

Usage:
    python generate_sample_data.py --orders 10000 --customers 1500 \
        --restaurants 100 --partners 200 --months 12 --out ../data/sample_food_delivery_orders.csv
"""
import argparse
import random
import string
import csv
from datetime import datetime, timedelta, date
import math

random.seed(42)

CITIES = {
    "Bengaluru": ["Koramangala", "Indiranagar", "Whitefield", "HSR Layout", "Jayanagar"],
    "Mumbai": ["Andheri", "Bandra", "Powai", "Dadar", "Malad"],
    "Delhi": ["Saket", "Dwarka", "Karol Bagh", "Rohini", "Connaught Place"],
    "Chennai": ["T Nagar", "Adyar", "Velachery", "Anna Nagar", "OMR"],
    "Coimbatore": ["RS Puram", "Peelamedu", "Gandhipuram", "Saibaba Colony", "Race Course"],
    "Hyderabad": ["Gachibowli", "Madhapur", "Banjara Hills", "Kondapur", "Kukatpally"],
}

CUISINES = ["North Indian", "South Indian", "Chinese", "Italian", "Fast Food",
            "Biryani", "Desserts", "Beverages", "Continental", "Mexican"]

FOOD_BY_CUISINE = {
    "North Indian": ["Butter Chicken", "Paneer Tikka", "Dal Makhani", "Naan", "Chole Bhature"],
    "South Indian": ["Masala Dosa", "Idli Sambar", "Vada", "Uttapam", "Filter Coffee"],
    "Chinese": ["Veg Fried Rice", "Chicken Manchurian", "Noodles", "Spring Rolls", "Chilli Chicken"],
    "Italian": ["Margherita Pizza", "Pasta Alfredo", "Garlic Bread", "Lasagna", "Pepperoni Pizza"],
    "Fast Food": ["Cheese Burger", "French Fries", "Chicken Nuggets", "Hot Dog", "Wrap"],
    "Biryani": ["Chicken Biryani", "Mutton Biryani", "Veg Biryani", "Egg Biryani", "Chicken 65"],
    "Desserts": ["Gulab Jamun", "Brownie", "Ice Cream Sundae", "Cheesecake", "Rasmalai"],
    "Beverages": ["Coke", "Fresh Lime Soda", "Cold Coffee", "Mango Lassi", "Mojito"],
    "Continental": ["Grilled Chicken", "Caesar Salad", "Mashed Potato", "Steak", "Soup"],
    "Mexican": ["Tacos", "Burrito", "Nachos", "Quesadilla", "Churros"],
}

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Wallet"]
CUSTOMER_TYPES = ["New", "Regular", "Premium"]
ORDER_STATUS_WEIGHTS = [("Delivered", 0.87), ("Cancelled", 0.08), ("Failed", 0.05)]

def weighted_choice(pairs):
    r = random.random()
    cum = 0
    for val, w in pairs:
        cum += w
        if r <= cum:
            return val
    return pairs[-1][0]

def rand_id(prefix, n, width=5):
    return f"{prefix}{str(n).zfill(width)}"

def gen_customers(n):
    customers = []
    for i in range(1, n + 1):
        city = random.choice(list(CITIES.keys()))
        area = random.choice(CITIES[city])
        # customer "value tier" drives frequency & spend correlation
        tier = weighted_choice([("low", 0.5), ("mid", 0.35), ("high", 0.15)])
        # some customers will become inactive (churn) - assign a "activity window"
        will_churn = random.random() < 0.28
        customers.append({
            "customer_id": rand_id("CUST", i, 5),
            "age": max(18, min(65, int(random.gauss(32, 9)))),
            "gender": random.choice(["Male", "Female", "Other"]),
            "city": city,
            "area": area,
            "tier": tier,
            "will_churn": will_churn,
        })
    return customers

def gen_restaurants(n):
    restaurants = []
    for i in range(1, n + 1):
        cuisine = random.choice(CUISINES)
        city = random.choice(list(CITIES.keys()))
        # quality tier correlates with rating & delivery time
        quality = weighted_choice([("premium", 0.2), ("average", 0.55), ("poor", 0.25)])
        restaurants.append({
            "restaurant_id": rand_id("REST", i, 4),
            "name": f"{cuisine.split()[0]} {random.choice(['House','Kitchen','Corner','Point','Junction','Hub'])} {i}",
            "cuisine": cuisine,
            "city": city,
            "quality": quality,
        })
    return restaurants

def gen_partners(n):
    partners = []
    for i in range(1, n + 1):
        exp = random.choice(["Beginner", "Intermediate", "Experienced"])
        partners.append({"partner_id": rand_id("DP", i, 4), "experience": exp})
    return partners

def peak_hour_weight(hour):
    # lunch 12-14, dinner 19-22
    if 12 <= hour <= 14:
        return 3.0
    if 19 <= hour <= 22:
        return 3.5
    if 7 <= hour <= 9:
        return 1.2
    return 0.6

def sample_hour():
    weights = [peak_hour_weight(h) for h in range(24)]
    total = sum(weights)
    r = random.random() * total
    cum = 0
    for h, w in enumerate(weights):
        cum += w
        if r <= cum:
            return h
    return 12

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=10000)
    parser.add_argument("--customers", type=int, default=1500)
    parser.add_argument("--restaurants", type=int, default=100)
    parser.add_argument("--partners", type=int, default=200)
    parser.add_argument("--food-items", type=int, default=300)
    parser.add_argument("--months", type=int, default=12)
    parser.add_argument("--out", type=str, default="../data/sample_food_delivery_orders.csv")
    args = parser.parse_args()

    customers = gen_customers(args.customers)
    restaurants = gen_restaurants(args.restaurants)
    partners = gen_partners(args.partners)

    end_date = date.today()
    start_date = end_date - timedelta(days=30 * args.months)
    total_days = (end_date - start_date).days

    # Weight customer selection so "high" tier customers order more often (frequency correlation),
    # and churned customers stop ordering after some cutoff day.
    customer_weights = []
    for c in customers:
        base = {"low": 1.0, "mid": 2.2, "high": 4.0}[c["tier"]]
        customer_weights.append(base)

    rows = []
    order_num = 0
    # Precompute per-customer churn cutoff day (as an offset from start)
    churn_cutoff = {}
    for c in customers:
        if c["will_churn"]:
            churn_cutoff[c["customer_id"]] = random.randint(int(total_days * 0.3), int(total_days * 0.85))
        else:
            churn_cutoff[c["customer_id"]] = total_days + 999

    day_of_week_weight = [1.0, 0.9, 0.9, 1.0, 1.15, 1.6, 1.7]  # Mon..Sun, weekend heavier

    attempts = 0
    while order_num < args.orders and attempts < args.orders * 5:
        attempts += 1
        day_offset = random.randint(0, total_days - 1)
        this_date = start_date + timedelta(days=day_offset)
        dow = this_date.weekday()
        if random.random() > day_of_week_weight[dow] / 1.7:
            continue

        cust = random.choices(customers, weights=customer_weights, k=1)[0]
        if day_offset > churn_cutoff[cust["customer_id"]]:
            continue  # this customer has "churned" by this date

        order_num += 1
        rest = random.choice([r for r in restaurants if r["city"] == cust["city"]] or restaurants)
        cuisine = rest["cuisine"]

        # ~35% of orders contain multiple distinct food items (for association-rule mining);
        # certain items are deliberately paired together so Apriori finds real patterns.
        pool = FOOD_BY_CUISINE[cuisine]
        if random.random() < 0.35 and len(pool) >= 2:
            n_items = random.choice([2, 2, 3])
            first = random.choice(pool)
            items = [first]
            # bias toward a "combo": item[i] pairs with item[i+1] in the list
            combo_idx = pool.index(first)
            if combo_idx + 1 < len(pool) and random.random() < 0.6:
                items.append(pool[combo_idx + 1])
            while len(items) < n_items:
                cand = random.choice(pool)
                if cand not in items:
                    items.append(cand)
        else:
            items = [random.choice(pool)]

        hour = sample_hour()
        minute = random.randint(0, 59)
        order_time = f"{hour:02d}:{minute:02d}:00"

        status = weighted_choice(ORDER_STATUS_WEIGHTS)

        distance_km = round(abs(random.gauss(4.5, 2.5)) + 0.5, 2)
        base_delivery_time = 15 + distance_km * 2.2
        peak_penalty = 8 if hour in (12, 13, 19, 20, 21) else 0
        quality_penalty = {"premium": -3, "average": 3, "poor": 12}[rest["quality"]]
        estimated_delivery_time = round(base_delivery_time + quality_penalty * 0.5, 1)
        actual_delivery_time = round(
            max(10, base_delivery_time + peak_penalty + quality_penalty + random.gauss(0, 5)), 1
        )

        partner = random.choice(partners)
        exp_bonus = {"Beginner": 4, "Intermediate": 0, "Experienced": -4}[partner["experience"]]
        actual_delivery_time = round(max(10, actual_delivery_time + exp_bonus), 1)

        rating_base = {"premium": 4.5, "average": 3.8, "poor": 2.7}[rest["quality"]]
        customer_rating = round(min(5, max(1, random.gauss(rating_base, 0.6))), 1)
        delivery_rating = round(min(5, max(1, random.gauss(4.2 - exp_bonus * 0.05, 0.7))), 1)

        if status != "Delivered":
            actual_delivery_time = ""
            customer_rating = ""
            delivery_rating = ""

        shared_order_id = rand_id("ORD", order_num, 6)
        customer_type_val = random.choice(CUSTOMER_TYPES)
        payment_val = random.choice(PAYMENT_METHODS)

        # One CSV row per food item in the order (shared order_id links them for basket analysis)
        for food_item in items:
            qty = max(1, int(random.gauss(2, 1)))
            unit_price = round(random.uniform(80, 550), 2)
            subtotal = round(qty * unit_price, 2)
            discount = round(subtotal * random.choice([0, 0, 0, 0.05, 0.1, 0.15]), 2)
            delivery_fee = round(random.uniform(20, 60), 2) if food_item == items[0] else 0

            row = {
                "order_id": shared_order_id,
                "order_date": this_date.isoformat(),
                "order_time": order_time,
                "customer_id": cust["customer_id"],
                "customer_age": cust["age"],
                "customer_gender": cust["gender"],
                "customer_city": cust["city"],
                "customer_area": cust["area"],
                "customer_type": customer_type_val,
                "restaurant_id": rest["restaurant_id"],
                "restaurant_name": rest["name"],
                "cuisine": cuisine,
                "food_category": cuisine,
                "food_item": food_item,
                "quantity": qty,
                "unit_price": unit_price,
                "subtotal": subtotal,
                "discount": discount,
                "delivery_fee": delivery_fee,
                "payment_method": payment_val,
                "order_status": status,
                "delivery_partner_id": partner["partner_id"],
                "delivery_partner_experience": partner["experience"],
                "distance_km": distance_km,
                "estimated_delivery_time": estimated_delivery_time,
                "actual_delivery_time": actual_delivery_time,
                "customer_rating": customer_rating,
                "delivery_rating": delivery_rating,
            }
            rows.append(row)

    # ---- Inject data quality issues intentionally ----
    n = len(rows)
    # Missing values (~1.5% across a few columns)
    for col in ["order_date", "subtotal", "customer_rating", "distance_km", "customer_city"]:
        for _ in range(int(n * 0.005)):
            idx = random.randint(0, n - 1)
            rows[idx][col] = ""

    # Duplicate rows (~0.3%)
    dup_count = max(1, int(n * 0.003))
    for _ in range(dup_count):
        idx = random.randint(0, n - 1)
        rows.append(dict(rows[idx]))

    # Invalid / inconsistent values (~0.2%)
    for _ in range(int(n * 0.002)):
        idx = random.randint(0, n - 1)
        rows[idx]["quantity"] = "N/A"
    for _ in range(int(n * 0.002)):
        idx = random.randint(0, n - 1)
        rows[idx]["subtotal"] = "-999"
    for _ in range(int(n * 0.001)):
        idx = random.randint(0, n - 1)
        rows[idx]["order_date"] = "31/31/2025"  # invalid date format

    random.shuffle(rows)

    out_path = args.out
    fieldnames = list(rows[0].keys())
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} rows -> {out_path}")
    print(f"Customers: {args.customers}, Restaurants: {args.restaurants}, Delivery Partners: {args.partners}")

if __name__ == "__main__":
    main()
