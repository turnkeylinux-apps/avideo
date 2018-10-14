#!/usr/bin/python
"""Set YouPHPTube admin password, email and domain
Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
    --domain=   unless provided, will ask interactively
                DEFAULT=www.example.com
"""

import sys
import getopt
import inithooks_cache
import re
import hashlib
from executil import system

from dialog_wrapper import Dialog
from mysqlconf import MySQL

def usage(s=None):
    if s:
        print >> sys.stderr, "Error:", s
    print >> sys.stderr, "Syntax: %s [options]" % sys.argv[0]
    print >> sys.stderr, __doc__
    sys.exit(1)

DEFAULT_DOMAIN="www.example.com"

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'pass=', 'email=', 'domain='])
    except getopt.GetoptError, e:
        usage(e)

    password = ""
    email = ""
    domain = ""
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt == '--pass':
            password = val
        elif opt == '--email':
            email = val
        elif opt == '--domain':
            domain = val

    if not password:
        d = Dialog('TurnKey Linux - First boot configuration')
        password = d.get_password(
            "YouPHPTube Password",
            "Enter new password for the YouPHPTube 'admin' account.")

    if not email:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        email = d.get_email(
            "YouPHPTube Email",
            "Please enter email address for the YouPHPTube 'admin' account.",
            "admin@example.com")

    inithooks_cache.write('APP_EMAIL', email)

    if not domain:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        domain = d.get_input(
            "YouPHPTube Domain",
            "Please enter the Domain or IP address for YouPHPTube.",
            DEFAULT_DOMAIN)

    if domain == "DEFAULT":
        domain = DEFAULT_DOMAIN

    inithooks_cache.write('APP_DOMAIN', domain)

    apache_conf = "/etc/apache2/sites-available/youphptube.conf"
    system("sed -i \"0,\|RewriteRule|! {\|RewriteRule|s|https://.*|https://%s/\$1 [R,L]|}\" %s" % (domain, apache_conf))
    hashpass = hashlib.md5(password).hexdigest()

    m = MySQL()
    m.execute('UPDATE yphptube.users SET email=\"%s\" WHERE user=\"admin\";' % email)
    m.execute('UPDATE yphptube.users SET password=\"%s\" WHERE user=\"admin\";' % hashpass)

    urlfrontend = re.escape('https://' + domain + '/')

    """Replace URL In YouPHPTube Config File"""
    system('sed', '-i', "s/.*webSiteRootURL.*/\$global\[\'webSiteRootURL\'\] = \'%s\'\;/g" % urlfrontend,
        '/var/www/youphptube/videos/configuration.php')
    """Restart Apache"""
    system('systemctl', 'restart', 'apache2.service')
    """Restart nginx"""
    system('systemctl', 'restart', 'nginx.service')

if __name__ == "__main__":
    main()
