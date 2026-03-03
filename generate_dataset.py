import numpy as np
import pandas as pd

# -------------------------------
# Constants
# -------------------------------
C = 3e8                     # Speed of light (m/s)
EARTH_RADIUS = 6371         # km
MU = 398600.4418            # km^3/s^2 (Earth gravitational parameter)
FREQ_HZ = 12e9              # 12 GHz Ku-band
TX_POWER_DBM = 40           # Satellite transmit power
TX_GAIN_DB = 30
RX_GAIN_DB = 35
SYSTEM_LOSS_DB = 2

# -------------------------------
# Ground Stations
# -------------------------------
GROUND_STATIONS = {
    "Bangalore": (12.97, 77.59),
    "Delhi": (28.61, 77.20),
    "Mumbai": (19.07, 72.87),
    "Chennai": (13.08, 80.27),
    "Kolkata": (22.57, 88.36)
}

# -------------------------------
# Helper Functions
# -------------------------------
def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
    return 2 * EARTH_RADIUS * np.arcsin(np.sqrt(a))

def elevation_angle(distance_km, sat_alt_km):
    return np.degrees(np.arctan(sat_alt_km / distance_km))

def doppler_shift(relative_velocity):
    return (relative_velocity / C) * FREQ_HZ

def free_space_path_loss(distance_km):
    return 32.44 + 20*np.log10(distance_km) + 20*np.log10(FREQ_HZ/1e6)

def atmospheric_loss(elevation):
    if elevation > 60:
        return 0.5
    elif elevation > 30:
        return 1.5
    else:
        return 3.0

# -------------------------------
# Dataset Generator
# -------------------------------
def generate_dataset(samples=3000):
    rows = []

    for _ in range(samples):
        # Orbit parameters
        orbit_type = np.random.choice(["LEO", "MEO", "GEO"])
        if orbit_type == "LEO":
            alt_km = np.random.uniform(500, 1200)
            velocity = 7.6e3
        elif orbit_type == "MEO":
            alt_km = np.random.uniform(8000, 20000)
            velocity = 3.9e3
        else:
            alt_km = 35786
            velocity = 3.07e3

        sat_lat = np.random.uniform(-60, 60)
        sat_lon = np.random.uniform(-180, 180)

        for station, (gs_lat, gs_lon) in GROUND_STATIONS.items():
            distance_km = haversine(sat_lat, sat_lon, gs_lat, gs_lon)
            elevation = elevation_angle(distance_km, alt_km)

            if elevation < 5:
                visible = 0
            else:
                visible = 1

            fspl = free_space_path_loss(distance_km)
            atm_loss = atmospheric_loss(elevation)
            rx_power = TX_POWER_DBM + TX_GAIN_DB + RX_GAIN_DB - fspl - atm_loss - SYSTEM_LOSS_DB

            doppler = doppler_shift(velocity * np.cos(np.radians(elevation)))

            rows.append({
                "orbit_type": orbit_type,
                "sat_altitude_km": alt_km,
                "sat_lat": sat_lat,
                "sat_lon": sat_lon,
                "gs_lat": gs_lat,
                "gs_lon": gs_lon,
                "distance_km": distance_km,
                "elevation": elevation,
                "doppler_hz": doppler,
                "fspl_db": fspl,
                "atm_loss_db": atm_loss,
                "rx_power_dbm": rx_power,
                "visible": visible,
                "station": station
            })

    df = pd.DataFrame(rows)

    # -------------------------------
    # Feature Engineering
    # -------------------------------
    df["sin_elevation"] = np.sin(np.radians(df["elevation"]))
    df["cos_elevation"] = np.cos(np.radians(df["elevation"]))
    df["distance_log"] = np.log1p(df["distance_km"])
    df["rx_margin"] = df["rx_power_dbm"] + 100
    df["orbit_type_enc"] = df["orbit_type"].map({"LEO": 0, "MEO": 1, "GEO": 2})

    return df

# -------------------------------
# Run Generator
# -------------------------------
if __name__ == "__main__":
    df = generate_dataset(samples=1000)
    df.to_csv("satcom_training_dataset.csv", index=False)
    print("✅ Dataset generated: satcom_training_dataset.csv")
    print(df.head())

