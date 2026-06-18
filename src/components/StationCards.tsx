import type { StationResult } from "../hooks/useSatellite";

function scoreColor(score: number) {
  if (score >= 0.75) return { bg: "bg-green-500/10 border-green-500/30", text: "text-green-400", bar: "bg-green-500" };
  if (score >= 0.5)  return { bg: "bg-yellow-500/10 border-yellow-500/30", text: "text-yellow-400", bar: "bg-yellow-500" };
  if (score >= 0.25) return { bg: "bg-orange-500/10 border-orange-500/30", text: "text-orange-400", bar: "bg-orange-500" };
  return { bg: "bg-red-500/10 border-red-500/30", text: "text-red-400", bar: "bg-red-500" };
}

interface Props {
  stations: StationResult[];
  bestStation: string | null;
  handoffNeeded: boolean;
}

export default function StationCards({ stations, bestStation, handoffNeeded }: Props) {
  return (
    <div className="space-y-3">
      {/* Handoff alert */}
      {handoffNeeded && (
        <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 rounded-lg px-4 py-2 text-amber-300 text-sm font-medium">
          <span className="text-base">⚠</span>
          Proactive handoff recommended — link quality dropping
        </div>
      )}
      {!handoffNeeded && stations.length > 0 && (
        <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/30 rounded-lg px-4 py-2 text-green-300 text-sm font-medium">
          <span className="text-base">✓</span>
          Link stable — no handoff needed
        </div>
      )}

      {/* Station cards */}
      {stations.map((s) => {
        const c = scoreColor(s.score_now);
        const isBest = s.station === bestStation;
        return (
          <div
            key={s.station}
            className={`rounded-xl border p-4 transition-all ${c.bg} ${isBest ? "ring-1 ring-white/20" : ""}`}
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <span className="font-semibold text-white text-sm">{s.station}</span>
                {isBest && (
                  <span className="ml-2 text-xs bg-white/10 text-white/70 px-2 py-0.5 rounded-full">
                    Best
                  </span>
                )}
              </div>
              <span className={`text-lg font-bold ${c.text}`}>
                {(s.score_now * 100).toFixed(0)}%
              </span>
            </div>

            {/* Score bar */}
            <div className="h-1.5 bg-white/10 rounded-full mb-3">
              <div
                className={`h-full rounded-full transition-all ${c.bar}`}
                style={{ width: `${s.score_now * 100}%` }}
              />
            </div>

            <div className="grid grid-cols-3 gap-2 text-xs text-slate-400">
              <div>
                <div className="text-slate-500">Elevation</div>
                <div className="text-white font-medium">{s.elevation_deg.toFixed(1)}°</div>
              </div>
              <div>
                <div className="text-slate-500">Distance</div>
                <div className="text-white font-medium">{s.distance_km.toFixed(0)} km</div>
              </div>
              <div>
                <div className="text-slate-500">Rx Power</div>
                <div className="text-white font-medium">{s.rx_power_dbm.toFixed(1)} dBm</div>
              </div>
            </div>

            {s.score_drop > 0.15 && (
              <div className="mt-2 text-xs text-orange-400">
                Score dropping {(s.score_drop * 100).toFixed(1)}% in 10s
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
