<div align="center">
  <br/>
  <h1>📈 AI Investment Dashboard</h1>
  <p>
    <strong>Production-grade full-stack investment research platform with AI-powered analytics,<br/>
    real-time market data, portfolio tracking, and risk management.</strong>
  </p>
  <br/>
  <p>
    <img src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white" alt="Python"/>
    <img src="https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white" alt="FastAPI"/>
    <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white" alt="React"/>
    <img src="https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript&logoColor=white" alt="TypeScript"/>
    <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL"/>
    <img src="https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white" alt="Redis"/>
    <img src="https://img.shields.io/badge/Vite-5-646CFF?logo=vite&logoColor=white" alt="Vite"/>
    <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker"/>
    <img src="https://img.shields.io/badge/lightweight--charts-5-FFB300?logo=tradingview&logoColor=white" alt="TradingView Charts"/>
  </p>
  <br/>
</div>

---

## 🚀 Overview

A comprehensive investment analysis platform that combines **real-time market data**, **technical analysis**, **AI-powered fundamental research**, and **portfolio risk management** into a single, polished web application. Built with the same architectural patterns used at quantitative hedge funds and fintech companies.

Designed to demonstrate production-quality full-stack engineering skills across the entire modern web stack — from async Python services and PostgreSQL optimization to React component architecture and real-time data streaming.

---

## ✨ Features

### 📊 Portfolio Management
- Multi-portfolio tracking with live P&L calculations
- Holdings management with weighted average cost basis
- Transaction journaling (buys/sells with auto-reconciliation)
- Performance analytics: return, volatility, Sharpe ratio, max drawdown
- Day P&L tracking with real-time price updates
- Asset allocation visualization

### 📈 Technical Analysis (TradingView-powered)
- **Candlestick charts** with volume overlay via TradingView's `lightweight-charts`
- **20+ technical indicators**: SMA, EMA, RSI, MACD, Bollinger Bands
- Overlapping indicator layers with customizable periods
- Time range selection (1M/3M/6M/1Y)
- Automated bullish/bearish signal detection
- Crosshair, zoom, and pan interactions

### 🤖 AI Stock Analysis
- **OpenAI-powered** fundamental analysis when API key is configured
- **Rule-based fallback** analysis using yfinance data (no API key required)
- Scored evaluation across three dimensions:
  - **Valuation**: P/E ratios, market comparison, growth metrics
  - **Trend**: Moving averages, RSI momentum, golden/death cross detection
  - **Risk**: Beta, debt-to-equity, volatility assessment
- Confidence scoring with visual gauge
- Natural language chat interface for stock Q&A

### 🔬 Options Flow Scanner
- Real-time unusual options activity detection
- Anomaly scoring based on volume/OI ratio and premium
- Put/call ratio analysis
- Premium aggregation and top unusual symbols
- Automated scanning every 5 minutes

### 📅 Earnings Calendar
- Upcoming earnings dates with consensus estimates
- Historical earnings performance with surprise analysis
- Whisper number tracking
- Price reaction analysis around earnings dates

### 👁️ Watchlists & Alerts
- Multiple watchlists with live price tracking
- Price threshold alerts (above/below)
- Volume surge detection
- Technical crossover alerts
- Automated alert evaluation every 60 seconds

### 🌍 Macro Dashboard
- Major index tracking (SPY, QQQ, DIA, IWM)
- Sector performance heatmap (11 sectors via XLF/XLK/XLE/...)
- Economic indicators dashboard

### 🛡️ Risk Analytics
- **Value at Risk (VaR)**: Historical simulation at configurable confidence levels
- **Conditional VaR (CVaR)**: Expected shortfall analysis
- **Beta**: Portfolio volatility vs. benchmark (SPY)
- **Correlation matrix**: Pairwise holding correlations
- **Drawdown analysis**: Maximum drawdown with recovery tracking
- **Stress testing**: Multi-scenario impact simulation

---

## 📸 Screenshots

> *Screenshots coming soon*

