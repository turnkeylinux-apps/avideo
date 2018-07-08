<?php
$global['disableAdvancedConfigurations'] = 0;
$global['videoStorageLimitMinutes'] = 0;
$global['webSiteRootURL'] = 'changedatboot';
$global['systemRootPath'] = '/var/www/youphptube/';
$global['salt'] = '1234567890123';


$mysqlHost = 'localhost';
$mysqlPort = '3306';
$mysqlUser = 'tubeuser';
$mysqlPass = 'tubepass';
$mysqlDatabase = 'yphptube';

/**
 * Do NOT change from here
 */

require_once $global['systemRootPath'].'objects/include_config.php';
