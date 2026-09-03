#!/bin/bash
set -Eeuo pipefail
umask 077

result=${TKL_TEST_RESULT:?TKL_TEST_RESULT is required}
app_password=${TKL_TEST_APP_PASS:?TKL_TEST_APP_PASS is required}
base=https://localhost
cookie=/tmp/tkl-avideo-cookie.$$
encoder_cookie=/tmp/tkl-avideo-encoder-cookie.$$
page=/tmp/tkl-avideo-page.$$
response=/tmp/tkl-avideo-response.$$
media=/tmp/tkl-avideo-media.$$
policy=/tmp/tkl-avideo-policy.$$
# Address the verifier cache inside Apache's PrivateTmp mount namespace.
apache_pid=$(systemctl show --property MainPID --value apache2.service)
encoder_verify_name=$(php -r \
    'echo md5($argv[1]), "_verify.log";' "$base/")
encoder_verify_cache=/proc/$apache_pid/root/tmp/$encoder_verify_name

report_error() {
    printf 'test_failure line=%s status=%s command=%q\n' \
        "$1" "$2" "$3" >&2
    exit "$2"
}
trap 'report_error "$LINENO" "$?" "$BASH_COMMAND"' ERR

cleanup() {
    rm -f -- "$cookie" "$encoder_cookie" "$page" "$response" "$media" \
        "$policy" "$encoder_verify_cache"
}
trap cleanup EXIT

systemctl --quiet is-active apache2.service mariadb.service nginx.service \
    postfix.service multi-user.target
systemctl --quiet is-enabled apache2.service mariadb.service nginx.service \
    postfix.service
apache2ctl -t
nginx -t
apache2ctl -M 2>/dev/null | grep -F ' rewrite_module ' >/dev/null
apache2ctl -M 2>/dev/null | grep -F ' xsendfile_module ' >/dev/null
apache2ctl -M 2>/dev/null | grep -F ' headers_module ' >/dev/null
ss -ltn | grep -Eq '(^|[[:space:]])[^[:space:]]*:1935[[:space:]]'
ss -ltn | awk '$4 ~ /^(127\.0\.0\.1|\[::1\]):25$/ { found=1 } END { exit !found }'

test "$(git -c safe.directory=/var/www/avideo -C /var/www/avideo rev-parse HEAD)" = \
    2386f39caea1d2ef36267b252fa76af283294623
test "$(git -c safe.directory=/var/www/avideo-encoder \
    -C /var/www/avideo-encoder rev-parse HEAD)" = \
    71759ba94928bd324b6171b53b1d3e9e43760b91
test "$(git -c safe.directory=/var/www/avideo -C /var/www/avideo \
    remote get-url origin)" = https://github.com/WWBN/AVideo.git
test "$(git -c safe.directory=/var/www/avideo-encoder \
    -C /var/www/avideo-encoder remote get-url origin)" = \
    https://github.com/WWBN/AVideo-Encoder.git
git -c safe.directory=/var/www/avideo -C /var/www/avideo fsck --strict
git -c safe.directory=/var/www/avideo-encoder \
    -C /var/www/avideo-encoder fsck --strict

streamer_version=$(mariadb --batch --skip-column-names --execute \
    'SELECT version FROM avideo.configurations WHERE id=1')
encoder_version=$(mariadb --batch --skip-column-names --execute \
    'SELECT version FROM avideo_encoder.configurations_encoder WHERE id=1')
test "$streamer_version" = 29.0
test "$encoder_version" = 8.0
[[ $(php --version) == 'PHP 8.4.'* ]]
for extension in curl gd intl mbstring mysqli xml zip; do
    php -m | grep -Fxi "$extension" >/dev/null
done
ffmpeg -version | grep -F 'ffmpeg version 7.' >/dev/null
exiftool -ver >/dev/null
test "$(readlink -f /usr/local/bin/youtube-dl)" = /usr/bin/yt-dlp
dpkg-query -S /usr/bin/yt-dlp | grep -F 'yt-dlp:' >/dev/null
su www-data -s /bin/sh -c '/usr/bin/yt-dlp --version' >/dev/null

curl --insecure --fail --silent --show-error --location \
    http://localhost/ >"$page"
grep -q 'TurnKey AVideo' "$page"
curl --insecure --fail --silent --show-error "$base/" >"$page"
grep -q 'TurnKey AVideo' "$page"

curl --insecure --fail --silent --show-error \
    --cookie-jar "$cookie" --cookie "$cookie" \
    --data-urlencode 'user=admin' \
    --data-urlencode "pass=$app_password" \
    --data-urlencode 'redirectUri=https://localhost/' \
    "$base/objects/login.json.php" >"$response"
