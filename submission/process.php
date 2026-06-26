<?php
function get_path($type) {
	$paths = [
		'nintendo_3ds' => '3dsmenu/themes',
		'nintendo_dsi' => 'dsimenu/themes',
		'r4' => 'r4menu/themes',
		'wood' => 'akmenu/themes',
		'font' => 'extras/fonts',
		'icon' => 'icons',
		'unlaunch' => 'unlaunch/backgrounds'
	];

	return BASE_DIR . '/_nds/TWiLightMenu/' . $paths[$type];
}

function get_staging_path($temp) {
	return BASE_DIR . "/submission/staging/$temp";
}

function cleanup_dir($dir_path) {
	if(empty($dir_path) || !is_dir($dir_path))
		return false;

	$dir_itr = new RecursiveDirectoryIterator($dir_path, RecursiveDirectoryIterator::SKIP_DOTS);
	$contents = new RecursiveIteratorIterator($dir_itr, RecursiveIteratorIterator::CHILD_FIRST);
	foreach($contents as $path)
		$path->isDir() ? rmdir($path->getPathname()) : unlink($path->getPathname());

	rmdir($dir_path);
	return true;
}

function fetch_database($id) {
	$query = 'SELECT * FROM submissions WHERE id=$1';
	$res = pg_query_params($query, [$id]) or die('Query failed');
	return pg_fetch_array($res, null, PGSQL_ASSOC);
}

function delete_database($id) {
	$query = 'DELETE FROM submissions WHERE id=$1';
	pg_query_params($query, [$id]) or die('Deletion query failed');
}

function uses_meta_json($type) {
	return $type == 'icon' || $type == 'unlaunch';
}

function update_meta_json($type, $key, $json) {
	// This is for the _meta.json these types use
	if(!uses_meta_json($type))
		return;

	// Remove extension
	$key = preg_replace('/\.\w+$/', '', $key);

	mkdir(get_path($type), 0775, true);
	$json_path = get_path($type) . '/_meta.json';

	$content = '{}'; // Fallback
	$fp = fopen($json_path,  'r');
	if($fp) {
		$content = fread($fp, filesize($json_path));
		fclose($fp);
	}

	$meta = json_decode($content, true);
	$meta[$key] = $json;
	ksort($meta);
	$content = str_replace('    ', "\t", json_encode($meta, JSON_PRETTY_PRINT));

	$fp = fopen($json_path,  'w') or die("Failed to open _meta.json for $key for writing.");
	fwrite($fp, $content);
	fclose($fp);
}

function approve($id) {
	$info = fetch_database($id);

	$meta_json = [
		'title' => $info['name'],
		'author' => $info['author']
	];
	if(!empty($info['description']))
		$meta_json['description'] = $info['description'];
	if(!empty($info['version']) && $info['version'] != 'v1.0.0')
		$meta_json['version'] = $info['version'];
	if(!empty($info['categories']))
		$meta_json['categories'] = explode(',', $info['categories']);

	// Write metadata JSON
	if(uses_meta_json($info['type'])) {
		update_meta_json($info['type'], $info['file'], $meta_json);
	} else {
		$json_str = str_replace('    ', "\t", json_encode($meta_json, JSON_PRETTY_PRINT));
		$meta_path = get_path($info['type']) . '/meta/' . preg_replace('/\.\w+$/', '', $info['file']);
		mkdir($meta_path, 0775, true);
		$fp = fopen($meta_path . '/info.json', 'w') or die("Failed to open $meta_path.");
		fwrite($fp, $json_str);
		fclose($fp);
	}

	// Move file
	$new_path = get_path($info['type']) . '/' . $info['file'];
	@unlink($new_path);
	rename(get_staging_path($info['temp']) . '/' . $info['file'], $new_path);

	// Move icon
	if(!empty($info['icon'])) {
		$new_path = $meta_path . '/' . $info['icon'];
		@unlink($new_path);
		rename(get_staging_path($info['temp']) . '/' . $info['icon'], $new_path);
	}

	// Move screenshots
	if(!empty($info['screenshots'])) {
		mkdir($meta_path . '/screenshots', 0775, true);
		$screenshots = explode('/', $info['screenshots']);
		foreach($screenshots as $screenshot) {
			$new_path = $meta_path . '/screenshots/' . $screenshot;
			@unlink($new_path);
			rename(get_staging_path($info['temp']) . '/' . $screenshot, $new_path);
		}
	}

	delete_database($id);
	rmdir(get_staging_path($info['temp']));
}

function reject($id) {
	$info = fetch_database($id);
	if(!empty($info['temp'])) {
		cleanup_dir(get_staging_path($info['temp']));
		delete_database($id);
	}
}

// Commands
function command($cmd) {
	if(!isset($cmd))
		return;

	header('Content-Type: text/html');
	$back = '[<a href="/">back</a>]';
	switch($cmd) {
		case 'git-pull':
			echo "Running git pull... $back<pre>";
			die(shell_exec('git pull 2>&1'));
		case 'git-push':
			echo "Running git push... $back<pre>";
			die(shell_exec('git stage ' . BASE_DIR . '/_nds 2>&1 && git commit -m "Add new files" 2>&1; git push 2>&1'));
		default:
			die("Invalid command. $back");
	}
}

function main() {
	header('Content-Type: text/plain');
	umask(2);

	// Basic authentication
	require_once('auth.php');

	// Connect to database
	require_once('vars.php');
	$dbc = pg_connect('host=' . DB_HOST . ' dbname=' . DB_NAME . ' user=' . DB_USER . ' password=' . DB_PASSWORD)
		or die('Could not connect: ' . pg_last_error());

	// Check for action
	$return  = true;
	$approve = $_POST['approve'];
	$reject = $_POST['reject'];
	$cmd = $_GET['cmd'];
	$authenticate = isset($_GET['authenticate']);
	if(isset($approve)) {
		approve($approve);
	} else if(isset($reject)) {
		reject($reject);
	} else if(isset($cmd)) {
		command($cmd);
		$return = false;
	} else if(isset($authenticate)) {
		// NOP
	} else {
		die("Error: No action requested.");
	}

	if($return)
		header('Location: /', true, 303);
	pg_close($dbc);
}

main();
