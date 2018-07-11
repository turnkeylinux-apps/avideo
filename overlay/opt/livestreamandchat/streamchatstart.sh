#!/bin/sh

#Start YouPHPTube Chat Server
nohup php /var/www/youphptube/plugin/LiveChat/chat-server.php &
#Start Nginx with RTMP Module
#/usr/local/nginx/sbin/nginx