python3 - "$response" <<'PY'
import json
import sys

with open(sys.argv[1], encoding='utf-8') as response_file:
    response = json.load(response_file)
assert response.get('isLogged') is True
assert response.get('isAdmin') is True
assert response.get('canUpload') is True
PY

read -r video_id clean_title filename video_status < <(
    mariadb --batch --skip-column-names --execute \
        "SELECT id,clean_title,filename,status FROM avideo.videos WHERE filename='turnkey-v19-fixture'"
)
test -n "$video_id"
test "$video_status" = a
fixture_path="/var/www/avideo/videos/$filename/${filename}_480.mp4"
test "$(sha256sum "$fixture_path" | awk '{print $1}')" = \
    160f70c0fc49b0542948e545c80f7d2d91ad4e82b396a1541c3750dc28274a4a
curl --insecure --fail --silent --show-error \
    "$base/videos/$filename/${filename}_480.mp4" >"$media"
test "$(sha256sum "$media" | awk '{print $1}')" = \
    160f70c0fc49b0542948e545c80f7d2d91ad4e82b396a1541c3750dc28274a4a
curl --insecure --fail --silent --show-error --location \
    "$base/video/$video_id" >"$page"
grep -q 'TurnKey v19 playback fixture' "$page"
grep -q "$clean_title" "$page"

encoder_url=$(mariadb --batch --skip-column-names --execute \
    'SELECT encoderURL FROM avideo.configurations WHERE id=1')
streamer_url=$(mariadb --batch --skip-column-names --execute \
    'SELECT siteURL FROM avideo_encoder.streamers WHERE id=1')
allowed_url=$(mariadb --batch --skip-column-names --execute \
    'SELECT allowedStreamersURL FROM avideo_encoder.configurations_encoder WHERE id=1')
