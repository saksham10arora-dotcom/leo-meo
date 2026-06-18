import json
import math
import datetime
import urllib.request
from http.server import BaseHTTPRequestHandler

# Celestrak TLE catalog URLs (no API key needed)
TLE_SOURCES = {
    "ISS":     "https://celestrak.org/satcat/tle.php?CATNR=25544",
    "STARLINK": "https://celestrak.org/SOCRATES/query.php?CATNR=44235",
    # Fallback: named group catalog
    "stations": "https://celestrak.org/SOCRATES/query.php?GROUP=stations&FORMAT=tle",
}

CELESTRAK_GROUPS = {
    "ISS":      "https://celestrak.org/SOCRATES/query.php?CATNR=25544",
    "STARLINK-1": "https://celestrak.org/SOCRATES/query.php?CATNR=44235",
}

# Simpler, more reliable Celestrak endpoint
TLE_URL = "https://celestrak.org/SOCRATES/query.php?CATNR=25544&FORMAT=TLE"
ISS_TLE_URL = "https://celestrak.org/satcat/tle.php?CATNR=25544"


def fetch_tle_lines(sat_id: str):
    """Fetch TLE lines from Celestrak. Returns (line1, line2, name)."""
    cat_num = {
        "ISS": "25544",
        "HST": "20580",
        "TERRA": "25994",
        "AQUA": "27424",
    }.get(sat_id.upper(), "25544")

    url = f"https://celestrak.org/satcat/tle.php?CATNR={cat_num}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "leo-meo/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            text = r.read().decode("utf-8").strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) >= 3:
            return lines[0], lines[1], lines[2]
        elif len(lines) == 2:
            return sat_id, lines[0], lines[1]
    except Exception:
        pass
    return None


