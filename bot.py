#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The Bot is created for checking weather in custom location.
It colects rain data every day and store it, so user can access rain history.
Also this Bot can remind, if at your locations were no rain last few days.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""

from telegram.ext import Updater, CommandHandler
import logging
import telegram
import datetime
import sqlite3
import urllib.request
import json
from data import *

# enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# db connection
try:
    connection = sqlite3.connect('log.db')
except sqlite3.Error as e:
    print("Error {}:".format(e.args[0]))


def json_to_dict(link):
    with urllib.request.urlopen(link) as url:
        return json.loads(url.read().decode())


def farenhToCelc(farenhT):
    return round((farenhT - 32) * (5/9), 1)


def unknown_location_check(location, update):
    if location not in places.keys():
        update.message.reply_text("Не найдено! Доступные локации: "
            + ", ".join(list(places.keys())) + " (чувствительно к регистру!)")
        return True


def current(bot, update, args):
    """Show current weather in custom location."""
    if unknown_location_check(args[0], update):
        return
    reply = "Местоположение: " + args[0].title() + "\n"

    data = json_to_dict(weather["forecast"]["DarkSky.net"]
        .format(places[args[0]]["coordinates"][0], places[args[0]]["coordinates"][1]))
    current = data['currently']

    current['time'] = datetime.datetime.fromtimestamp(current['time'])
    current['temperature'] = str(farenhToCelc(current['temperature'])) + ' C'
    current['apparentTemperature'] = str(
        farenhToCelc(current['apparentTemperature'])) + ' C'
    current['dewPoint'] = str(farenhToCelc(current['dewPoint'])) + ' C'
    current['humidity'] = str(current['humidity'] * 100) + ' %'
    current['windSpeed'] = str(current['windSpeed']) + ' m/s'
    current['pressure'] = str(current['pressure']) + ' hps'

    for key, val in current.items():
        reply += f"<code>{key}</code> :  {val}\n"

    chatId = update.message.chat.id
    bot.send_message(chatId, text=reply, parse_mode=telegram.ParseMode.HTML)


def rain(location):
    """Get current rain data in custom location among 3 services."""
    data = {}
    for key, value in weather["current"].items():
        # take api links, insert into the coordinates taken from location list by key
        data[key] = json_to_dict(value
            .format(places[location]["coordinates"][0], places[location]["coordinates"][1]))
    # openweather JSON have no "rain" key, when there are no rain in location
    if "rain" in data["OpenWeatherMap.org"]:
        own_rain = data["OpenWeatherMap.org"]["rain"]["3h"] 
    else:
        own_rain = 0
    return (own_rain, 
        data["DarkSky.net"]["currently"]["precipIntensity"], 
        data["APIXU.com"]["current"]["precip_mm"])


def rain_now(bot, update, args):
    """Show rain data in custom location."""
    if unknown_location_check(args[0], update):
        return
    # get rain data and pack it do dictionary
    rain_data = dict(zip(weather["current"].keys(), rain(args[0])))

    reply = "Местоположение: " + args[0].title() + "\n"
    for service in weather["current"].keys():
        reply += "{0} : осадки {1} mm \n".format(service, rain_data[service])
    update.message.reply_text(reply)


def history(days, location):
    """Get rain log from database in custom location and time range"""
    connection = sqlite3.connect('log.db')
    cursor = connection.cursor()
    # get data from custom location`s database
    cursor.execute("select * from {};".format(places[location]["history_db"]))
    return cursor.fetchall()[-int(days):]


def today(location):
    """Get rain log from database in custom location and time range"""
    connection = sqlite3.connect('log.db')
    cursor = connection.cursor()
    # get data from custom location`s database
    cursor.execute("select * from {};".format(places[location]["today_db"]))
    return cursor.fetchall()


def history_and_today(bot, update, args):
    """Show rain log for last week in custom location."""
    if unknown_location_check(args[0], update):
        return
    # get rain log
    rows = history(7, args[0])
    rows += today(args[0])
    template = "{0:10} {1:10} {2:10} {3:10} \n"
    reply = "Местоположение: " + args[0].title() + "\n"
    reply += template.format("Время", "       OWM", "  DarkSky", "APIXU")
    for row in rows:
        reply += template.format(row[0], row[1], row[2], row[3])
    update.message.reply_text(reply)


