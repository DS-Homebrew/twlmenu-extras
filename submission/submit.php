<?php
header('Content-Type: text/plain');

// Return source code
if(isset($_GET['source']))
	die(file_get_contents(basename($_SERVER['PHP_SELF'])));

require_once('vars.php');
define('TEMP_DIR', sha1(time()));

class Entry {
	public $type;
	public $name;
	public $author;
	public $description;
	public $file;
	public $version;
	public $categories;
	public $icon;
	public $screenshots;
	public $tid;
	public $email;
};

function staging_path($file='') {
	return BASE_DIR . '/submission/staging/' . TEMP_DIR . (empty($file) ? "" : "/$file");
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

function handle_file($file, $accepted_types) {
	$name = $file['name'];
	$tmp_name = $file['tmp_name'];
	$error = $file['error'];
	$type = $file['type'];

	if($error != 0) {
		echo "Warning: Upload $name failed, error $error.\n";
		return false;
	}

	if(!in_array($type, $accepted_types)) {
		echo "Warning: File $name of incorrect content type. ($type)\n";
		return false;
	}

	if(strlen($name) > 128) {
		echo "Warning: File name too long. ($name)\n";
		return false;
	}

	return move_uploaded_file($tmp_name, staging_path($name));
}

function add_database($entry) {
	$screenshot_list = NULL;
	if(count($entry->screenshots) > 0) {
		$screenshot_list = implode('/', array_column($entry->screenshots, 'name'));
	}

	// Add post to database
	$query = 'INSERT INTO submissions (type, temp, name, author, file, description, version, categories, icon, screenshots, tid, email) ' .
		'VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)';
	$params = [
		$entry->type,
		TEMP_DIR,
		$entry->name,
		$entry->author,
		$entry->file['name'],
		empty($entry->description) ? NULL : $entry->description,
		empty($entry->version) ? "v1.0.0" : $entry->version,
		count($entry->categories) == 0 ? NULL : implode(',', $entry->categories),
		$entry->icon['error'] == 0 ? $entry->icon['name'] : NULL,
		$screenshot_list,
		empty($entry->tid) ? NULL : $entry->tid,
		empty($entry->email) ? NULL : $entry->email
	];
	pg_query_params($query, $params) or die('Query failed: ' . pg_last_error());
	echo "Done! Submission recorded successfully.\n";
}

function handle_theme($entry) {
	if(!handle_file($entry->file, ['application/x-7z-compressed', 'application/x-compressed', 'application/octet-stream'])) {
		echo "Error: Invalid theme archive provided!!\n";
		return false;
	}

	if(count($entry->screenshots) > 0) {
		foreach($entry->screenshots as $key => $val) {
			if(!handle_file($val, ['image/png', 'image/gif'])) {
				echo "Warning: Invalid screenshot! Ignoring...\n";
				unset($entry->screenshots[$key]);
			}
		}
	}

	add_database($entry);
	return true;
}

function handle_font($entry) {
	if(!handle_file($entry->file, ['application/x-7z-compressed', 'application/x-compressed', 'application/octet-stream'])) {
		echo "Error: Invalid font archive provided!!\n";
		return false;
	}

	add_database($entry);
	return true;
}

function handle_icon($entry) {
	if($entry->file['type'] == 'application/octet-stream') {
		$entry->file['name'] = preg_replace('/\.bin$/', '.bnr', $entry->file['name']);
		if(!in_array($entry->file['size'], [0x23c0, 0xA40, 0x940, 0x840])) {
			echo "Error: Banner of invalid size!\n";
			return false;
		}
	}

	if(!handle_file($entry->file, ['image/png', 'application/octet-stream'])) {
		echo "Error: Invalid icon!!\n";
		return false;
	}

	if(!empty($entry->tid) && !preg_match('/^[A-Z0-9]{4}$/', $entry->tid)) {
		echo "Error Invalid title ID $entry->tid.\n";
		return false;
	}

	add_database($entry);
	return true;
}

function handle_unlaunch($entry) {
	if(!handle_file($entry->file, ['image/gif'])) {
		echo "Error: Invalid gif provided!!\n";
		return false;
	}

	add_database($entry);
	return true;
}

function main() {
	umask(2);
	mkdir(staging_path()) or die('Error: Failed to mkdir: ' . staging_path());

	$dbc = pg_connect('host=' . DB_HOST . ' dbname=' . DB_NAME . ' user=' . DB_USER . ' password=' . DB_PASSWORD)
		or die('Could not connect: ' . pg_last_error());

	if($_POST['submit'] != 'Submit')
		die("Error: No data submitted.");

	$entry = new Entry();
	$entry->type = trim($_POST['category']);
	$entry->name = trim($_POST['name']);
	$entry->author = trim($_POST['author']);
	$entry->description = trim($_POST['description']);
	$entry->version = trim($_POST['version']);
	$entry->tid = trim($_POST['tid']);
	$entry->email = trim($_POST['email']);
	$entry->file = $_FILES['file'];

	$entry->icon = $_FILES['icon'];
	if(!empty($entry->icon) && $entry->icon['error'] == 0) {
		$ct = ['image/png', 'image/gif'];
		if(in_array($entry->icon['type'], $ct))
			$entry->icon['name'] = 'icon.' . substr($entry->icon['type'], 6);

		if(!handle_file($entry->icon, $ct)) {
			echo "Warning: Invalid icon! Ignoring...\n";
			$entry->icon = NULL;
		}
	}

	$entry->categories = explode(',', $_POST['categories']);
	foreach($entry->categories as $cat => $val) {
		$entry->categories[$cat] = trim($val);
	}

	$entry->screenshots = [];
	$ss_temp = $_FILES['screenshots'];
	if(!empty($ss_temp)) {
		for($i = 0; $i < count($ss_temp['name']); $i++) {
			// PHP structures multiple file uploads as file->name[], I want file[]->name
			if($ss_temp['error'][$i] == 4) // Ignore 'no screenshot'
				continue;

			$entry->screenshots[] = [
				"name" => $ss_temp['name'][$i],
				"full_path" => $ss_temp['full_path'][$i],
				"type" => $ss_temp['type'][$i],
				"tmp_name" => $ss_temp['tmp_name'][$i],
				"error" => $ss_temp['error'][$i],
				"size" => $ss_temp['size'][$i],
			];
		}
	}

	$success = false;
	switch($entry->type) {
		case 'nintendo_3ds':
		case 'nintendo_dsi':
		case 'r4':
		case 'wood':
			$success = handle_theme($entry);
			break;
		case 'font':
			$success = handle_font($entry);
			break;
		case 'icon':
			$success = handle_icon($entry);
			break;
		case 'unlaunch':
			$success = handle_unlaunch($entry);
			break;
		default:
			echo "Error: Unsupported type $entry->type.\n";
			break;
	}

	if(!$success) {
		echo "Nothing added. Cleaning up...\n";
		cleanup_dir(staging_path());
	}

	pg_close($dbc);
}

main();
