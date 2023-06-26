import json
import requests
import datetime
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import City
from .forms import CityForm
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def save_weather_details(request):
    if request.method == 'POST':
        # Process the weather details and save them to the database
        # Retrieve the data from the request.POST dictionary
        city = request.POST.get('city')
        temperature = request.POST.get('temperature')
        description = request.POST.get('description')
        latitude = request.POST.get('latitude')
        longitude = request.POST.get('longitude')

        # Save the weather details to the database using the City model
        City.objects.create(name=city, temperature=temperature, description=description, latitude=latitude,
                            longitude=longitude)

        # Return a response indicating the success or failure of the operation
        return HttpResponse('Weather details saved successfully.')
    else:
        return HttpResponse('Invalid request method.')


def index(request):
    url = 'http://api.openweathermap.org/data/2.5/weather?q={}&units=imperial&appid=38f57cbac624820134a7b8b26f77247c'
    url1 = 'https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid=38f57cbac624820134a7b8b26f77247c'
    city_list = City.objects.all()
    paginator = Paginator(city_list, 3)
    page_number = request.GET.get('page')
    cities = paginator.get_page(page_number)

    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name']
            if City.objects.filter(name=city_name).exists():
                error_message = 'City already exists in the database.'
                context = {'form': form, 'error_message': error_message, 'cities': cities}
                return render(request, 'weather/home.html', context)

            try:
                city_weather = requests.get(url.format(city_name)).json()
            except (json.JSONDecodeError, requests.RequestException):
                error_message = 'Error retrieving weather data. Please try again later.'
                context = {'form': form, 'error_message': error_message, 'cities': cities}
                return render(request, 'weather/home.html', context)

            if city_weather.get('cod') == '404':
                error_message = 'City not found. Please enter a valid city name.'
                context = {'form': form, 'error_message': error_message, 'cities': cities}
                return render(request, 'weather/home.html', context)

            form.save()

    form = CityForm()
    weather_data = []

    for city in cities:
        city_weather = requests.get(url.format(city.name)).json()
        if city_weather.get('cod') == '404':
            continue

        latitude = city_weather['coord']['lat']
        longitude = city_weather['coord']['lon']

        weather = {
            'city': city.name,
            'temperature': city_weather['main']['temp'],
            'description': city_weather['weather'][0]['description'],
            'icon': city_weather['weather'][0]['icon'],
            'latitude': latitude,
            'longitude': longitude
        }

        # Retrieve the hourly forecast data
        city_weather1 = requests.get(url1.format(latitude, longitude)).json()
        hourly_forecast = city_weather1.get('list', [])[:3]  # Get the first 5 hourly forecasts

        # Process and format the hourly forecast data as needed
        hourly_data = []
        for forecast in hourly_forecast:
            timestamp = forecast['dt']
            temperature = round(forecast['main']['temp'], 1)
            description = forecast['weather'][0]['description'].capitalize()
            icon = forecast['weather'][0]['icon']

            forecast_datetime = datetime.datetime.fromtimestamp(timestamp)
            formatted_datetime = forecast_datetime.strftime('%Y-%m-%d %H:%M:%S')

            forecast_data = {
                'datetime': formatted_datetime,
                'temperature': temperature,
                'description': description,
                'icon': icon
            }
            hourly_data.append(forecast_data)

        weather['hourly_forecast'] = hourly_data

        weather_data.append(weather)

    context = {'weather_data': json.dumps(weather_data), 'form': form, 'cities': cities, 'weather': weather_data}
    return render(request, 'weather/home.html', context)


def delete_city(request):
    if request.method == 'POST':
        city_name = request.POST.get('city_name')

        # Retrieve the city object(s) with the matching name
        cities = City.objects.filter(name=city_name)

        # Delete the city object(s) from the database
        cities.delete()

        # Redirect to the index page or any other appropriate page
        return HttpResponse("deleted.... kindly go back to the main page")

    # Handle the GET request or any other cases
    return render(request, 'weather/home.html')

