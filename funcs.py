import urllib.request, json

from data import *

def json_to_dict(link):
     with urllib.request.urlopen( link ) as url:
        return json.loads(url.read().decode())


def farenhToCelc(farenhT):
        return round((farenhT - 32) * (5/9), 1) 


def unknown_location_check(location, update):
    if location not in locations.keys():
        update.message.reply_text("Не найдено! Доступные локации: " 
        + ", ".join(list(locations.keys())) + " (чувствительно к регистру!)")
        return True 


# return current rain data in custom location among 3 services
def rain(location):
    data = {}    
    for key, value in current_weather.items():
        # take api links, insert into the coordinates taken from location list by key
        data[key] = json_to_dict(value.format(locations[location][0], locations[location][1]))
    # openweather JSON have no "rain" key, when there are no rain in location
    own_rain = data["OpenWeatherMap.org"]["rain"]["3h"] if "rain" in data["OpenWeatherMap.org"] else 0  
    return own_rain, data["DarkSky.net"]["currently"]["precipIntensity"], data["APIXU.com"]["current"]["precip_mm"]


