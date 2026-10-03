# TradeVision AI — Full Project Analysis

## 1. Executive Summary

TradeVision AI is a full-stack trading analysis application designed to help users analyze stock or market charts from screenshots and raw market data. The current implementation combines:

- OCR-driven chart upload and symbol detection
- Secure user authentication
- Real-time and historical market data queries
- Technical analysis (EMA, RSI, MACD, support/resistance, volume)
- Market sentiment and risk assessment
- A designed dashboard and authenticated frontend workflow

The project is organized as a monorepo with a Python FastAPI backend and a TypeScript React frontend, supported by PostgreSQL and Docker-based local infrastructure.

---

## 2. Product Purpose

The project aims to automate the analysis workflow for trading chart images. In practical terms, a user can:

1. Create an account or sign in.
2. Upload a chart screenshot (for example, TradingView style images).
3. Let the backend extract chart metadata such as symbol, exchange, and timeframe.
4. Review the detected values and correct them if needed.
5. Fetch market data and run technical analysis.
6. Receive a quick risk and sentiment summary based on price action and news context.

The app is positioned as an intelligent decision-support tool for stock chart interpretation rather than a brokerage or trading execution platform.

---

## 3. Technology Stack

### Frontend

- React + TypeScript
- Vite
- TanStack Start / TanStack Router
- Tailwind CSS
- Radix UI component primitives
- shadcn-style UI layer
- Lucide icons
- Zod and React Hook Form for form handling

### Backend

- Python 3.11
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- JWT-based auth with Passlib/Bcrypt
- Requests for external APIs
- OCR and image processing stack: OpenCV, Pillow, PaddleOCR

### Data and Infrastructure

- PostgreSQL via Docker Compose
- `.env`-driven configuration
- Axios-like typed frontend API client pattern
- Local upload directory for OCR processing

### External API Integrations

- Twelve Data for market quote and historical data
- Finnhub for company news and sentiment
- Gemini API key is configured but not currently active in the main code path

---

## 4. Repository Structure

The repository is organized into a root-level monorepo with the following key areas:

```text
TradeVision-AI/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── auth.py
│   │   │       ├── market.py
│   │   │       └── ocr.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── security.py
│   │   ├── domain/
│   │   │   ├── models.py
│   │   │   └── schemas.py
│   │   ├── infrastructure/
│   │   │   └── db/
│   │   │       └── session.py
│   │   ├── services/
│   │   │   ├── market_service.py
│   │   │   ├── news_service.py
│   │   │   ├── ocr_service.py
│   │   │   ├── risk_service.py
│   │   │   └── technical_analysis_service.py
│   │   ├── main.py
│   │   └── __pycache__
│   ├── alembic/
│   ├── .env
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── routes/
│   │   └── ...
│   ├── app/
│   ├── package.json
│   ├── vite.config.ts
│   └── README.md
├── docker-compose.yml
├── Project_Structure.md
├── run.txt
└── PROJECT_ANALYSIS.md
```

A planning document, `Project_Structure.md`, shows a more complete layered architecture including modules such as reports, chat, history, and infrastructure clients. The implementation currently reflects the core workflow more than the full planned architecture.

---

## 5. Backend Architecture and Modules

### 5.1 Application Entry

The FastAPI app is created in `backend/app/main.py`.

Key responsibilities:

- Starts the application with the title `TradeVision AI`
- Enables CORS for frontend dev origins (`localhost:3000`, `localhost:8080`, `localhost:8082`)
- Mounts API routers for authentication, OCR, and market features
- Exposes `/health` for a basic boot-up health check

### 5.2 Authentication Module

`backend/app/api/v1/auth.py` defines the following API endpoints:

