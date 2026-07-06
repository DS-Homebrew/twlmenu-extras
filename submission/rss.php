<?php
// Return source code
if(isset($_GET['source'])) {
	header("Content-Type: text/plain");
	die(file_get_contents(basename($_SERVER['PHP_SELF'])));
}

function get_submissions() {
	$query = 'SELECT id, type, name, author, description, '
			. "TO_CHAR(time, 'Dy, DD Mon YYYY HH24:MI:SS TZHTZM') AS ts FROM submissions "
			. 'ORDER BY submissions.time DESC LIMIT 10';
	$result = pg_query($query) or die('Query failed: ' . pg_last_error());

	$type_names = [
		'nintendo_3ds' => '3DS theme',
		'nintendo_dsi' => 'DSi theme',
		'r4' => 'R4 theme',
		'wood' => 'Wood theme',
		'font' => 'font',
		'icon' => 'icon',
		'unlaunch' => 'Unlaunch background'
	];

	$res = [];
	while($row = pg_fetch_array($result)) {
		$res[] = [
			'title' => "New {$type_names[$row['type']]} \"{$row['name']}\" submitted!",
			'link' => 'https://' . $_SERVER['SERVER_NAME'],
			'description' => $row['description'],
			'author' => $row['author'],
			'pubDate' => $row['ts'],
			'guid' => $row['id']
		];
	}

	return $res;
}

function main() {
	require_once('vars.php');
	$dbc = pg_connect('host=' . DB_HOST . ' dbname=' . DB_NAME . ' user=' . DB_USER . ' password=' . DB_PASSWORD)
	or die('Could not connect: ' . pg_last_error());

	global $entries;
	$entries = get_submissions();
	pg_close($dbc);

	header("Content-Type: application/rss+xml");
}

main();

?><?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom" xmlns:dc="http://purl.org/dc/elements/1.1/">
	<channel>
		<title>TWiLight Menu++ Theme Submissions</title>
		<link>http://submit.skins.ds-homebrew.com</link>
		<atom:link href="https://submit.skins.ds-homebrew.com/rss.php" rel="self" type="application/rss+xml" />
		<description>Submission review for the TWiLight Menu++ skins site</description>
		<lastBuildDate><?php echo $entries[0]['pubDate']; ?></lastBuildDate>
		<language>en-US</language>
		<?php foreach($entries as $entry) { ?>
			<item>
				<title><?php echo $entry['title']; ?></title>
				<link><?php echo $entry['link']; ?></link>
				<description><?php echo $entry['description']; ?></description>
				<author><?php echo $entry['author']; ?></author>
				<pubDate><?php echo $entry['pubDate']; ?></pubDate>
				<guid isPermaLink="false"><?php echo $entry['guid']; ?></guid>
			</item>
		<?php } ?>
	</channel>
</rss>
