import { useState, useCallback } from "react";

export type Constellation = "Starlink" | "OneWeb" | "Iridium";

// Satyansh's API types
export interface HandoffEvent {
  time_step: number;
  old_sat: string;
  new_sat: string;
  reason: string;
  metric_delta: number;
}

export interface StationResult {
  // Shared fields (both APIs)
  name: string;
  lat?: number;
  lon?: number;

  // Simple API fields
  score_now?: number;
  score_future?: number;
  score_drop?: number;
  elevation_deg?: number;
  distance_km?: number;
  rx_power_dbm?: number;
  visible?: boolean;

  // Satyansh's API fields
  snr_mean?: number;
  snr_min?: number;
  snr_std?: number;
  snr_p10?: number;
  snr_series?: number[];
  rain_db_series?: number[];
  pkt_loss_series?: number[];
  elevation_series?: number[];
  outage_fraction?: number;
  avg_rain_db?: number;
  avg_pkt_loss?: number;
  rain_fraction?: number;
  handoff_events?: HandoffEvent[];
  elevation?: number;
  slant_km?: number;
  doppler_hz?: number;
}

export interface SimulationResult {
  results: StationResult[];
}

export interface SummaryResult {
  availability: number;
  handoffs: number;
}

export interface TleResult {
  sat_id: string;
  name: string;
  lat: number;
  lon: number;
  alt_km: number;
  simulated: boolean;
  source: string;
}

// Ground station coords (for map display, not sent to Satyansh's API)
export const STATION_COORDS: Record<string, [number, number]> = {
  Delhi:     [28.6139, 77.2090],
  Tokyo:     [35.6762, 139.6503],
  Berlin:    [52.5200, 13.4050],
  "Sao Paulo": [-23.5505, -46.6333],
};

const SIMPLE_API = import.meta.env.VITE_API_URL ?? "";
const SIM_API    = import.meta.env.VITE_SIM_API_URL ?? "";


export function useSatellite() {
  const [satLat, setSatLat]         = useState(10.0);
  const [satLon, setSatLon]         = useState(75.0);
  const [satAlt, setSatAlt]         = useState(550.0);
  const [constellation, setConstellation] = useState<Constellation>("Starlink");
  const [durationMin, setDurationMin]     = useState(60);
  const [simResult, setSimResult]   = useState<SimulationResult | null>(null);
  const [summaries, setSummaries]   = useState<Record<string, SummaryResult>>({});
  const [tleData, setTleData]       = useState<TleResult | null>(null);
  const [loading, setLoading]       = useState(false);
  const [tleLoading, setTleLoading] = useState(false);
  const [error, setError]           = useState<string | null>(null);
  const [mode, setMode]             = useState<"sim" | "simple">(SIM_API ? "sim" : "simple");

  // Full simulation — Satyansh's API
  const runSimulation = useCallback(async () => {
    if (!SIM_API) { setError("Simulation backend not configured"); return; }
    setLoading(true);
    setError(null);
    try {
      const body = {
        constellation,
        n_steps: durationMin * 60,
        dt_s: 1.0,
        handoff_policy: "highest_elevation",
        hysteresis: 0.5,
        min_dwell_steps: 10,
      };
      const res = await fetch(`${SIM_API}/simulate/full`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`Simulation API ${res.status}`);
      const data: SimulationResult = await res.json();
      // Attach coords to results
      data.results.forEach(r => {
        const coords = STATION_COORDS[r.name];
        if (coords) { r.lat = coords[0]; r.lon = coords[1]; }
      });
      setSimResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Simulation failed");
    } finally {
      setLoading(false);
    }
  }, [constellation, durationMin]);

  // Quick summary per station
  const fetchSummary = useCallback(async (station: string) => {
    if (!SIM_API) return;
    try {
      const res = await fetch(`${SIM_API}/simulate/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ station, constellation, duration: durationMin }),
      });
      if (!res.ok) return;
      const data: SummaryResult = await res.json();
      setSummaries(prev => ({ ...prev, [station]: data }));
    } catch { /* silent */ }
  }, [constellation, durationMin]);

  // Simple physics scoring (own Vercel API — always available)
  const runSimple = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(
        `${SIMPLE_API}/api/predict?sat_lat=${satLat}&sat_lon=${satLon}&sat_alt=${satAlt}&orbit_type=LEO`
      );
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data = await res.json();
      // Convert simple API response to StationResult shape
      const results: StationResult[] = data.stations.map((s: any) => ({
        name: s.station,
        lat: s.lat,
        lon: s.lon,
        score_now: s.score_now,
        score_future: s.score_future,
        score_drop: s.score_drop,
        elevation_deg: s.elevation_deg,
        distance_km: s.distance_km,
        rx_power_dbm: s.rx_power_dbm,
        visible: s.visible,
      }));
      setSimResult({ results });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [satLat, satLon, satAlt]);

  const fetchLiveTle = useCallback(async (satId = "ISS") => {
    setTleLoading(true);
    try {
      const res = await fetch(`${SIMPLE_API}/api/tle?sat=${satId}`);
      if (!res.ok) throw new Error(`TLE API ${res.status}`);
      const data: TleResult = await res.json();
      setTleData(data);
      setSatLat(data.lat);
      setSatLon(data.lon);
      setSatAlt(data.alt_km);
      return data;
    } catch { return null; }
    finally { setTleLoading(false); }
  }, []);

  return {
    satLat, setSatLat, satLon, setSatLon, satAlt, setSatAlt,
    constellation, setConstellation,
    durationMin, setDurationMin,
    simResult, summaries, tleData,
    loading, tleLoading, error,
    mode, setMode,
    runSimulation, runSimple, fetchSummary, fetchLiveTle,
    hasSimApi: !!SIM_API,
  };
}
