import { useState, useCallback } from "react";

export type OrbitType = "LEO" | "MEO" | "GEO";

export interface StationResult {
  station: string;
  lat: number;
  lon: number;
  score_now: number;
  score_future: number;
  score_drop: number;
  elevation_deg: number;
  distance_km: number;
  rx_power_dbm: number;
  visible: boolean;
}

export interface PredictResult {
  stations: StationResult[];
  best_station: string;
  handoff_needed: boolean;
  sat_lat: number;
  sat_lon: number;
  sat_alt_km: number;
  orbit_type: OrbitType;
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

const API = import.meta.env.VITE_API_URL ?? "";

export function useSatellite() {
  const [satLat, setSatLat]         = useState(10.0);
  const [satLon, setSatLon]         = useState(75.0);
  const [satAlt, setSatAlt]         = useState(550.0);
  const [orbitType, setOrbitType]   = useState<OrbitType>("LEO");
  const [result, setResult]         = useState<PredictResult | null>(null);
  const [tleData, setTleData]       = useState<TleResult | null>(null);
  const [loading, setLoading]       = useState(false);
  const [tleLoading, setTleLoading] = useState(false);
  const [error, setError]           = useState<string | null>(null);

  const predict = useCallback(async (lat?: number, lon?: number, alt?: number, orbit?: OrbitType) => {
    setLoading(true);
    setError(null);
    const l = lat ?? satLat;
    const o = lon ?? satLon;
    const a = alt ?? satAlt;
    const t = orbit ?? orbitType;
    try {
      const res = await fetch(
        `${API}/api/predict?sat_lat=${l}&sat_lon=${o}&sat_alt=${a}&orbit_type=${t}`
      );
      if (!res.ok) throw new Error(`API ${res.status}`);
      const data: PredictResult = await res.json();
      setResult(data);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }, [satLat, satLon, satAlt, orbitType]);

  const fetchLiveTle = useCallback(async (satId = "ISS") => {
    setTleLoading(true);
    try {
      const res = await fetch(`${API}/api/tle?sat=${satId}`);
      if (!res.ok) throw new Error(`TLE API ${res.status}`);
      const data: TleResult = await res.json();
      setTleData(data);
      setSatLat(data.lat);
      setSatLon(data.lon);
      setSatAlt(data.alt_km);
      return data;
    } catch {
      return null;
    } finally {
      setTleLoading(false);
    }
  }, []);

  return {
    satLat, setSatLat,
    satLon, setSatLon,
    satAlt, setSatAlt,
    orbitType, setOrbitType,
    result,
    tleData,
    loading,
    tleLoading,
    error,
    predict,
    fetchLiveTle,
  };
}
