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

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend framework | Django 5.0 |
| HTTP client | requests 2.32 |
| Environment config | python-decouple 3.8 |
| Frontend reactivity | Alpine.js 3.14 (CDN) |
| CSS framework | Bootstrap 5.3 (CDN) |
| Icons | Bootstrap Icons 1.11 (CDN) |
| Fonts | Inter — Google Fonts (CDN) |
| Geocoding | OpenStreetMap Nominatim (free, no key) |
| Weather & AI data | WeatherAI API (`https://api.weather-ai.co`) |

---

## Project Structure

```
WeatherAI_Assessment/
│
├── manage.py                         # Django management entry point
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variable template
├── .gitignore
│
├── weather_advisor/                  # Django project configuration
│   ├── __init__.py
│   ├── settings.py                   # App settings (reads from .env)
│   ├── urls.py                       # Root URL dispatcher
│   └── wsgi.py
│
└── advisor/                          # Main Django application
    ├── __init__.py
    ├── urls.py                       # App URL patterns
    ├── views.py                      # Request handlers (index + weather API)
    ├── services.py                   # Business logic layer
    │   ├── geocode_city()            #   City name → lat/lon via Nominatim
    │   ├── get_weather_forecast()    #   WeatherAI API call
    │   ├── generate_packing_list()   #   Rule-based packing recommendations
    │   └── process_travel_weather()  #   Response normalisation + aggregation
    ├── static/
    │   └── advisor/                  # (reserved for future static assets)
    └── templates/
        └── advisor/
            └── index.html            # Single-page template (Alpine.js + Bootstrap 5)
```

---

## Prerequisites

