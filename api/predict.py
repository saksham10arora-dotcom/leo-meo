import json
import math
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

GROUND_STATIONS = {
    "Bangalore": (12.9716, 77.5946),
    "Delhi":     (28.6139, 77.2090),
    "Mumbai":    (19.0760, 72.8777),
    "Chennai":   (13.0827, 80.2707),
    "Kolkata":   (22.5726, 88.3639),
}

ORBIT_VELOCITY = {"LEO": 7600, "MEO": 3900, "GEO": 3070}
FREQ_HZ = 12e9   # Ku-band

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat, dlon = lat2 - lat1, lon2 - lon1
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

def visibility_score(elevation_deg, rx_power_dbm):
    """
    Physics-derived scoring. Trained RF on this same dataset learned elevation
    and rx_power as the dominant features. Replicate directly.
    Below 5 deg: line-of-sight blocked by Earth's curvature.
    """
    if elevation_deg < 5:
        return 0.0
    # Sigmoid-shaped score: elevation weight 0.65, signal strength 0.35
    el_score = min(elevation_deg / 90.0, 1.0)
    # rx_power range: ~-150 to -50 dBm for this geometry; center at -100
    rx_score = max(0.0, min(1.0, (rx_power_dbm + 150) / 100.0))
    return round(0.65 * el_score + 0.35 * rx_score, 4)

def score_station(sat_lat, sat_lon, sat_alt_km, orbit_type, gs_lat, gs_lon):
    vel = ORBIT_VELOCITY.get(orbit_type, 7600)
    d = haversine(sat_lat, sat_lon, gs_lat, gs_lon)
    el = elevation_angle(d, sat_alt_km)
    fspl = free_space_path_loss(d)
    atm = atm_loss(el)
    rx = 40 + 30 + 35 - fspl - atm - 2
    doppler = (vel * math.cos(math.radians(el)) / 3e8) * FREQ_HZ
    score = visibility_score(el, rx)
    return {
        "distance_km": round(d, 1),
        "elevation_deg": round(el, 1),
        "rx_power_dbm": round(rx, 1),
        "doppler_hz": round(doppler),
        "score": score,
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass  # suppress access logs

    def do_GET(self):
        parsed = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}

        try:
            sat_lat    = float(params.get("sat_lat", 10.0))
            sat_lon    = float(params.get("sat_lon", 75.0))
            sat_alt_km = float(params.get("sat_alt", 550.0))
            orbit_type = params.get("orbit_type", "LEO").upper()

            # Score each station now and 10 s ahead
            lon_delta = 0.05 if orbit_type != "GEO" else 0.0
            results = []
            for name, (gs_lat, gs_lon) in GROUND_STATIONS.items():
                now    = score_station(sat_lat, sat_lon, sat_alt_km, orbit_type, gs_lat, gs_lon)
                future = score_station(sat_lat, sat_lon + lon_delta, sat_alt_km, orbit_type, gs_lat, gs_lon)
                drop   = round(now["score"] - future["score"], 4)
                results.append({
                    "station":      name,
                    "lat":          gs_lat,
                    "lon":          gs_lon,
                    "score_now":    now["score"],
                    "score_future": future["score"],
                    "score_drop":   drop,
                    "elevation_deg": now["elevation_deg"],
                    "distance_km":  now["distance_km"],
                    "rx_power_dbm": now["rx_power_dbm"],
                    "visible":      now["score"] >= 0.3,
                })

            results.sort(key=lambda x: x["score_now"], reverse=True)
            best = results[0]

            body = json.dumps({
                "stations":       results,
                "best_station":   best["station"],
                "handoff_needed": best["score_drop"] > 0.25,
                "sat_lat":        sat_lat,
                "sat_lon":        sat_lon,
                "sat_alt_km":     sat_alt_km,
                "orbit_type":     orbit_type,
            })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
