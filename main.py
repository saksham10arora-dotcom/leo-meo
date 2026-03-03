import streamlit as st
import pandas as pd
import numpy as np
import joblib
import streamlit.components.v1 as components

# ----------------------------------
# Page Configuration
# ----------------------------------
st.set_page_config(
    page_title="Satellite Handover Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------------------------
# Custom CSS
# ----------------------------------
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #00d4ff;
        --secondary-color: #7b2cbf;
        --success-color: #00ff88;
        --warning-color: #ffaa00;
    }
    
    /* Header styling */
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    .main-header h1 {
        color: white;
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: #e0e0e0;
        font-size: 1.2rem;
        margin-top: 0.5rem;
    }
    
    /* Card styling */
    .metric-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        margin: 1rem 0;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00ff88;
        text-shadow: 0 0 10px rgba(0,255,136,0.5);
    }
    
    .metric-label {
        font-size: 1rem;
        color: #b0b0b0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Best station card */
    .best-station {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        box-shadow: 0 8px 30px rgba(0,0,0,0.3);
        margin: 2rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 8px 30px rgba(0,0,0,0.3); }
        50% { box-shadow: 0 8px 40px rgba(56,239,125,0.5); }
    }
    
    .best-station h2 {
        margin-top: 0;
        font-size: 1.8rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    
    /* Station table styling */
    .station-table {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 1rem;
        backdrop-filter: blur(10px);
    }
    
    /* Input section */
    .input-section {
        background: linear-gradient(135deg, #2d3561 0%, #1f2544 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        margin-bottom: 2rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Button styling */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 20px rgba(102,126,234,0.4);
    }
    
    /* Info box */
    .info-box {
        background: rgba(0,212,255,0.1);
        border-left: 4px solid #00d4ff;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .status-optimal {
        background: linear-gradient(135deg, #00ff88 0%, #00cc6a 100%);
        color: #003d1a;
    }
    
    .status-good {
        background: linear-gradient(135deg, #ffaa00 0%, #ff8800 100%);
        color: #4d2200;
    }
    
    .status-poor {
        background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------
# Load trained ML model
# ----------------------------------
model = joblib.load("visibility_model.pkl")
FEATURES = list(model.feature_names_in_)

# ----------------------------------
# Satellite constellation (from first code) - SPREAD GLOBALLY
# ----------------------------------
SATELLITES = [
    {"id": "SAT-LEO-1", "orbit_type": "LEO", "lat": 20, "lon": 77, "alt_km": 550},
    {"id": "SAT-LEO-2", "orbit_type": "LEO", "lat": -30, "lon": 150, "alt_km": 550},
    {"id": "SAT-LEO-3", "orbit_type": "LEO", "lat": 45, "lon": -100, "alt_km": 550},
    {"id": "SAT-MEO-1", "orbit_type": "MEO", "lat": 10, "lon": 30, "alt_km": 12000},
    {"id": "SAT-MEO-2", "orbit_type": "MEO", "lat": -20, "lon": -60, "alt_km": 12000},
    {"id": "SAT-MEO-3", "orbit_type": "MEO", "lat": 35, "lon": 120, "alt_km": 12000},
]

# ----------------------------------
# Ground station database
# ----------------------------------
GROUND_STATIONS = {
    "Bangalore": (12.9716, 77.5946),
    "Delhi": (28.61, 77.2),
    "Mumbai": (19.07, 72.87),
    "Chennai": (13.08, 80.27),
}

# ----------------------------------
# Station load (0 = free, 1 = saturated)
# ----------------------------------
STATION_LOAD = {
    "Bangalore": 0.30,
    "Delhi": 0.45,
    "Mumbai": 0.60,
    "Chennai": 0.20,
}

# ----------------------------------
# Utility Functions
# ----------------------------------
def fspl(distance_km, freq_ghz=12):
    return 92.45 + 20 * np.log10(distance_km) + 20 * np.log10(freq_ghz)

def estimate_doppler(distance_km):
    return 0.02 * distance_km

def get_status_badge(score):
    if score >= 0.7:
        return "status-optimal", "🟢 Optimal"
    elif score >= 0.4:
        return "status-good", "🟡 Good"
    else:
        return "status-poor", "🔴 Poor"

def distance_deg(a_lat, a_lon, b_lat, b_lon):
    return np.sqrt((a_lat - b_lat)**2 + (a_lon - b_lon)**2)

# ----------------------------------
# Header
# ----------------------------------
st.markdown("""
<div class="main-header">
    <h1>🛰️ Satellite Handover Dashboard</h1>
    <p>Physics-Aware ML • Load-Balanced Decision Engine • Real-Time Analysis</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------
# Sidebar - Satellite Configuration
# ----------------------------------
with st.sidebar:
    st.markdown("### 🎯 Satellite Configuration")
    st.markdown("---")
    
    orbit_type = st.selectbox(
        "🌍 Orbit Type",
        ["LEO", "MEO", "GEO"],
        help="Low Earth Orbit (LEO), Medium Earth Orbit (MEO), or Geostationary Orbit (GEO)"
    )
    orbit_type_enc = {"LEO": 0, "MEO": 1, "GEO": 2}[orbit_type]
    
    st.markdown("---")
    st.markdown("### 📡 Orbital Parameters")
    
    sat_altitude_km = st.slider(
        "Altitude (km)",
        300, 36000, 550,
        help="Satellite altitude above Earth's surface"
    )
    
    elevation = st.slider(
        "Elevation Angle (°)",
        0.0, 90.0, 45.0,
        help="Angle between ground station and satellite"
    )
    
    distance_km = st.slider(
        "Slant Range (km)",
        200.0, 40000.0, 1200.0,
        help="Direct distance from satellite to ground station"
    )
    
    st.markdown("---")
    st.markdown("### 📊 Active Satellites")
    leo_count = sum(1 for s in SATELLITES if s['orbit_type'] == 'LEO')
    meo_count = sum(1 for s in SATELLITES if s['orbit_type'] == 'MEO')
    st.info(f"""
    **LEO Satellites:** {leo_count} 🔵  
    **MEO Satellites:** {meo_count} 🟠  
    **Total:** {len(SATELLITES)}
    """)
    
    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.info(f"""
    **Active Orbit:** {orbit_type}  
    **Stations:** {len(GROUND_STATIONS)}  
    **ML Model:** Loaded ✓
    """)

# ----------------------------------
# Prediction Logic
# ----------------------------------
rows = []

for station, (gs_lat, gs_lon) in GROUND_STATIONS.items():
    distance_log = np.log1p(distance_km)
    sin_elev = np.sin(np.radians(elevation))
    cos_elev = np.cos(np.radians(elevation))
    doppler_hz = estimate_doppler(distance_km)
    fspl_db = fspl(distance_km)
    atm_loss_db = 2 + (1 - sin_elev) * 3
    rx_power_dbm = -fspl_db - atm_loss_db
    rx_margin = rx_power_dbm + 120

    row = {
        "orbit_type_enc": orbit_type_enc,
        "sat_altitude_km": sat_altitude_km,
        "gs_lat": gs_lat,
        "gs_lon": gs_lon,
        "distance_km": distance_km,
        "elevation": elevation,
        "doppler_hz": doppler_hz,
        "fspl_db": fspl_db,
        "atm_loss_db": atm_loss_db,
        "rx_power_dbm": rx_power_dbm,
        "distance_log": distance_log,
        "sin_elevation": sin_elev,
        "cos_elevation": cos_elev,
        "rx_margin": rx_margin
    }

    X = pd.DataFrame([row])[FEATURES]
    prob = model.predict_proba(X)[0][1]
    load = STATION_LOAD.get(station, 0)
    final_score = prob * (1 - load)

    rows.append({
        "Station": station,
        "Raw Probability": round(prob, 4),
        "Load Factor": load,
        "Final Score": round(final_score, 4),
        "Latitude": gs_lat,
        "Longitude": gs_lon
    })

df = pd.DataFrame(rows).sort_values("Final Score", ascending=False)

if df.empty:
    st.error("❌ No ground stations available.")
    st.stop()

best = df.iloc[0]

# ----------------------------------
# Key Metrics Row
# ----------------------------------
st.markdown("### 📊 Real-Time Metrics")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Best Station",
        value=best['Station'],
        delta=f"Score: {best['Final Score']:.3f}"
    )

with col2:
    st.metric(
        label="Raw Probability",
        value=f"{best['Raw Probability']:.1%}",
        delta=f"{'High' if best['Raw Probability'] > 0.7 else 'Moderate'}"
    )

with col3:
    avg_load = df['Load Factor'].mean()
    st.metric(
        label="Avg Network Load",
        value=f"{avg_load:.1%}",
        delta=f"{'Busy' if avg_load > 0.5 else 'Available'}"
    )

with col4:
    active_stations = len(df[df['Final Score'] > 0.5])
    st.metric(
        label="Active Stations",
        value=f"{active_stations}/{len(df)}",
        delta=f"{active_stations/len(df):.0%} Ready"
    )

st.markdown("---")

# ----------------------------------
# Main Content Tabs
# ----------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Station Rankings",
    "🌍 3D Satellite View",
    "📈 Analytics",
    "🎯 Station Details"
])

# ----------------------------------
# TAB 1: Station Rankings
# ----------------------------------
with tab1:
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.markdown("### 🏆 Ground Station Performance")
        
        # Create enhanced dataframe display
        display_df = df[['Station', 'Final Score', 'Raw Probability', 'Load Factor']].copy()
        display_df['Raw Probability'] = display_df['Raw Probability'].apply(lambda x: f"{x:.1%}")
        display_df['Load Factor'] = display_df['Load Factor'].apply(lambda x: f"{x:.1%}")
        display_df['Final Score'] = display_df['Final Score'].apply(lambda x: f"{x:.4f}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=300
        )
        
        # Score distribution chart
        st.markdown("#### 📊 Station Score Comparison")
        chart_df = df.set_index('Station')[['Final Score']]
        st.bar_chart(chart_df, height=350, color='#00ff88')
    
    with col_right:
        status_class, status_text = get_status_badge(best['Final Score'])
        
        st.markdown(f"""
        <div class="best-station">
            <h2>🎯 Recommended Station</h2>
            <h1 style="font-size: 2.5rem; margin: 1rem 0;">{best['Station']}</h1>
            <div class="status-badge {status_class}" style="margin: 1rem 0;">
                {status_text}
            </div>
            <hr style="border-color: rgba(255,255,255,0.3); margin: 1.5rem 0;">
            <div style="font-size: 1.1rem;">
                <p><strong>Final Score:</strong> {best['Final Score']:.4f}</p>
                <p><strong>Raw Probability:</strong> {best['Raw Probability']:.1%}</p>
                <p><strong>Load Factor:</strong> {best['Load Factor']:.1%}</p>
                <p><strong>Location:</strong> {best['Latitude']:.2f}°, {best['Longitude']:.2f}°</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📡 Load Distribution")
        for idx, row in df.iterrows():
            st.write(f"**{row['Station']}**")
            st.progress(row['Load Factor'], text=f"{row['Load Factor']:.1%} Load")

# ----------------------------------
# TAB 2: 3D Satellite View with Movement
# ----------------------------------
with tab2:
    st.markdown("### 🌍 Global Satellite Network Visualization")
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.info("🛰️ **6 Satellites orbiting in real-time!** LEO satellites (CYAN), MEO satellites (ORANGE)")
    with col_info2:
        st.success("🔗 **Bright GREEN lines** show active ground-to-satellite connections")
    
    # Cesium Setup Vars
    CESIUM_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiJlNzljNTkxOC0wNzM4LTRlMmYtOGU5OS1lNmRmOGM5MjYwNTAiLCJpZCI6Mzg4MTgyLCJpYXQiOjE3NzA0ODIzODJ9.jSEjwdyZOylZLa7ieIuJ3anC2IMGZQbJNhv5LgBWzBc"
    
    # Generate ground station entities
    station_js = ""
    for name, (lat, lon) in GROUND_STATIONS.items():
        station_js += f"""
        viewer.entities.add({{
            id: "{name}",
            name: "{name}",
            position: Cesium.Cartesian3.fromDegrees({lon}, {lat}, 50),
            point: {{ 
                pixelSize: 16, 
                color: Cesium.Color.YELLOW,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 3
            }},
            label: {{
                text: "{name}",
                font: "bold 14px sans-serif",
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 3,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(0, -22),
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            }}
        }});
        """
    
    # Generate satellite entities with orbital movement - EACH SATELLITE SEPARATE
    satellites_js = ""
    sat_index = 0
    for sat in SATELLITES:
        sat_index += 1
        color = "Cesium.Color.CYAN" if sat['orbit_type'] == "LEO" else "Cesium.Color.ORANGE"
        trail_color = "Cesium.Color.CYAN.withAlpha(0.5)" if sat['orbit_type'] == "LEO" else "Cesium.Color.ORANGE.withAlpha(0.5)"
        
        # Find nearest ground station for this satellite
        nearest_station = None
        min_dist = 999999
        for gs_name, (gs_lat, gs_lon) in GROUND_STATIONS.items():
            dist = distance_deg(sat['lat'], sat['lon'], gs_lat, gs_lon)
            if dist < min_dist:
                min_dist = dist
                nearest_station = gs_name
        
        satellites_js += f"""
        // ========== SATELLITE {sat_index}: {sat['id']} ==========
        console.log("Creating satellite: {sat['id']}");
        
        var posProp{sat_index} = new Cesium.SampledPositionProperty();
        var startTime{sat_index} = viewer.clock.currentTime.clone();
        
        // Generate orbital path
        for (var i = 0; i <= 360; i += 5) {{
            var t = Cesium.JulianDate.addSeconds(startTime{sat_index}, i * 10, new Cesium.JulianDate());
            var lon = {sat['lon']} + i * 0.25;
            var lat = {sat['lat']} + Math.sin(Cesium.Math.toRadians(i)) * {'3' if sat['orbit_type'] == 'LEO' else '1.5'};
            var alt = {sat['alt_km']} * 1000;
            
            posProp{sat_index}.addSample(t, Cesium.Cartesian3.fromDegrees(lon, lat, alt));
        }}
        
        // Create satellite entity
        var satEntity{sat_index} = viewer.entities.add({{
            id: "{sat['id']}",
            name: "{sat['id']}",
            position: posProp{sat_index},
            point: {{
                pixelSize: 20,
                color: {color},
                outlineColor: Cesium.Color.WHITE,
                outlineWidth: 3,
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            }},
            path: {{
                show: true,
                leadTime: 0,
                trailTime: 1000,
                width: 4,
                material: {trail_color},
                resolution: 1
            }},
            label: {{
                text: "{sat['id']}",
                font: "bold 14px sans-serif",
                fillColor: Cesium.Color.WHITE,
                outlineColor: Cesium.Color.BLACK,
                outlineWidth: 3,
                style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                pixelOffset: new Cesium.Cartesian2(0, -25),
                showBackground: true,
                backgroundColor: Cesium.Color.BLACK.withAlpha(0.9),
                backgroundPadding: new Cesium.Cartesian2(8, 4),
                disableDepthTestDistance: Number.POSITIVE_INFINITY
            }}
        }});
        
        console.log("Satellite {sat['id']} created successfully");
        
        // Create ground link to nearest station: {nearest_station}
        viewer.entities.add({{
            name: "Link-{sat['id']}-to-{nearest_station}",
            polyline: {{
                positions: new Cesium.CallbackProperty(function(time) {{
                    var satPos = satEntity{sat_index}.position.getValue(time);
                    var gsEntity = viewer.entities.getById("{nearest_station}");
                    var gsPos = gsEntity ? gsEntity.position.getValue(time) : null;
                    if (satPos && gsPos) {{
                        return [gsPos, satPos];
                    }}
                    return null;
                }}, false),
                width: 6,
                material: Cesium.Color.LIME,
                arcType: Cesium.ArcType.NONE,
                clampToGround: false
            }}
        }});
        
        console.log("Link created for {sat['id']} to {nearest_station}");
        
        """
    
    satellites_js += """
    console.log("Total satellites created: " + viewer.entities.values.length);
    """
    
    cesium_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <script src="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Cesium.js"></script>
    <link href="https://cesium.com/downloads/cesiumjs/releases/1.104/Build/Cesium/Widgets/widgets.css" rel="stylesheet">
    <style>
    html, body, #cesiumContainer {{
        width: 100%;
        height: 700px;
        margin: 0;
        padding: 0;
    }}
    .legend {{
        position: absolute;
        top: 10px;
        right: 10px;
        background: rgba(0, 0, 0, 0.8);
        color: white;
        padding: 15px;
        border-radius: 8px;
        font-family: sans-serif;
        font-size: 12px;
        z-index: 1000;
    }}
    .legend-item {{
        margin: 8px 0;
        display: flex;
        align-items: center;
    }}
    .legend-color {{
        width: 20px;
        height: 20px;
        margin-right: 10px;
        border-radius: 50%;
        border: 2px solid rgba(255,255,255,0.5);
    }}
    .debug-info {{
        position: absolute;
        bottom: 10px;
        left: 10px;
        background: rgba(0, 0, 0, 0.9);
        color: lime;
        padding: 10px;
        border-radius: 5px;
        font-family: monospace;
        font-size: 11px;
        z-index: 1000;
        max-width: 300px;
    }}
    </style>
    </head>
    <body>
    <div id="cesiumContainer"></div>
    <div class="legend">
        <h3 style="margin-top: 0; margin-bottom: 10px; border-bottom: 1px solid #444; padding-bottom: 5px;">Legend</h3>
        <div class="legend-item">
            <div class="legend-color" style="background: cyan;"></div>
            <span>LEO Satellites (550 km)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: orange;"></div>
            <span>MEO Satellites (12,000 km)</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: yellow;"></div>
            <span>Ground Stations</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: lime;"></div>
            <span>Active Ground Links</span>
        </div>
    </div>
    <div class="debug-info" id="debugInfo">
        Loading satellites...
    </div>
    <script>
    Cesium.Ion.defaultAccessToken = "{CESIUM_TOKEN}";
    const viewer = new Cesium.Viewer('cesiumContainer', {{
        animation: false,
        timeline: false,
        homeButton: false,
        geocoder: false,
        baseLayerPicker: false,
        sceneModePicker: false,
        navigationHelpButton: false,
        fullscreenButton: false,
        shouldAnimate: true
    }});
    
    // Enable globe lighting
    viewer.scene.globe.enableLighting = true;
    
    // Configure clock for animation
    viewer.clock.shouldAnimate = true;
    viewer.clock.multiplier = 10;
    viewer.clock.clockRange = Cesium.ClockRange.UNBOUNDED;
    
    // Add ground stations
    {station_js}
    
    // Add satellites with orbital motion
    {satellites_js}
    
    // Set initial camera view - zoom out to see all satellites
    viewer.camera.flyTo({{
        destination: Cesium.Cartesian3.fromDegrees(80, 20, 35000000),
        duration: 3
    }});
    
    // Log entities for debugging
    console.log("=== CESIUM INITIALIZATION COMPLETE ===");
    console.log("Total entities: " + viewer.entities.values.length);
    viewer.entities.values.forEach(function(entity) {{
        console.log("Entity: " + (entity.id || entity.name) + " | Type: " + (entity.point ? "Point" : entity.polyline ? "Polyline" : "Other"));
    }});
    
    // Update debug info
    function updateDebugInfo() {{
        var satellites = 0;
        var stations = 0;
        var links = 0;
        
        viewer.entities.values.forEach(function(e) {{
            if (e.id && e.id.startsWith("SAT-")) satellites++;
            else if (e.point && !e.id.startsWith("SAT-")) stations++;
            else if (e.polyline) links++;
        }});
        
        document.getElementById("debugInfo").innerHTML = 
            "✓ Satellites: " + satellites + "<br>" +
            "✓ Ground Stations: " + stations + "<br>" +
            "✓ Active Links: " + links + "<br>" +
            "✓ Total Entities: " + viewer.entities.values.length;
    }}
    
    updateDebugInfo();
    setInterval(updateDebugInfo, 2000);
    </script>
    </body>
    </html>
    """
    
    components.html(cesium_html, height=750)
    
    # Satellite status table
    st.markdown("### 🛰️ Active Satellite Constellation")
    sat_df = pd.DataFrame(SATELLITES)
    sat_df['Altitude (km)'] = sat_df['alt_km']
    sat_df['Orbit'] = sat_df['orbit_type']
    sat_df['Satellite ID'] = sat_df['id']
    sat_df['Position'] = sat_df.apply(lambda x: f"{x['lat']:.1f}°, {x['lon']:.1f}°", axis=1)
    
    display_sat_df = sat_df[['Satellite ID', 'Orbit', 'Altitude (km)', 'Position']]
    st.dataframe(display_sat_df, use_container_width=True)

# ----------------------------------
# TAB 3: Analytics
# ----------------------------------
with tab3:
    st.markdown("### 📈 Performance Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Station Performance Overview")
        
        # Create comparison dataframe
        comparison_df = df[['Station', 'Raw Probability', 'Load Factor', 'Final Score']].copy()
        comparison_df = comparison_df.set_index('Station')
        
        st.bar_chart(comparison_df[['Raw Probability', 'Final Score']], height=350)
        
        st.markdown("#### Load by Station")
        load_df = df.set_index('Station')[['Load Factor']]
        st.bar_chart(load_df, height=300, color='#ff6b6b')
    
    with col2:
        st.markdown("#### Performance Metrics")
        
        # Best station metrics
        st.info(f"""
        **Best Station: {best['Station']}**
        
        - Final Score: {best['Final Score']:.4f}
        - Raw Probability: {best['Raw Probability']:.1%}
        - Availability: {(1 - best['Load Factor']):.1%}
        """)
        
        st.markdown("#### Top 3 Stations")
        top3 = df.head(3)
        
        for idx, row in top3.iterrows():
            with st.container():
                st.markdown(f"**{idx+1}. {row['Station']}**")
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Final Score", f"{row['Final Score']:.3f}")
                with col_b:
                    st.metric("Raw Prob", f"{row['Raw Probability']:.1%}")
                st.divider()
        
        st.markdown("#### Score Distribution")
        score_df = df.set_index('Station')[['Final Score']]
        st.area_chart(score_df, height=300, color='#00d4ff')
        
        # Satellite constellation stats
        st.markdown("#### 🛰️ Constellation Status")
        leo_sats = [s for s in SATELLITES if s['orbit_type'] == 'LEO']
        meo_sats = [s for s in SATELLITES if s['orbit_type'] == 'MEO']
        
        st.success(f"""
        **LEO Satellites:** {len(leo_sats)} active  
        **MEO Satellites:** {len(meo_sats)} active  
        **Coverage:** Global
        """)

# ----------------------------------
# TAB 4: Station Details
# ----------------------------------
with tab4:
    st.markdown("### 🎯 Detailed Station Information")
    
    selected_station = st.selectbox("Select Station for Details", df['Station'].tolist())
    station_data = df[df['Station'] == selected_station].iloc[0]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Final Score</div>
            <div class="metric-value">{station_data['Final Score']:.4f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Raw Probability</div>
            <div class="metric-value">{station_data['Raw Probability']:.1%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">Load Factor</div>
            <div class="metric-value">{station_data['Load Factor']:.1%}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📍 Geographic Information")
        st.info(f"""
        **Latitude:** {station_data['Latitude']:.4f}°  
        **Longitude:** {station_data['Longitude']:.4f}°  
        **Status:** {'🟢 Operational' if station_data['Final Score'] > 0.5 else '🟡 Limited'}
        """)
        
        st.markdown("#### 🔧 Calculated Parameters")
        st.code(f"""
Elevation Angle: {elevation:.2f}°
Slant Range: {distance_km:.2f} km
Satellite Altitude: {sat_altitude_km:.2f} km
Orbit Type: {orbit_type}
        """, language="text")
        
        # Find nearest satellites
        st.markdown("#### 🛰️ Nearest Satellites")
        gs_lat, gs_lon = station_data['Latitude'], station_data['Longitude']
        sat_distances = []
        for sat in SATELLITES:
            dist = distance_deg(gs_lat, gs_lon, sat['lat'], sat['lon'])
            sat_distances.append({
                'Satellite': sat['id'],
                'Type': sat['orbit_type'],
                'Distance': f"{dist:.2f}°"
            })
        sat_dist_df = pd.DataFrame(sat_distances).sort_values('Distance')
        st.dataframe(sat_dist_df.head(3), use_container_width=True)
    
    with col2:
        st.markdown("#### 📊 Performance Metrics")
        
        # Score indicator
        st.markdown("**Station Score**")
        st.progress(station_data['Final Score'], text=f"{station_data['Final Score']:.4f}")
        
        # Performance breakdown
        st.markdown("**Performance Breakdown**")
        metrics_data = {
            'Raw Probability': station_data['Raw Probability'],
            'Availability': 1 - station_data['Load Factor'],
            'Final Score': station_data['Final Score']
        }
        
        for metric, value in metrics_data.items():
            col_m1, col_m2 = st.columns([3, 1])
            with col_m1:
                st.progress(value, text=metric)
            with col_m2:
                st.write(f"{value:.2%}")
        
        # Status indicator
        status_class, status_text = get_status_badge(station_data['Final Score'])
        if 'optimal' in status_class:
            st.success(f"Status: {status_text}")
        elif 'good' in status_class:
            st.warning(f"Status: {status_text}")
        else:
            st.error(f"Status: {status_text}")

# ----------------------------------
# Footer
# ----------------------------------
st.markdown("---")
st.markdown(f"""
<div style="text-align: center; padding: 2rem; color: #888;">
    <p><strong>🛰️ Satellite Handover Dashboard v2.0</strong></p>
    <p>Feature-Locked • Physics-Informed • Production-Safe</p>
    <p style="font-size: 0.8rem; margin-top: 1rem;">
        Powered by ML Prediction Engine | Real-time Load Balancing | Cesium 3D Visualization
    </p>
    <p style="font-size: 0.75rem; margin-top: 0.5rem; color: #666;">
        Active Satellites: {len(SATELLITES)} | Ground Stations: {len(GROUND_STATIONS)} | Real-time Orbital Tracking ✓
    </p>
</div>
""", unsafe_allow_html=True)