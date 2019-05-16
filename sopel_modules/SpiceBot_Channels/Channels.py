#!/usr/bin/env python
# coding=utf-8
from __future__ import unicode_literals, absolute_import, print_function, division

# sopel imports
import sopel.module
from sopel.config.types import StaticSection, ValidatedAttribute, ListAttribute

from sopel_modules.SpiceBot_Events.System import botevents
from sopel_modules.SpiceBot_SBTools import (
                                            join_all_channels, chanadmin_all_channels, channel_list_current,
                                            bot_logging
                                            )

import spicemanip

import time


class SpiceBot_Channels_MainSection(StaticSection):
    announcenew = ValidatedAttribute('announcenew', default=False)
    joinall = ValidatedAttribute('joinall', default=False)
    operadmin = ValidatedAttribute('operadmin', default=False)
    chanignore = ListAttribute('chanignore')


def configure(config):
    config.define_section("SpiceBot_Channels", SpiceBot_Channels_MainSection, validate=False)
    config.SpiceBot_Channels.configure_setting('announcenew', 'SpiceBot_Channels Announce New Channels')
    config.SpiceBot_Channels.configure_setting('announcenew', 'SpiceBot_Channels JOIN New Channels')
    config.SpiceBot_Channels.configure_setting('announcenew', 'SpiceBot_Channels OPER ADMIN MODE')
    config.SpiceBot_Channels.configure_setting('chanignore', 'SpiceBot_Channels Ignore JOIN for channels')


class BotChannels():
    """This Logs all channels known to the server"""
    def __init__(self):
        self.SpiceBot_Channels = {
                                "list": {}
                                }


botchannels = BotChannels()


def setup(bot):
    bot_logging(bot, 'SpiceBot_Channels', "Starting setup procedure")
    botevents.startup_add([botevents.BOT_CHANNELS])

    bot.config.define_section("SpiceBot_Channels", SpiceBot_Channels_MainSection, validate=False)

    if "SpiceBot_Channels" not in bot.memory:
        bot.memory["SpiceBot_Channels"] = {"channels": {}, "InitialProcess": False, "ProcessLock": False}


def shutdown(bot):
    if "SpiceBot_Channels" in bot.memory:
        del bot.memory["SpiceBot_Channels"]


@sopel.module.event(botevents.BOT_CONNECTED)
@sopel.module.rule('.*')
def trigger_channel_list_initial(bot, trigger):

    # Unkickable
    bot.write(('SAMODE', bot.nick, '+q'))

    bot.write(['LIST'])
    bot.memory['SpiceBot_Channels']['ProcessLock'] = True

    bot_logging(bot, 'SpiceBot_Channels', "Initial Channel list populating")
    starttime = time.time()

    while not bot.memory['SpiceBot_Channels']['InitialProcess']:
        timesince = time.time() - starttime
        if timesince < 60:
            pass
        else:
            bot_logging(bot, 'SpiceBot_Channels', "Initial Channel list populating Timed Out")
            bot.memory['SpiceBot_Channels']['InitialProcess'] = True

    channel_list_current(bot)
    foundchannelcount = len(bot.memory['SpiceBot_Channels']['channels'].keys())
    bot_logging(bot, 'SpiceBot_Channels', "Channel listing finished! " + str(foundchannelcount) + " channel(s) found.")

    join_all_channels(bot)
    chanadmin_all_channels(bot)

    if "*" in bot.memory['SpiceBot_Channels']['channels']:
        del bot.memory['SpiceBot_Channels']['channels']["*"]

    botevents.trigger(bot, botevents.BOT_CHANNELS, "SpiceBot_Channels")


@sopel.module.event(botevents.BOT_CHANNELS)
@sopel.module.rule('.*')
def trigger_channel_list_recurring(bot, trigger):
    while True:
        try:
            time.sleep(1800)

            oldlist = list(bot.memory['SpiceBot_Channels']['channels'].keys())
            bot.write(['LIST'])
            bot.memory['SpiceBot_Channels']['ProcessLock'] = True

            while bot.memory['SpiceBot_Channels']['ProcessLock']:
                pass

            newlist = [item.lower() for item in oldlist if item.lower() not in bot.memory['SpiceBot_Channels']['channels']]
            if "*" in newlist:
                newlist.remove("*")
            if len(newlist) and bot.config.SpiceBot_Channels.announcenew:
                bot.osd(["The Following channel(s) are new:", spicemanip.main(newlist, 'andlist')], bot.channels.keys())

            join_all_channels(bot)

            chanadmin_all_channels(bot)

            if "*" in bot.memory['SpiceBot_Channels']['channels']:
                del bot.memory['SpiceBot_Channels']['channels']["*"]

        except KeyError:
            return


@sopel.module.event(botevents.BOT_CHANNELS)
@sopel.module.rule('.*')
def bot_part_empty(bot, trigger):
    """Don't stay in empty channels"""
    ignorepartlist = []
    if bot.config.SpiceBot_Logs.logging_channel:
        ignorepartlist.append(bot.config.SpiceBot_Logs.logging_channel)
    while True:
        for channel in bot.channels.keys():
            if len(bot.channels[channel].privileges.keys()) == 1 and channel not in ignorepartlist:
                bot.part(channel, "Leaving Empty Channel")
                if channel.lower() in bot.memory['SpiceBot_Channels']['channels']:
                    del bot.memory['SpiceBot_Channels']['channels'][channel.lower()]
