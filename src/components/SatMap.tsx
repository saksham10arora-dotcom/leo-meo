import { useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
// Fix default icon
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png",
  shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png",
});

function scoreColor(score: number): string {
  if (score >= 0.75) return "#22c55e";
  if (score >= 0.5)  return "#f59e0b";
  if (score >= 0.25) return "#f97316";
  return "#ef4444";
}

const satIcon = L.divIcon({
  className: "",
  html: `<div style="width:22px;height:22px;background:#6366f1;border-radius:50%;border:3px solid white;box-shadow:0 0 12px #6366f1,0 2px 6px rgba(0,0,0,0.5);display:flex;align-items:center;justify-content:center;font-size:10px;">🛰</div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function stationIcon(score: number) {
  const c = scoreColor(score);
  return L.divIcon({
    className: "",
    html: `<div style="width:26px;height:26px;background:${c};border-radius:50%;border:3px solid white;box-shadow:0 2px 8px rgba(0,0,0,0.4);display:flex;align-items:center;justify-content:center;color:white;font-size:9px;font-weight:bold;">${Math.round(score * 100)}</div>`,
    iconSize: [26, 26],
    iconAnchor: [13, 13],
  });
}

function FlyTo({ lat, lon }: { lat: number; lon: number }) {
  const map = useMap();
  useEffect(() => {
    map.flyTo([lat, lon], 5, { duration: 1.0 });
  }, [lat, lon, map]);
  return null;
}

interface MapStation {
  name: string;
  lat: number;
  lon: number;
  score_now: number;
}

interface Props {
  satLat: number;
  satLon: number;
  satAlt: number;
  stations: MapStation[];
  bestStation: string | null;
}

export default function SatMap({ satLat, satLon, satAlt, stations, bestStation }: Props) {
  return (
    <div className="relative h-full w-full rounded-xl overflow-hidden border border-white/10">
      <MapContainer
        center={[20, 78]}
        zoom={4}
        scrollWheelZoom={true}
        className="h-full w-full"
        style={{ background: "#0f172a" }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution="&copy; OpenStreetMap contributors"
        />

        <FlyTo lat={satLat} lon={satLon} />

        {/* Satellite marker */}
        <Marker position={[satLat, satLon]} icon={satIcon}>
          <Popup>
            <strong>Satellite</strong><br />
            {satLat.toFixed(2)}°N, {satLon.toFixed(2)}°E<br />
            Alt: {satAlt.toFixed(0)} km
          </Popup>
        </Marker>

        {/* Ground stations */}
        {stations.map((s) => (
          <div key={s.name}>
            <Marker
              position={[s.lat, s.lon]}
              icon={stationIcon(s.score_now)}
            >
              <Popup>
                <strong>{s.name}</strong>
                {s.name === bestStation && " ★ Best"}<br />
                Score: {(s.score_now * 100).toFixed(1)}%
              </Popup>
            </Marker>
            <Circle
              center={[s.lat, s.lon]}
              radius={s.score_now * 400000}
              pathOptions={{
                color: scoreColor(s.score_now),
                fillColor: scoreColor(s.score_now),
                fillOpacity: 0.08,
                weight: 1.5,
              }}
            />
          </div>
        ))}
      </MapContainer>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-slate-900/90 backdrop-blur border border-white/10 rounded-lg p-3 text-xs text-white space-y-1">
        <div className="font-semibold mb-1 text-slate-300">Visibility Score</div>
        {[["#22c55e","≥75%"],["#f59e0b","50–75%"],["#f97316","25–50%"],["#ef4444","<25%"]].map(([c,l]) => (
          <div key={l} className="flex items-center gap-2">
            <span style={{ background: c }} className="w-3 h-3 rounded-full inline-block" />
            {l}
          </div>
        ))}
      </div>
    </div>
  );
}
