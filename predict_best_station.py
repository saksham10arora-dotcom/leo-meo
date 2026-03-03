import joblib
import pandas as pd
import numpy as np

# ===============================
# Load trained model & features
# ===============================
model = joblib.load("visibility_model.pkl")
FEATURES = joblib.load("model_features.pkl")

# ===============================
# Ground stations
# ===============================
ground_stations = {
    "Delhi": (28.6139, 77.2090),
    "Bangalore": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "Chennai": (13.0827, 80.2707),
}

# ===============================
# Satellite state (NOW)
# ===============================
sat_lat_now = 10.0
sat_lon_now = 75.0
sat_alt_km = 550        # LEO
orbit_type_enc = 0      # LEO

# Simple forward motion assumption
SAT_LON_DELTA_10S = 0.05   # degrees in 10 seconds

# ===============================
# Utility functions
# ===============================
def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * R * np.arcsin(np.sqrt(a))

def elevation_angle(distance_km):
    return max(0, 90 - (distance_km / 100))

def physics_features(distance_km, elevation_deg):
    fspl_db = 20 * np.log10(distance_km * 1000 + 1)
    atm_loss_db = 2 / np.sin(np.radians(max(elevation_deg, 1)))
    rx_power_dbm = -fspl_db - atm_loss_db
    rx_margin = rx_power_dbm + 120

    return fspl_db, atm_loss_db, rx_power_dbm, rx_margin

# ===============================
# Build prediction rows
# ===============================
rows_now = []
rows_future = []

for name, (gs_lat, gs_lon) in ground_stations.items():

    # ---- NOW ----
    d_now = haversine(gs_lat, gs_lon, sat_lat_now, sat_lon_now)
    el_now = elevation_angle(d_now)

    fspl, atm, rx_pwr, rx_margin = physics_features(d_now, el_now)

    rows_now.append({
        "orbit_type_enc": orbit_type_enc,
        "sat_altitude_km": sat_alt_km,
        "distance_km": d_now,
        "distance_log": np.log(d_now + 1),
        "elevation": el_now,
        "sin_elevation": np.sin(np.radians(el_now)),
        "cos_elevation": np.cos(np.radians(el_now)),
        "doppler_hz": 0,
        "fspl_db": fspl,
        "atm_loss_db": atm,
        "rx_power_dbm": rx_pwr,
        "rx_margin": rx_margin,
        "gs_lat": gs_lat,
        "gs_lon": gs_lon,
        "station": name
    })

    # ---- FUTURE (+10s) ----
    d_f = haversine(gs_lat, gs_lon, sat_lat_now, sat_lon_now + SAT_LON_DELTA_10S)
    el_f = elevation_angle(d_f)

    fspl, atm, rx_pwr, rx_margin = physics_features(d_f, el_f)

    rows_future.append({
        "orbit_type_enc": orbit_type_enc,
        "sat_altitude_km": sat_alt_km,
        "distance_km": d_f,
        "distance_log": np.log(d_f + 1),
        "elevation": el_f,
        "sin_elevation": np.sin(np.radians(el_f)),
        "cos_elevation": np.cos(np.radians(el_f)),
        "doppler_hz": 0,
        "fspl_db": fspl,
        "atm_loss_db": atm,
        "rx_power_dbm": rx_pwr,
        "rx_margin": rx_margin,
        "gs_lat": gs_lat,
        "gs_lon": gs_lon,
        "station": name
    })

# ===============================
# Predict
# ===============================
df_now = pd.DataFrame(rows_now)
df_future = pd.DataFrame(rows_future)

X_now = df_now[FEATURES]
X_future = df_future[FEATURES]

df_now["score_now"] = model.predict_proba(X_now)[:, 1]
df_future["score_future"] = model.predict_proba(X_future)[:, 1]

df = df_now.merge(
    df_future[["station", "score_future"]],
    on="station"
)

df["drop"] = df["score_now"] - df["score_future"]

best = df.sort_values("score_now", ascending=False).iloc[0]

# ===============================
# Output
# ===============================
print("\n Best Ground Station (Now)")
print("----------------------------------")
print(f"Station     : {best['station']}")
print(f"Score NOW   : {best['score_now']:.3f}")
print(f"Score +10s  : {best['score_future']:.3f}")
print(f"Score Drop  : {best['drop']:.3f}")

if best["drop"] > 0.25:
    print("\n⚠️  PROACTIVE HANDOFF RECOMMENDED")
else:
    print("\n✅ Link Stable (No Handoff Needed)")


