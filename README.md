# RetailIQ: AI Powered Retail Intelligence & Inventory Optimization Platform

A comprehensive AI powered retail analytics platform with demand forecasting, inventory optimization, explainable AI, automated business insights, and real time business intelligence, wrapped in a modern **React + FastAPI** web application, fully containerized with **Docker Compose**.

---

## Badges

![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge\&logo=react\&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge\&logo=vite\&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge\&logo=mysql\&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-FF4438?style=for-the-badge\&logo=redis\&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=for-the-badge\&logo=celery\&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-24.0-2496ED?style=for-the-badge\&logo=docker\&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-2C5282?style=for-the-badge)
![LightGBM](https://img.shields.io/badge/LightGBM-4.3-38A169?style=for-the-badge)
![Prophet](https://img.shields.io/badge/Prophet-1.1-805AD5?style=for-the-badge)
![SHAP](https://img.shields.io/badge/SHAP-Explainable%20AI-3182CE?style=for-the-badge)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?style=for-the-badge\&logo=scikit-learn\&logoColor=white)

---

## Table of Contents

* [Project Overview](#project-overview)
* [Screenshots](#screenshots)
* [Features](#features)
* [Architecture](#architecture)
* [Prerequisites](#prerequisites)
* [Installation](#installation)
* [Configuration](#configuration)
* [Running the Application](#running-the-application)
* [Usage Guide](#usage-guide)
* [Project Structure](#project-structure)
* [Data Pipeline](#data-pipeline)
* [API Reference](#api-reference)
* [Celery Tasks](#celery-tasks)
* [Troubleshooting](#troubleshooting)
* [Technologies Used](#technologies-used)
* [Contributing](#contributing)
* [Support](#support)

---

# Project Overview

Retail businesses face constant challenges in managing inventory, forecasting demand, and making data driven decisions. Without the right tools, they rely on intuition, leading to stockouts, overstock, lost revenue, and tied up capital.

RetailIQ solves this by providing a complete AI powered retail intelligence platform that ingests raw sales data and runs it through a full pipeline: data validation, automated feature engineering, multi model demand forecasting with 5 competing ML models, inventory optimization including safety stock, EOQ, reorder points, and stockout prediction, SHAP based explainability, and automated natural language business insights.

The platform is **Pakistan context aware**: it understands local seasons including Spring, Summer, Monsoon, Autumn, and Winter, Islamic holidays including Eid, Ramadan, and Muharram, and fixed Pakistan holidays including Pakistan Day and Independence Day. It adjusts demand multipliers and inventory recommendations accordingly. It also integrates live weather data via OpenWeatherMap for real time context aware forecasting.

The platform is built as a modern two tier web application:

| Tier               | Tech                                          | Role                                   |
| ------------------ | --------------------------------------------- | -------------------------------------- |
| **Frontend**       | React 18 + Vite + Tailwind CSS + Recharts     | Interactive SPA dashboard              |
| **Backend**        | FastAPI + SQLAlchemy (async) + Celery + Redis | REST API, ML pipeline, background jobs |
| **Database**       | MySQL 8.0                                     | Persistent relational storage          |
| **Cache / Broker** | Redis 7                                       | Caching + Celery message broker        |
| **Deployment**     | Docker Compose                                | Single command full stack startup      |

---

# Screenshots

## Login & Authentication

<img width="1917" height="962" alt="image" src="https://github.com/user-attachments/assets/7b756f59-ce09-45b5-9a58-edc137d6718e" />

---

## Executive Dashboard

<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/3cd8776d-adf3-4376-a269-8c2f7d232ec1" />

---

## Sales Trends & Analytics

<img width="1916" height="692" alt="image" src="https://github.com/user-attachments/assets/5a03d3ce-11e5-4c62-bef0-0f5bac503f62" />

<img width="1251" height="380" alt="image" src="https://github.com/user-attachments/assets/e07940e4-37d1-4cf7-923a-d4574466b6be" />

<img width="1197" height="667" alt="image" src="https://github.com/user-attachments/assets/11881414-f26d-4d1b-a19f-b272f2471645" />

<img width="1202" height="378" alt="image" src="https://github.com/user-attachments/assets/ebc7061b-2376-451f-93fa-6c091cbc2b77" />

---

## Demand Forecasting

<img width="1917" height="962" alt="image" src="https://github.com/user-attachments/assets/a215e72f-6e90-46e6-92ae-25b8b1b35523" />

<img width="1917" height="965" alt="image" src="https://github.com/user-attachments/assets/6e02f530-5ed0-401d-bb4d-2b216b85da48" />

<img width="1207" height="360" alt="image" src="https://github.com/user-attachments/assets/b89ece9b-7d35-461f-83d8-ba69be5f5115" />

---

## Model Insights & Explainability

<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/6667a1d3-5a53-4ef9-917f-646d8c45aa80" />

---

## Inventory Optimization

<img width="1917" height="963" alt="image" src="https://github.com/user-attachments/assets/87e4092b-7c15-422c-ae9b-14f65af7455a" />

<img width="1917" height="867" alt="image" src="https://github.com/user-attachments/assets/66260b7b-459c-42dd-8ca3-d769bb609a0a" />

<img width="1192" height="380" alt="image" src="https://github.com/user-attachments/assets/ec480db9-2f4f-4a9f-9e25-666d248cb5aa" />

---

## Store Performance

<img width="1907" height="762" alt="image" src="https://github.com/user-attachments/assets/7cfb4c15-56e4-42d0-8670-f21d3c8a2557" />

<img width="1202" height="455" alt="image" src="https://github.com/user-attachments/assets/9fa8b70d-c066-4fa8-af95-b0f9b4dc0f42" />

---

## Product Performance

<img width="1917" height="967" alt="image" src="https://github.com/user-attachments/assets/724018f8-7acb-4dec-860f-83433d12e178" />

---

## Upload Data & CSV Processing

<img width="1917" height="967" alt="image" src="https://github.com/user-attachments/assets/5b1d5c28-8f7f-4ea2-be3a-7af1adfdcc89" />

---

## AI Insights & Business Intelligence

<img width="1917" height="965" alt="image" src="https://github.com/user-attachments/assets/b8ee5e26-ee21-4fe3-b010-9630c1f50976" />

---

## Smart Business Advisor

<img width="1917" height="963" alt="image" src="https://github.com/user-attachments/assets/bd91872d-c707-457b-8c11-5765231f61c9" />

---

## What-If Analysis

<img width="1917" height="965" alt="image" src="https://github.com/user-attachments/assets/0157d4ab-90c3-4fd2-a8ef-17c7c6ba96f4" />

<img width="1917" height="967" alt="image" src="https://github.com/user-attachments/assets/2ceba13b-ada8-4e4c-9c06-5f10f7e1a9c9" />

---

## Smart Alerts & Monitoring

<img width="1917" height="966" alt="image" src="https://github.com/user-attachments/assets/d75b1860-b72b-421a-b292-3cc7512b3f87" />

---

## Data Health Center

<img width="1917" height="967" alt="image" src="https://github.com/user-attachments/assets/85f4ca02-e671-4be8-a3b7-57fbce810b73" />

---

## Automated Reports

<img width="1917" height="965" alt="image" src="https://github.com/user-attachments/assets/e232ac67-af86-43c1-9a3c-55c58cc68484" />

---

## Model Performance & Insights

<img width="1917" height="962" alt="image" src="https://github.com/user-attachments/assets/09ab48a0-bd72-4fb2-8819-95cb2a08580d" />

---

# Features

### Data Upload & Auto Processing

* Upload your own retail sales CSV
* Auto validate column structure and data quality
* Auto clean missing values, fix data types, and remove duplicates
* Append to existing historical data
* MySQL database stores all uploads, forecasts, and inventory history

### AI Demand Forecasting

* 5 competing ML models: Baseline, Random Forest, XGBoost, LightGBM, Prophet
* One click model comparison using MAE, RMSE, MAPE, and R²
* Automatically selects and saves the best performing model
* Preset horizons: 7 days, 30 days, 90 days
* Autoregressive forecasting based on today's date and available data
* Async training via Celery worker with live progress tracking

### Live Context Integration

* Weather API: real time temperature, conditions, and 5 day forecast
* Holiday API: holiday aware forecasting with built in Pakistan holiday fallback
* Uses the current date for all forecasting calculations

### Inventory Optimization

* Safety Stock calculation: Z score × demand variability × √Lead Time
* Reorder Point with lead time adjustment
* EOQ, Economic Order Quantity
* Stockout Prediction: predicts exactly when stock will run out
* Overstock Detection: identifies items tying up capital
* Low Stock Alerts with severity levels: OK, LOW, CRITICAL, EXCESS
* Demand Multipliers: automatically adjusts for peak seasons and holidays
* Seasonal Product Alerts: flags in season and out of season items

### Explainable AI, SHAP

* Global feature importance rankings
* SHAP summary plot showing feature impact distribution
* Individual prediction explanations
* Feature dependency analysis

### Business Intelligence, Analytics Dashboard

* Sales trend analysis: daily, seasonal, and yearly
* Product, store, and category performance rankings
* Day of week sales patterns
* Seasonal trend analysis across 5 Pakistan seasons
* Interactive charts using Recharts: line, bar, pie, and KPI cards
* Date range selector: 30, 90, and 180 days

### AI Generated Business Insights

* Automated natural language insights about your data
* Seasonal demand advice with product level recommendations
* Weather impact analysis using temperature and sales correlation
* Holiday stock up calendar with countdown timers
* Recommended actions such as weekend promotions, seasonal preparation, and diversification
* Data Health Score from 0 to 100 with specific improvement suggestions

### Reports & Export

* CSV export on every dashboard page
* PDF report generation using fpdf2 for forecasts, inventory, and model insights
* Combined summary reports with metrics and visualizations

### Operational Infrastructure

* **JWT authentication** with login, registration, refresh tokens, and role based access for admin and analyst users
* **Celery worker + beat** for background training and scheduled daily insight generation
* **Redis caching** for weather and holiday lookups and frequent queries
* **Container healthchecks** on every service

---

# Architecture

```text
                         ┌──────────────────────────────────────────┐
                         │              Browser (SPA)               │
                         │    React 18 + Vite + Tailwind + Recharts │
                         └──────────────────┬───────────────────────┘
                                            │  HTTP :3000
                                            ▼
                         ┌──────────────────────────────────────────┐
                         │          Nginx (client container)        │
                         │        proxies /api → FastAPI :8000      │
                         └──────────────────┬───────────────────────┘
                                            │  HTTP :8000
                                            ▼
                    ┌───────────────────────────────────────────────────┐
                    │            FastAPI Backend (uvicorn)              │
                    │  /api/v1/auth · analytics · forecast · inventory  │
                    │  /api/v1/model · insights · upload · weather      │
                    └───────┬──────────────────────┬────────────────────┘
                            │                      │
                    ┌───────▼────────┐    ┌────────▼─────────┐
                    │   MySQL 8.0    │    │     Redis 7      │
                    │  relational DB │    │  cache + broker   │
                    └────────────────┘    └────────┬─────────┘
                                                   │
                              ┌────────────────────┴─────────────┐
                              │  Celery Worker        Celery Beat │
                              │  async training   scheduled jobs │
                              └──────────────────────────────────┘
```

### Container Topology, `docker-compose.yml`

| Service         | Container                | Port        | Purpose                         |
| --------------- | ------------------------ | ----------- | ------------------------------- |
| `api`           | `retailiq-api`           | 8000 → 8000 | FastAPI backend                 |
| `client`        | `retailiq-client`        | 3000 → 80   | React SPA served by Nginx       |
| `db`            | `retailiq-db`            | 3307 → 3306 | MySQL 8.0                       |
| `redis`         | `retailiq-redis`         | 6379 → 6379 | Cache + Celery broker           |
| `celery-worker` | `retailiq-celery-worker` | —           | Async ML training               |
| `celery-beat`   | `retailiq-celery-beat`   | —           | Scheduled tasks, daily insights |

---

# Prerequisites

* **Docker Desktop**, or Docker Engine + Compose v2, for Windows, macOS, or Linux
* **Git**, optional, for cloning
* **Approximately 4 GB free RAM** and **10 GB free disk space** for images and data

No Python or Node installation is needed. Everything runs inside containers.

---

# Installation

### 1. Clone the repository

```bash
git clone https://github.com/MoazzamFarooqui/RetailIQ.git
cd RetailIQ
```

### 2. Configure environment, optional

Copy the example file and add your API keys if you have them:

```bash
cp .env.example .env
```

### 3. Start the stack

```bash
docker compose up -d --build
```

The first build downloads base images and installs dependencies including Python ML packages and Node modules. Allow approximately 10 to 20 minutes. Subsequent starts take seconds.

### 4. Verify

```bash
docker compose ps
```

All six containers should report `healthy` or `Up`.

---

# Configuration

### Environment Variables

Create a `.env` file in the project root, using `.env.example` as a reference:

```env
# Application
APP_NAME=RetailIQ API
APP_VERSION=3.0.0
ENVIRONMENT=development
DEBUG=true

# Database
# For Docker Compose, internal network:
DATABASE_URL=mysql+aiomysql://retailiq:retailiq@db:3306/retailiq

# For local development, SQLite:
# DATABASE_URL=sqlite+aiosqlite:///data/retailiq_v2.db

# Redis
# For Docker Compose:
REDIS_URL=redis://redis:6379/0

# For local development:
# REDIS_URL=redis://localhost:6379/0

# JWT Authentication
SECRET_KEY=change-this-to-a-long-random-string-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# API Keys, optional
# Weather data
OPENWEATHER_API_KEY=your_key_here

# Holiday data
HOLIDAY_API_KEY=your_key_here

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/1

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173","http://localhost:8000"]
```

> **Note:** In Docker, `docker-compose.yml` overrides `DATABASE_URL` with `mysql+aiomysql://retailiq:retailiq@db:3306/retailiq`, so the backend always uses the containerized MySQL database. Without API keys, the platform falls back to built in Pakistan Islamic holiday tables covering 2024 to 2028 and seasonal defaults, allowing the system to remain fully functional offline.

### Dataset

RetailIQ ships with the **M5 Walmart retail dataset**, containing 30,490 products across 1,941 days in `data/raw/`. A subsample covering 3 stores and the full 2011 to 2016 range is pre processed into `data/processed/engineered_features.csv`, along with compact analytics aggregates.

You can upload your own retail sales CSV at any time through the Upload page.

---

# Running the Application

### Quick Start

```bash
docker compose up -d
```

### Open the App

| What                              | URL                          |
| --------------------------------- | ---------------------------- |
| **Frontend, main app**            | http://localhost:3000        |
| **API interactive docs, Swagger** | http://localhost:8000/docs   |
| **API health check**              | http://localhost:8000/health |

### Default Credentials

| Username | Password   | Role          |
| -------- | ---------- | ------------- |
| `admin`  | `admin123` | Administrator |

### Everyday Commands

| Action                  | Command                               |
| ----------------------- | ------------------------------------- |
| Start everything        | `docker compose up -d`                |
| Stop everything         | `docker compose down`                 |
| Restart the API         | `docker restart retailiq-api`         |
| Rebuild backend image   | `docker compose up -d --build api`    |
| Rebuild frontend image  | `docker compose up -d --build client` |
| View logs, all services | `docker compose logs -f`              |
| View API logs           | `docker logs retailiq-api -f`         |
| Check status            | `docker compose ps`                   |

---

# Usage Guide

### Dashboard, Home

* View live KPIs including total sales, average daily sales, products, and stores
* One click navigation to every module through the sidebar

### Upload

* Upload a retail sales CSV file
* The system automatically validates required columns: `date`, `sales`, `item_id`, `store_id`
* Automatically cleans missing values, fixes data types, and caps negative sales
* Preview cleaned data before saving
* Append data to the historical database with one click

### Train Model

* Configure training parameters including sample size and test split
* Select which models to train: Baseline, Random Forest, XGBoost, LightGBM, Prophet
* One click training runs asynchronously through Celery with progress tracking
* View side by side comparison using MAE, RMSE, MAPE, and R²
* Best model is automatically saved to `models/best_model.joblib`

### Analytics

* KPI row showing total sales, average daily sales, product count, and store count
* Sales trends over 30, 90, and 180 days using an interactive line chart
* Top 10 products by revenue using a bar chart
* Store performance comparison table
* Day of week sales patterns with peak percentage across all 7 days
* Seasonal breakdown across the 5 Pakistan seasons using a pie chart

### Forecast

* Select a specific product and store combination
* View live weather and holiday context
* Generate 7, 30, or 90 day demand forecasts
* Interactive chart with historical and predicted values
* View forecast KPIs including total, average, percentage change, and peak day
* Check holidays during the forecast period with stock advice
* Get integrated inventory recommendations including safety stock, reorder point, EOQ, and stockout date
* Export forecasts as CSV or PDF reports

### Inventory

* Configure service level from 80% to 99%, lead time, and excess threshold
* View inventory KPIs including total items, healthy percentage, at risk percentage, and overstock percentage
* Stockout predictions sorted by days until stockout, with critical alerts
* Overstock detection with excess units and days of stock
* Critical and low stock items requiring immediate reorder
* Recommended actions including total units to order and average order size
* Filterable recommendations table
* Export complete reports as CSV or PDF

### Model Insights

* View current model information including type, features, and estimators
* Compare all trained models side by side using performance metrics
* View feature importance rankings
* Generate SHAP analysis with summary plots showing feature impact
* Explain individual predictions by selecting any data point and viewing feature contributions
* Export model comparisons as CSV

### AI Insights

* Live context including today's date, weather, season, and upcoming holidays
* Seasonal demand analysis with current season advice and high or low demand products
* Weather impact analysis using temperature and sales data
* AI generated insights categorized as Summary, Trends, Seasonality, Products, Stores, Revenue, and Data Quality
* Recommended actions with explanations
* Holiday stock up calendar with countdowns and priority levels
* Data Health Score from 0 to 100 with itemized deductions and improvement suggestions
* Export insights as text or CSV

---

# Project Structure

```text
RetailIQ/
│
├── docker-compose.yml               # Full stack orchestration, 6 services
├── README.md                        # Project documentation
├── .env / .env.example              # Environment configuration
│
├── backend/                         # FastAPI backend, bind mounted into containers
│   ├── Dockerfile                   # Multi stage Python 3.12 image
│   ├── requirements.txt             # Python dependencies
│   ├── alembic/                     # DB migration scaffolding
│   ├── scripts/
│   │   ├── regenerate_engineered_data.py
│   │   │                              # Rebuild engineered features from raw M5
│   │   └── regenerate_analytics_aggregates.py
│   │                                  # Rebuild compact analytics aggregates
│   ├── tests/                       # Pytest suite
│   └── app/
│       ├── main.py                  # FastAPI app factory + lifespan
│       ├── core/                    # Config, database, security, cache, dependencies
│       ├── models/                  # SQLAlchemy ORM models, 7 tables
│       ├── schemas/                 # Pydantic request and response schemas
│       ├── api/v1/endpoints/        # Auth, users, upload, forecast, inventory,
│       │                            # analytics, model, insights, weather
│       ├── services/                # Forecasting, inventory optimizer,
│       │                            # feature engineering, explainability,
│       │                            # insights engine, weather, holiday, report
│       └── tasks/                   # Celery app, training, forecast, report tasks
│
├── client/                          # React 18 SPA
│   ├── Dockerfile                   # Multi stage Vite build + Nginx serve
│   ├── nginx.conf                   # SPA + /api proxy to backend
│   ├── package.json
│   └── src/
│       ├── main.jsx / App.jsx       # Entry + routing
│       ├── services/                # API client, axios
│       ├── contexts/AuthContext.jsx # JWT auth state
│       ├── components/              # Layout, KpiCard, LoadingState, StatusBadge
│       └── pages/                   # Dashboard, Analytics, Forecast, Inventory,
│                                    # ModelInsights, AIInsights, Upload, Login
│
├── data/                            # Mounted into containers
│   ├── raw/                         # Original M5 Walmart dataset
│   │   ├── calendar.csv             # Date metadata, 1,969 rows
│   │   ├── sales_train_evaluation.csv
│   │   │                              # Sales, 30,490 products × 1,941 days
│   │   └── sell_prices.csv          # Product pricing, 6.8M records
│   └── processed/                   # Auto generated
│       ├── engineered_features.csv  # Long format feature frame
│       ├── analytics_daily.csv      # Compact daily aggregates
│       ├── analytics_products.csv   # Per product totals
│       ├── analytics_meta.json      # Overview metrics
│       └── backup/                  # Safety backups of generated files
│
├── models/
│   └── best_model.joblib            # Trained best model, auto generated
│
└── reports/
    ├── exports/                     # Generated reports, CSV and PDF
    └── figures/                     # Generated figures, PNG
```

---

# Data Pipeline

RetailIQ processes data through a structured pipeline with five major stages.

### 1. Ingestion & Validation

```text
Upload CSV → validation (date, sales, item_id, store_id) → data quality report
```

### 2. Cleaning & Storage

```text
Auto clean (missing values, types, duplicates) → Save to MySQL → Save to data/processed/
```

### 3. Feature Engineering

```text
Load cleaned data → FeatureEngineer.create_all_features()

  ├── Time features (year, month, day, dayofweek, is_weekend)
  ├── Cyclical encoding (sin/cos of month, day of week, day of year)
  ├── Pakistan seasons (Spring, Summer, Monsoon, Autumn, Winter)
  ├── Holiday features (is_holiday, days_to_holiday, pre Ramadan/Eid windows)
  ├── Weather features (temp, humidity, rain flags, weather × season interactions)
  ├── Lag features (1, 7, 14, 28 days)
  ├── Rolling statistics (7, 14, 28 day means + stds)
  ├── Price features (change, momentum, price vs average)
  └── Event & SNAP features
```

### 4. Model Training & Forecasting

```text
Train 5 models → Compare metrics (MAE, RMSE, MAPE, R²) → Select best → Save

Autoregressive forecast → 7, 30, 90 day horizon → Store in MySQL

Async via Celery worker, scheduled daily insights via Celery Beat
```

### 5. Inventory & Insights

```text
Forecast → InventoryOptimizer (safety stock, EOQ, reorder, stockout, overstock)

Data → InsightsEngine → Natural language insights, recommendations, health score
```

### Data Regeneration Scripts

The analytics endpoints read compact aggregate files, `analytics_daily.csv`, `analytics_products.csv`, and `analytics_meta.json`, rather than the full engineered frame, which can reach hundreds of MB. Regenerate them after any raw data change:

```bash
# 1. Rebuild the long format engineered frame from data/raw/, 3 stores by default
python backend/scripts/regenerate_engineered_data.py --stores CA_1,TX_2,WI_3

# 2. Rebuild the compact analytics aggregates
python backend/scripts/regenerate_analytics_aggregates.py
```

### Database Schema, MySQL

| Table                       | Purpose                                         |
| --------------------------- | ----------------------------------------------- |
| `users`                     | Users, roles, admin or analyst, password hashes |
| `datasets`                  | Upload metadata                                 |
| `forecast_headers`          | Forecast session metadata                       |
| `forecasts`                 | Individual forecast records                     |
| `inventory_recommendations` | Per item inventory calculations                 |
| `model_history`             | Training runs and metrics                       |
| `business_insights`         | Generated insight text and categories           |

---

# API Reference

Base URL: `http://localhost:8000`

Interactive documentation is available at `/docs` through Swagger UI.

All endpoints except `/auth/register` and `/auth/login` require an `Authorization: Bearer <token>` header.

### Authentication

| Method | Endpoint                | Description                                  |
| ------ | ----------------------- | -------------------------------------------- |
| POST   | `/api/v1/auth/register` | Register a new user, role: analyst           |
| POST   | `/api/v1/auth/login`    | Login, returns JWT access and refresh tokens |
| POST   | `/api/v1/auth/refresh`  | Refresh an expired access token              |

### Analytics

| Method | Endpoint                                  | Description                           |
| ------ | ----------------------------------------- | ------------------------------------- |
| GET    | `/api/v1/analytics/overview`              | KPI overview metrics                  |
| GET    | `/api/v1/analytics/sales-trend?days=90`   | Daily sales trend for the last N days |
| GET    | `/api/v1/analytics/top-products?limit=10` | Top selling products                  |
| GET    | `/api/v1/analytics/store-performance`     | Per store sales comparison            |
| GET    | `/api/v1/analytics/seasonal`              | Sales by Pakistan season              |
| GET    | `/api/v1/analytics/day-of-week`           | Sales by day of week                  |

### Forecast & Model

| Method | Endpoint                    | Description                                    |
| ------ | --------------------------- | ---------------------------------------------- |
| POST   | `/api/v1/forecast/generate` | Generate forecast for item, store, and horizon |
| GET    | `/api/v1/forecast/history`  | Forecast history                               |
| POST   | `/api/v1/model/train`       | Train all models, sync or async through Celery |
| GET    | `/api/v1/model/history`     | Model training history                         |
| GET    | `/api/v1/model/compare`     | Model comparison metrics                       |
| GET    | `/api/v1/model/features`    | Feature importance                             |

### Inventory & Insights

| Method | Endpoint                            | Description                |
| ------ | ----------------------------------- | -------------------------- |
| GET    | `/api/v1/inventory/recommendations` | Inventory recommendations  |
| POST   | `/api/v1/inventory/optimize`        | Run inventory optimization |
| GET    | `/api/v1/insights/recent`           | Recent generated insights  |
| POST   | `/api/v1/insights/generate`         | Generate new insights      |

### Upload & Weather

| Method | Endpoint                   | Description                   |
| ------ | -------------------------- | ----------------------------- |
| POST   | `/api/v1/upload`           | Upload a sales CSV            |
| GET    | `/api/v1/weather/current`  | Current weather with fallback |
| GET    | `/api/v1/weather/forecast` | 5 day weather forecast        |

### External API Integrations

**OpenWeatherMap**, live weather data for context aware forecasting:

| Endpoint        | Usage                                             | Frequency              |
| --------------- | ------------------------------------------------- | ---------------------- |
| Current Weather | Fetch temperature, conditions, humidity, and wind | On dashboard load      |
| 5 Day Forecast  | Weather forecast for the prediction period        | On forecast generation |

Free Tier: 1,000 calls per day.

Fallback: seasonal defaults when no API key is available.

**Calendarific**, national and religious holiday data:

| Endpoint     | Usage                                 | Frequency            |
| ------------ | ------------------------------------- | -------------------- |
| Holidays API | Fetch national and religious holidays | On application start |

Fallback: built in Islamic holiday tables from 2024 to 2028 and fixed Pakistan holidays. The application remains fully functional offline.

---

# Celery Tasks

Background jobs run on the `celery-worker` container, with the scheduler, `celery-beat`, triggering periodic work.

| Task                                               | Schedule  | Description                            |
| -------------------------------------------------- | --------- | -------------------------------------- |
| `app.tasks.training_tasks.train_all_models_task`   | On demand | Trains all 5 models and saves the best |
| `app.tasks.forecast_tasks.*`                       | On demand | Forecast generation jobs               |
| `app.tasks.training_tasks.generate_daily_insights` | **Daily** | Generates automated business insights  |
| `app.tasks.report_tasks.*`                         | On demand | PDF and CSV report generation          |

Broker and result backend: Redis, database 1.

Task time limit: 1 hour.

---

# Troubleshooting

### API Container Keeps Restarting, `Exited (3)`

Check the logs for the underlying error:

```bash
docker logs retailiq-api --tail 100
```

Historically resolved issues include:

* **`ping() missing 1 required positional argument: 'reconnect'`**, caused by `aiomysql 0.2.0` and `PyMySQL ≥1.1` signature changes compared with SQLAlchemy's pool pre ping. Fixed by pinning `sqlalchemy[asyncio]==2.0.31` and `PyMySQL==1.0.3` in `backend/requirements.txt`.
* **`Field "model_type" has conflict with protected namespace "model_"`**, a Pydantic v2 warning. Silenced using `model_config = {"protected_namespaces": ()}` on the schemas.

### Analytics Page Shows an Error or Empty Charts

The API needs `data/processed/analytics_daily.csv`, `analytics_products.csv`, and `analytics_meta.json`.

Regenerate them:

```bash
python backend/scripts/regenerate_analytics_aggregates.py
```

Then hard refresh the browser using `Ctrl + F5` to load the rebuilt frontend bundle.

### Frontend Changes Do Not Appear

The client is a static build inside the image. After changing `client/src/*`, rebuild the client:

```bash
docker compose up -d --build client
```

### Backend Changes Do Not Appear

`./backend` is bind mounted, so after editing Python files, restart the API:

```bash
docker restart retailiq-api
```

### Port Already in Use

If port 3000, 8000, 3307, or 6379 is already taken, change the host side of the mapping in `docker-compose.yml`, for example:

```text
"3001:80"
```

---

# Technologies Used

### Frontend & Visualization

* **React 18**, interactive single page application
* **Vite 5**, fast build tooling and development server
* **Tailwind CSS**, utility first styling
* **Recharts**, interactive charts including line, bar, pie, and KPI cards
* **Lucide React**, icon library

### Backend & API

* **FastAPI**, high performance async Python API
* **Uvicorn**, ASGI server
* **Pydantic v2**, validation and serialization
* **SQLAlchemy 2 async**, ORM with `aiomysql` driver
* **Alembic**, migration tooling

### Machine Learning

* **scikit learn**, Random Forest, preprocessing, and metrics
* **XGBoost**, gradient boosting
* **LightGBM**, leaf wise gradient boosting
* **Prophet**, time series forecasting
* **SHAP**, Shapley additive explanations for model interpretability

### Data Processing & Storage

* **Pandas / NumPy**, data manipulation
* **SciPy / Statsmodels**, scientific and statistical computing
* **MySQL 8.0**, relational database, containerized
* **Redis 7**, cache and Celery broker
* **Celery 5**, distributed task queue
* **Joblib**, model serialization

### Infrastructure

* **Docker Compose**, multi container orchestration
* **Nginx**, frontend static serving and API reverse proxy
* **python jose / passlib / bcrypt**, JWT authentication and password hashing

### External APIs

* **OpenWeatherMap**, live weather data and forecasts
* **Calendarific**, national and religious holiday data

### Reporting

* **fpdf2**, PDF report generation

---

# Contributing

Contributions are welcome. Here is how you can help improve RetailIQ:

1. Fork the repository.
2. Create a feature branch:

```bash
git checkout -b feature/amazing-feature
```

3. Make your changes.
4. Test the application thoroughly:

```bash
docker compose up -d --build
```

5. Commit your changes:

```bash
git commit -m 'Add amazing feature'
```

6. Push your branch:

```bash
git push origin feature/amazing-feature
```

7. Open a Pull Request.

### Development Ideas

* Add additional forecasting models such as ARIMA, LSTM, and Transformer
* Implement multi warehouse inventory support
* Add multi tenant support beyond role based authentication
* Integrate with real POS systems through an API
* Add email and SMS alerting for stockout predictions
* Add PostgreSQL as an alternative database backend
* Add comparative analysis across multiple stores and chains
* Implement A/B testing for promotional effectiveness

---

# Support

If you encounter any issues, have feature requests, or need assistance:

* Open an issue in this repository
* Check the existing documentation in the `notebooks/` directory for detailed walkthroughs
* Review the source code, each module contains clear documentation and type hints
* Use the troubleshooting section above for common Docker related issues

# Retailsense
