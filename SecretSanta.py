'''
SecretSanta - helpful classes
'''
#
# Future imports
#
from __future__ import print_function
#
# Standard imports
#
import json
import logging
import random
#
# Non-standard imports
#

#
##############################################################################
#
# Person()
#
# pylint: disable=too-few-public-methods
class Person(object):
    '''
    Person - tiny class representing a secret santa participant
    '''
    def __init__(self, name, email, dont_pair, wish_list=None):
        super(Person, self).__init__()
        self.name = name
        self.email = email
        self.invalid_matches = dont_pair
        self.wish_list = wish_list

        self._logger = logging.getLogger('.'.join([__name__, self.__class__.__name__]))

    def __repr__(self):
        return '"{name}" <{email}>'.format(name=self.name, email=self.email)

    def __str__(self):
        return "{name} <{email}>".format(name=self.name, email=self.email)

    def get_key(self):
        '''get_key() - use name for sorting, etc'''
        return self.name

    def serialize(self):
        '''
        serialize() - special serialize call
        '''
        output = self.__dict__

        output.pop('_logger', 0)
        return output
    #
    ##############################################################################
    #
    # _json_dump() - Little output to DRY
    #
    @staticmethod
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
    # choose_reciever() - Match
    #
    def choose_reciever(self, recievers=None):
        '''
        choose_reciever() - Choose a random Person to give a present to
        '''
        if None not in [recievers]:

            # print("{0} possible:".format(len(recievers)), end='')
            # print(", ".join([person.name for person in recievers]))

            try:
                choice = random.choice(recievers)
            except Exception as err:
                raise Exception(err)

            # Invalid is ourslef or someone in our exclusion list
            if ((self.name == choice.name) or
                    (self.invalid_matches and choice.name in self.invalid_matches)):
                if len(recievers) is 1:
                    raise Exception('Only one reciever left, try again')
                self._logger.info("BAD Match '%s' -> '%s'", self, choice)
                return self.choose_reciever(recievers)
            else:
                self._logger.info("Matched '%s' -> '%s'", self, choice)
                return choice
        else:
            raise RuntimeError("No recievers provided!")
#
##############################################################################
#
# Pair()
#
# pylint: disable=too-few-public-methods
class Pair(object):
    '''
    Pair - tiny class representing secret santa assignment
    '''
    def __init__(self, giver, reciever):
        super(Pair, self).__init__()
        self.giver = giver
        self.reciever = reciever

    def __repr__(self):
        return "{0:16} ---> {1}".format(self.giver.name, self.reciever.name)

    def __str__(self):
        return "{0:16} ---> {1}".format(self.giver.name, self.reciever.name)

    def get_key(self):
        '''get_key() - use giver name for sorting, etc'''
        return self.giver.name

    def generate_email(self, message):
        '''
        generate_email() - format the message for this Pair
        '''
        if None in [message]:
            raise RuntimeError("No message to format!")
        else:
            return message.format(santa=self.giver.name,
                                  santee=self.reciever.name,
                                  wish_list=self.reciever.wish_list)
#
##############################################################################
#
# Usage() - WHY?!?!
#
# class Usage(Exception):
#     def __init__(self, msg):
#         super(Usage, self).__init__()
#         self.msg = msg
