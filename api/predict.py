import os
import sys
import json
import math
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import joblib
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "visibility_model.pkl")
    FEAT_PATH  = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model_features.pkl")
    model = joblib.load(MODEL_PATH)
    FEATURES = joblib.load(FEAT_PATH)
    MODEL_LOADED = True
except Exception as e:
    MODEL_LOADED = False
    MODEL_ERROR = str(e)

GROUND_STATIONS = {
    "Bangalore": (12.9716, 77.5946),
    "Delhi":     (28.6139, 77.2090),
    "Mumbai":    (19.0760, 72.8777),
    "Chennai":   (13.0827, 80.2707),
    "Kolkata":   (22.5726, 88.3639),
}

ORBIT_ENC = {"LEO": 0, "MEO": 1, "GEO": 2}
FREQ_HZ   = 12e9

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def elevation_angle(distance_km, alt_km):
    return math.degrees(math.atan(alt_km / max(distance_km, 1)))

def free_space_path_loss(distance_km):
    return 32.44 + 20*math.log10(max(distance_km, 1)) + 20*math.log10(FREQ_HZ/1e6)

def atm_loss(elevation):
    if elevation > 60: return 0.5
    if elevation > 30: return 1.5
    return 3.0

def score_station(sat_lat, sat_lon, sat_alt_km, orbit_type_enc, gs_lat, gs_lon, velocity=7600):
    d     = haversine(sat_lat, sat_lon, gs_lat, gs_lon)
    el    = elevation_angle(d, sat_alt_km)
    fspl  = free_space_path_loss(d)
    atm   = atm_loss(el)
    rx    = 40 + 30 + 35 - fspl - atm - 2  # TX_POWER + TX_GAIN + RX_GAIN - losses
    doppler = (velocity * math.cos(math.radians(el)) / 3e8) * FREQ_HZ
    return {
        "orbit_type_enc": orbit_type_enc,
        "sat_altitude_km": sat_alt_km,
        "distance_km": d,
        "distance_log": math.log1p(d),
        "elevation": el,
        "sin_elevation": math.sin(math.radians(el)),
        "cos_elevation": math.cos(math.radians(el)),
        "doppler_hz": doppler,
        "fspl_db": fspl,
        "atm_loss_db": atm,
        "rx_power_dbm": rx,
        "rx_margin": rx + 100,
        "gs_lat": gs_lat,
        "gs_lon": gs_lon,
    }

def handler(request):
    try:
        if not MODEL_LOADED:
            return {"statusCode": 500, "body": json.dumps({"error": MODEL_ERROR})}

        params = dict(request.query_params) if hasattr(request, 'query_params') else {}
        # Also try query string parsing
        if not params:
            from urllib.parse import parse_qs, urlparse
            qs = getattr(request, 'query_string', b'').decode()
            parsed = parse_qs(qs)
            params = {k: v[0] for k, v in parsed.items()}

        sat_lat      = float(params.get("sat_lat", 10.0))
        sat_lon      = float(params.get("sat_lon", 75.0))
        sat_alt_km   = float(params.get("sat_alt", 550.0))
        orbit_type   = params.get("orbit_type", "LEO").upper()
        orbit_enc    = ORBIT_ENC.get(orbit_type, 0)

        # Velocity by orbit type
        velocities = {"LEO": 7600, "MEO": 3900, "GEO": 3070}
        vel = velocities.get(orbit_type, 7600)

        # Score each station
        results = []
        for name, (gs_lat, gs_lon) in GROUND_STATIONS.items():
            row = score_station(sat_lat, sat_lon, sat_alt_km, orbit_enc, gs_lat, gs_lon, vel)
            X   = np.array([[row[f] for f in FEATURES]])
            prob_visible = float(model.predict_proba(X)[0][1])

            # Proactive handoff: score 10 seconds ahead
            lon_delta   = 0.05 if orbit_type != "GEO" else 0
            row_future  = score_station(sat_lat, sat_lon + lon_delta, sat_alt_km, orbit_enc, gs_lat, gs_lon, vel)
            X_future    = np.array([[row_future[f] for f in FEATURES]])
            prob_future = float(model.predict_proba(X_future)[0][1])

            results.append({
                "station":       name,
                "lat":           gs_lat,
                "lon":           gs_lon,
                "score_now":     round(prob_visible, 4),
                "score_future":  round(prob_future, 4),
                "score_drop":    round(prob_visible - prob_future, 4),
                "elevation_deg": round(row["elevation"], 1),
                "distance_km":   round(row["distance_km"], 1),
                "rx_power_dbm":  round(row["rx_power_dbm"], 1),
                "visible":       prob_visible >= 0.5,
            })

        results.sort(key=lambda x: x["score_now"], reverse=True)
        best = results[0]

        body = json.dumps({
            "stations":         results,
            "best_station":     best["station"],
            "handoff_needed":   best["score_drop"] > 0.25,
            "sat_lat":          sat_lat,
            "sat_lon":          sat_lon,
            "sat_alt_km":       sat_alt_km,
            "orbit_type":       orbit_type,
        })
        return {"statusCode": 200, "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}, "body": body}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


# Vercel Python handler
from http.server import BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params_raw = parse_qs(parsed.query)
        params = {k: v[0] for k, v in params_raw.items()}

        class Req:
            query_params = params
            query_string = parsed.query.encode()

        result = handler(Req())
        self.send_response(result["statusCode"])
        for k, v in result.get("headers", {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(result["body"].encode())
