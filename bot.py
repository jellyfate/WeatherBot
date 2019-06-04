 #!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The Bot is created for checking weather in custom location.
It colects rain data every day and store it, so user can access rain history.
Also this Bot can remind, if at your locations were no rain last few days.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""

from telegram.ext import Updater, CommandHandler #, MessageHandler, Filters
import logging, telegram, datetime
import sqlite3 as sql
from apscheduler.schedulers.background import BackgroundScheduler
from funcs import *

# db connection
try:
    connection = sql.connect('log.db')    
except sql.Error as e:
    print("Error {}:".format(e.args[0]))   

# enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


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


# send rain history for 5 days
def history(bot, update, args):
    if unknown_location_check(args[0], update): return 
    connection = sql.connect('log.db') 
    cursor = connection.cursor()
    cursor.execute("select * from {};".format(places[args[0]]["history_db"]))
    rows = cursor.fetchall()[-5:]
    
    template = "{0:20} {1:^15} {2:^15} {3:15} \n"
    reply = "Местоположение: " + args[0].title() + "\n"
    reply += template.format("День", "OWM", "DarkSky", "   APIXU")
    for row in rows:
        reply += template.format(row[0], row[1], row[2], row[3])
    update.message.reply_text(reply)


# hourly saving rain data
def hourly_log(): 
    connection = sql.connect('log.db') 
    cursor = connection.cursor()
    for location in locations.keys():
        owm, darksky, apixu = rain(location)
        # print('INSERT INTO {} VALUES("{}",{},{},{});'.format(
        #     today_db[location], datetime.date.today(), owm, darksky, apixu))
        print(datetime.datetime.now())        
        cursor.execute('INSERT INTO {} VALUES("{}",{},{},{});'.format(
            today_db[location], datetime.datetime.now(), owm, darksky, apixu))
        connection.commit()

# daily saving rain data
def daily_log():
    connection = sql.connect('log.db') 
    cursor = connection.cursor()
    for location in locations.keys():

        cursor.execute("select * from {};".format(places[location]["today_db"]))
        rows = cursor.fetchall()        
        rows = [item for t in rows for item in t]  
        cursor.execute("delete from {};".format(places[location]["today_db"]))

        cursor.execute('INSERT INTO {} VALUES("{}",{},{},{});'.format(
            places[location]["history_db"], datetime.date.today(), 
            max(rows[1::4]), max(rows[2::4]), max(rows[3::4])))
        connection.commit()


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
    dp.add_handler(CommandHandler("история", history, pass_args=True))
    # log all errors
    dp.add_error_handler(error)

    # executing hourly and daily schedules in background
    scheduler = BackgroundScheduler()
    scheduler.add_job(hourly_log, 'interval', hours=1)
    scheduler.add_job(daily_log, 'interval', hours=24, start_date='2019-06-01 23:59:00')
    # scheduler.add_job(reminder, 'interval', hours=24, start_date='2019-06-01 00:12:00')
    scheduler.start()

    try:
        # Start the Bot
        updater.start_polling()   
        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary if daemonic mode is enabled but should be done if possible
        scheduler.shutdown()
        connection.close()

if __name__ == '__main__':
    main()