| Dashboard | Technical Analysis | Portfolio Detail |
|:---:|:---:|:---:|
| *Placeholder* | *Placeholder* | *Placeholder* |

| AI Analysis | Watchlists | Risk Analytics |
|:---:|:---:|:---:|
| *Placeholder* | *Placeholder* | *Placeholder* |

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     React SPA (Vite)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Trading │ │   React  │ │  Zustand │ │  React Query  │  │
│  │   View   │ │  Router  │ │   Store  │ │  (TanStack)   │  │
│  │  Charts  │ │          │ │  (WS/    │ │  (Server      │  │
│  │          │ │          │ │  Auth)   │ │   State)      │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────┬───────┘  │
│                                                  │          │
│                                      Axios (JWT Interceptor) │
└──────────────────────────────────────┬──────────┬───────────┘
                                       │ HTTP     │ WebSocket
                                       ▼          ▼
┌──────────────────────────────────────────────────────────────┐
│                 FastAPI (Uvicorn + APScheduler)               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────────┐  │
│  │  Routes  │ │ Services │ │ External │ │  Background   │  │
│  │  (auth,  │ │(portfolio│ │ (yfinance│ │   Tasks       │  │
│  │portfolios│ │technical │ │ polygon, │ │(price poller, │  │
│  │analysis, │ │   risk,  │ │  openai) │ │ options scan, │  │
│  │   ...)   │ │   ...)   │ │          │ │ alert checker)│  │
│  └──────────┘ └──────────┘ └──────────┘ └───────┬───────┘  │
│                                                  │          │
│     SQLAlchemy (async)          redis-py         │          │
└──────────────────┬──────────────────┬────────────┘          │
                   │                  │                       │
                   ▼                  ▼                       │
┌──────────────────────┐ ┌──────────────────────┐            │
│    PostgreSQL 16     │ │      Redis 7          │◄──────────┘
│   (AsyncPG driver)   │ │  (Cache + Pub/Sub)    │  (WebSocket
│                      │ │                       │   broadcast)
│  • User data         │ │  • API response cache │
│  • Portfolios        │ │  • Rate limit counters│
│  • Holdings          │ │  • Price pub/sub      │
│  • Watchlists        │ │  • Session data       │
│  • Options flow      │ │                       │
│  • Earnings calendar │ │                       │
└──────────────────────┘ └──────────────────────┘
```

### Data Flow

```
Real-Time Prices:  yfinance → APScheduler (30s) → Redis → WebSocket → React
Portfolio P&L:     Portfolio → yfinance quote → compute P&L → React Query
Technical Analysis: Symbol → yfinance history → numpy compute → cache → React
AI Analysis:       Symbol → yfinance fundamentals → OpenAI → cache → React
Risk Metrics:      Holdings → price history → numpy/scipy → React
```

---

## 🛠️ Tech Stack

### Frontend
| Technology | Purpose |
|---|---|
| **React 18** | Component library |
| **TypeScript 5.3** | Type safety |
| **Vite 5** | Build tooling & HMR |
| **React Router 6** | Client-side routing |
| **TanStack React Query** | Server state & caching |
| **Zustand** | Real-time WebSocket state |
| **TradingView lightweight-charts 5** | Professional financial charts |
| **Tailwind CSS 3** | Utility-first styling |
| **Axios** | HTTP client with JWT interceptor |

### Backend
| Technology | Purpose |
|---|---|
| **Python 3.12** | Runtime |
| **FastAPI** | Async web framework |
| **SQLAlchemy 2.0** | Async ORM |
| **PostgreSQL 16** | Primary database |
| **Redis 7** | Caching, rate limiting, pub/sub |
| **APScheduler** | Background task orchestration |
| **yfinance** | Free market data (primary) |
| **Polygon.io** | Premium market data (fallback) |
| **OpenAI API** | AI-powered stock analysis |
| **NumPy / Pandas** | Technical indicators & risk computation |
| **python-jose** | JWT authentication |
| **SlowAPI** | Rate limiting |
| **Alembic** | Database migrations |

### Infrastructure
| Technology | Purpose |
|---|---|
| **Docker Compose** | Local development with 4 services |
| **Nginx** | (Recommended for production reverse proxy) |

---

## 📋 Prerequisites

- **Docker Desktop** 27+ and **Docker Compose** v2+ (recommended)
- OR Python 3.12+, Node.js 18+, PostgreSQL 16 (local development)
- API keys (optional):
  - `OPENAI_API_KEY` — AI analysis features
  - `POLYGON_API_KEY` — Premium market data fallback

---

## 🚀 Quick Start (Docker)

```bash
# 1. Clone the repository
git clone <repository-url>
cd ai-investment-dashboard

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (optional):
#   OPENAI_API_KEY=sk-...
#   POLYGON_API_KEY=...
#   SECRET_KEY=<generate-a-random-256-bit-key>

