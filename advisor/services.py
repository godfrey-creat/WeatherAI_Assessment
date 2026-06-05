import requests
from datetime import datetime, date
from decouple import config

WEATHERAI_API_KEY = config('WEATHERAI_API_KEY', default='')
WEATHERAI_BASE_URL = 'https://api.weather-ai.co'


def geocode_city(city_name: str) -> tuple[float, float, str]:
    """Convert a city name to lat/lon via OpenStreetMap Nominatim (no key required)."""
    url = 'https://nominatim.openstreetmap.org/search'
    params = {'q': city_name, 'format': 'json', 'limit': 1}
    headers = {'User-Agent': 'WeatherAI-TravelAdvisor/1.0 (assessment-project)'}

    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()

    results = resp.json()
    if not results:
        raise ValueError(f"Location \"{city_name}\" not found. Please check the city name and try again.")

    r = results[0]
    return float(r['lat']), float(r['lon']), r.get('display_name', city_name)


def get_weather_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Fetch weather forecast from WeatherAI API with AI summary included."""
    if not WEATHERAI_API_KEY:
        raise ValueError("WEATHERAI_API_KEY is not set. Please add it to your .env file.")

    url = f'{WEATHERAI_BASE_URL}/v1/weather'
    params = {
        'lat': lat,
        'lon': lon,
        'days': days,
        'ai': 'true',
        'units': 'metric',
    }
    headers = {'Authorization': f'Bearer {WEATHERAI_API_KEY}'}

    resp = requests.get(url, params=params, headers=headers, timeout=15)

    if resp.status_code == 401:
        raise ValueError("Invalid or expired API key. Please check your WEATHERAI_API_KEY.")
    if resp.status_code == 429:
        raise ValueError("Monthly API quota exceeded. Please upgrade your WeatherAI plan.")
    if resp.status_code == 403:
        raise ValueError("Your plan does not support this feature.")

    resp.raise_for_status()
    return resp.json()


# ── helpers ──────────────────────────────────────────────────────────────────

def _pick(d: dict, *keys, default=None):
    """Return the first non-None value found among the given keys."""
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return default


def _nested(d, *path, default=None):
    """Safely traverse a nested dict path."""
    for key in path:
        if not isinstance(d, dict):
            return default
        d = d.get(key, default)
    return d


def _to_pct(val) -> float:
    """Normalise rain probability to 0-100 range."""
    v = float(val)
    return v * 100 if v <= 1.0 else v


# ── packing logic ─────────────────────────────────────────────────────────────

def generate_packing_list(min_temp: float | None, max_temp: float | None, avg_rain: float) -> list[str]:
    """Rule-based packing suggestions derived from forecast conditions."""
    items: list[str] = []

    if min_temp is None:
        min_temp = 20.0
    if max_temp is None:
        max_temp = 25.0

    # Cold layers
    if min_temp < 5:
        items += ["Heavy winter coat", "Thermal underlayers", "Warm gloves & scarf", "Insulated boots"]
    elif min_temp < 12:
        items += ["Medium-weight jacket", "Warm sweater or fleece", "Layered clothing"]
    elif min_temp < 18:
        items += ["Light jacket or cardigan", "Layered clothing"]
    else:
        items += ["Light, breathable clothing", "Short-sleeve shirts"]

    # Hot weather extras
    if max_temp > 30:
        items += ["Sunscreen (SPF 50+)", "Sunglasses", "Wide-brim hat", "Cooling towel"]
    elif max_temp > 25:
        items += ["Sunscreen (SPF 30+)", "Sunglasses", "Cap or hat"]

    # Rain gear
    if avg_rain > 60:
        items += ["Waterproof rain jacket", "Compact umbrella", "Quick-dry clothing", "Waterproof bag cover"]
    elif avg_rain > 35:
        items += ["Compact travel umbrella", "Light rain jacket"]
    elif avg_rain > 15:
        items += ["Foldable umbrella (just in case)"]

    # Always useful
    items += ["Comfortable walking shoes", "Portable power bank", "Travel first-aid essentials"]

    # Deduplicate while preserving order
    seen: set[str] = set()
    return [x for x in items if not (x in seen or seen.add(x))]  # type: ignore[func-returns-value]


# ── response processing ───────────────────────────────────────────────────────

def _parse_date(val) -> date | None:
    """Parse a date value that may be a string, int (unix ts), or None."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return date.fromtimestamp(int(val))
        return datetime.strptime(str(val)[:10], '%Y-%m-%d').date()
    except (ValueError, OSError, TypeError):
        return None


