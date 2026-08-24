<?php

if (PHP_SAPI !== 'cli') {
    fwrite(STDERR, "Command line only\n");
    exit(1);
}

$root = '/var/www/avideo';
$source = "{$root}/install/assets/testVideo.mp4";
$expectedHash = '160f70c0fc49b0542948e545c80f7d2d91ad4e82b396a1541c3750dc28274a4a';

if (!is_file($source) || hash_file('sha256', $source) !== $expectedHash) {
    fwrite(STDERR, "Pinned AVideo fixture failed its SHA-256 check\n");
    exit(1);
}

require "{$root}/videos/configuration.php";
$_SESSION['user'] = ['id' => 1];

$filename = 'turnkey-v19-fixture';
$video = new Video('TurnKey v19 playback fixture', $filename);
$video->setDuration('00:00:45');
$video->setDuration_in_seconds(45);
$video->setType('video');
$video->setDescription('Deterministic media fixture for appliance acceptance');
$video->setUsers_id(1);
$video->setCategories_id(1);
$video->setStatus(Video::STATUS_ACTIVE);
$video->setFilesize(filesize($source));

$destination = Video::getPathToFile("{$filename}_480.mp4", true);
if (empty($destination) || !copy($source, $destination)) {
    fwrite(STDERR, "Unable to install the AVideo playback fixture\n");
    exit(1);
}

$videoId = $video->save(false, true);
if (empty($videoId)) {
    fwrite(STDERR, "Unable to register the AVideo playback fixture\n");
    exit(1);
}

fwrite(STDOUT, "fixture_video_id={$videoId}\n");
