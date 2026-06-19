import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from "recharts";
import type { StationResult } from "../hooks/useSatellite";

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ef4444"];

interface Props {
  results: StationResult[];
  durationMin: number;
}

function buildTimeSeries(results: StationResult[], key: keyof StationResult) {
  const len = (results[0]?.[key] as number[] | undefined)?.length ?? 0;
  return Array.from({ length: len }, (_, i) => {
    const point: Record<string, number> = { t: i };
    results.forEach(r => {
      const series = r[key] as number[] | undefined;
      if (series) point[r.name] = parseFloat(series[i].toFixed(2));
    });
    return point;
  });
}

export default function SimCharts({ results, durationMin }: Props) {
  if (!results.length || !results[0].snr_series?.length) return null;

  const snrData  = buildTimeSeries(results, "snr_series");
  const rainData = buildTimeSeries(results, "rain_db_series");
  const pktData  = buildTimeSeries(results, "pkt_loss_series");

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const tickFormatter = (v: any) => {
    const n = typeof v === "number" ? v : parseInt(v, 10);
    const sec = (n / snrData.length) * durationMin * 60;
    return sec < 60 ? `${Math.round(sec)}s` : `${Math.round(sec/60)}m`;
  };

  return (
    <div className="space-y-6">
      {/* SNR */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          SNR over time (dB)
        </h3>
        <ResponsiveContainer width="100%" height={180}>
          <LineChart data={snrData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="t" tickFormatter={tickFormatter} tick={{ fill: "#64748b", fontSize: 10 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit=" dB" width={48} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
              labelFormatter={tickFormatter}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
            {results.map((r, i) => (
              <Line key={r.name} type="monotone" dataKey={r.name}
                stroke={COLORS[i % COLORS.length]} dot={false} strokeWidth={1.5} />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Rain attenuation */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Rain attenuation (dB)
        </h3>
        <ResponsiveContainer width="100%" height={140}>
          <AreaChart data={rainData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="t" tickFormatter={tickFormatter} tick={{ fill: "#64748b", fontSize: 10 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit=" dB" width={48} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
              labelFormatter={tickFormatter}
            />
            <Legend wrapperStyle={{ fontSize: 11, color: "#94a3b8" }} />
            {results.map((r, i) => (
              <Area key={r.name} type="monotone" dataKey={r.name}
                stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]}
                fillOpacity={0.1} dot={false} strokeWidth={1.5} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Packet loss */}
      <div>
        <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
          Packet loss (%)
        </h3>
        <ResponsiveContainer width="100%" height={120}>
          <AreaChart data={pktData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis dataKey="t" tickFormatter={tickFormatter} tick={{ fill: "#64748b", fontSize: 10 }} />
            <YAxis tick={{ fill: "#64748b", fontSize: 10 }} unit="%" width={48} />
            <Tooltip
              contentStyle={{ background: "#1e293b", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8 }}
              labelFormatter={tickFormatter}
            />
            {results.map((r, i) => (
              <Area key={r.name} type="monotone" dataKey={r.name}
                stroke={COLORS[i % COLORS.length]} fill={COLORS[i % COLORS.length]}
                fillOpacity={0.15} dot={false} strokeWidth={1} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
