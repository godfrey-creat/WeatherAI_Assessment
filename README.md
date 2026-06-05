# AI Travel Weather Advisor

> An intelligent travel planning web application that analyses WeatherAI forecasts and generates personalised packing recommendations for any destination in the world.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [How It Works](#how-it-works)
- [API Integration](#api-integration)
- [Packing Logic](#packing-logic)
- [Error Handling](#error-handling)
- [Deployment](#deployment)
- [WeatherAI Plan Limits](#weatherai-plan-limits)

---

## Overview

AI Travel Weather Advisor is a Django-powered web application built as part of the WeatherAI Developer Assessment. It allows travellers to enter a destination city and travel date range, then instantly receive an AI-generated weather summary, temperature and rain forecasts, and a smart packing checklist — all derived from the WeatherAI API.

**Example interaction:**

| Input | Value |
|-------|-------|
| Destination | Nairobi |
| Departure | June 15 |
| Return | June 18 |

| Output | Value |
|--------|-------|
| Temperature | 18°C – 26°C |
| Rain probability | Moderate (42%) |
| AI Summary | *"Expect cool mornings and occasional afternoon showers."* |
| Packing checklist | Light jacket, Compact umbrella, Sunscreen, Walking shoes… |

---

## Features

- **City-name input** — users type any city name; the app resolves coordinates automatically via OpenStreetMap Nominatim (no additional API key required).
- **Date range selection** — departure and return date pickers with same-day minimum validation.
- **WeatherAI forecast** — calls `GET /v1/weather` with `ai=true` to retrieve multi-day forecast data plus an AI-generated weather narrative.
- **Temperature range** — displays minimum and maximum temperatures across the travel window with a colour-coded gradient bar.
- **Rain probability** — aggregated average probability shown as a percentage, progress bar, and Low / Moderate / High label.
- **AI weather summary** — verbatim AI narrative from the WeatherAI API rendered in a dedicated card.
- **Smart packing checklist** — rule-based recommendations generated from the forecast (temperature, rain, wind) displayed in a two-column chip grid.
- **Day-by-day timeline** — horizontally scrollable per-day cards showing high, low, rain probability, and weather emoji.
- **Responsive design** — works on mobile, tablet, and desktop.
- **Zero-reload UX** — Alpine.js handles form submission and result rendering without a page refresh.
- **Production-ready** — served by Gunicorn with WhiteNoise for static file handling; deployable to Render in minutes.

---

## Tech Stack

| Layer | Technology | Version |
|-------|-----------|---------|
| Backend framework | Django | 5.0.6 |
| Production WSGI server | Gunicorn | 22.0.0 |
| Static file serving | WhiteNoise | 6.7.0 |
| HTTP client | requests | 2.32.3 |
| Environment config | python-decouple | 3.8 |
| Frontend reactivity | Alpine.js (CDN) | 3.14 |
| CSS framework | Bootstrap (CDN) | 5.3 |
| Icons | Bootstrap Icons (CDN) | 1.11 |
| Fonts | Inter via Google Fonts (CDN) | — |
| Geocoding | OpenStreetMap Nominatim (free, no key) | — |
| Weather & AI data | WeatherAI API | v1 |

---

## Project Structure

```
WeatherAI_Assessment/
│
├── manage.py                         # Django management entry point
├── requirements.txt                  # Python dependencies (dev + production)
├── build.sh                          # Render build script (pip install + collectstatic)
├── render.yaml                       # Render infrastructure-as-code config
├── .env.example                      # Environment variable template
├── .gitignore
│
├── weather_advisor/                  # Django project configuration
│   ├── __init__.py
│   ├── settings.py                   # App settings — reads from .env via python-decouple
│   ├── urls.py                       # Root URL dispatcher
│   └── wsgi.py                       # WSGI entry point (used by Gunicorn in production)
│
└── advisor/                          # Main Django application
    ├── __init__.py
    ├── urls.py                       # App URL patterns
    ├── views.py                      # Request handlers (index page + /api/weather/ endpoint)
    ├── services.py                   # Business logic layer
    │   ├── geocode_city()            #   City name → lat/lon via Nominatim
    │   ├── get_weather_forecast()    #   WeatherAI API call with Bearer auth
    │   ├── generate_packing_list()   #   Rule-based packing recommendations
    │   └── process_travel_weather()  #   Response normalisation + aggregation
    ├── static/
    │   └── advisor/                  # Reserved for future local static assets
    └── templates/
        └── advisor/
            └── index.html            # Single-page template (Alpine.js + Bootstrap 5)
```

---

## Prerequisites

- **Python 3.12+**
- A **WeatherAI API key** — sign up at [weather-ai.co](https://weather-ai.co), then go to **Dashboard → API Keys** to generate a key. Keys are prefixed with `wai_`.
- **Git** and a **GitHub account** (required for Render deployment).
- Internet access during runtime (for geocoding and weather API calls).

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/godfrey-creat/WeatherAI_Assessment.git
cd WeatherAI_Assessment
```

**2. Create and activate a virtual environment**

```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Configuration

**1. Copy the environment template**

```bash
cp .env.example .env
```

**2. Open `.env` and fill in your values**

```ini
# A long random string used for Django's cryptographic signing
SECRET_KEY=your-long-random-secret-key-here

# Set to False in production
DEBUG=True

# Comma-separated list of allowed hostnames
ALLOWED_HOSTS=localhost,127.0.0.1

# Your WeatherAI API key (from https://weather-ai.co/dashboard → API Keys)
WEATHERAI_API_KEY=wai_your_api_key_here
```

> **Security note:** `.env` is listed in `.gitignore` and must never be committed. Your API key is read server-side only and is never exposed to the browser.

### Environment variable reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | insecure placeholder | Django secret key used for CSRF and session signing |
| `DEBUG` | No | `True` | Set to `False` in production |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated list of permitted hostnames |
| `WEATHERAI_API_KEY` | **Yes** | — | WeatherAI Bearer token (`wai_` prefix) |
| `DJANGO_SETTINGS_MODULE` | No (Render only) | auto-set | Set to `weather_advisor.settings` on Render |

---

## Running the Application

### Development

```bash
# Verify Django configuration
python manage.py check

# Start the development server
python manage.py runserver
```

Open **http://127.0.0.1:8000** in your browser.

### Production (local test with Gunicorn)

```bash
python manage.py collectstatic --noinput
gunicorn weather_advisor.wsgi:application --workers 2 --timeout 60
```

---

## How It Works

The application follows a clean five-step request flow:

```
User (browser)
     │
     │  POST /api/weather/  { city, start_date, end_date }
     ▼
advisor/views.py  ──── validates inputs ─────────────────────────────────────┐
     │                                                                        │
     │  geocode_city(city)                                                    │
     ▼                                                                        │
OpenStreetMap Nominatim                                                       │
     │  returns lat, lon, display_name                                        │  error →
     │                                                                        │  JSON 400/502
     │  get_weather_forecast(lat, lon, days)                                  │
     ▼                                                                        │
WeatherAI API  GET /v1/weather?lat=…&lon=…&days=…&ai=true                   │
     │  Authorization: Bearer wai_<key>                                       │
     │  returns forecast[], ai_summary, current{}                             │
     │                                                                        │
     │  process_travel_weather(data, start_date, end_date)                    │
     ▼                                                                        │
advisor/services.py                                                           │
     │  • filters forecast array to travel date window                        │
     │  • aggregates temp_min, temp_max, avg rain probability                 │
     │  • derives rain_label (Low / Moderate / High) + rain_color             │
     │  • calls generate_packing_list() with aggregated conditions            │
     │  • builds per-day forecast timeline                                    │
     │                                                                        │
     │  returns JSON payload ───────────────────────────────────────────────►│
     ▼
Alpine.js (browser)
     • renders result cards without page reload
     • smooth-scrolls to results section
```

### URL routes

| Method | Path | Handler | Description |
|--------|------|---------|-------------|
| `GET` | `/` | `views.index` | Renders the main HTML page |
| `POST` | `/api/weather/` | `views.get_weather` | Returns forecast JSON for a city + date range |

---

## API Integration

### Authentication

All requests to the WeatherAI API use **Bearer token** authentication:

```
Authorization: Bearer wai_<your_api_key>
```

This header is constructed in `advisor/services.py → get_weather_forecast()` and the key is read from the `WEATHERAI_API_KEY` environment variable. The key is never sent to or stored in the browser.

### Primary endpoint

```
GET https://api.weather-ai.co/v1/weather
```

**Query parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `lat` | float | Latitude (resolved from city name via Nominatim) |
| `lon` | float | Longitude (resolved from city name via Nominatim) |
| `days` | 1–7 | Forecast span (capped at 7 for Free plan) |
| `ai` | `true` | Include AI-generated weather narrative |
| `units` | `metric` | Return temperatures in °C |

**Example request:**

```bash
curl "https://api.weather-ai.co/v1/weather?lat=-1.2921&lon=36.8219&days=7&ai=true&units=metric" \
  -H "Authorization: Bearer wai_your_api_key_here"
```

### Geocoding

City names are resolved to coordinates using the free **OpenStreetMap Nominatim** API — no extra API key required:

```
GET https://nominatim.openstreetmap.org/search?q=Nairobi&format=json&limit=1
```

A descriptive `User-Agent` header is sent on every request as required by Nominatim's terms of service.

### Response normalisation

WeatherAI field names can vary slightly across API versions and plan tiers. `services.py` applies a multi-key fallback strategy to every field extraction:

```python
# Temperature — tries multiple key names before giving up
min_t = _pick(day, 'temp_min', 'min_temp', 'tempmin') or _nested(day, 'temp', 'min')

# AI summary — checks several possible root-level keys
ai_summary = (
    weather_data.get('ai_summary')
    or weather_data.get('ai')
    or weather_data.get('summary')
    or _nested(weather_data, 'current', 'ai_summary')
)
```

This pattern applies to `rain_probability`, `condition`, date fields, and the forecast array — making the integration resilient to response shape differences.

---

## Packing Logic

Recommendations are generated in `advisor/services.py → generate_packing_list()` using a rule-based system applied to the aggregated forecast conditions across the full travel window:

| Condition | Threshold | Items added |
|-----------|-----------|-------------|
| Very cold | min temp < 5°C | Heavy winter coat, Thermal underlayers, Gloves & scarf, Insulated boots |
| Cold | min temp 5–12°C | Medium-weight jacket, Warm sweater or fleece, Layered clothing |
| Cool | min temp 12–18°C | Light jacket or cardigan, Layered clothing |
| Warm | min temp ≥ 18°C | Light breathable clothing, Short-sleeve shirts |
| Hot | max temp > 30°C | Sunscreen SPF 50+, Sunglasses, Wide-brim hat, Cooling towel |
| Warm-sunny | max temp 25–30°C | Sunscreen SPF 30+, Sunglasses, Cap |
| High rain | avg probability > 60% | Waterproof rain jacket, Compact umbrella, Quick-dry clothing, Waterproof bag cover |
| Moderate rain | avg probability 35–60% | Compact umbrella, Light rain jacket |
| Low rain | avg probability 15–35% | Foldable umbrella (just in case) |
| Always | — | Comfortable walking shoes, Portable power bank, Travel first-aid essentials |

Items are deduplicated (insertion-order preserved) and returned in priority order.

---

## Error Handling

The `/api/weather/` endpoint returns structured JSON for every failure case:

| Scenario | HTTP status | Message returned |
|----------|-------------|-----------------|
| Missing city | `400` | "Please enter a destination city." |
| Missing dates | `400` | "Please provide both departure and return dates." |
| Invalid date format | `400` | "Invalid date format. Expected YYYY-MM-DD." |
| Return date in the past | `400` | "Return date must be today or in the future." |
| Start date after end date | `400` | "Departure date must be on or before the return date." |
| City not found | `400` | "Location "XYZ" not found. Please check the city name." |
| API key not set | `400` | "WEATHERAI_API_KEY is not set. Please add it to your .env file." |
| Invalid / expired API key | `400` | "Invalid or expired API key. Please check your WEATHERAI_API_KEY." |
| Monthly quota exceeded | `400` | "Monthly API quota exceeded. Please upgrade your WeatherAI plan." |
| Geocoding service failure | `502` | "Geocoding failed: …" |
| WeatherAI service failure | `502` | "Failed to fetch weather data: …" |

All errors are surfaced in the UI as an inline alert directly above the submit button — no page reload required.

---

## Deployment

The application is configured for one-click deployment to **[Render](https://render.com)** using the included `render.yaml` and `build.sh` files.

### How deployment works

| File | Role |
|------|------|
| `build.sh` | Render's build step — runs `pip install` then `collectstatic` |
| `render.yaml` | Declares the service type, build/start commands, and environment variables |
| `gunicorn` | Production WSGI server that replaces Django's development `runserver` |
| `whitenoise` | Serves compressed static files directly from Django — no separate CDN or nginx needed |
| `STATIC_ROOT` | Directory where `collectstatic` gathers all static assets for WhiteNoise to serve |

### Step-by-step guide

**1. Push your code to GitHub**

```bash
git push origin main
```

**2. Create a Render account**

Go to [render.com](https://render.com) → sign up with your GitHub account → authorise Render to access your repositories.

**3. Create a new Web Service**

In the Render dashboard: **New +** → **Web Service** → **Connect a repository** → select `WeatherAI_Assessment` → **Connect**.

**4. Confirm service settings**

Render auto-detects `render.yaml`. Verify these values are set:

| Setting | Value |
|---------|-------|
| Name | `weatherai-travel-advisor` |
| Region | Closest to your users (e.g. Frankfurt for Africa / Europe) |
| Branch | `main` |
| Runtime | `Python 3` |
| Build Command | `./build.sh` |
| Start Command | `gunicorn weather_advisor.wsgi:application --workers 2 --timeout 60` |
| Instance Type | `Free` |

**5. Set environment variables**

In the **Environment** section, add the following key/value pairs:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Click **Generate** — Render creates a cryptographically secure random value |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `.onrender.com` |
| `DJANGO_SETTINGS_MODULE` | `weather_advisor.settings` |
| `WEATHERAI_API_KEY` | `wai_your_actual_key_here` ← paste your real key here |

> `WEATHERAI_API_KEY` must be entered manually. All other values can be copied exactly as shown above.

**6. Deploy**

Click **Create Web Service**. Render will clone the repo, run `build.sh`, then start Gunicorn. The build log streams live. A successful deploy ends with:

```
==> Your service is live 🎉
```

Your live URL will be: `https://weatherai-travel-advisor.onrender.com`

**7. Auto-deploy on push**

`render.yaml` sets `autoDeploy: true`. Every subsequent `git push origin main` triggers a new deploy automatically.

### Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `DisallowedHost at /` | Render domain not in `ALLOWED_HOSTS` | Set `ALLOWED_HOSTS` to `.onrender.com` in Render env vars |
| `Invalid or expired API key` | Wrong key value | Re-check `WEATHERAI_API_KEY` in Render → Environment |
| `Application error` (500) | Missing env var or import error | Open **Logs** tab in Render dashboard for the exact traceback |
| Static files return 404 | `collectstatic` didn't run | Confirm `build.sh` completed without error in the build log |
| App sleeps after inactivity | Free plan behaviour | Free instances spin down after 15 min idle; first request after sleep takes ~30 s to respond |

---

## WeatherAI Plan Limits

This application defaults to the **Free plan**, which caps forecasts at **7 days**.

| Plan | Monthly requests | AI requests | Max forecast days |
|------|-----------------|-------------|-------------------|
| Free | 1,000 | 200 | 7 |
| Pro | 50,000 | 10,000 | 14 |
| Scale | 500,000 | 100,000 | 16 |

To unlock longer forecasts, upgrade your plan on the WeatherAI dashboard and increase the `days_needed` cap in `advisor/views.py` (currently `min(days_until_end, 7)`).

---

*Built with the WeatherAI API · Django · Gunicorn · WhiteNoise · Alpine.js · Bootstrap 5*
