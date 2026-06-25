---
layout: default
title: App Request
---

# Theme Submission

Please fill out the form below to submit themes or other TWiLight Menu++ files
to the repository. This will submit a request for manual review, you can also
sumit a pull request directly to the GitHub repository.

If you have any issues, please as on the [Discord server](https://ds-homebrew.com/discord).

<div id="errorDiv"></div>

<form action="https://submit.skins.ds-homebrew.com/submit.php" method="post" enctype="multipart/form-data">
	<div class="input-group">
		<label class="input-group-text" for="category">Catergory</label>
		<select class="form-control" name="category" id="category" onchange="createForm(event.target.value)">
			<option value="---" disabled selected>--- Please select ---</option>
			<option value="---" disabled>Themes:</option>
			<option value="nintendo_3ds" >Nintendo 3DS</option>
			<option value="nintendo_dsi">Nintendo DSi</option>
			<option value="r4">R4 original</option>
			<option value="wood">Wood UI</option>
			<option value="---" disabled>Extras:</option>
			<option value="font">Font</option>
			<option value="icon">Icon</option>
			<option value="unlaunch">Unlaunch background</option>
		</select>
	</div>
	<br>
	<div id="itemData" class="mb-3"></div>
</form>

<script src="/assets/js/submit.js"></script>
