<?php
$global['webSiteRootURL'] = 'replacedatfirstboot';
$global['systemRootPath'] = '/var/www/YouPHPTube-Encoder/';

$global['disableConfigurations'] = false;
$global['disableBulkEncode'] = false;

$mysqlHost = 'localhost';
$mysqlUser = 'tubeuser';
$mysqlPass = 'tubepass';
$mysqlDatabase = 'encoder';

$global['allowed'] = array('mp4', 'avi', 'mov', 'mkv', 'flv', 'mp3', 'wav', 'm4v', 'webm', 'wmv', 'mpg', 'mpeg');
/**
 * Do NOT change from here
 */

require_once $global['systemRootPath'].'objects/include_config.php';