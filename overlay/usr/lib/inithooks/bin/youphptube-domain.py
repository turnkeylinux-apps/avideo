#!/usr/bin/python
"""Set YouPHPTube Domain
Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
    --domain=   unless provided, will ask interactively
                default: www.example.com
"""

import sys
import getopt
import inithooks_cache
import re
import hashlib
import random

from executil import system
from dialog_wrapper import Dialog
from mysqlconf import MySQL

DEFAULT_DOMAIN = "www.example.com"

def usage(s=None):
    if s:
        print >> sys.stderr, "Error:", s
    print >> sys.stderr, "Syntax: %s [options]" % sys.argv[0]
    print >> sys.stderr, __doc__
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'domain='])
    except getopt.GetoptError, e:
        usage(e)

    domain = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt == '--domain':
            domain = val



    if not domain:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        domain = d.inputbox(
            "YouPHPTube Domain",
            "Please enter the Domain or IP address for YouPHPTube.",
            DEFAULT_DOMAIN)
    domain = domain[1]

    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyz"
    chars=[]
    for i in range(13):
	chars.append(random.choice(ALPHABET))
	salty="".join(chars)

    streamkey=[] 
    for i in range(13):
	streamkey.append(random.choice(ALPHABET))
	key="".join(chars)

    m = MySQL()
    m.execute('UPDATE yphptube.users SET channelName=\"%s\" WHERE user=\"admin\";' % key)

    urlfrontend = 'https://' + domain + '/'
    eurlfrontend = re.escape(urlfrontend)

    """Replace Salt In YouPHPTube Config File"""
    system('sed', '-i', "s/.*salt.*/\$global\[\'salt\'\] = \'%s\'\;/g" % salty, '/var/www/youphptube/videos/configuration.php')
    """Replace URL In YouPHPTube Config File"""
    system('sed', '-i', "s/.*webSiteRootURL.*/\$global\[\'webSiteRootURL\'\] = \'%s\'\;/g" % eurlfrontend, '/var/www/youphptube/videos/configuration.php')
    """Restart Apache"""
    system('systemctl', 'restart', 'apache2.service')
    """Restart nginx"""
    system('systemctl', 'restart', 'nginx.service')


if __name__ == "__main__":
    main()
