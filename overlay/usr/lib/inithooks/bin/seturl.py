#!/usr/bin/python
"""Set YouPHPTube admin password and email
Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
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

def usage(s=None):
    if s:
        print >> sys.stderr, "Error:", s
    print >> sys.stderr, "Syntax: %s [options]" % sys.argv[0]
    print >> sys.stderr, __doc__
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'url='])
    except getopt.GetoptError, e:
        usage(e)

    url = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt == '--url':
            url = val



    if not url:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        url = d.inputbox(
            "YouPHPTube URL",
            "Please enter the URL address for YouPHPTube.",
            "example.com")
    url = url[1]

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

    urlfrontend = 'https://' + url + '/'
    eurlfrontend = re.escape(urlfrontend)
    streamingurl1 = 'http://' + url + '/plugin/Live/on_publish.php;'
    estreamingurl1 = re.escape(streamingurl1)
    streamingurl2 = 'http://' + url + '/plugin/Live/on_play.php;'
    estreamingurl2 = re.escape(streamingurl2)
    streamingurl3 = 'http://' + url + '/plugin/Live/on_record_done.php;'
    estreamingurl3 = re.escape(streamingurl3)

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
