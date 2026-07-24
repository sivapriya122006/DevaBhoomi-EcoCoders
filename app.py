from flask import Flask, render_template, request, jsonify
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from ml.model import predict_waste, match_farmers, get_upcoming_festivals, train_waste_model

app = Flask(__name__)

# ── In-memory DB ──────────────────────────────────────────────────────
DB = {
    "temples": [
        {"id": 1, "name": "Manakula Vinayagar Temple", "name_ta": "மணக்குள விநாயகர் கோவில்",
         "size": "major", "lat": 11.9340, "lon": 79.8360, "contact": "9876543210", "city": "Puducherry"},
        {"id": 2, "name": "Arulmigu Vedapureeswarar Temple", "name_ta": "வேதபுரீஸ்வரர் கோவில்",
         "size": "large", "lat": 11.9416, "lon": 79.8083, "contact": "9876543211", "city": "Puducherry"},
        {"id": 3, "name": "Varadaraja Perumal Temple", "name_ta": "வரதராஜ பெருமாள் கோவில்",
         "size": "medium", "lat": 11.9300, "lon": 79.8200, "contact": "9876543212", "city": "Puducherry"},
    ],
    "farmers": [
        {"id": 1, "name": "Murugan R", "name_ta": "முருகன் ர", "lat": 11.9200, "lon": 79.8100,
         "farm_size": 2.5, "crop": "Vegetables", "contact": "9876501111", "city": "Puducherry"},
        {"id": 2, "name": "Selvam K", "name_ta": "செல்வம் க", "lat": 11.9500, "lon": 79.8400,
         "farm_size": 1.8, "crop": "Rice", "contact": "9876502222", "city": "Puducherry"},
        {"id": 3, "name": "Rajan P", "name_ta": "ராஜன் ப", "lat": 11.9100, "lon": 79.8500,
         "farm_size": 3.2, "crop": "Flowers", "contact": "9876503333", "city": "Puducherry"},
        {"id": 4, "name": "Anbu S", "name_ta": "அன்பு ச", "lat": 11.9600, "lon": 79.8250,
         "farm_size": 0.8, "crop": "Vegetables", "contact": "9876504444", "city": "Puducherry"},
        {"id": 5, "name": "Vel M", "name_ta": "வேல் ம", "lat": 11.9450, "lon": 79.8600,
         "farm_size": 4.0, "crop": "Sugarcane", "contact": "9876505555", "city": "Puducherry"},
    ],
    "waste_logs": [],
    "matches": []
}

# ── Train ML model on startup ─────────────────────────────────────────
try:
    train_waste_model()
except Exception as e:
    print(f"Model training skipped: {e}")

