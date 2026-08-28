<?php

if (PHP_SAPI !== 'cli' || $argc !== 2) {
    fwrite(STDERR, "Usage: update-db.php streamer|encoder\n");
    exit(1);
}

if ($argv[1] === 'streamer') {
    $root = '/var/www/avideo';
    $updateDirectory = "{$root}/updatedb";
} elseif ($argv[1] === 'encoder') {
    $root = '/var/www/avideo-encoder';
    $updateDirectory = "{$root}/update";
} else {
    fwrite(STDERR, "Unknown AVideo component: {$argv[1]}\n");
    exit(1);
}

require "{$root}/videos/configuration.php";
if (!is_object($config ?? null)) {
    require_once "{$root}/objects/Configuration.php";
    $config = new Configuration();
}
$currentVersion = $config->getVersion();
$updates = [];

foreach (glob("{$updateDirectory}/updateDb.v*.sql") as $filename) {
    if (!preg_match('/updateDb\.v([0-9.]+)\.sql$/', $filename, $match)) {
        continue;
    }
    if (version_compare($match[1], $currentVersion, '>')) {
        $updates[$match[1]] = $filename;
    }
}

uksort($updates, 'version_compare');
foreach ($updates as $version => $filename) {
    $statement = '';
    foreach (file($filename) as $line) {
        if (str_starts_with($line, '--') || trim($line) === '') {
            continue;
        }
        $statement .= $line;
        if (substr(trim($line), -1) !== ';') {
            continue;
        }
        try {
            $global['mysqli']->query($statement);
        } catch (Throwable $error) {
            fwrite(STDERR, "Migration {$version} failed: {$error->getMessage()}\n");
            exit(1);
        }
        $statement = '';
    }
    if (trim($statement) !== '') {
        fwrite(STDERR, "Migration {$version} contains an incomplete SQL statement\n");
        exit(1);
    }
    fwrite(STDOUT, "database_migration={$version}\n");
}

if (empty($updates)) {
    fwrite(STDOUT, "database_current={$currentVersion}\n");
}
