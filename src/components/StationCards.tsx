import type { StationResult } from "../hooks/useSatellite";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444"];

function snrColor(snr: number) {
  if (snr >= 20) return { bg: "bg-green-500/10 border-green-500/30", text: "text-green-400", bar: "bg-green-500" };
  if (snr >= 12) return { bg: "bg-yellow-500/10 border-yellow-500/30", text: "text-yellow-400", bar: "bg-yellow-500" };
  if (snr >= 5)  return { bg: "bg-orange-500/10 border-orange-500/30", text: "text-orange-400", bar: "bg-orange-500" };
  return { bg: "bg-red-500/10 border-red-500/30", text: "text-red-400", bar: "bg-red-500" };
}

function scoreColor(score: number) {
  if (score >= 0.75) return { bg: "bg-green-500/10 border-green-500/30", text: "text-green-400", bar: "bg-green-500" };
  if (score >= 0.5)  return { bg: "bg-yellow-500/10 border-yellow-500/30", text: "text-yellow-400", bar: "bg-yellow-500" };
  if (score >= 0.25) return { bg: "bg-orange-500/10 border-orange-500/30", text: "text-orange-400", bar: "bg-orange-500" };
  return { bg: "bg-red-500/10 border-red-500/30", text: "text-red-400", bar: "bg-red-500" };
}

interface Props {
  results: StationResult[];
  isSimMode: boolean;
}

export default function StationCards({ results, isSimMode }: Props) {
  if (!results.length) return null;

  // Sort by SNR (sim mode) or score (simple mode)
  const sorted = [...results].sort((a, b) =>
    isSimMode
      ? (b.snr_mean ?? 0) - (a.snr_mean ?? 0)
      : (b.score_now ?? 0) - (a.score_now ?? 0)
  );
  const best = sorted[0];

  return (
    <div className="space-y-3">
      {isSimMode ? (
        /* Sim mode — show ITU-R results */
        sorted.map((s, i) => {
          const snr = s.snr_mean ?? 0;
          const c = snrColor(snr);
          const availability = s.outage_fraction != null
            ? ((1 - s.outage_fraction) * 100).toFixed(1) + "%"
            : "--";
          return (
            <div key={s.name} className={`rounded-xl border p-4 ${c.bg} ${s.name === best.name ? "ring-1 ring-white/20" : ""}`}>
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full inline-block" style={{ background: COLORS[i % COLORS.length] }} />
                  <span className="font-semibold text-white text-sm">{s.name}</span>
                  {s.name === best.name && (
                    <span className="text-xs bg-white/10 text-white/70 px-2 py-0.5 rounded-full">Best</span>
                  )}
                </div>
                <span className={`text-base font-bold ${c.text}`}>{snr.toFixed(1)} dB</span>
              </div>
              <div className="h-1.5 bg-white/10 rounded-full mb-3">
                <div className={`h-full rounded-full ${c.bar}`} style={{ width: `${Math.min(snr / 30 * 100, 100)}%` }} />
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs text-slate-400">
                <div>
                  <div className="text-slate-500">Availability</div>
                  <div className="text-white font-medium">{availability}</div>
                </div>
                <div>
                  <div className="text-slate-500">SNR p10</div>
                  <div className="text-white font-medium">{s.snr_p10?.toFixed(1) ?? "--"} dB</div>
                </div>
                <div>
                  <div className="text-slate-500">Rain atten.</div>
                  <div className="text-white font-medium">{s.avg_rain_db?.toFixed(2) ?? "--"} dB</div>
                </div>
              </div>
              {s.handoff_events && s.handoff_events.length > 0 && (
                <div className="mt-2 text-xs text-indigo-400">
                  {s.handoff_events.length} handoff{s.handoff_events.length > 1 ? "s" : ""} detected
                </div>
              )}
            </div>
          );
        })
      ) : (
        /* Simple mode — physics scoring */
        <>
          {(sorted[0].score_drop ?? 0) > 0.25 && (
            <div className="flex items-center gap-2 bg-amber-500/10 border border-amber-500/30 rounded-lg px-4 py-2 text-amber-300 text-sm font-medium">
              <span>⚠</span> Proactive handoff recommended
            </div>
          )}
          {sorted.map((s) => {
            const score = s.score_now ?? 0;
            const c = scoreColor(score);
            return (
              <div key={s.name} className={`rounded-xl border p-4 ${c.bg} ${s.name === best.name ? "ring-1 ring-white/20" : ""}`}>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <span className="font-semibold text-white text-sm">{s.name}</span>
                    {s.name === best.name && <span className="ml-2 text-xs bg-white/10 text-white/70 px-2 py-0.5 rounded-full">Best</span>}
                  </div>
                  <span className={`text-lg font-bold ${c.text}`}>{(score * 100).toFixed(0)}%</span>
                </div>
                <div className="h-1.5 bg-white/10 rounded-full mb-3">
                  <div className={`h-full rounded-full ${c.bar}`} style={{ width: `${score * 100}%` }} />
                </div>
                <div className="grid grid-cols-3 gap-2 text-xs text-slate-400">
                  <div><div className="text-slate-500">Elevation</div><div className="text-white font-medium">{s.elevation_deg?.toFixed(1)}°</div></div>
                  <div><div className="text-slate-500">Distance</div><div className="text-white font-medium">{s.distance_km?.toFixed(0)} km</div></div>
                  <div><div className="text-slate-500">Rx Power</div><div className="text-white font-medium">{s.rx_power_dbm?.toFixed(1)} dBm</div></div>
                </div>
              </div>
            );
          })}
        </>
      )}
    </div>
  );
}