def process_travel_weather(
    weather_data: dict,
    start_date: date,
    end_date: date,
    location_name: str,
) -> dict:
    """Transform raw WeatherAI response into travel-advisory payload."""

    # ── AI summary ────────────────────────────────────────────────────────────
    ai_summary = (
        weather_data.get('ai_summary')
        or weather_data.get('ai')
        or weather_data.get('summary')
        or _nested(weather_data, 'current', 'ai_summary')
        or _nested(weather_data, 'data', 'ai_summary')
    )
    if isinstance(ai_summary, dict):
        ai_summary = ai_summary.get('text') or ai_summary.get('summary') or ''
    ai_summary = str(ai_summary).strip() if ai_summary else (
        "Conditions look typical for this destination and time of year. "
        "Check local sources for real-time updates before your trip."
    )

    # ── Forecast array ────────────────────────────────────────────────────────
    forecast: list[dict] = (
        weather_data.get('forecast')
        or weather_data.get('daily')
        or weather_data.get('days')
        or _nested(weather_data, 'data', 'forecast')
        or []
    )

    today = date.today()

    # Filter to travel date range; fall back to offset-slice if dates are absent
    travel_days: list[dict] = []
    has_dates = False

    for day in forecast:
        raw_date = _pick(day, 'date', 'dt', 'datetime', 'time')
        day_date = _parse_date(raw_date)
        if day_date is not None:
            has_dates = True
            if start_date <= day_date <= end_date:
                travel_days.append(day)
        else:
            travel_days.append(day)

    if not travel_days or not has_dates:
        offset = max((start_date - today).days, 0)
        length = (end_date - start_date).days + 1
        travel_days = forecast[offset: offset + length] or forecast

    # ── Aggregate stats ───────────────────────────────────────────────────────
    temps_min: list[float] = []
    temps_max: list[float] = []
    rain_probs: list[float] = []

    for day in travel_days:
        min_t = _pick(day, 'temp_min', 'min_temp', 'tempmin') or _nested(day, 'temp', 'min')
        max_t = _pick(day, 'temp_max', 'max_temp', 'tempmax') or _nested(day, 'temp', 'max')
        rain  = _pick(day, 'rain_probability', 'precipitation_probability', 'pop', 'precip_probability')

        if min_t is not None:
            temps_min.append(float(min_t))
        if max_t is not None:
            temps_max.append(float(max_t))
        if rain is not None:
            rain_probs.append(_to_pct(rain))

    # Fall back to current conditions if daily forecast had no temps
    current = weather_data.get('current', {}) or {}
    if not temps_min:
        temp = _pick(current, 'temp', 'temperature')
        if temp is not None:
            t = float(temp)
            temps_min, temps_max = [t - 4], [t + 4]

    temp_min  = round(min(temps_min)) if temps_min else None
    temp_max  = round(max(temps_max)) if temps_max else None
    avg_rain  = round(sum(rain_probs) / len(rain_probs)) if rain_probs else 0

    if avg_rain > 60:
        rain_label, rain_color = "High", "danger"
    elif avg_rain > 35:
        rain_label, rain_color = "Moderate", "warning"
    else:
        rain_label, rain_color = "Low", "success"

    # ── Per-day forecast for timeline display ─────────────────────────────────
    daily_forecast: list[dict] = []
    for day in travel_days[:7]:
        raw_date = _pick(day, 'date', 'dt', 'datetime', 'time')
        day_date = _parse_date(raw_date)
        label = day_date.strftime('%a, %b %d') if day_date else 'Day'

        min_t = _pick(day, 'temp_min', 'min_temp', 'tempmin') or _nested(day, 'temp', 'min')
        max_t = _pick(day, 'temp_max', 'max_temp', 'tempmax') or _nested(day, 'temp', 'max')
        rain  = _pick(day, 'rain_probability', 'precipitation_probability', 'pop')
        cond  = _pick(day, 'condition', 'description', 'weather', 'summary', 'text')

        if isinstance(cond, list):
            cond = cond[0].get('description', '') if cond else ''
        if isinstance(cond, dict):
            cond = cond.get('description', '') or cond.get('main', '')

        daily_forecast.append({
            'date':     label,
            'temp_min': round(float(min_t)) if min_t is not None else None,
            'temp_max': round(float(max_t)) if max_t is not None else None,
            'rain':     round(_to_pct(rain))  if rain is not None else None,
            'condition': str(cond).title()    if cond else None,
        })

    packing_list = generate_packing_list(temp_min, temp_max, avg_rain)
    city_short   = location_name.split(',')[0].strip()

    return {
        'location':        location_name,
        'city':            city_short,
        'start_date':      start_date.strftime('%b %d'),
        'end_date':        end_date.strftime('%b %d, %Y'),
        'duration':        (end_date - start_date).days + 1,
        'temp_min':        temp_min,
        'temp_max':        temp_max,
        'rain_probability': avg_rain,
        'rain_label':      rain_label,
        'rain_color':      rain_color,
        'ai_summary':      ai_summary,
        'packing_list':    packing_list,
        'daily_forecast':  daily_forecast,
    }
