<?php
require_once('vars.php');

if(!isset($AUTH_REQUIRED))
	$AUTH_REQUIRED = true;

define('AUTHENTICATED', isset($_SERVER['PHP_AUTH_PW']) && in_array($_SERVER['PHP_AUTH_PW'], AUTH_TOKENS));

if($AUTH_REQUIRED && !AUTHENTICATED) {
	header('Content-Type: text/html');
	header('HTTP/1.1 401 Unauthorized');
	header('WWW-Authenticate: Basic realm="com.ds-homebrew.skins.submit"');
	die('<p>Authentication failed. Return to <a href="/">home page</a>?</p>');
}
