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
    system("sed -i \"\|RewriteCond|s|!^.*|!^%s$|\" %s" % (domain, apache_conf))
    hashpass = hashlib.md5(password).hexdigest()

    m = MySQL()

    m.execute('UPDATE youphptube.configurations SET contactEmail="%s" WHERE users_id="1";' % email)
    m.execute('UPDATE youphptube.users SET email="%s" WHERE user="admin";' % email)
    m.execute('UPDATE youphptube.users SET password="%s" WHERE user="admin";' % hashpass)

    """Set password details in youPHPTube-Encoder Database (Clear and Encrypted)"""
    m.execute('UPDATE youphptube_encoder.streamers SET pass="%s" WHERE id=1;' % password)
    m.execute('UPDATE youphptube_encoder.streamers SET pass="%s" WHERE id=2;' % hashpass)

    domain = domain + '/'
    url = 'https://' + domain
    enc = url + 'encoder/'

    """Set Streamer Site Configuration in Encoder"""
    m.execute('UPDATE youphptube_encoder.streamers SET siteURL="%s" WHERE id=1;' % url)
    m.execute('UPDATE youphptube_encoder.streamers SET siteURL="%s" WHERE id=2;' % url)

    """Configure YouPHPTube To Use Local Encoder"""
    m.execute('UPDATE youphptube.configurations SET encoderURL="%s" WHERE id=1;' % (enc))

    """Lock Down Encoder To Specified Streamer Domain"""
    m.execute('UPDATE youphptube_encoder.configurations SET allowedStreamersURL="%s" WHERE id=1;' % url)

    """Replace URL in Config Files"""
    conf_path = '/var/www/{}/videos/configuration.php'
    for _config, _url in (
                    (conf_path.format('youphptube'), url),
                    (conf_path.format('youphptube-encoder'), enc)):
        with open(_config, 'r') as fob:
            lines = []
            for line in fob.readlines():
                if "$global['webSiteRootURL'] = 'http" in line:
                    line = line.split('=')
                    url_prt = line[1].split("'")
                    url_prt[1] = _url
                    line[1] = "'".join(url_prt)
                    line = '='.join(line)
                lines.append(line)
        with open(_config, 'w') as fob:
            fob.writelines(lines)

    """Restart Apache"""
    system('systemctl', 'restart', 'apache2.service')
    """Restart nginx"""
    system('systemctl', 'restart', 'nginx.service')

if __name__ == "__main__":
    main()
