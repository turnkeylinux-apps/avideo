#!/usr/bin/python3
"""Set AVideo admin password, email and domain
Option:
    --pass=     unless provided, will ask interactively
    --email=    unless provided, will ask interactively
    --domain=   unless provided, will ask interactively
                DEFAULT=www.example.com
"""

import sys
import getopt
from libinithooks import inithooks_cache
import re
import ipaddress
import subprocess

from libinithooks.dialog_wrapper import Dialog
from mysqlconf import MySQL

def usage(s=None):
    if s:
        print("Error:", s, file=sys.stderr)
    print("Syntax: %s [options]" % sys.argv[0], file=sys.stderr)
    print(__doc__, file=sys.stderr)
    sys.exit(1)

DEFAULT_DOMAIN="www.example.com"


def normalize_domain(domain):
    domain = domain.strip().rstrip('/')
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        hostname = re.compile(
            r'(?=^.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}'
            r'[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}'
            r'[a-zA-Z0-9])?'
        )
        if not hostname.fullmatch(domain):
            usage('domain must be a hostname or IP address')
    return domain


def password_hash(password):
    result = subprocess.run(
        [
            'php', '-r',
            'echo md5(hash("whirlpool", sha1(stream_get_contents(STDIN))));'
        ],
        input=password,
        text=True,
        capture_output=True,
        check=True,
    )
    if not re.fullmatch(r'[0-9a-f]{32}', result.stdout):
        raise RuntimeError('AVideo password hashing failed')
    return result.stdout

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], "h",
                                       ['help', 'pass=', 'email=', 'domain='])
    except getopt.GetoptError as e:
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
            "AVideo Password",
            "Enter new password for the AVideo 'admin' account.")

    if not email:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        email = d.get_email(
            "AVideo Email",
            "Please enter email address for the AVideo 'admin' account.",
            "admin@example.com")

    inithooks_cache.write('APP_EMAIL', email)

    if not domain:
        if 'd' not in locals():
            d = Dialog('TurnKey Linux - First boot configuration')

        domain = d.get_input(
            "AVideo Domain",
            "Please enter the Domain or IP address for AVideo.",
            DEFAULT_DOMAIN)

    if domain == "DEFAULT":
        domain = DEFAULT_DOMAIN

    domain = normalize_domain(domain)

    inithooks_cache.write('APP_DOMAIN', domain)

    apache_conf = "/etc/apache2/sites-available/avideo.conf"
    url_host = '[{}]'.format(domain) if ':' in domain else domain
    with open(apache_conf, 'r') as fob:
        apache_data = fob.read()
    apache_data = apache_data.replace(
        'RewriteCond %{HTTP_HOST} !^localhost$',
        'RewriteCond %{HTTP_HOST} !^{}$'.format(re.escape(url_host)))
    apache_data = apache_data.replace(
        'https://localhost/$1', 'https://{}/$1'.format(url_host))
    with open(apache_conf, 'w') as fob:
        fob.write(apache_data)

    hashpass = password_hash(password)

    m = MySQL()

    m.execute('UPDATE avideo.configurations SET contactEmail=%s WHERE users_id="1";', (email,))
    m.execute('UPDATE avideo.users SET email=%s WHERE user="admin";', (email,))
    m.execute('UPDATE avideo.users SET password=%s WHERE user="admin";', (hashpass,))

    """Set password details in AVideo-Encoder Database (Clear and Encrypted)"""
    m.execute('UPDATE avideo_encoder.streamers SET pass=%s WHERE id=1;', (password,))

    url = 'https://' + url_host + '/'
    enc = url + 'encoder/'

    """Set Streamer Site Configuration in Encoder"""
    m.execute('UPDATE avideo_encoder.streamers SET siteURL=%s WHERE id=1;', (url,))
    m.execute('UPDATE avideo_encoder.streamers SET siteURL=%s WHERE id=2;', (url,))

    """Configure AVideo To Use Local Encoder"""
    m.execute('UPDATE avideo.configurations SET encoderURL=%s WHERE id=1;', (enc,))

    """Lock Down Encoder To Specified Streamer Domain"""
    m.execute('UPDATE avideo_encoder.configurations_encoder SET allowedStreamersURL=%s WHERE id=1;', (url,))

    """Replace URL in Config Files"""
    conf_path = '/var/www/{}/videos/configuration.php'
    for _config, _url in (
                    (conf_path.format('avideo'), url),
                    (conf_path.format('avideo-encoder'), enc)):
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
    subprocess.run(['apache2ctl', '-t'], check=True)
    subprocess.run(['systemctl', 'restart', 'apache2.service'], check=True)
    """Restart nginx"""
    subprocess.run(['nginx', '-t'], check=True)
    subprocess.run(['systemctl', 'restart', 'nginx.service'], check=True)

if __name__ == "__main__":
    main()
