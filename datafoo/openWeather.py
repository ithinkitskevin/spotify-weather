import json
import requests

# Weather App Id
WEATHER_APP_ID = "decca2633db37406aa20f5fba1267d59"

# OpenWeatherMap URLS
WEATHER_API_BASE_URL = "http://api.openweathermap.org/data"
WEATHER_API_VERSION = "2.5"
WEATHER_API_URL = "{}/{}/weather".format(WEATHER_API_BASE_URL, WEATHER_API_VERSION)

def getWeatherFromZip(zipcode):
    state = 'us'
    weather_api_endpoint = "{}?zip={},{}&appid={}".format(WEATHER_API_URL,zipcode,state,WEATHER_APP_ID)
    weather_response = requests.get(weather_api_endpoint)
    weather_data = json.loads(weather_response.text)

    return weather_data