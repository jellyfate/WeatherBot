 #!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging, telegram, datetime, sched, time
from threading import Thread
import sqlite3 as sql
from funcs import *

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# db connection
try:
    connection = sql.connect('log.db')
    cursor = connection.cursor()
except sql.Error as e:
    print("Error {}:".format(e.args[0]))
# finally:
#     if connection:
#         connection.close()

# hourly saving rain data
def daily_log(sc): 
    for location in locations.keys():
        owm, darksky, apixu = rain(location)
        # print('INSERT INTO {} VALUES("{}",{},{},{});'.format(
        #     today_db[location], datetime.date.today(), owm, darksky, apixu))
        print(datetime.datetime.now())
        cursor.execute('INSERT INTO {} VALUES("{}",{},{},{});'.format(
            today_db[location], datetime.datetime.now(), owm, darksky, apixu))
        connection.commit()
    scheduler.enter(3600, 1, daily_log, (sc,))

# sheduler to hourly launch daily_log function
scheduler = sched.scheduler(time.time, time.sleep)
scheduler.enter(3600, 1, daily_log, (scheduler,))


def start(bot, update): 
    update.message.reply_text('Hi!')

def help(bot, update):
    update.message.reply_text('Help!')

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def echo(bot, update, args):
    if unknown_location_check(args[0], update): return 
    reply = "Местоположение: " + args[0].title() + "\n"
               
    data = json_to_dict(forecast["DarkSky.net"].format(locations[args[0]][0], locations[args[0]][1]))
    current = data['currently']

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


# send "rain" message
def rain_now(bot, update, args):
    if unknown_location_check(args[0], update): return     
    # get rain data and pack it do dictionary
    rain_data = dict(zip(current_weather.keys(), rain(args[0])))

    reply = "Местоположение: " + args[0].title() + "\n"
    for service in current_weather.keys():
        reply += "{0} : осадки {1} mm \n".format(service, rain_data[service])
    update.message.reply_text(reply)


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("765960442:AAFyVQMSztNU4uBwRqBLyOuyMir8W5h3NW4")

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

    scheduler.run()
    
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()

if __name__ == '__main__':
    main()