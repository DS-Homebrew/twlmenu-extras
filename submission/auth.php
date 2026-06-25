<?php
require_once('vars.php');
if(!isset($_SERVER['PHP_AUTH_PW']) || !in_array($_SERVER['PHP_AUTH_PW'], AUTH_TOKENS)) {
    header('HTTP/1.1 401 Unauthorized');
    header('WWW-Authenticate: Basic realm="com.ds-homebrew.skins.submit"');
    die('<p>Authentication failed. You may be looking for the <a href="https://skins.ds-homebrew.com/submit">submission form</a>.</p>');
}
