# Leo Meo

**AI-Powered Satellite Data Intelligence Platform**

Leo Meo automates satellite data scraping, processing, and analysis using Machine Learning and a Retrieval-Augmented Generation (RAG) pipeline. It is designed to extract satellite datasets (e.g., NASA data), process them efficiently, and provide intelligent insights through a scalable backend architecture.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [How It Works](#how-it-works)
- [Impact](#impact)
- [Team](#team)
- [Roadmap](#roadmap)
- [License](#license)

---

## Features

- Automated satellite data scraping from public sources
- NASA and public dataset integration
- ML-based data processing and prediction
- RAG pipeline for intelligent, context-aware retrieval
- FastAPI async backend
- Lightweight SQLite database for MVP
- Clean frontend integration

---

## Tech Stack

### Backend
| Tool | Purpose |
|------|---------|
| FastAPI | High-performance async API framework |
| Python | Core language |
| SQLite | MVP database |
| Uvicorn | ASGI server |

### Machine Learning
| Tool | Purpose |
|------|---------|
| Scikit-learn | Model training and inference |
| Pandas | Data manipulation |
| NumPy | Numerical computing |

### Data Scraping & Automation
| Tool | Purpose |
|------|---------|
| BeautifulSoup | HTML parsing |
| Selenium | JS-rendered page automation |
| Requests | HTTP data fetching |

### RAG Pipeline
- Embedding-based retrieval
- Vector similarity search
- Context-aware AI response generation

### Frontend
- HTML, CSS, JavaScript

---

## Project Structure

```
Leo-Meo/
│
├── backend/
│   ├── main.py
│   ├── api/
│   ├── models/
│   └── database/
│
├── ml_api/
│   ├── training.py
│   ├── inference.py
│   └── rag_pipeline.py
│
├── scraper/
│   ├── nasa_scraper.py
│   └── automation.py
│
├── frontend/
├── requirements.txt
└── README.md
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/clone891/Leo-Meo.git
cd Leo-Meo
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Mac / Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Backend Server

```bash
uvicorn main:app --reload
```

The server will start at:

```
http://127.0.0.1:8000
```

Swagger API docs available at:

```
http://127.0.0.1:8000/docs
```

---

## How It Works

1. **Scrape** — Automated extraction of satellite datasets from NASA and public sources.
2. **Clean & Preprocess** — Raw data is normalized and structured for downstream processing.
3. **ML Inference** — Processed data is passed through trained models to generate predictions.
4. **Embed & Index** — Outputs are embedded into vectors and indexed for fast retrieval.
5. **RAG Response** — Retrieval-augmented generation delivers contextual, AI-driven insights on demand.

---

## Impact

Leo Meo simplifies satellite data accessibility by:

- Automating complex data extraction workflows
- Reducing manual data processing time
- Enabling intelligent querying over scientific datasets
- Making space-data analysis more accessible to researchers and developers

---

## Team

| Name | Role |
|------|------|
| Vaibhav | Project Lead, ML Developer, Backend & Frontend |
| Suraj Samanta | Backend & Frontend |
| Satyansh Gaur | Machine Learning Engineer |
| Saksham Arora | ML Developer |
| Movendu Singh | ML Developer |

---

## Roadmap

- [ ] Cloud deployment (AWS / GCP)
- [ ] Docker containerization
- [ ] PostgreSQL production database
- [ ] Real-time satellite API integration
- [ ] Advanced ML forecasting models

---

## License

This project is intended for educational and research purposes.

---

*Built with vision, engineered with precision.*