- `GET /api/v1/auth/me`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`

The auth flow is backed by:

- `app/core/security.py`: JWT creation, password hashing, token validation, user lookup
- `app/domain/models.py`: `User` and refresh token models
- `app/domain/schemas.py`: auth request/response models

This gives the app a standard stateless JWT authentication flow with refresh-token support.

### 5.3 OCR Module

`backend/app/api/v1/ocr.py` implements the chart-upload workflow.

Flow:

1. Accept uploaded image via FastAPI `UploadFile`
2. Validate MIME type is image-based
3. Save the file into the local `uploads/` folder
4. Insert an `UploadedImage` record in PostgreSQL
5. Preprocess the image with OCR-related utilities
6. Extract text and parse metadata such as symbol/exchange/timeframe
7. Update OCR status and return the OCR result

This route is designed to support later report persistence and user history tracking.

### 5.4 Market and Technical Analysis Module

`backend/app/api/v1/market.py` exposes:

- `GET /api/v1/market/quote/{symbol}`
- `GET /api/v1/market/candles/{symbol}`
- `GET /api/v1/market/analysis/{symbol}`
- `GET /api/v1/market/risk/{symbol}`

These endpoints call services that:

- fetch ticker quotes from Twelve Data
- retrieve OHLCV series
- compute EMA, RSI, MACD, support/resistance, and volume data
- assess sentiment from recent company news
- calculate a risk and confidence score

### 5.5 Core Service Layer

The service layer is the analytical engine of the application:

- `market_service.py`: quote + historical series retrieval
- `technical_analysis_service.py`: EMA / RSI / MACD / trend / volume analysis
- `news_service.py`: Finnhub-based headline sentiment analysis
- `risk_service.py`: risk classification and confidence scoring
- `ocr_service.py`: image preprocessing, text extraction, chart metadata parsing

The app’s real analytical value is concentrated in this layer.

---

## 6. Data Model

The SQLAlchemy models in `backend/app/domain/models.py` include the following entities:

- `User`
- `UploadedImage`
- `Report`
- `AnalysisHistory`
- `ChatMessage`
- `Watchlist`
- `Settings`
- `RefreshToken`

This indicates the product was planned around a richer trading journal workflow with:

- user uploads
- saved analysis reports
- per-report history
- chat-based explanation
- watchlists
- user settings

Currently, the runtime code clearly implements the user and uploaded-image flow, while some report/history/chat features are scaffolded in the data model but not fully exposed in the API.

---

## 7. Frontend Application Structure

The frontend is built in `frontend/src` and uses a route-driven architecture.

### Key routes

- `/login` — sign in screen
- `/register` — user registration screen
- `/dashboard` — overview and summary home
- `/upload` — screenshot upload and analysis workflow
- `/history` — likely intended report history view
- `/settings` — account settings and preferences
- `/profile` and `/watchlist` — user-specific views

### Frontend capabilities currently observed

- secure auth state via context provider
- local storage token management
- upload drag-and-drop chart input
- preview of uploaded image
- OCR result review and manual symbol/market confirmation
- technical analysis panels showing RSI, EMA, MACD, support/resistance
- detection of trend direction and volume strength

This is a strong single-product workflow and matches the backend architecture closely.

---

## 8. Core User Flow

The app’s main end-to-end flow is:

1. User logs in or registers.
2. The frontend stores access and refresh tokens.
3. User uploads chart image in the `/upload` route.
4. Backend validates file type and saves it.
5. OCR extracts text and identifies probable symbol/data.
6. Frontend shows the OCR result and allows manual correction.
7. User confirms the asset metadata.
8. Backend fetches price and historical data via Twelve Data.
9. Technical analysis is computed from OHLCV data.
10. News sentiment and risk scoring are added.
11. The dashboard can display the resulting overview and report data.

This is a clean, compelling workflow for a chart-based trading assistant.

---

## 9. Notable Implementation Details

### Security

- JWT access tokens are issued with HS256
- Passwords are hashed with bcrypt
- Authorization is enforced via FastAPI dependencies
- development CORS is enabled for local frontend origins

### Configuration

`backend/app/core/config.py` reads settings from `backend/.env` using `pydantic-settings`.

Important config values include:

- `DATABASE_URL`
- `SECRET_KEY`
- `TWELVE_DATA_API_KEY`
- `FINNHUB_API_KEY`
- `GEMINI_API_KEY`

### Database and Persistence

`docker-compose.yml` defines a local PostgreSQL instance:

- service: `postgres`
- image: `postgres:16-alpine`
- database: `tradevision_db`
- user: `tradevision`
- port mapping: `5433:5432`

This allows local development without external infrastructure.

---

## 10. Runtime Setup and Commands

The project includes instructions in `run.txt` for a typical local setup:

```bash
cd /run/media/sagar/4b11a45d-e86c-4f78-93ef-475814043003/CSPIT/Project/TradeVision-AI/backend
source .venv/bin/activate
python --version

docker compose up -d
docker ps -a

cd backend
uvicorn app.main:app --reload

# new terminal
cd frontend
npm run dev
```

The intended production-ready flow is therefore:

- start Postgres via Docker
- run the FastAPI app
- run the frontend dev server

---

## 11. What Is Already Built vs. Planned

### Implemented well

- user auth
- OCR image upload flow
- chart metadata extraction
- market quote + historical series retrieval
- technical indicator analysis
- sentiment and risk scoring
- frontend dashboard/upload flow
- local database scaffold

### Partially planned or scaffolded

- chat-based trade explanation
- report generation and persistence
- history feed and analysis archival
- watchlist management
- settings screen
- richer modular infrastructure for external clients and reporting

The codebase suggests a product that is mid-implementation: the project has the architectural vision and initial working modules, but not every planned feature is fully connected and production-hardened.

---

## 12. Strengths of the Project

- Clear separation between API, domain, services, and infrastructure
- Good monorepo structure for a practical product workflow
- Real trading utility instead of generic boilerplate
- Strong end-user flow: upload → analyze → interpret → decide
- External API integration is realistic and production-relevant
- Frontend is modern, polished, and route-driven

---

## 13. Observations and Improvement Opportunities

1. The repository includes a richer architecture document than the currently active API surface.
2. Some logical modules appear planned but not fully wired into the app.
3. The current risk and sentiment logic is useful, but still relatively rule-based rather than AI-driven.
4. The project would benefit from automated tests for the market, OCR, and auth routes.
5. The OCR and technical-analysis pipeline is strong for a prototype, but the persistence and reporting layer still looks like a next phase.
6. Security and environment handling are good for local development, but production hardening would require stronger secrets management and deployment checks.

---

## 14. Final Assessment

TradeVision AI is a thoughtful and practical trading-analysis application with a coherent architecture and an attractive user journey. It is not just a demo app; it is a real-world workflow idea implemented in a modern stack.

The strongest parts of the project are:

- OCR + chart interpretation
- technical market analytics
- modern frontend UX
- service-based backend design

The next stage for this project would likely be to connect the remaining domain entities and user-history/report modules into the actual live app experience, then harden the system with tests, deployment configuration, and production-level observability.

---

## 15. Summary in One Line

TradeVision AI is a FastAPI + React trading chart analysis platform that turns uploaded market screenshots into technical analysis, sentiment scoring, and risk insights for traders.