# ── Route Optimizer Functions ─────────────────────────────────────────
def haversine_dist(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

def optimize_route(farmer_lat, farmer_lon, temples):
    unvisited = temples.copy()
    route = []
    total = 0
    clat, clon = farmer_lat, farmer_lon
    while unvisited:
        nearest = min(unvisited, key=lambda t: haversine_dist(clat, clon, t["lat"], t["lon"]))
        dist = haversine_dist(clat, clon, nearest["lat"], nearest["lon"])
        total += dist
        route.append({**nearest, "dist_from_prev": round(dist, 2), "cumulative_km": round(total, 2)})
        clat, clon = nearest["lat"], nearest["lon"]
        unvisited.remove(nearest)
    return route, round(total + haversine_dist(clat, clon, farmer_lat, farmer_lon), 2)

# ── Page Routes ───────────────────────────────────────────────────────

@app.route("/")
def index():
    festivals = get_upcoming_festivals(30)
    stats = {
        "temples": len(DB["temples"]),
        "farmers": len(DB["farmers"]),
        "matches": len(DB["matches"]),
        "waste_collected": sum(log.get("predicted_kg", 0) for log in DB["waste_logs"])
    }
    return render_template("index.html", festivals=festivals, stats=stats)

@app.route("/temple")
def temple_dashboard():
    today = datetime.today()
    festivals = get_upcoming_festivals(30)
    return render_template("temple.html", temples=DB["temples"], festivals=festivals, today=today)

@app.route("/farmer")
def farmer_dashboard():
    return render_template("farmer.html", farmers=DB["farmers"], temples=DB["temples"])

@app.route("/admin")
def admin_dashboard():
    festivals = get_upcoming_festivals(30)
    stats = {
        "temples": len(DB["temples"]),
        "farmers": len(DB["farmers"]),
        "matches": len(DB["matches"]),
        "total_waste_kg": round(sum(log.get("predicted_kg", 0) for log in DB["waste_logs"]), 1),
        "logs": DB["waste_logs"][-10:][::-1]
    }
    return render_template("admin.html", festivals=festivals, stats=stats,
                           temples=DB["temples"], farmers=DB["farmers"])

@app.route("/route")
def route_optimizer():
    return render_template("route.html", temples=DB["temples"], farmers=DB["farmers"])

# ── API Routes ────────────────────────────────────────────────────────

@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.json
    today = datetime.today()
    result = predict_waste(
        month=int(data.get("month", today.month)),
        day=int(data.get("day", today.day)),
        weekday=today.weekday(),
        temple_size=data.get("temple_size", "medium")
    )
    temple_id = int(data.get("temple_id", 1))
    temple = next((t for t in DB["temples"] if t["id"] == temple_id), DB["temples"][0])
    matched = match_farmers(temple["lat"], temple["lon"], DB["farmers"], top_k=3)
    result["matched_farmers"] = matched
    result["temple_name"] = temple["name"]
    log_entry = {
        "temple": temple["name"],
        "predicted_kg": result["predicted_kg"],
        "festival": result["festival"],
        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p"),
        "farmers_alerted": len(matched)
    }
    DB["waste_logs"].append(log_entry)
    DB["matches"].extend([{"temple": temple["name"], "farmer": f["name"]} for f in matched])
    return jsonify(result)

@app.route("/api/festivals")
def api_festivals():
    days = int(request.args.get("days", 30))
    return jsonify(get_upcoming_festivals(days))

@app.route("/api/temples", methods=["GET", "POST"])
def api_temples():
    if request.method == "POST":
        data = request.json
        new_temple = {
            "id": len(DB["temples"]) + 1,
            "name": data["name"],
            "name_ta": data.get("name_ta", data["name"]),
            "size": data.get("size", "medium"),
            "lat": float(data.get("lat", 11.9340)),
            "lon": float(data.get("lon", 79.8360)),
            "contact": data.get("contact", ""),
            "city": data.get("city", "Puducherry")
        }
        DB["temples"].append(new_temple)
        return jsonify({"success": True, "temple": new_temple})
    return jsonify(DB["temples"])

@app.route("/api/farmers", methods=["GET", "POST"])
def api_farmers():
    if request.method == "POST":
        data = request.json
        new_farmer = {
            "id": len(DB["farmers"]) + 1,
            "name": data["name"],
            "name_ta": data.get("name_ta", data["name"]),
            "lat": float(data.get("lat", 11.9200)),
            "lon": float(data.get("lon", 79.8100)),
            "farm_size": float(data.get("farm_size", 1.0)),
            "crop": data.get("crop", "Vegetables"),
            "contact": data.get("contact", ""),
            "city": data.get("city", "Puducherry")
        }
        DB["farmers"].append(new_farmer)
        return jsonify({"success": True, "farmer": new_farmer})
    return jsonify(DB["farmers"])

@app.route("/api/stats")
def api_stats():
    return jsonify({
        "temples": len(DB["temples"]),
        "farmers": len(DB["farmers"]),
        "matches": len(DB["matches"]),
        "total_waste_kg": round(sum(log.get("predicted_kg", 0) for log in DB["waste_logs"]), 1),
        "fertilizer_saved_kg": round(sum(log.get("predicted_kg", 0) for log in DB["waste_logs"]) * 0.3, 1),
        "co2_saved_kg": round(sum(log.get("predicted_kg", 0) for log in DB["waste_logs"]) * 0.5, 1),
    })

@app.route("/api/optimize-route", methods=["POST"])
def api_optimize_route():
    data = request.json
    farmer_id = int(data.get("farmer_id", 1))
    temple_ids = data.get("temple_ids", [int(t["id"]) for t in DB["temples"]])
    selected_temples = [t for t in DB["temples"] if t["id"] in temple_ids]
    farmer = next((f for f in DB["farmers"] if f["id"] == farmer_id), DB["farmers"][0])
    today = datetime.today()
    temples_copy = []
    for temple in selected_temples:
        t = dict(temple)
        pred = predict_waste(today.month, today.day, today.weekday(), t["size"])
        t["predicted_kg"] = pred["predicted_kg"]
        t["festival"] = pred["festival"]
        t["urgency"] = "CRITICAL" if pred["predicted_kg"] > 200 else "HIGH" if pred["predicted_kg"] > 80 else "MEDIUM" if pred["predicted_kg"] > 30 else "LOW"
        temples_copy.append(t)
    route, total_km = optimize_route(farmer["lat"], farmer["lon"], temples_copy)
    total_waste = sum(t["predicted_kg"] for t in temples_copy)
    fuel_saved = max(0, round((len(temples_copy) * 3.5) - total_km, 2))
    return jsonify({
        "farmer": farmer,
        "route": route,
        "total_km": total_km,
        "total_waste_kg": round(total_waste, 1),
        "temples_count": len(route),
        "fuel_saved_km": fuel_saved,
        "co2_saved_kg": round(fuel_saved * 0.21, 2),
        "estimated_time_mins": round(total_km * 3, 0)
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
