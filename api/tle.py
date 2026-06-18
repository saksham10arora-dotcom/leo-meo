import json
import math
import datetime
import urllib.request
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Celestrak GP data API (new format, active since 2022)
CATALOG_IDS = {
    "ISS":   "25544",
    "HST":   "20580",
    "TERRA": "25994",
    "AQUA":  "27424",
}

def fetch_tle_lines(sat_id: str):
    """Fetch TLE from Celestrak GP API. Returns (name, line1, line2)."""
    cat_num = CATALOG_IDS.get(sat_id.upper(), "25544")
    url = f"https://celestrak.org/NORAD/elements/gp.php?CATNR={cat_num}&FORMAT=TLE"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "leo-meo/1.0"})
        with urllib.request.urlopen(req, timeout=5) as r:
            text = r.read().decode("utf-8").strip()
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        if len(lines) >= 3:
            return lines[0], lines[1], lines[2]
    except Exception:
        pass
    return None


def sgp4_propagate(tle_name, tle_line1, tle_line2):
    """
    Minimal SGP4 propagation — stdlib only, no skyfield/sgp4 package.
    Returns (lat_deg, lon_deg, alt_km).
    """
    # Parse epoch from line 1 (chars 18-31)
    epoch_str = tle_line1[18:32].strip()
    year_2d   = int(epoch_str[:2])
    year      = (2000 + year_2d) if year_2d < 57 else (1900 + year_2d)
    day_of_yr = float(epoch_str[2:])

    epoch_dt = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc) + \
               datetime.timedelta(days=day_of_yr - 1)
    now      = datetime.datetime.now(datetime.timezone.utc)
    dt_min   = (now - epoch_dt).total_seconds() / 60.0

    # Mean motion (rev/day) — line 2 chars 52-62
    mean_motion_rev_day = float(tle_line2[52:63])
    n = mean_motion_rev_day * 2 * math.pi / (24 * 60)  # rad/min

    # Orbital elements
    inc  = math.radians(float(tle_line2[8:16]))
    raan = math.radians(float(tle_line2[17:25]))
    ecc  = float("0." + tle_line2[26:33])
    argp = math.radians(float(tle_line2[34:42]))
    M0   = math.radians(float(tle_line2[43:51]))
    M    = M0 + n * dt_min

    # Solve Kepler's equation (Newton iterations)
    E = M
    for _ in range(10):
        E = E - (E - ecc * math.sin(E) - M) / (1 - ecc * math.cos(E))

    # True anomaly
    nu = 2 * math.atan2(
        math.sqrt(1 + ecc) * math.sin(E / 2),
        math.sqrt(1 - ecc) * math.cos(E / 2)
    )

    # Semi-major axis from mean motion
    MU = 398600.4418
    a  = (MU / (n / 60) ** 2) ** (1 / 3)
    r  = a * (1 - ecc * math.cos(E))

    # Perifocal to ECI
    cos_raan, sin_raan = math.cos(raan), math.sin(raan)
    cos_inc,  sin_inc  = math.cos(inc),  math.sin(inc)
    cos_argp, sin_argp = math.cos(argp), math.sin(argp)

    x_orb, y_orb = r * math.cos(nu), r * math.sin(nu)

    x_eci = (cos_raan*cos_argp - sin_raan*sin_argp*cos_inc)*x_orb + \
            (-cos_raan*sin_argp - sin_raan*cos_argp*cos_inc)*y_orb
    y_eci = (sin_raan*cos_argp + cos_raan*sin_argp*cos_inc)*x_orb + \
            (-sin_raan*sin_argp + cos_raan*cos_argp*cos_inc)*y_orb
    z_eci = (sin_argp*sin_inc)*x_orb + (cos_argp*sin_inc)*y_orb

    # ECI to ECEF — rotate by Greenwich Sidereal Time
    j2000 = datetime.datetime(2000, 1, 1, 12, tzinfo=datetime.timezone.utc)
    days_since_j2000 = (now - j2000).total_seconds() / 86400.0
    gst = math.radians((280.46061837 + 360.98564724 * days_since_j2000) % 360)

    x_ecef =  x_eci * math.cos(gst) + y_eci * math.sin(gst)
    y_ecef = -x_eci * math.sin(gst) + y_eci * math.cos(gst)
    z_ecef =  z_eci

    # ECEF to geodetic (WGS84 iterative)
    R_EARTH = 6378.137
    E2      = 0.00669437999014
    p       = math.sqrt(x_ecef**2 + y_ecef**2)
    lon_rad = math.atan2(y_ecef, x_ecef)
    lat_rad = math.atan2(z_ecef, p * (1 - E2))
    for _ in range(5):
        N       = R_EARTH / math.sqrt(1 - E2 * math.sin(lat_rad)**2)
        lat_rad = math.atan2(z_ecef + E2 * N * math.sin(lat_rad), p)

    alt_km = (p / math.cos(lat_rad)) - R_EARTH \
             if abs(math.degrees(lat_rad)) < 89 \
             else abs(z_ecef) / math.sin(lat_rad) - R_EARTH * (1 - E2)

    return math.degrees(lat_rad), math.degrees(lon_rad), alt_km


def simulate_position():
    """Fallback: simulated ISS-like orbit."""
    now    = datetime.datetime.now(datetime.timezone.utc)
    t      = now.timestamp()
    period = 92 * 60
    phase  = (t % period) / period * 2 * math.pi
    lat    = 51.6 * math.sin(phase)
    lon    = (((t / period) * 360) % 360) - 180
    return lat, lon, 408.0


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_): pass

    def do_GET(self):
        parsed = urlparse(self.path)
        params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        sat_id = params.get("sat", "ISS").upper()

        try:
            result = fetch_tle_lines(sat_id)
            if result:
                name, line1, line2 = result
                lat, lon, alt = sgp4_propagate(name, line1, line2)
                body = json.dumps({
                    "sat_id":    sat_id,
                    "name":      name.strip(),
                    "lat":       round(lat, 4),
                    "lon":       round(lon, 4),
                    "alt_km":    round(alt, 1),
                    "simulated": False,
                    "source":    "Celestrak GP",
                })
            else:
                lat, lon, alt = simulate_position()
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
