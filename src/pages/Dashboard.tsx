import { useState } from "react";
import { useSatellite, type OrbitType } from "../hooks/useSatellite";
import SatMap from "../components/SatMap";
import StationCards from "../components/StationCards";

const ORBIT_ALTS: Record<OrbitType, number> = { LEO: 550, MEO: 12000, GEO: 35786 };

export default function Dashboard() {
  const {
    satLat, setSatLat,
    satLon, setSatLon,
    satAlt, setSatAlt,
    orbitType, setOrbitType,
    result, tleData, loading, tleLoading, error,
    predict, fetchLiveTle,
  } = useSatellite();

  const [satIdInput, setSatIdInput] = useState("ISS");

  const handleOrbitChange = (o: OrbitType) => {
    setOrbitType(o);
    setSatAlt(ORBIT_ALTS[o]);
  };

  const handleLive = async () => {
    const data = await fetchLiveTle(satIdInput);
    if (data) {
      await predict(data.lat, data.lon, data.alt_km, "LEO");
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col">
      {/* Header */}
      <header className="border-b border-white/10 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🛰</span>
          <div>
            <h1 className="font-bold text-lg leading-none">Leo-Meo</h1>
            <p className="text-xs text-slate-400 mt-0.5">Satellite Handover Predictor</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-400">
          <span className="w-2 h-2 rounded-full bg-green-500 inline-block animate-pulse" />
          Powered by Celestrak TLE + scikit-learn RF
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <aside className="w-80 border-r border-white/10 flex flex-col overflow-y-auto">
          <div className="p-5 space-y-5 flex-1">

            {/* Live TLE fetch */}
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
                  onClick={handleLive}
                  disabled={tleLoading}
                  className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 px-3 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap"
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
            </section>

            {/* Manual input */}
            <section>
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Manual Position
              </h2>
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Latitude</label>
                    <input
                      type="number"
                      value={satLat}
                      onChange={(e) => setSatLat(parseFloat(e.target.value))}
                      step="0.1"
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div>
                    <label className="text-xs text-slate-500 mb-1 block">Longitude</label>
                    <input
                      type="number"
                      value={satLon}
                      onChange={(e) => setSatLon(parseFloat(e.target.value))}
                      step="0.1"
                      className="w-full bg-slate-800 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-xs text-slate-500 mb-1 block">Altitude (km): {satAlt}</label>
                  <input
                    type="range"
                    min={300} max={36000}
                    value={satAlt}
                    onChange={(e) => setSatAlt(parseFloat(e.target.value))}
                    className="w-full accent-indigo-500"
                  />
                </div>
              </div>
            </section>

            {/* Orbit type */}
            <section>
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Orbit Type
              </h2>
              <div className="flex gap-2">
                {(["LEO", "MEO", "GEO"] as OrbitType[]).map((o) => (
                  <button
                    key={o}
                    onClick={() => handleOrbitChange(o)}
                    className={`flex-1 py-2 rounded-lg text-sm font-medium transition-colors ${
                      orbitType === o
                        ? "bg-indigo-600 text-white"
                        : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                  >
                    {o}
                  </button>
                ))}
              </div>
            </section>

            {/* Predict button */}
            <button
              onClick={() => predict()}
              disabled={loading}
              className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 py-3 rounded-xl text-sm font-semibold transition-colors"
            >
              {loading ? "Running model…" : "Predict Best Station"}
            </button>

            {error && (
              <div className="text-red-400 text-xs bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2">
                {error}
              </div>
            )}

            {/* Results */}
            {result && (
              <StationCards
                stations={result.stations}
                bestStation={result.best_station}
                handoffNeeded={result.handoff_needed}
              />
            )}
          </div>
        </aside>

        {/* Map */}
        <main className="flex-1 p-4">
          <SatMap
            satLat={satLat}
            satLon={satLon}
            satAlt={satAlt}
            stations={result?.stations ?? []}
            bestStation={result?.best_station ?? null}
          />
        </main>
      </div>
    </div>
  );
}
