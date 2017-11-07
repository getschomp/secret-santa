#!/usr/bin/env python
# -*- coding: utf8 -*-
#
'''
secret_santa.py - Run a secret santa from a yaml config
'''
#
# Future imports
#
from __future__ import print_function
#
# Standard imports
#
import argparse
import datetime
import json
import logging
import os
import random
import smtplib
import socket
import sys
import time
#
# Non-standard imports
#
import pytz
import yaml
#
# You might need this to better handle utf8 characters
# https://stackoverflow.com/questions/21129020/how-to-fix-unicodedecodeerror-ascii-codec-cant-decode-byte#21190382
reload(sys)
# pylint: disable=no-member
sys.setdefaultencoding('utf8')
#
# Ensure . is in the lib path for local includes
#
sys.path.append(os.path.realpath('.'))
# pylint: disable=wrong-import-position
### local directory imports here
from SecretSanta import Person, Pair
#
##############################################################################
#
# Global variables
#
DEFAULT_LOG_LEVEL = 'WARNING'

MAX_SEARCHES = 100

HELP_MESSAGE = '''
To use, fill out config.yml with your own participants. You can also specify
DONT-PAIR so that people don't get assigned their significant other.

You'll also need to specify your mail server settings. An example is provided
for routing mail through gmail.

For more information, see README.
'''

REQUIRED = (
    'SMTP_SERVER',
    'SMTP_PORT',
    'USERNAME',
    'PASSWORD',
    'TIMEZONE',
    'PARTICIPANTS',
    'FROM',
    'SUBJECT',
    'MESSAGE',
)

HEADER = """Date: {date}
Content-Type: text/plain; charset="utf-8"
Message-Id: {message_id}
From: {frm}
To: {to}
Subject: {subject}

"""

CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yml')
#
##############################################################################
#
# _json_dump() - Little output to DRY
#
def _json_dump(the_thing, pretty=False):
    '''_json_dump() - Little output to DRY'''
    output = None
    if pretty:
        output = json.dumps(the_thing, sort_keys=True, indent=4,
                            separators=(',', ': '))
    else:
        output = json.dumps(the_thing)
    return output
#
##############################################################################
#
# _get_logger() - reuable code to get the correct logger by name
#
def _get_logger():
    '''_get_logger() - reuable code to get the correct logger by name'''
    return logging.getLogger(os.path.basename(__file__))
#
##############################################################################
#
# parse_yaml()
#
def parse_yaml(yaml_path=CONFIG_PATH):
    '''parse_yaml() - load the config file'''
    return yaml.safe_load(open(yaml_path, 'rb'))
#
##############################################################################
#
# create_pairs()
#
def create_pairs(old_givers=None, old_recievers=None):
    '''
    create_pairs() - match givers and recievers
    '''
    logger = _get_logger()
    pairs = None
    if None not in [old_givers, old_recievers]:

        givers = old_givers[:]
        recievers = old_recievers[:]
        pairs = []

        # randomize the array of givers, otherwise config position can limit
        random.shuffle(givers)
        for giver in givers:
            logger.info("Finding match for %s", giver)
            try:
                reciever = giver.choose_reciever(recievers)
                recievers.remove(reciever)
                pairs.append(Pair(giver, reciever))
            # pylint: disable=broad-except
            except Exception as (err):
                logger.info("Exception '%s', RESTART", err)
                pairs = None
                raise RuntimeError("Restarting the search")
                # NOTE: recursing here was causing issues
                # return create_pairs(old_givers, old_recievers)
    return pairs
#
##############################################################################
#
# pairs_summary()
#
def pairs_summary(pairs=None):
    '''
    pairs_summary() - summarize the matches
    '''
    if None not in [pairs]:
        message = """
Test pairings:

%s

To send out emails with new pairings,
call with the --send argument:

    $ ./secret_santa.py --send

        """ % ("\n".join([str(pair) for pair in sorted(pairs, key=lambda x: x.getKey())]))
        print(message)
