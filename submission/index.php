<?php
// Return source code
if(isset($_GET['source'])) {
	header("Content-Type: text/plain");
	die(file_get_contents(basename($_SERVER['PHP_SELF'])));
}

// Basic authentication
require_once('auth.php');
require_once('vars.php');

// Check git status
$git_status = shell_exec('git rev-list --left-right --count origin/master...HEAD');
$git_status = preg_replace('/(\d+)\t(\d+)/', '↓ \1 ↑ \2', $git_status);

// Run commands
if(isset($_GET['cmd'])) {
	umask(2);
	$back = '[<a href="/">back</a>]';
	switch($_GET['cmd']) {
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

// Connect to the database
$dbc = pg_connect('host=' . DB_HOST . ' dbname=' . DB_NAME . ' user=' . DB_USER . ' password=' . DB_PASSWORD)
	or die('Could not connect: ' . pg_last_error());

function format($val, $col, $row) {
	switch($col) {
		case 'time':
			return date('Y-m-d H:i', strtotime($val));
		case 'file':
		case 'icon':
			return "<a href=\"/staging/${row['temp']}/$val\">$val</a>";
		case 'screenshots':
			$res = [];
			foreach(explode('/', $val) as $screenshot) {
				$res[] = "<a href=\"/staging/$temp/$screenshot\">$screenshot</a>";
			}
			return implode('<br>', $res);
		case 'author':
			if(!empty($row['email']))
				return "<a href=\"mailto:${row['email']}\">$val</a>";
		default:
			return $val;
	}
}

?><!DOCTYPE html>
<html lang="en">
<head>
	<meta charset="utf-8">
	<meta name="viewport" content="width=device-width, initial-scale=1">
	<title>Submission Review</title>
	<style>
		table { border-collapse: collapse }
		th { padding: 0 1rem }
		td { text-align: center; border-bottom: 1px solid lightgray }
	</style>
</head>
<body>
	<div>
		<p>
			[<?php echo $git_status; ?>]
			[<a href="?cmd=git-pull">git pull</a>]
			[<a href="?cmd=git-push">git push</a>]
		</p>
	</div>
	<div>
		<table>
			<thead>
				<tr>
					<th>Actions</th>
					<th>Type</th>
					<th>Name</th>
					<th>Author</th>
					<th>File</th>
					<th>Version</th>
					<th>Description</th>
					<th>Categories</th>
					<th>Icon</th>
					<th>Screenshots</th>
					<th>Title ID</th>
					<th>Timestamp</th>
				<tr>
			</thead>
			<tbody>
				<?php
					$query = "SELECT type, name, author, file, version, description, categories, icon, screenshots, tid, time, temp, id, email FROM submissions";
					$res = pg_query($query);

					while($row = pg_fetch_array($res, null, PGSQL_ASSOC)) {
						echo '<tr>';
						echo '<td><form action="/process.php" method="post">';
						echo '<button type="submit" name="approve" value="' . $row['id']. '">O</button> ';
						echo '<button type="submit" name="reject" value="' . $row['id'] . '">X</button>';
						echo '</form></td>';

						foreach($row as $col => $val) {
							if(in_array($col, ['temp', 'id', 'email']))
								continue;
							echo '<td>' . format($val, $col, $row) . '</td>';
						}
						echo '</tr>';
					}
				?>
			</tbody>
		</table>
	</div>
</body>
</html>