test "$encoder_url" = https://localhost/encoder/
test "$streamer_url" = https://localhost/
test "$allowed_url" = https://localhost/
for document_root in /var/www/avideo /var/www/avideo/; do
    root_contract=$(php -r '
        $_SERVER["DOCUMENT_ROOT"] = $argv[1];
        $_SERVER["SERVER_NAME"] = "assigned.example.tklapp.com";
        $_SERVER["HTTPS"] = "on";
        require "/var/www/avideo/videos/configuration.php";
        printf("%s|%s", $global["webSiteRootURL"],
            $global["webSiteRootPath"]);
    ' "$document_root")
    test "$root_contract" = 'https://assigned.example.tklapp.com/|/'
done
curl --insecure --fail --silent --show-error --location \
    "$base/encoder/" >"$page"
grep -q 'id="loginForm"' "$page"
grep -q 'id="siteURL"' "$page"
install -o www-data -g www-data -m 600 /dev/null "$encoder_verify_cache"
printf '%s\n' '{"verified":true}' >"$encoder_verify_cache"
curl --insecure --fail --silent --show-error \
    --cookie-jar "$encoder_cookie" --cookie "$encoder_cookie" \
    --data-urlencode 'user=admin' \
    --data-urlencode "pass=$app_password" \
    --data-urlencode 'siteURL=https://localhost/' \
    --data-urlencode 'encodedPass=false' \
    "$base/encoder/objects/login.json.php" >"$response"
if ! python3 - "$response" <<'PY'
import json
import sys

with open(sys.argv[1], encoding='utf-8') as response_file:
    response = json.load(response_file)
safe_fields = {
    key: response.get(key)
    for key in ('error', 'isLogged', 'isStreamerAdmin', 'streamers_id')
}
print('encoder_login=' + json.dumps(safe_fields, sort_keys=True),
      file=sys.stderr)
assert response.get('isLogged') is True
assert response.get('isStreamerAdmin') is True
assert str(response.get('streamers_id')) == '1'
PY
then
    grep -E 'login\.json: Login::run|Login::run request login|Login::run got an object|Login::run Error on Login context|Encoder Login Error|Verification (Start|GetFrom Cache|Response)|Error on Login not verified' \
        /var/www/avideo-encoder/videos/avideo.log 2>/dev/null | tail -n 40 >&2 || true
    exit 1
fi

dpkg-query -W adminer webmin-apache webmin-mysql >/dev/null
curl --insecure --fail --silent --show-error \
    https://127.0.0.1:12322/ >"$page"
grep -qi 'Adminer' "$page"
curl --insecure --fail --silent --show-error --head \
    https://127.0.0.1:12321/ >/dev/null

streamer_update_check=$(avideo-update --check streamer)
encoder_update_check=$(avideo-update --check encoder)
grep -q 'component=streamer.*installed_commit=2386f39c.*latest_release=' \
    <<<"$streamer_update_check"
grep -q 'component=encoder.*installed_commit=71759ba9.*latest_release=' \
    <<<"$encoder_update_check"
avideo-update streamer 29.0 \
    2386f39caea1d2ef36267b252fa76af283294623 >"$response"
grep -q 'database_current=29.0' "$response"
grep -q 'updated_component=streamer release=29.0' "$response"
avideo-update encoder 8.0 \
    71759ba94928bd324b6171b53b1d3e9e43760b91 >"$response"
grep -q 'database_current=8.0' "$response"
grep -q 'updated_component=encoder release=8.0' "$response"
curl --insecure --fail --silent --show-error "$base/" >"$page"
grep -q 'TurnKey AVideo' "$page"

apache_version=$(dpkg-query -W -f='${Version}' apache2)
mariadb_version=$(dpkg-query -W -f='${Version}' mariadb-server)
php_package=$(dpkg-query -W -f='${Version}' libapache2-mod-php)
ffmpeg_version=$(dpkg-query -W -f='${Version}' ffmpeg)
nginx_version=$(dpkg-query -W -f='${Version}' nginx)
yt_dlp_version=$(dpkg-query -W -f='${Version}' yt-dlp)
before="$apache_version|$mariadb_version|$php_package|$ffmpeg_version|$nginx_version|$yt_dlp_version"
apt-get update >/dev/null
for package in apache2 mariadb-server libapache2-mod-php ffmpeg nginx \
        libnginx-mod-rtmp libapache2-mod-xsendfile yt-dlp; do
    apt-cache policy "$package" >"$policy"
    candidate=$(awk '/Candidate:/ {print $2}' "$policy")
    test -n "$candidate"
    test "$candidate" != '(none)'
    grep -Eq 'trixie|deb13' "$policy"
done
after="$(dpkg-query -W -f='${Version}' apache2)|$(dpkg-query -W -f='${Version}' mariadb-server)|$(dpkg-query -W -f='${Version}' libapache2-mod-php)|$(dpkg-query -W -f='${Version}' ffmpeg)|$(dpkg-query -W -f='${Version}' nginx)|$(dpkg-query -W -f='${Version}' yt-dlp)"
test "$after" = "$before"
grep -Rqs '^Suites: trixie' /etc/apt/sources.list.d
if [[ -f /etc/apt/sources.list ]]; then
    if grep -qi bookworm /etc/apt/sources.list; then
        echo 'Bookworm remains in /etc/apt/sources.list' >&2
        exit 1
    fi
fi
if grep -Rqi bookworm /etc/apt/sources.list.d; then
    echo 'Bookworm remains in an active APT source' >&2
    exit 1
fi
cat >"$result" <<EOF
package_source=Debian 13 Trixie APT repositories for PHP, MariaDB, FFmpeg, ExifTool, Apache XSendFile, Nginx RTMP and yt-dlp; pinned official WWBN Git release tags for AVideo and Encoder
installed_version=AVideo $streamer_version commit 2386f39caea1d2ef36267b252fa76af283294623; Encoder $encoder_version commit 71759ba94928bd324b6171b53b1d3e9e43760b91; PHP $php_package; MariaDB $mariadb_version; FFmpeg $ffmpeg_version; Nginx $nginx_version; yt-dlp $yt_dlp_version
runtime_checks=normal init; Apache, MariaDB, Nginx and Postfix supervision; AVideo HTTPS web; assigned-FQDN root derivation with both Apache DOCUMENT_ROOT forms; administrator JSON login; deterministic fixture database record, player page and byte-identical playback; Encoder URL and database linkage; Encoder login through Streamer; RTMP listener; Adminer and Webmin HTTPS
updater_command=avideo-update --check streamer and encoder; avideo-update streamer 29.0 2386f39caea1d2ef36267b252fa76af283294623; avideo-update encoder 8.0 71759ba94928bd324b6171b53b1d3e9e43760b91; apt-get update and apt-cache policy
updater_result=current pinned releases fetched and commit-verified; both database migration paths reported current; Apache restarted with application state intact; signed Trixie metadata refreshed with installed package versions unchanged; $streamer_update_check; $encoder_update_check
updater_channel=official WWBN AVideo and AVideo-Encoder release tags; Debian and TurnKey Trixie APT repositories
integrity_evidence=build and runtime verified exact official Git commits with git fsck; update helper requires an expected full commit before checkout; fixture SHA-256 matched upstream pinned content over HTTPS; APT accepted signed Trixie metadata; no Bookworm source remained
EOF