#
##############################################################################
#
# send_emails()
#
def send_emails(config=None, pairs=None, fake=True):
    '''
    send_emails() - send the secret santa notification emails
    '''
    if None not in [config, pairs]:
        logger = _get_logger()
        server = None

        if not fake:
            logger.info("Connecting to: '%s'", config['SMTP_SERVER'])
            server = smtplib.SMTP(config['SMTP_SERVER'], config['SMTP_PORT'])
            # server.set_debuglevel(True)
            server.starttls()
            server.login(config['USERNAME'], config['PASSWORD'])

        time_zone = pytz.timezone(config['TIMEZONE'])
        for pair in pairs:

            now = time_zone.localize(datetime.datetime.now())

            # Sun, 21 Dec 2008 06:25:23 +0000
            date = now.strftime('%a, %d %b %Y %T %Z')
            message_id = '<{random}@{host}>'.format(random=str(time.time()) + str(random.random()),
                                                    host=socket.gethostname())

            subject = config['SUBJECT'].format(santa=pair.giver.name,
                                               santee=pair.reciever.name)
            header = HEADER.format(date=date,
                                   message_id=message_id,
                                   frm=config['FROM'],
                                   to=pair.giver.email,
                                   subject=subject,
                                  )

            body = header + pair.generate_email(message=config['MESSAGE'])

            if not fake:
                logger.info("Sending email to: '%s'...", pair.giver.email)
                result = server.sendmail(config['FROM'], [pair.giver.email], body)
                logger.debug("Result: '%s'", result)
                logger.info("Emailed %s", pair.giver)
            else:
                print(body)

        if None not in [server]:
            server.quit()
#
##############################################################################
#
# main
#
def main():
    '''main() - Handle the arguments and do the work'''
    #
    # Handle CLI args
    #
    parser = argparse.ArgumentParser(description=HELP_MESSAGE)

    # add arguments

    parser.add_argument('-l', '--log-level', action='store', required=False,
                        choices=["debug", "info", "warning", "error", "critical"],
                        default=DEFAULT_LOG_LEVEL,
                        help='Logging verbosity. Default: {}'.format(DEFAULT_LOG_LEVEL))

    parser.add_argument('-f', '--fake', action='store_true', required=False, default=False)

    parser.add_argument('-s', '--send', action='store_true', required=False, default=False)

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(format='%(asctime)s %(levelname)s:%(name)s.%(funcName)s:%(message)s',
                        level=getattr(logging, args.log_level.upper()))

    logger = _get_logger()

    logger.info("Log level is '%s'", args.log_level.upper())
    logger.debug("Arguments were: %s", _json_dump(args.__dict__))

    try:
        config = parse_yaml()
    except (Exception) as err:
        error = "Error reading config '{0}': '{1}'".format(CONFIG_PATH, err)
        logger.error(error)
        raise RuntimeError(error)

    # add some xmas emoji hotness
    config['MESSAGE'] += "\n" + "🌲   " * 10 + "\n\n" + "  🎅 " * 9 + "\n\n" + "🌲   " * 10

    logger.debug("Message template is: %s", config['MESSAGE'])

    for key in REQUIRED:
        if key not in config.keys():
            error = 'Required parameter "{0}" not in yaml config file!'.format(key)
            logger.error(error)
            raise RuntimeError(error)

    participants = config['PARTICIPANTS']

    if len(participants) < 2:
        raise Exception('Not enough participants specified.')

    givers = []
    for person in participants:

        person = Person(**person)
        givers.append(person)

    recievers = givers[:]

    # loop instead of recursing
    max_attempts = MAX_SEARCHES

    pairs = None
    while None in [pairs] and max_attempts > 0:
        try:
            max_attempts -= 1
            pairs = create_pairs(givers, recievers)
        # pylint: disable=broad-except
        except Exception:
            pass

    if None in [pairs]:
        raise RuntimeError("Unable to find matches after {0} attempts!".format(MAX_SEARCHES))
    else:
        logger.info("It took %s tries to match everyone.", (MAX_SEARCHES - max_attempts))

    if not args.send:
        pairs_summary(pairs)

    elif args.send:
        send_emails(config=config, pairs=pairs, fake=args.fake)

#
##############################################################################
#
# do it
#
if __name__ == "__main__":
    main()