# 3. Start all services
docker compose up --build

# 4. Open the app
#    Frontend: http://localhost:5173
#    Backend API: http://localhost:8000
#    API Docs: http://localhost:8000/docs
#    PostgreSQL: localhost:5432
#    Redis: localhost:6379
```

**Register a user** at `/register` and start exploring.

---

## 💻 Local Development (Without Docker)

### Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Start PostgreSQL and Redis (must be running locally)
# Update .env with local connection strings

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

---

## 🔌 API Structure

```
/api
├── /auth              # Register, login, refresh, logout, profile
├── /portfolios        # CRUD portfolios, holdings, transactions, performance
├── /analysis          # AI fundamental analysis, chat, history
├── /technical         # SMA, EMA, RSI, MACD, Bollinger Bands, signals
├── /options           # Options flow scanner, stats, triggers
├── /earnings          # Earnings calendar, history, whisper numbers
├── /watchlists        # CRUD watchlists with items
├── /alerts            # Price/volume/technical alerts with evaluation
├── /macro             # Market indices, sector performance, economics
├── /risk              # VaR, Beta, drawdown, correlation, stress testing
├── /market            # Quote, history, symbol search
├── /dashboard         # Aggregated portfolio + market summary
└── /ws                # WebSocket endpoint for real-time prices
```

Full interactive documentation available at `http://localhost:8000/docs` when the backend is running.

---

## 📂 Project Structure

```
ai-investment-dashboard/
├── docker-compose.yml          # 4-service orchestration
├── .env.example                # Environment template
│
├── backend/
│   ├── app/
│   │   ├── main.py             # FastAPI app with lifespan events
│   │   ├── core/               # Config, security, caching, rate limiting
│   │   ├── db/                 # SQLAlchemy async engine, session, base
│   │   ├── models/             # 17 ORM models (users, portfolios, ...)
│   │   ├── schemas/            # Pydantic v2 request/response schemas
│   │   ├── api/routes/         # 12 route modules
│   │   ├── services/           # Business logic layer
│   │   ├── external/           # yfinance, Polygon, OpenAI integrations
│   │   ├── websocket/          # Connection manager & handlers
│   │   └── tasks/              # APScheduler background jobs
│   ├── alembic/                # Database migrations
│   └── pyproject.toml          # Python dependencies
│
├── frontend/
│   └── src/
│       ├── api/                # Axios client + typed endpoint modules
│       ├── components/         # UI primitives, charts, layout, shared
│       ├── features/           # Feature-specific component groups
│       ├── pages/              # 15 page components
│       ├── hooks/              # Custom hooks (auth, websocket, market data)
│       ├── store/              # Zustand stores (auth, WebSocket)
│       ├── types/              # TypeScript interfaces
│       ├── utils/              # Formatters, validators
│       └── router/             # Protected routes, auth guards
```

---

## 🧠 Key Design Decisions

