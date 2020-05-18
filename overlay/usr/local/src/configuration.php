<?php
$global['configurationVersion'] = 3;
$global['disableAdvancedConfigurations'] = 0;
$global['videoStorageLimitMinutes'] = 0;
if(!empty($_SERVER['SERVER_NAME']) && $_SERVER['SERVER_NAME']!=='localhost' && !filter_var($_SERVER['SERVER_NAME'], FILTER_VALIDATE_IP)) { 
    // get the subdirectory, if exists
    $subDir = str_replace(array($_SERVER["DOCUMENT_ROOT"], 'videos/configuration.php'), array('',''), __FILE__);
    $global['webSiteRootURL'] = "http".(!empty($_SERVER['HTTPS'])?"s":"")."://".$_SERVER['SERVER_NAME'].$subDir;
}else{
    $global['webSiteRootURL'] = 'https://www.example.com/';
}
$global['systemRootPath'] = '/var/www/youphptube/';
$global['salt'] = '';
$global['enableDDOSprotection'] = 1;
$global['ddosMaxConnections'] = 40;
$global['ddosSecondTimeout'] = 5;
$global['strictDDOSprotection'] = 0;
$global['noDebug'] = 0;
$global['webSiteRootPath'] = '/';
if(empty($global['webSiteRootPath'])){
    preg_match('/https?:\/\/[^\/]+(.*)/i', $global['webSiteRootURL'], $matches);
    if(!empty($matches[1])){
        $global['webSiteRootPath'] = $matches[1];
    }
}
if(empty($global['webSiteRootPath'])){
    die('Please configure your webSiteRootPath');
}

$mysqlHost = 'localhost';
$mysqlUser = 'youphptube';
$mysqlPass = '';
$mysqlDatabase = 'youphptube';

/**
 * Do NOT change from here
 */

require_once $global['systemRootPath'].'objects/include_config.php';