def sgp4_propagate(tle_name, tle_line1, tle_line2):
    """
    Minimal SGP4 propagation to get current ECI position.
    Uses only stdlib math — no external packages.
    Returns (lat_deg, lon_deg, alt_km).
    """
    # Parse TLE epoch
    epoch_str = tle_line1[18:32].strip()
    year_2d   = int(epoch_str[:2])
    year      = (2000 + year_2d) if year_2d < 57 else (1900 + year_2d)
    day_of_yr = float(epoch_str[2:])

    epoch_dt = datetime.datetime(year, 1, 1) + datetime.timedelta(days=day_of_yr - 1)
    now      = datetime.datetime.utcnow()
    dt_min   = (now - epoch_dt).total_seconds() / 60.0

    # Mean motion (rev/day) from TLE
    mean_motion_rev_day = float(tle_line2[52:63])
    n = mean_motion_rev_day * 2 * math.pi / (24 * 60)  # rad/min

    # Mean anomaly at epoch
    M0 = math.radians(float(tle_line2[43:51]))
    # Current mean anomaly
    M  = M0 + n * dt_min

    # Inclination
    inc = math.radians(float(tle_line2[8:16]))
    # RAAN
    raan = math.radians(float(tle_line2[17:25]))
    # Eccentricity
    ecc = float("0." + tle_line2[26:33])
    # Argument of perigee
    argp = math.radians(float(tle_line2[34:42]))

    # Solve Kepler's equation for eccentric anomaly (Newton's method)
    E = M
    for _ in range(10):
        E = E - (E - ecc * math.sin(E) - M) / (1 - ecc * math.cos(E))

    # True anomaly
    nu = 2 * math.atan2(
        math.sqrt(1 + ecc) * math.sin(E / 2),
        math.sqrt(1 - ecc) * math.cos(E / 2)
    )

    # Semi-major axis from mean motion (km)
    MU = 398600.4418
    a = (MU / (n / 60)**2) ** (1/3)

    # Radius (km)
    r = a * (1 - ecc * math.cos(E))

    # Position in orbital plane
    x_orb = r * math.cos(nu)
    y_orb = r * math.sin(nu)

    # Rotate to ECI (simplified — perifocal → ECI)
    cos_raan = math.cos(raan)
    sin_raan = math.sin(raan)
    cos_inc  = math.cos(inc)
    sin_inc  = math.sin(inc)
    cos_argp = math.cos(argp)
    sin_argp = math.sin(argp)

    # Rotation matrices
    x_eci = (cos_raan * cos_argp - sin_raan * sin_argp * cos_inc) * x_orb + \
            (-cos_raan * sin_argp - sin_raan * cos_argp * cos_inc) * y_orb
    y_eci = (sin_raan * cos_argp + cos_raan * sin_argp * cos_inc) * x_orb + \
            (-sin_raan * sin_argp + cos_raan * cos_argp * cos_inc) * y_orb
    z_eci = (sin_argp * sin_inc) * x_orb + (cos_argp * sin_inc) * y_orb

    # ECI → ECEF (rotate by Earth's sidereal angle)
    OMEGA_EARTH = 7.2921150e-5  # rad/s
    t_sec = dt_min * 60
    # Greenwich sidereal time at J2000 epoch (approx)
    gst0_deg = 280.46061837
    gst_deg  = gst0_deg + 360.98564724 * (
        (now - datetime.datetime(2000, 1, 1, 12)).total_seconds() / 86400.0
    )
    gst = math.radians(gst_deg % 360)

    x_ecef =  x_eci * math.cos(gst) + y_eci * math.sin(gst)
    y_ecef = -x_eci * math.sin(gst) + y_eci * math.cos(gst)
    z_ecef =  z_eci

    # ECEF → geodetic (lat/lon/alt)
    R_EARTH = 6378.137  # km
    lon_rad = math.atan2(y_ecef, x_ecef)
    p = math.sqrt(x_ecef**2 + y_ecef**2)
    lat_rad = math.atan2(z_ecef, p * (1 - 0.00669437999014))  # WGS84 approx
    for _ in range(5):
        N   = R_EARTH / math.sqrt(1 - 0.00669437999014 * math.sin(lat_rad)**2)
        lat_rad = math.atan2(z_ecef + 0.00669437999014 * N * math.sin(lat_rad), p)

    alt_km = p / math.cos(lat_rad) - R_EARTH if abs(math.degrees(lat_rad)) < 89 else abs(z_ecef) / math.sin(lat_rad) - R_EARTH * (1 - 0.00669437999014)

    return math.degrees(lat_rad), math.degrees(lon_rad), alt_km


# Default fallback: simulated ISS-like orbit when Celestrak is unreachable
def simulate_position():
    now = datetime.datetime.utcnow()
    t = now.timestamp()
    PERIOD_S = 92 * 60  # ~92 min ISS orbit
    phase = (t % PERIOD_S) / PERIOD_S * 2 * math.pi
    lat = 51.6 * math.sin(phase)
    lon = (((t / PERIOD_S) * 360) % 360) - 180
    return lat, lon, 408.0, True  # lat, lon, alt, is_simulated


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        sat_id = params.get("sat", ["ISS"])[0].upper()

        try:
            result = fetch_tle_lines(sat_id)
            if result:
                name, line1, line2 = result
                lat, lon, alt = sgp4_propagate(name, line1, line2)
                body = json.dumps({
                    "sat_id":       sat_id,
                    "name":         name,
                    "lat":          round(lat, 4),
                    "lon":          round(lon, 4),
                    "alt_km":       round(alt, 1),
                    "simulated":    False,
                    "source":       "Celestrak",
                })
            else:
                lat, lon, alt, sim = simulate_position()
                body = json.dumps({
                    "sat_id":    sat_id,
                    "name":      "ISS (simulated)",
                    "lat":       round(lat, 4),
                    "lon":       round(lon, 4),
                    "alt_km":    round(alt, 1),
                    "simulated": True,
                    "source":    "fallback",
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
