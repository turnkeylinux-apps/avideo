<?php

if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "Command line only\n");
    exit(1);
}

if ($argc < 9) {
    fwrite(STDERR, "Missing AVideo installer arguments\n");
    exit(1);
}

[$script, $component, $root, $rootUrl, $database, $databaseUser,
    $databasePass, $adminPass, $email] = $argv;

$root = rtrim($root, '/') . '/';
$rootUrl = rtrim($rootUrl, '/') . '/';
$post = [
    'systemRootPath' => $root,
    'webSiteRootURL' => $rootUrl,
    'databaseHost' => 'localhost',
    'databasePort' => '3306',
    'databaseName' => $database,
    'databaseUser' => $databaseUser,
    'databasePass' => $databasePass,
    'createTables' => 1,
];

if ($component === 'streamer') {
    $post += [
        'contactEmail' => $email,
        'systemAdminPass' => $adminPass,
        'mainLanguage' => 'en',
        'webSiteTitle' => 'TurnKey AVideo',
    ];
} elseif ($component === 'encoder') {
    if ($argc !== 10) {
        fwrite(STDERR, "Missing Streamer URL for Encoder installation\n");
        exit(1);
    }
    $siteUrl = rtrim($argv[9], '/') . '/';
    $post += [
        'siteURL' => $siteUrl,
        'inputUser' => 'admin',
        'inputPassword' => $adminPass,
        'allowedStreamers' => $siteUrl,
        'defaultPriority' => 1,
    ];
} else {
    fwrite(STDERR, "Unknown AVideo component: {$component}\n");
    exit(1);
}

$_POST = $post;
$_REQUEST = $post;
chdir("{$root}install");
ob_start();
include './checkConfiguration.php';
ob_end_clean();

if (empty($obj->success) || !empty($obj->error)) {
    $error = isset($obj->error) ? strip_tags((string) $obj->error) : 'unknown error';
    fwrite(STDERR, "{$component} installation failed: {$error}\n");
    exit(1);
}

if ($component === 'streamer') {
    $configurationPath = "{$root}videos/configuration.php";
    $configuration = file_get_contents($configurationPath);
    $subDirAssignment = <<<'PHP'
    $subDir = str_replace(array($_SERVER["DOCUMENT_ROOT"], 'videos/configuration.php'), array('',''), $file);
PHP;
    $subDirNormalization = "    \$subDir = '/' . ltrim(\$subDir, '/');";

    if ($configuration === false ||
            substr_count($configuration, $subDirAssignment) !== 1) {
        fwrite(STDERR, "Unable to locate AVideo root path assignment\n");
        exit(1);
    }
    $configuration = str_replace(
        $subDirAssignment,
        $subDirAssignment . PHP_EOL . $subDirNormalization,
        $configuration,
        $replacements
    );
    if ($replacements !== 1 ||
            file_put_contents($configurationPath, $configuration) === false) {
        fwrite(STDERR, "Unable to normalize AVideo root path\n");
        exit(1);
    }
}

fwrite(STDOUT, "installed_component={$component}\n");
