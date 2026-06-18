# Leo-Meo — Satellite Handover Predictor

Real-time satellite visibility prediction across Indian ground stations, with proactive handoff recommendations.

**Live:** https://leo-meo.vercel.app

---

## What it does

Given a satellite's position (LEO/MEO/GEO), Leo-Meo scores each Indian ground station for visibility using physics-based features and a trained RandomForest classifier. It tells you which station has the best link right now and whether a proactive handoff is needed in the next 10 seconds.

---

## Tech stack

| Layer | What |
|-------|------|
| Data source | Celestrak TLE catalog (free, no API key) |
| Orbit propagation | SGP4 via stdlib math only |
| ML model | scikit-learn RandomForestClassifier (300 trees, max_depth=12) |
| Training data | Physics-simulated dataset: haversine, FSPL, atmospheric loss, Doppler |
| Backend | FastAPI serverless on Vercel |
| Frontend | React + TypeScript + Vite + Tailwind + react-leaflet |
| Deployment | Vercel |

---

## Ground stations

Bangalore, Delhi, Mumbai, Chennai, Kolkata.

---

## Physics features

- Elevation angle (geometry)
- Free space path loss (Friis transmission)
- Atmospheric loss (elevation-dependent)
- Received power in dBm
- Doppler shift (Ku-band, 12 GHz)
- sin/cos encoding of elevation angle

---

## Handoff logic

For each station, the model scores visibility now (`score_now`) and 10 seconds ahead (`score_future`). If `score_drop > 0.25` for the best station, a proactive handoff is flagged before the link degrades.

---

## Local dev

```bash
git clone https://github.com/saksham10arora-dotcom/leo-meo
cd leo-meo
npm install
npm run dev
```

---

## Team

Built at hackathon by Vaibhav, Suraj, Satyansh, Saksham, Movendu.
Production rewrite by Saksham Arora.
