import { useState } from "react";
import { useSatellite, type Constellation, STATION_COORDS } from "../hooks/useSatellite";
import SatMap from "../components/SatMap";
import StationCards from "../components/StationCards";
import SimCharts from "../components/SimCharts";

const CONSTELLATIONS: Constellation[] = ["Starlink", "OneWeb", "Iridium"];
const DURATIONS = [
  { label: "30 min", value: 30 },
  { label: "1 h",   value: 60 },
  { label: "6 h",   value: 360 },
  { label: "24 h",  value: 1440 },
];

export default function Dashboard() {
  const {
    satLat, setSatLat, satLon, setSatLon, satAlt,
    constellation, setConstellation,
    durationMin, setDurationMin,
    simResult, tleData,
    loading, tleLoading, error,
    mode, setMode,
    runSimulation, runSimple, fetchLiveTle,
    hasSimApi,
  } = useSatellite();

  const [satIdInput, setSatIdInput] = useState("ISS");
  const [activeTab, setActiveTab]   = useState<"cards" | "charts">("cards");

  const handleFetch = async () => {
    const data = await fetchLiveTle(satIdInput);
    if (data && mode === "simple") runSimple();
  };

  const handleRun = () => {
    if (mode === "sim") runSimulation();
    else runSimple();
  };

  // Map stations: use simResult if available, otherwise empty
  const mapStations = simResult?.results.map(r => {
    const coords = (r.lat != null && r.lon != null)
      ? [r.lat, r.lon] as [number, number]
      : STATION_COORDS[r.name] ?? [0, 0] as [number, number];
    const score = r.snr_mean != null
      ? Math.min(r.snr_mean / 25, 1)
      : (r.score_now ?? 0);
    return {
      name: r.name,
      lat: coords[0],
      lon: coords[1],
      score_now: score,
    };
  }) ?? [];

  const bestStation = simResult
    ? [...simResult.results].sort((a, b) =>
        mode === "sim"
          ? (b.snr_mean ?? 0) - (a.snr_mean ?? 0)
          : (b.score_now ?? 0) - (a.score_now ?? 0)
      )[0]?.name ?? null
    : null;

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🛰</span>
          <div>
            <h1 className="font-bold text-lg leading-none">Leo-Meo</h1>
            <p className="text-xs text-slate-400 mt-0.5">Satellite Link Optimizer</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          {hasSimApi && (
            <div className="flex bg-slate-800 rounded-lg p-1 text-xs">
              <button
                onClick={() => setMode("sim")}
                className={`px-3 py-1.5 rounded-md transition-colors font-medium ${mode === "sim" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                ITU-R Sim
              </button>
              <button
                onClick={() => setMode("simple")}
                className={`px-3 py-1.5 rounded-md transition-colors font-medium ${mode === "simple" ? "bg-indigo-600 text-white" : "text-slate-400 hover:text-white"}`}
              >
                Quick
              </button>
            </div>
          )}
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse" />
            {mode === "sim" ? "Satyansh's physics engine + ITU-R models" : "Celestrak TLE + physics scoring"}
          </div>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 border-r border-white/10 flex flex-col overflow-y-auto">
          <div className="p-5 space-y-5 flex-1">

            {/* Live TLE (simple mode only) */}
            {mode === "simple" && (
              <section>
                <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                  Live Satellite Position
                </h2>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={satIdInput}
                    onChange={(e) => setSatIdInput(e.target.value.toUpperCase())}
                    placeholder="ISS / HST / TERRA"
                    className="flex-1 bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                  />
                  <button
                    onClick={handleFetch}
                    disabled={tleLoading}
                    className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-3 py-2 rounded-lg text-sm font-medium transition-colors"
                  >
                    {tleLoading ? "…" : "Fetch"}
                  </button>
                </div>
                {tleData && (
                  <div className="mt-2 text-xs text-slate-400 bg-slate-800/50 rounded-lg px-3 py-2">
                    {tleData.name} — {tleData.lat.toFixed(2)}°, {tleData.lon.toFixed(2)}°, {tleData.alt_km.toFixed(0)} km
                    {tleData.simulated && <span className="ml-1 text-yellow-400">(simulated)</span>}
                  </div>
                )}
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Latitude</label>
                    <input type="number" value={satLat} onChange={e => setSatLat(parseFloat(e.target.value))}
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Longitude</label>
                    <input type="number" value={satLon} onChange={e => setSatLon(parseFloat(e.target.value))}
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500" />
                  </div>
                </div>
              </section>
            )}

            {/* Simulation controls (sim mode) */}
            {mode === "sim" && (
              <>
                <section>
                  <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                    Constellation
                  </h2>
                  <div className="flex gap-2">
                    {CONSTELLATIONS.map(c => (
                      <button key={c} onClick={() => setConstellation(c)}
                        className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${constellation === c ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}>
                        {c}
                      </button>
                    ))}
                  </div>
                </section>

                <section>
                  <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                    Simulation Duration
                  </h2>
                  <div className="grid grid-cols-4 gap-1">
                    {DURATIONS.map(d => (
                      <button key={d.value} onClick={() => setDurationMin(d.value)}
                        className={`py-2 rounded-lg text-xs font-medium transition-colors ${durationMin === d.value ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"}`}>
                        {d.label}
                      </button>
                    ))}
                  </div>
                </section>
              </>
            )}

            {/* Run button */}
            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-3 rounded-xl text-sm font-semibold transition-colors"
            >
              {loading
                ? (mode === "sim" ? "Running ITU-R simulation…" : "Running…")
                : (mode === "sim" ? `Run ${durationMin}min Simulation` : "Predict Best Station")
              }
            </button>

            {error && (
              <div className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">{error}</div>
            )}

            {/* Results */}
            {simResult && (
              <>
                {mode === "sim" && (
                  <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
                    <button onClick={() => setActiveTab("cards")}
                      className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === "cards" ? "bg-slate-700 text-white" : "text-slate-400 hover:text-white"}`}>
                      Summary
                    </button>
                    <button onClick={() => setActiveTab("charts")}
                      className={`flex-1 py-1.5 rounded-md text-xs font-medium transition-colors ${activeTab === "charts" ? "bg-slate-700 text-white" : "text-slate-400 hover:text-white"}`}>
                      Time Series
                    </button>
                  </div>
                )}

                {activeTab === "cards" || mode === "simple" ? (
                  <StationCards results={simResult.results} isSimMode={mode === "sim"} />
                ) : (
                  <SimCharts results={simResult.results} durationMin={durationMin} />
                )}
              </>
            )}
          </div>
        </aside>

        {/* Map */}
        <main className="flex-1 p-4">
          <SatMap
            satLat={satLat}
            satLon={satLon}
            satAlt={satAlt}
            stations={mapStations}
            bestStation={bestStation}
          />
        </main>
      </div>
    </div>
  );
}
