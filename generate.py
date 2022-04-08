#!/usr/bin/env python3

import git
import json
import urllib.parse
import yaml

from bannergif import bannergif
from datetime import datetime
from glob import glob
from os import listdir, makedirs, mkdir, path, system
from PIL import Image
from py7zr import SevenZipFile


def webName(name: str) -> str:
	"""Convert names to lowercase alphanumeric + underscore and hyphen"""

	name = name.lower()
	out = ""
	for letter in name:
		if letter in "abcdefghijklmnopqrstuvwxyz0123456789-_":
			out += letter
		elif letter in ". ":
			out += "-"
	return out


def getTheme(path: str) -> int:
	"""Gets the theme of a skin based on its path"""

	if "3dsmenu/" in path:
		return "Nintendo 3DS"
	elif "akmenu/" in path:
		return "Wood UI"
	elif "dsimenu/" in path:
		return "Nintendo DSi"
	elif "r4menu/" in path:
		return "R4 Original"
	elif "extras/fonts/" in path:
		return "Font"
	elif "icons/" in path:
		return "Icon"
	elif "unlaunch/" in path:
		return "Unlaunch"
	return ""


def getDefaultIcon(path: str) -> int:
	"""Gets the default icon of a skin based on its path"""

	if "3dsmenu/" in path:
		return 0
	elif "akmenu/" in path:
		return -1
	elif "dsimenu/" in path:
		return 1
	elif "r4menu/" in path:
		return 2
	elif "extras/fonts/" in path:
		return 3
	elif "icons/" in path:
		return 4
	return -1


def lastUpdated(sevenZip):
	"""Gets the latest date from the items in a 7z"""

	latest = None
	for item in sevenZip.list():
		if latest is None or item.creationtime > latest:
			latest = item.creationtime

	return latest


def downloadScript(skin: str, inFolder: bool) -> list:
	"""Makes a script to download the specified skin"""

	skinName = skin[skin.rfind("/") + 1:skin.rfind(".")]

	if skin.endswith(".7z"):
		return [
			{
				"type": "downloadFile",
				"file": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + urllib.parse.quote(skin),
				"output": f"/{skinName}.7z"
			},
			{
				"type": "extractFile",
				"file": f"/{skinName}.7z",
				"input": (skinName + "/") if inFolder else "",
				"output": f"/{skin[:-3]}/"
			},
			{
				"type": "deleteFile",
				"file": f"/{skinName}.7z"
			}
		]
	else:
		return [
			{
				"type": "downloadFile",
				"file": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + urllib.parse.quote(skin),
				"output": "/" + skin
			}
		]


# Read version from old unistore
unistoreOld = {}
if path.exists(path.join("unistore", "twlmenu-skins.unistore")):
	with open(path.join("unistore", "twlmenu-skins.unistore"), "r", encoding="utf8") as file:
		unistoreOld = json.load(file)

# Output JSON
output = []

# Create UniStore base
unistore = {
	"storeInfo": {
		"title": "TWiLight Menu++ Skins",
		"author": "DS-Homebrew",
		"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/unistore/twlmenu-skins.unistore",
		"file": "twlmenu-skins.unistore",
		"sheetURL": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/unistore/twlmenu-skins.t3x",
		"sheet": "twlmenu-skins.t3x",
		"description": "A collection of skins for TWiLight Menu++\nfrom DS-Homebrew/twlmenu-extras on GitHub\n\n(The 'Console' is the theme in TWiLight)",
		"version": 3,
		"revision": 0 if ("storeInfo" not in unistoreOld or "revision" not in unistoreOld["storeInfo"]) else unistoreOld["storeInfo"]["revision"]
	},
	"storeContent": [],
}

# Icons array
icons = []
iconIndex = 0

# Make 3DS, DSi, R4 icons
for file in ["3ds.png", "dsi.png", "r4.png", "font.png"]:
	with Image.open(open(path.join("unistore", "icons", file), "rb")) as icon:
		if not path.exists(path.join("unistore", "temp")):
			mkdir(path.join("unistore", "temp"))

		icon.thumbnail((48, 48))
		icon.save(path.join("unistore", "temp", str(iconIndex) + ".png"))
		icons.append(str(iconIndex) + ".png")
		iconIndex += 1

