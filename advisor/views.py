import json
from datetime import datetime, date

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .services import geocode_city, get_weather_forecast, process_travel_weather


def index(request):
    return render(request, 'advisor/index.html')


@require_http_methods(["POST"])
def get_weather(request):
    # Parse JSON body
    try:
        payload = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request format.'}, status=400)

    city          = (payload.get('city') or '').strip()
    start_date_str = (payload.get('start_date') or '').strip()
    end_date_str   = (payload.get('end_date') or '').strip()

    # Validate inputs
    if not city:
        return JsonResponse({'error': 'Please enter a destination city.'}, status=400)
    if not start_date_str or not end_date_str:
        return JsonResponse({'error': 'Please provide both departure and return dates.'}, status=400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date   = datetime.strptime(end_date_str,   '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format. Expected YYYY-MM-DD.'}, status=400)

    today = date.today()

    if start_date > end_date:
        return JsonResponse({'error': 'Departure date must be on or before the return date.'}, status=400)
    if end_date < today:
        return JsonResponse({'error': 'Return date must be today or in the future.'}, status=400)

    # How many forecast days we need (capped at Free-plan max of 7)
    days_until_end = (end_date - today).days + 1
    days_needed    = max(min(days_until_end, 7), 1)

    # Geocode
    try:
        lat, lon, location_name = geocode_city(city)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({'error': f'Geocoding failed: {exc}'}, status=502)

    # Fetch forecast
    try:
        weather_data = get_weather_forecast(lat, lon, days_needed)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)
    except Exception as exc:
        return JsonResponse({'error': f'Failed to fetch weather data: {exc}'}, status=502)

    result = process_travel_weather(weather_data, start_date, end_date, location_name)
    return JsonResponse(result)