def hourly_log(bot, job):
    """Write current rain data in today`s database."""
    connection = sqlite3.connect('log.db')
    cursor = connection.cursor()

    for location in places.keys():
        # get current rain data
        owm, darksky, apixu = rain(location)
        cursor.execute('INSERT INTO {} VALUES("{}",{},{},{});'.format(
            places[location]["today_db"], datetime.datetime.now().strftime(
                'today %H:%M'),
            "{0:.1f}".format(owm),
            "{0:.1f}".format(darksky),
            "{0:.1f}".format(apixu)))
        connection.commit()


def set_hourly(job_queue):
    """Shedule sending rain log."""
    job_queue.run_repeating(hourly_log, interval=3600,
                            first=datetime.time(hour=0, minute=0))
    print('Ежечасные события установлены.')


def daily_log(bot, job):
    """Write today rain data in history database."""
    connection = sqlite3.connect('log.db')
    cursor = connection.cursor()

    for location in places.keys():
        cursor.execute(
            "select * from {};".format(places[location]["today_db"]))
        rows = cursor.fetchall()
        # next line needed to get max()
        rows = [item for t in rows for item in t]
        cursor.execute('INSERT INTO {} VALUES("{}",{},{},{});'.format(
            places[location]["history_db"], datetime.date.today(),
            max(rows[1::4]), max(rows[2::4]), max(rows[3::4])))
        # clean the today db because its data transfered to history db
        cursor.execute("delete from {};".format(places[location]["today_db"]))
        connection.commit()


def set_daily(job_queue):
    """Shedule sending rain log."""
    job_queue.run_repeating(daily_log, interval=86400,
                            first=datetime.time(hour=23, minute=59))
    print('Eжедневные события установлены.')


def reminder(bot, job):
    """Send rain log in custom location and time range every day."""
    # get rain log for last N days
    rows = history(job.context["days"], job.context["location"])

    reply = "Местоположение: " + job.context["location"].title() + "\n"
    template = "{0:10} {1:10} {2:10} {3:10} \n"
    reply += template.format("День", "       OWM", "  DarkSky", "APIXU")
    for row in rows:
        reply += template.format(row[0], row[1], row[2], row[3])
    bot.send_message(chat_id=job.context["chat_id"], text=reply)


def set_reminder(bot, update, job_queue, args):
    """Schedule sending rain log."""
    if unknown_location_check(args[0], update):
        return

    job_queue.run_repeating(reminder, interval=86400,
                            first=datetime.time(hour=16, minute=00),
                            context={"chat_id": update.message.chat_id,
                                     "days": args[1], "location": args[0]})
    update.message.reply_text('Мониторинг установлен.')


def unset_reminder(bot, update, job_queue):
    """Unshedule sending rain log."""
    if not all(job_queue.jobs()):
        update.message.reply_text('Нет активных мониторингов.')
        return

    for job in job_queue.jobs():
        job.schedule_removal()
    update.message.reply_text('Мониторинги сняты.')


def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("812215138:AAENIsKiCloqVsdZlrEvCcPuEUT3OgMSBf8")
    job_queue = updater.job_queue
    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("погода", current, pass_args=True))
    dp.add_handler(CommandHandler("дождь", rain_now, pass_args=True))
    dp.add_handler(CommandHandler(
        "история", history_and_today, pass_args=True))
    dp.add_handler(CommandHandler("мониторинг", set_reminder,
                                  pass_args=True,
                                  pass_job_queue=True,))
    dp.add_handler(CommandHandler("размониторить", unset_reminder,
                                  pass_job_queue=True,))
    # log all errors
    dp.add_error_handler(error)

    # start saving to db jobs
    set_daily(job_queue)
    set_hourly(job_queue)
    try:
        # Start the Bot
        updater.start_polling()
        print('Бот работает...')
        # until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT. 
        updater.idle()
    except (KeyboardInterrupt, SystemExit):
        # Not strictly necessary but should be done if possible
        connection.close()
        updater.stop()


if __name__ == '__main__':
    main()
