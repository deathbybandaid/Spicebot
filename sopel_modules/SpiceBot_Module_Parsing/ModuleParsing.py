# coding=utf-8

from __future__ import unicode_literals, absolute_import, division, print_function

import sopel
import sopel.module

import os

from sopel_modules.SpiceBot.Logs import botlogs
from sopel_modules.SpiceBot.Events import botevents
from sopel_modules.SpiceBot.Commands import botcommands

import spicemanip


def setup(bot):
    botlogs.log('SpiceBot_CommandsQuery', "Starting setup procedure")
    botevents.startup_add([botevents.BOT_COMMANDSQUERY])

    filepathlisting = []

    # main Modules directory
    main_dir = os.path.dirname(os.path.abspath(sopel.__file__))
    modules_dir = os.path.join(main_dir, 'modules')
    filepathlisting.append(modules_dir)

    # Home Directory
    home_modules_dir = os.path.join(bot.config.homedir, 'modules')
    if os.path.isdir(home_modules_dir):
        filepathlisting.append(home_modules_dir)

    # pypi installed
    try:
        import sopel_modules
        for plugin_dir in set(sopel_modules.__path__):
            for pathname in os.listdir(plugin_dir):
                pypi_modules_dir = os.path.join(plugin_dir, pathname)
                filepathlisting.append(pypi_modules_dir)
    except Exception as e:
        botlogs.log('SpiceBot_CommandsQuery', "sopel_modules not loaded :" + str(e))

    # Extra directories
    filepathlist = []
    for directory in bot.config.core.extra:
        filepathlisting.append(directory)

    for directory in filepathlisting:
        for pathname in os.listdir(directory):
            path = os.path.join(directory, pathname)
            if (os.path.isfile(path) and path.endswith('.py') and not path.startswith('_')):
                if pathname not in ["SpiceBot_dummycommand.py"]:
                    filepathlist.append(str(path))

    # CoreTasks
    ct_path = os.path.join(main_dir, 'coretasks.py')
    filepathlist.append(ct_path)

    for modulefile in filepathlist:

        module_file_lines = []
        module_file = open(modulefile, 'r')
        lines = module_file.readlines()
        for line in lines:
            module_file_lines.append(line)
        module_file.close()

        dict_from_file = dict()

        detected_lines = []
        for line in module_file_lines:

            if str(line).startswith("@"):
                line = str(line)[1:]

                if str(line).startswith(tuple(["commands", "module.commands", "sopel.module.commands"])):
                    line = str(line).split("commands")[-1]
                    line = "commands" + line
                    detected_lines.append(line)
                elif str(line).startswith(tuple(["nickname_commands", "module.nickname_commands", "sopel.module.nickname_commands"])):
                    line = str(line).split("nickname_commands")[-1]
                    line = "nickname_commands" + line
                    detected_lines.append(line)
                elif str(line).startswith(tuple(["rule", "module.rule", "sopel.module.rule"])):
                    line = str(line).split("rule")[-1]
                    line = "rule" + line
                else:
                    line = None

                if line:
                    detected_lines.append(line)

        if len(detected_lines):

            filelinelist = []
            currentsuccesslines = 0
            for detected_line in detected_lines:

                # Commands
                if str(detected_line).startswith("commands"):
                    comtype = "module"
                    validcoms = eval(str(detected_line).split("commands")[-1])
                elif str(detected_line).startswith("nickname_commands"):
                    comtype = "nickname"
                    validcoms = eval(str(detected_line).split("nickname_commands")[-1])
                elif str(detected_line).startswith("rule"):
                    comtype = "rule"
                    validcoms = eval(str(detected_line).split("rule")[-1])

                if isinstance(validcoms, tuple):
                    validcoms = list(validcoms)
                else:
                    validcoms = [validcoms]
                for regexcom in ["(.*)", '^\?(.*)']:
                    if regexcom in validcoms:
                        while regexcom in validcoms:
                            validcoms.remove(regexcom)

                if len(validcoms):
                    validcomdict = {"comtype": comtype, "validcoms": validcoms}
                    filelinelist.append(validcomdict)
                    currentsuccesslines += 1

            if currentsuccesslines:
                botcommands.SpiceBot_Commands['counts'] += 1

            if len(filelinelist):
                for atlinefound in filelinelist:

                    dict_from_file = dict()

                    comtype = atlinefound["comtype"]
                    validcoms = atlinefound["validcoms"]

                    # default command to filename
                    if "validcoms" not in dict_from_file.keys():
                        dict_from_file["validcoms"] = validcoms

                    maincom = dict_from_file["validcoms"][0]
                    if len(dict_from_file["validcoms"]) > 1:
                        comaliases = spicemanip.main(dict_from_file["validcoms"], '2+', 'list')
                    else:
                        comaliases = []

                    botcommands.SpiceBot_Commands['commands'][comtype][maincom] = dict_from_file
                    for comalias in comaliases:
                        if comalias not in botcommands.SpiceBot_Commands['commands'][comtype].keys():
                            botcommands.SpiceBot_Commands['commands'][comtype][comalias] = {"aliasfor": maincom}

    for comtype in ['module', 'nickname', 'rule']:
        botlogs.log('SpiceBot_CommandsQuery', "Found " + str(len(botcommands.SpiceBot_Commands['commands'][comtype].keys())) + " " + comtype + " commands.", True)

    for command in botcommands.SpiceBot_Commands['commands']['rule'].keys():
        if command.startswith("$nickname"):
            command = command.split("$nickname")[-1]
            if command not in botcommands.SpiceBot_Commands['nickrules']:
                botcommands.SpiceBot_Commands['nickrules'].append(command)

    botevents.trigger(bot, botevents.BOT_COMMANDSQUERY, "SpiceBot_CommandsQuery")


@sopel.module.event(botevents.BOT_LOADED)
@sopel.module.rule('.*')
def bot_events_complete(bot, trigger):

    for comtype in botcommands.SpiceBot_Commands['commands'].keys():
        if comtype not in ['module', 'nickname', 'rule']:
            botlogs.log('SpiceBot_CommandsQuery', "Found " + str(len(botcommands.SpiceBot_Commands['commands'][comtype].keys())) + " " + comtype + " commands.", True)