- **Python 3.12+**
- A **WeatherAI API key** — sign up at [weather-ai.co](https://weather-ai.co), then go to **Dashboard → API Keys** to generate a key. Keys are prefixed `wai_`.
- Internet access (for geocoding and weather API calls during runtime).

---

## Installation

**1. Clone the repository**

```bash
git clone <repository-url>
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
SECRET_KEY=your-secret-key-here

# Set to False in production
DEBUG=True

# Comma-separated list of allowed hostnames
ALLOWED_HOSTS=localhost,127.0.0.1

# Your WeatherAI API key (from https://weather-ai.co/dashboard → API Keys)
WEATHERAI_API_KEY=wai_your_api_key_here
```

> **Security note:** The `.env` file is listed in `.gitignore` and must never be committed to version control. Your API key is only stored locally and is never exposed to the browser.

### Environment variable reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | Yes | insecure placeholder | Django secret key for session/CSRF signing |
| `DEBUG` | No | `True` | Enable Django debug mode |
| `ALLOWED_HOSTS` | No | `localhost,127.0.0.1` | Comma-separated hostnames |
| `WEATHERAI_API_KEY` | **Yes** | — | WeatherAI Bearer token (prefix `wai_`) |

---

## Running the Application

```bash
# Confirm Django is configured correctly
python manage.py check

# Start the development server
python manage.py runserver
```

Open your browser at **http://127.0.0.1:8000**

---

## How It Works

The application follows a clean five-step request flow:

```
User (browser)
     │
     │  POST /api/weather/  { city, start_date, end_date }
     ▼
advisor/views.py  ──── validates inputs ────────────────────────────────────┐
     │                                                                       │
     │  geocode_city(city)                                                   │
     ▼                                                                       │
OpenStreetMap Nominatim                                                      │
     │  returns lat, lon, display_name                                       │ error →
     │                                                                       │ JSON 400
     │  get_weather_forecast(lat, lon, days)                                 │
     ▼                                                                       │
WeatherAI API  GET /v1/weather?lat=…&lon=…&days=…&ai=true                  │
     │  Authorization: Bearer wai_<key>                                      │
     │  returns forecast[], ai_summary, current{}                            │
     │                                                                       │
     │  process_travel_weather(data, start_date, end_date)                   │
     ▼                                                                       │
advisor/services.py                                                          │
     │  • filters forecast to travel date window                             │
     │  • aggregates temp_min, temp_max, avg rain probability                │
     │  • derives rain_label + rain_color                                    │
     │  • calls generate_packing_list()                                      │
     │  • builds per-day timeline                                            │
     │                                                                       │
     │  returns JSON payload ──────────────────────────────────────────────►│
     ▼
Alpine.js (browser)
     • renders results without page reload
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

All requests to the WeatherAI API are authenticated using a **Bearer token**:

```
Authorization: Bearer wai_<your_api_key>
```

This header is set in `advisor/services.py → get_weather_forecast()` and read from the `WEATHERAI_API_KEY` environment variable. The key is never sent to the browser.

### Primary endpoint used

```
GET https://api.weather-ai.co/v1/weather
```

**Query parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `lat` | float | Latitude (resolved from city name) |
| `lon` | float | Longitude (resolved from city name) |
| `days` | 1–7 | Number of forecast days (capped at 7 for Free plan) |
| `ai` | `true` | Include AI-generated weather narrative |
| `units` | `metric` | Temperature in °C |

**Example request (curl):**

```bash
curl "https://api.weather-ai.co/v1/weather?lat=-1.2921&lon=36.8219&days=7&ai=true&units=metric" \
  -H "Authorization: Bearer wai_your_api_key_here"
```

### Geocoding (no additional key required)

City names are resolved to coordinates using the **OpenStreetMap Nominatim** public API:

```
GET https://nominatim.openstreetmap.org/search?q=Nairobi&format=json&limit=1
```

A `User-Agent` header is included as required by Nominatim's terms of service.

### Response normalisation

Because WeatherAI may return field names that vary slightly across plan tiers, `services.py` uses a multi-key fallback strategy for every field:

```python
# Example: extracting minimum temperature with fallbacks
min_t = _pick(day, 'temp_min', 'min_temp', 'tempmin') or _nested(day, 'temp', 'min')
```

The same pattern applies to `ai_summary`, `rain_probability`, `condition`, and date fields — making the integration resilient to minor API response variations.

---

## Packing Logic

Packing recommendations are generated in `generate_packing_list()` using a rule-based system applied to the aggregated forecast for the travel window:

| Condition | Threshold | Items added |
|-----------|-----------|-------------|
| Very cold | min temp < 5°C | Heavy winter coat, Thermal underlayers, Gloves & scarf, Insulated boots |
| Cold | min temp 5–12°C | Medium-weight jacket, Fleece, Layered clothing |
| Cool | min temp 12–18°C | Light jacket or cardigan, Layered clothing |
| Warm | min temp ≥ 18°C | Light breathable clothing, Short-sleeve shirts |
| Hot | max temp > 30°C | Sunscreen SPF 50+, Sunglasses, Wide-brim hat, Cooling towel |
| Warm-sunny | max temp 25–30°C | Sunscreen SPF 30+, Sunglasses, Cap |
| High rain | avg probability > 60% | Waterproof rain jacket, Compact umbrella, Quick-dry clothing, Bag cover |
| Moderate rain | avg probability 35–60% | Compact umbrella, Light rain jacket |
| Low rain | avg probability 15–35% | Foldable umbrella |
| Always | — | Comfortable walking shoes, Portable power bank, First-aid essentials |

Items are deduplicated and returned in priority order.

---

## Error Handling

The API endpoint returns structured JSON errors for all failure modes:

| Scenario | HTTP status | Example message |
|----------|-------------|-----------------|
| Missing fields | `400` | "Please enter a destination city." |
| Invalid date format | `400` | "Invalid date format. Expected YYYY-MM-DD." |
| End date in the past | `400` | "Return date must be today or in the future." |
| City not found | `400` | "Location "XYZ" not found. Please check the city name." |
| Invalid / expired API key | `400` | "Invalid or expired API key. Please check your WEATHERAI_API_KEY." |
| Monthly quota exceeded | `400` | "Monthly API quota exceeded. Please upgrade your WeatherAI plan." |
| Geocoding service failure | `502` | "Geocoding failed: …" |
| WeatherAI service failure | `502` | "Failed to fetch weather data: …" |

All errors are surfaced in the UI as an inline red alert above the submit button.

---

## WeatherAI Plan Limits

This application is built for the **Free plan** by default. The forecast is capped at **7 days** to stay within the free tier.

| Plan | Monthly requests | AI requests | Max forecast days |
|------|-----------------|-------------|-------------------|
| Free | 1,000 | 200 | 7 |
| Pro | 50,000 | 10,000 | 14 |
| Scale | 500,000 | 100,000 | 16 |

To unlock longer forecasts, upgrade your plan on the WeatherAI dashboard and increase the `days_needed` cap in `advisor/views.py`.

---

*Built with the WeatherAI API · Django · Alpine.js · Bootstrap 5*
