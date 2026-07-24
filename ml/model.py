import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import pickle
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime

FESTIVALS = {
    "Pongal":          {"month": 1,  "day": 14, "multiplier": 8},
    "Maha Shivaratri": {"month": 2,  "day": 18, "multiplier": 10},
    "Ugadi":           {"month": 3,  "day": 30, "multiplier": 6},
    "Ram Navami":      {"month": 4,  "day": 6,  "multiplier": 7},
    "Tamil New Year":  {"month": 4,  "day": 14, "multiplier": 6},
    "Ganesh Chaturthi":{"month": 9,  "day": 2,  "multiplier": 12},
    "Navratri":        {"month": 10, "day": 2,  "multiplier": 12},
    "Vijayadasami":    {"month": 10, "day": 12, "multiplier": 9},
    "Diwali":          {"month": 10, "day": 20, "multiplier": 15},
    "Karthigai":       {"month": 11, "day": 25, "multiplier": 8},
}

TEMPLE_BASE_WASTE = {"small": 15, "medium": 45, "large": 120, "major": 300}

def get_festival_multiplier(month, day):
    for name, info in FESTIVALS.items():
        if info["month"] == month and abs(info["day"] - day) <= 3:
            return name, info["multiplier"]
    return None, 1.0

def train_waste_model():
    np.random.seed(42)
    records = []
    sizes = list(TEMPLE_BASE_WASTE.keys())
    for _ in range(2000):
        month = np.random.randint(1, 13)
        day = np.random.randint(1, 29)
        weekday = np.random.randint(0, 7)
        size_name = np.random.choice(sizes)
        base = TEMPLE_BASE_WASTE[size_name]
        size_enc = sizes.index(size_name)
        _, mult = get_festival_multiplier(month, day)
        weekend_bonus = 1.3 if weekday >= 4 else 1.0
        noise = np.random.normal(1.0, 0.1)
        waste_kg = base * mult * weekend_bonus * noise
        records.append({"month": month, "day": day, "weekday": weekday,
                         "size_enc": size_enc, "waste_kg": round(waste_kg, 2)})
    df = pd.DataFrame(records)
    X = df[["month", "day", "weekday", "size_enc"]]
    y = df["waste_kg"]
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    os.makedirs("ml", exist_ok=True)
    with open("ml/waste_model.pkl", "wb") as f:
        pickle.dump(model, f)
    return model

def predict_waste(month, day, weekday, temple_size):
    import os
    sizes = list(TEMPLE_BASE_WASTE.keys())
    size_enc = sizes.index(temple_size) if temple_size in sizes else 1
    try:
        with open("ml/waste_model.pkl", "rb") as f:
            model = pickle.load(f)
    except FileNotFoundError:
        model = train_waste_model()
    X = pd.DataFrame([[month, day, weekday, size_enc]],
                     columns=["month", "day", "weekday", "size_enc"])
    predicted = model.predict(X)[0]
    festival_name, mult = get_festival_multiplier(month, day)
    return {
        "predicted_kg": round(predicted, 1),
        "festival": festival_name,
        "festival_multiplier": mult,
        "is_festival": festival_name is not None
    }

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1 - a))

def match_farmers(temple_lat, temple_lon, farmers, top_k=5):
    results = []
    for f in farmers:
        dist = haversine(temple_lat, temple_lon, f["lat"], f["lon"])
        results.append({**f, "distance_km": round(dist, 2)})
    results.sort(key=lambda x: x["distance_km"])
    return results[:top_k]

def get_upcoming_festivals(days_ahead=30):
    today = datetime.today()
    upcoming = []
    for name, info in FESTIVALS.items():
        try:
            fest_date = datetime(today.year, info["month"], info["day"])
        except ValueError:
            continue
        delta = (fest_date - today).days
        if 0 <= delta <= days_ahead:
            upcoming.append({
                "name": name,
                "date": fest_date.strftime("%d %b %Y"),
                "days_away": delta,
                "waste_multiplier": info["multiplier"],
                "alert_level": "HIGH" if info["multiplier"] >= 10 else "MEDIUM" if info["multiplier"] >= 6 else "LOW"
            })
    upcoming.sort(key=lambda x: x["days_away"])
    return upcoming
