 #!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import json
import urllib.request
import datetime
import telegram

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

locations = {   
    'еньков': [51.470473, 31.375846], 
    'кск':    [51.463262, 31.269598],
}

current_weather = {   
    'OpenWeatherMap.org': "https://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid=b7f629081f4f576144361ffc63ee8fad", 
    'DarkSky.net':  "https://api.darksky.net/forecast/cfc279055ab44b7e0c7084262d668ca4/{},{}",
    'APIXU.com': "http://api.apixu.com/v1/current.json?key=3cc653a5a4474dcd828182331193005&q={},{}",
}

forecast = {   
    'OpenWeatherMap.org': "https://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid=b7f629081f4f576144361ffc63ee8fad", 
    'DarkSky.net':  "https://api.darksky.net/forecast/cfc279055ab44b7e0c7084262d668ca4/{},{}",
    'APIXU.com': "http://api.apixu.com/v1/forecast.json?key=3cc653a5a4474dcd828182331193005&q={},{}",
}


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


def start(bot, update): 
    update.message.reply_text('Hi!')

def help(bot, update):
    update.message.reply_text('Help!')


def echo(bot, update, args):
    if unknown_location_check(args[0], update): return 
    reply = "Местоположение: " + args[0].title() + "\n"
               
    data = json_to_dict(forecast["DarkSky.net"].format(locations[args[0]][0], locations[args[0]][1]))
    current = data['currently']
    # data = {}    
    # for key, value in current_weather.items():
    #     # take api links, insert into the coordinates taken from location list by key
    #     data[key] = json_to_dict(value.format(locations[args[0]][0], locations[args[0]][1]))

    current['time'] = datetime.datetime.fromtimestamp(current['time'])
    current['temperature'] = str(farenhToCelc(current['temperature'])) + ' C'
    current['apparentTemperature'] = str(farenhToCelc(current['apparentTemperature'])) + ' C'
    current['dewPoint'] = str(farenhToCelc(current['dewPoint'])) + ' C'
    current['humidity'] = str(current['humidity'] * 100) + ' %'
    current['windSpeed'] = str(current['windSpeed']) + ' m/s'
    current['pressure'] = str(current['pressure']) + ' hps'

    for key,val in current.items():
        reply += f"<code>{key}</code> :  {val}\n"

    chatId = update.message.chat.id
    bot.send_message(chatId, text = reply, parse_mode=telegram.ParseMode.HTML)


def rain_now(bot, update, args):
    if unknown_location_check(args[0], update): return 
    message = "Местоположение: " + args[0].title() + "\n"

    data = {}    
    for key, value in current_weather.items():
        # take api links, insert into the coordinates taken from location list by key
        data[key] = json_to_dict(value.format(locations[args[0]][0], locations[args[0]][1]))
        
    # openweather JSON have no "rain" key, when there are no rain in location
    if "rain" in data["OpenWeatherMap.org"]:
        own_rain = data["OpenWeatherMap.org"]["rain"]["3h"]
    else:
        own_rain = 0    

    template = "{0} : осадки {1} mm \n"
    message += template.format("OpenWeatherMap.org", own_rain)
    message += template.format("DarkSky.net", data["DarkSky.net"]["currently"]["precipIntensity"])
    message += template.format("APIXU.com", data["APIXU.com"]["current"]["precip_mm"])
    update.message.reply_text(message)


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("812215138:AAENIsKiCloqVsdZlrEvCcPuEUT3OgMSBf8")

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("погода", echo, pass_args=True))
    dp.add_handler(CommandHandler("дождь", rain_now, pass_args=True))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, rain_now))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
