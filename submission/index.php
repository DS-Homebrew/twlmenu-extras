<?php
// Return source code
if(isset($_GET['source'])) {
	header("Content-Type: text/plain");
	die(file_get_contents(basename($_SERVER['PHP_SELF'])));
}

// Basic authentication
$AUTH_REQUIRED = false;
require_once('auth.php');
require_once('vars.php');

// Check git status
if(AUTHENTICATED) {
	$git_status = shell_exec('git rev-list --left-right --count origin/master...HEAD');
	$git_status = preg_replace('/(\d+)\t(\d+)/', '↓ \1 ↑ \2', $git_status);
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
				$res[] = "<a href=\"/staging/${row['temp']}/$screenshot\">$screenshot</a>";
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
		<?php if(AUTHENTICATED) { ?>
			<p>
				[<?php echo $git_status; ?>]
				[<a href="/process.php?cmd=git-pull">git pull</a>]
				[<a href="/process.php?cmd=git-push">git push</a>]
			</p>
		<?php } else { ?>
			<p>
				[<a href="/process.php?authenticate">moderation</a>]
			<p>
		<?php } ?>
	</div>
	<div>
		<table>
			<thead>
				<tr>
					<?php if(AUTHENTICATED) echo '<th>Actions</th>'; ?>
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
					$email = AUTHENTICATED ? ',email' : '';
					$query = "SELECT type, name, author, file, version, description, categories, icon, screenshots, tid, time, temp, id $email FROM submissions";
					$res = pg_query($query);

					while($row = pg_fetch_array($res, null, PGSQL_ASSOC)) {
						echo '<tr>';
						if(AUTHENTICATED) {
							echo '<td><form action="/process.php" method="post">';
							echo '<button type="submit" name="approve" value="' . $row['id']. '">O</button> ';
							echo '<button type="submit" name="reject" value="' . $row['id'] . '">X</button>';
							echo '</form></td>';
						}

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
