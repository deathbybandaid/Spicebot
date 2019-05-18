# coding=utf-8
from __future__ import unicode_literals, absolute_import, division, print_function

import sopel.module
import sopel.tools
import sopel.config

from sopel_modules.SpiceBot.Logs import botlogs
from sopel_modules.SpiceBot.Events import botevents


def setup(bot):
    botlogs.log('SpiceBot_Logs', "Starting Setup Procedure")
    botevents.startup_add([botevents.BOT_LOGS])
    botevents.trigger(bot, botevents.BOT_LOGS, "SpiceBot_Logs")


@sopel.module.event('001')
@sopel.module.rule('.*')
def join_log_channel(bot, trigger):

    if bot.config.core.logging_channel:
        channel = bot.config.core.logging_channel
        if channel not in bot.channels.keys():
            bot.write(('JOIN', bot.nick, channel))
            if channel not in bot.channels.keys() and bot.config.SpiceBot_Channels.operadmin:
                bot.write(('SAJOIN', bot.nick, channel))

        while True:
            if len(botlogs.SpiceBot_Logs["queue"]):
                bot.say(str(botlogs.SpiceBot_Logs["queue"][0]), channel)
                del botlogs.SpiceBot_Logs["queue"][0]
    else:
        botlogs.sopel_config["logging_channel"] = False
        botlogs.SpiceBot_Logs["queue"] = []


@sopel.module.event('001')
@sopel.module.rule('.*')
def join_log_channel(bot, trigger):
    notdonelist = []
    while True:
        for number in botevents.SpiceBot_Events["startup_required"]:
            if str(number) not in botevents.SpiceBot_Events["triggers_recieved"].keys():
                notdonelist.append(number)
        events_not_done = []
        for number in notdonelist:
            if number in botevents.SpiceBot_Events["assigned_IDs"].keys():
                events_not_done.append(str(eval(botevents.SpiceBot_Events["assigned_IDs"][number])))
        bot.osd(events_not_done, "#deathbybandaid")
