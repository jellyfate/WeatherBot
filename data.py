places = {
    'еньков': {
        'coordinates':  [51.470473, 31.375846],
        'today_db':     'enkov_today',
        'history_db':   'enkov_history'
    },
    'нефтебаза':  {
        'coordinates':  [51.463262, 31.269598],
        'today_db':     'neftebaza_today',
        'history_db':   'neftebaza_history'
    },
}

weather = {
    'current': {
        'OpenWeatherMap.org': "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid=b7f629081f4f576144361ffc63ee8fad",
        'DarkSky.net': "https://api.darksky.net/forecast/cfc279055ab44b7e0c7084262d668ca4/{},{}?units=si&exclude=minutely,hourly,daily,alerts,flags",
        'APIXU.com': "http://api.apixu.com/v1/current.json?key=3cc653a5a4474dcd828182331193005&q={},{}",
    },
    'forecast': {
        'OpenWeatherMap.org': "https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid=b7f629081f4f576144361ffc63ee8fad",
        'DarkSky.net': "https://api.darksky.net/forecast/cfc279055ab44b7e0c7084262d668ca4/{},{}?units=si",
        'APIXU.com': "http://api.apixu.com/v1/forecast.json?key=3cc653a5a4474dcd828182331193005&q={},{}",
    }
}