# Get skin files
files = [f for f in glob("_nds/TWiLightMenu/*menu/themes/*.7z")]
files += [f for f in glob("_nds/TWiLightMenu/extras/fonts/*.7z")]
files += [f for f in glob("_nds/TWiLightMenu/icons/*.png")]
files += [f for f in glob("_nds/TWiLightMenu/icons/*.bin")]
files += [f for f in glob("_nds/TWiLightMenu/unlaunch/backgrounds/*.gif")]

# Generate UniStore entries
for skin in files:
	print(skin)

	# Skip Wood UI for now
	if(getTheme(skin) == "Wood UI"):
		continue

	info = {}
	updated = datetime.utcfromtimestamp(0)
	inFolder = False
	skinName = skin[skin.rfind("/") + 1:skin.rfind(".")]

	if skin[-2:] == "7z":
		with SevenZipFile(skin) as a:
			updated = lastUpdated(a)
			inFolder = skinName in a.getnames()
	else:
		updated = datetime.utcfromtimestamp(int(git.Repo(".").git.log(["-n1", "--pretty=format:%ct", "--", skin]) or 0))

	created = datetime.utcfromtimestamp(int(git.Repo(".").git.log(["--pretty=format:%ct", "--", skin]).split("\n")[-1] or 0))

	if path.exists(path.join(skin[:skin.rfind("/")], "meta", skinName, "info.json")):
		with open(path.join(skin[:skin.rfind("/")], "meta", skinName, "info.json")) as file:
			info = json.load(file)
	elif path.exists(path.join(skin[:skin.rfind("/")], "_meta.json")):
		with open(path.join(skin[:skin.rfind("/")], "_meta.json")) as file:
			j = json.load(file)
			if skinName in j:
				info = j[skinName]

	screenshots = []
	if path.exists(path.join(skin[:skin.rfind("/")], "meta", skinName, "screenshots")):
		dirlist = listdir((path.join(skin[:skin.rfind("/")], "meta", skinName, "screenshots")))
		dirlist.sort()
		for screenshot in dirlist:
			if screenshot[-3:] == "png":
				screenshots.append({
					"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin[:skin.rfind("/")] + "/meta/" + urllib.parse.quote(skinName) + "/screenshots/" + screenshot,
					"description": screenshot[:screenshot.rfind(".")].capitalize().replace("-", " ")
				})
	elif skin[-3:] in ("gif", "png"):  # Unlaunch bg or icon
		screenshots.append({
			"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin,
			"description": skinName.capitalize().replace("-", " ")
		})
	elif skin[-3:] == "bin":  # banner.bin icon
		if not path.exists(path.join(skin[:skin.rfind("/")], "gif")):
			mkdir(path.join(skin[:skin.rfind("/")], "gif"))

		gifPath = path.join(skin[:skin.rfind("/")], "gif", skinName + ".gif")
		with open(skin, "rb") as f:
			bannergif(f, gifPath)

		screenshots.append({
			"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + gifPath,
			"description": skinName.capitalize().replace("-", " ")
		})

	skinInfo = {
		"title": info["title"] if "title" in info else skinName,
		"version": info["version"] if "version" in info else "v1.0.0",
		"author": info["author"] if "author" in info else "",
		"category": info["categories"] if "categories" in info else [],
		"console": getTheme(skin),
		"icon_index": getDefaultIcon(skin),
		"description": info["description"] if "description" in info else "",
		"screenshots": screenshots,
		"license": info["license"] if "license" in info else "",
		"last_updated": updated.strftime("%Y-%m-%d at %H:%M (UTC)")
	}

	color = None

	if ("unistore_exclude" not in info or info["unistore_exclude"] is False) and (getTheme(skin) != "Unlaunch"):
		# Make icon for UniStore
		if not path.exists(path.join("unistore", "temp")):
			mkdir(path.join("unistore", "temp"))
		iconPath = None
		if path.exists(path.join(skin[:skin.rfind("/")], "meta", skinName, "icon.png")):
			iconPath = path.join(skin[:skin.rfind("/")], "meta", skinName, "icon.png")
		elif skin[-3:] == "png":
			iconPath = skin
		elif skin[-3:] == "bin":
			iconPath = path.join(skin[:skin.rfind("/")], "gif", skinName + ".gif")

		if iconPath:
			with Image.open(iconPath) as icon:
				if skin[-3:] not in ("png", "bin"):
					icon.thumbnail((48, 48))

				icon.save(path.join("unistore", "temp", str(iconIndex) + ".png"))
				icons.append(str(iconIndex) + ".png")
				skinInfo["icon_index"] = iconIndex
				iconIndex += 1

				color = icon.copy().convert("RGB")
				color.thumbnail((1, 1))
				color = color.getpixel((0, 0))
				color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"

		# Add entry to UniStore
		unistore["storeContent"].append({
			"info": skinInfo,
			info["title"] if "title" in info else skinName: downloadScript(skin, inFolder)
		})

	# Website file
	web = skinInfo.copy()
	web["layout"] = "app"
	web["created"] = created.strftime("%Y-%m-%dT%H:%M:%SZ")
	web["updated"] = updated.strftime("%Y-%m-%dT%H:%M:%SZ")
	web["systems"] = [web["console"]]
	if color:
		web["color"] = color
	web["downloads"] = {skin[skin.rfind("/") + 1:]: {
		"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin,
		"size": path.getsize(skin)
	}}
	if skin[-3:] in ("gif", "png"):
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin
	elif skin[-3:] == "bin":
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + path.join(skin[:skin.rfind("/")], "gif", skinName + ".gif")
	elif web["icon_index"] < 3:
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/unistore/icons/" + ["3ds", "dsi", "r4", "ak"][web["icon_index"]] + ".png"
	else:
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin[:skin.rfind("/")] + "/meta/" + urllib.parse.quote(skinName) + "/icon.png"
	web["image"] = web["icon"]
	web.pop("icon_index")
	if "title" in web:
		if not path.exists(path.join("docs", "_" + webName(web["console"]))):
			mkdir(path.join("docs", "_" + webName(web["console"])))
		with open(path.join("docs", "_" + webName(web["console"]), webName(web["title"]) + ".md"), "w", encoding="utf8") as file:
			file.write("---\n" + yaml.dump(web) + "---\n")

	for category in web["category"]:
		if not path.exists(path.join("docs", webName(web["console"]), "category")):
			makedirs(path.join("docs", webName(web["console"]), "category"))
		with open(path.join("docs", webName(web["console"]), "category", category + ".md"), "w", encoding="utf8") as file:
			file.write(f"---\nlayout: cards\ntitle: {getTheme(skin)} - {category}\nsystem: {webName(web['console'])}\ncategory: {category}\n---\n<div class=\"alert alert-secondary mb-4\"><span class=\"i18n innerHTML-category\">Category: </span><span class=\"i18n innerHTML-cat-{category}\">{category}</span></div>\n")

	output.append(web)

# Make t3x
with open(path.join("unistore", "temp", "icons.t3s"), "w", encoding="utf8") as file:
	file.write("--atlas -f rgba -z auto\n\n")
	for icon in icons:
		file.write(icon + "\n")
system("tex3ds -i " + path.join("unistore", "temp", "icons.t3s") + " -o " + path.join("unistore", "twlmenu-skins.t3x"))

# Increment revision if not the same
if unistore != unistoreOld:
	unistore["storeInfo"]["revision"] += 1

# Write unistore to file
with open(path.join("unistore", "twlmenu-skins.unistore"), "w", encoding="utf8") as file:
	file.write(json.dumps(unistore, sort_keys=True))

# Write output file
if not path.exists(path.join("docs", "data")):
	makedirs(path.join("docs", "data"))
with open(path.join("docs", "data", "full.json"), "w", encoding="utf8") as file:
	file.write(json.dumps(output, sort_keys=True, ensure_ascii=False))
