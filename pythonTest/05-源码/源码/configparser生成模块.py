__author__ = "Alex Li"

import configparser #ConfigParser

config = configparser.ConfigParser()

config["DEFAULT"] = {'ServerAliveInterval': '45',
                     'Compression': 'yes',
                     'CompressionLevel': '9'}

config['bitbucket.org'] = {}
config['bitbucket.org']['User'] = 'hg'

config['topsecret.server.com'] = {}
config['topsecret.server.com']
config['topsecret.server.com']['Host Port'] = '50022'  # mutates the parser
config['topsecret.server.com']['ForwardX11'] = 'no'  # same here

config['DEFAULT']['ForwardX11'] = 'yes'


with open('example.ini', 'w') as configfile:
    config.write(configfile)