| Decision | Rationale |
|---|---|
| **Async SQLAlchemy + asyncpg** | Non-blocking DB access during high-frequency price updates and WebSocket broadcasts |
| **APScheduler over Celery** | Simpler single-container deployment; extract to Celery worker if horizontal scaling needed |
| **yfinance primary, Polygon fallback** | yfinance is free and covers all needs (quotes, history, options, fundamentals); abstracted behind `market_data_service` for swap-ability |
| **Redis for 3 concerns** | Cache (API responses), Rate limiting (sliding window counters), Pub/Sub (WebSocket broadcasting) — single Redis instance, three use cases |
| **Zustand + React Query split** | React Query manages HTTP cache/refetch; Zustand holds only real-time WebSocket price state — clean separation of concerns |
| **Server-side numpy/pandas** | All financial math (VaR, Sharpe, Beta, drawdown) computed in Python where NumPy/Pandas are available and testable; frontend is pure presentation |
| **lightweight-charts (TradingView)** | Industry standard for financial charting; provides candlestick, crosshair, zoom, and subchart support out of the box |
| **In-process table creation** | `Base.metadata.create_all` runs in FastAPI lifespan — zero-config startup for development; Alembic available for production migrations |

---

## 🗺️ Roadmap

- [ ] **Real-time WebSocket price streaming** — Live price updates across all views
- [ ] **Portfolio equity curve chart** — Historical portfolio value visualization
- [ ] **Backtesting engine** — Strategy backtesting with historical data
- [ ] **Trade journal** — Annotated trade log with screenshots and notes
- [ ] **Multi-currency support** — International portfolio tracking
- [ ] **Dark mode / theme toggle** (currently dark-only)
- [ ] **PWA support** — Offline-first with service worker caching
- [ ] **CI/CD pipeline** — GitHub Actions for tests + deployment
- [ ] **Kubernetes deployment** — Production-grade orchestration
- [ ] **Mobile responsive layout** — Adaptive sidebar, touch interactions

---

## 📄 Resume-Relevant Highlights

This project demonstrates proficiency in:

<details>
<summary><strong>Full-Stack Engineering &bull; Click to expand</strong></summary>

- **Full-stack TypeScript + Python** — End-to-end feature ownership from database schema to React components
- **Async Python** — 12 async route modules, 10 async service modules, 5 background task schedulers using `asyncio` + `APScheduler`
- **SQLAlchemy 2.0** — 17 ORM models with async sessions, complex relationships, JSONB fields, composite unique constraints, batch operations
- **React + TypeScript** — Custom hooks, Zustand state management, TanStack Query caching, error boundaries, strict typing across 40+ source files
- **TradingView integration** — Real financial charting with `lightweight-charts`, candlestick + volume + overlay series
- **REST API design** — 60+ endpoints with Pydantic v2 validation, rate limiting, JWT auth, WebSocket broadcasting
- **Docker Compose** — 4-service architecture (Python, Node, PostgreSQL, Redis) with health checks and volume mounts
- **Financial computation** — Portfolio VaR (historical simulation), Beta (CAPM), Sharpe ratio, max drawdown, RSI, MACD, Bollinger Bands — all implemented in NumPy/Pandas
- **External API integration** — yfinance, Polygon.io, OpenAI — with rate limiting, retry logic, caching, and graceful fallback
- **Latency optimization** — Redis caching layer with configurable TTLs, N+1 query prevention, eager loading

</details>

---

## ⚠️ Disclaimer

**This software is for educational and research purposes only.**

- **Not financial advice.** Nothing in this application constitutes investment advice, recommendation, or solicitation.
- **No warranty.** This software is provided "as is" without warranty of any kind. Use at your own risk.
- **Data accuracy.** Market data is sourced from third-party APIs and may be delayed or inaccurate.
- **Past performance.** Historical data and backtested results do not guarantee future returns.
- **API costs.** Using OpenAI and Polygon APIs may incur charges. Monitor your usage.

Always consult a qualified financial advisor before making investment decisions.

---

<div align="center">
  <p>
    <sub>Built with React, FastAPI, PostgreSQL, and TradingView lightweight-charts.</sub>
  </p>
  <p>
    <sub>© 2026 &mdash; Open source for educational purposes.</sub>
  </p>
</div>
