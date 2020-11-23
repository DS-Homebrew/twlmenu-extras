#!/usr/bin/env python3

import datetime
import glob
import io
import json
import os
from PIL import Image, ImageDraw
import py7zr
import sys
import urllib.parse

# No py 2
if(sys.version_info.major != 3):
	print("This is Python %d!\nPlease use Python 3!" % sys.version_info.major)
	exit()

def getTheme(path):
	if "3dsmenu/" in path:
		return "3DS"
	elif "akmenu/" in path:
		return "Wood UI"
	elif "dsimenu/" in path:
		return "DSi"
	elif "r4menu/" in path:
		return "Original R4"
	return ""

def getDefaultIcon(path):
	if "3dsmenu/" in path:
		return 0
	elif "akmenu/" in path:
		return -1
	elif "dsimenu/" in path:
		return 1
	elif "r4menu/" in path:
		return 2
	return -1

def lastUpdated(sevenZip):
	latest = None
	for item in sevenZip.list():
		if latest == None or item.creationtime > latest:
			latest = item.creationtime

	return latest

# Read version from old unistore
unistoreOld = {}
if os.path.exists("twlmenu-themes.unistore"):
	with open("twlmenu-themes.unistore", "r", encoding="utf8") as file:
		unistoreOld = json.load(file)

# Create UniStore base
unistore = {
	"storeInfo": {
		"title": "TWiLight Menu++ Themes",
		"author": "DS-Homebrew",
		"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/unistore/twlmenu-themes.unistore",
		"file": "twlmenu-themes.unistore",
		"sheetURL": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/unistore/twlmenu-themes.t3x",
		"sheet": "twlmenu-themes.t3x",
		"description": "A collection of themes for TWiLight Menu++",
		"version": 3,
		"revision": 0 if ("storeInfo" not in unistoreOld or "revision" not in unistoreOld["storeInfo"]) else unistoreOld["storeInfo"]["revision"]
	},
	"storeContent": [],
}

# Icons array
icons = []
iconIndex = 0

# Make 3DS, DSi, R4 icons
for file in ["icons/3ds.png", "icons/dsi.png", "icons/r4.png"]:
	with Image.open(open(file, "rb")) as icon:
		if not os.path.exists("temp"):
			os.mkdir("temp")

		icon.thumbnail((48, 48))
		icon.save(os.path.join("temp", str(iconIndex) + ".png"))
		icons.append(str(iconIndex) + ".png")
		iconIndex += 1

# Auth header
header = None
if len(sys.argv) > 1:
	header = {"Authorization": "token " + sys.argv[1]}

# Get theme files
files = [f for f in glob.glob("../_nds/TWiLightMenu/*menu/themes/*.7z")]

# Generate UniStore entries
for skin in files:
	# Skip Wood UI for now
	if(getTheme(skin) == "Wood UI"):
		continue

	info = {}
	icon = None
	updated = datetime.datetime.utcfromtimestamp(0)
	with py7zr.SevenZipFile(skin) as a:
		updated = lastUpdated(a)

		meta = a.read(["meta/info.json", "meta/icon.png"])
		if "meta/info.json" in meta:
			info = json.load(meta["meta/info.json"])
		if "meta/icon.png" in meta:
			icon = Image.open(meta["meta/icon.png"])

	if not "unistore_exclude" in info or info["unistore_exclude"] == False:
		# Make icon for UniStore
		if icon:
			if not os.path.exists("temp"):
				os.mkdir("temp")

			icon.thumbnail((48, 48))
			icon.save(os.path.join("temp", str(iconIndex) + ".png"))
			icons.append(str(iconIndex) + ".png")
			iconIndex += 1

		skinName = skin[skin.rfind("/")+1:-3]

		# Add entry to UniStore
		unistore["storeContent"].append({
			"info": {
				"title": info["title"] if "title" in info else skinName,
				"version": info["version"] if "version" in info else "",
				"author": info["author"] if "author" in info else "",
				"category": info["categories"] if "categories" in info else [],
				"console": getTheme(skin),
				"icon_index": len(icons) - 1 if icon else getDefaultIcon(skin),
				"description": info["description"] if "description" in info else "",
				"license": info["license"] if "license" in info else "",
				"last_updated": updated.strftime("%Y-%m-%d at %H:%M (UTC)")
			},
			info["title"] if "title" in info else skinName: [
				{
					"type": "downloadFile",
					"file": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + urllib.parse.quote(skin[3:]),
					"output": "sdmc:/" + skinName + ".7z",
					"message": "Downloading " + info["title"] if "title" in info else skinName + "..."
				},
				{
					"type": "extractFile",
					"file": "sdmc:/" + skinName + ".7z",
					"input": skinName + "/",
					"output": "sdmc:/" + skin[3:-3] + "/",
					"message": "Extracting " + info["title"] if "title" in info else skinName + "..."
				},
				{
					"type": "deleteFile",
					"file": "sdmc:/" + skinName + ".7z",
					"message": "Deleting " + skinName + ".7z..."
				}
			]
		})

# Make t3x
with open(os.path.join("temp", "icons.t3s"), "w", encoding="utf8") as file:
	file.write("--atlas -f rgba -z auto\n\n")
	for icon in icons:
		file.write(icon + "\n")
os.system("tex3ds -i " + os.path.join("temp", "icons.t3s") + " -o " +"twlmenu-themes.t3x")

# Increment revision if not the same
if unistore != unistoreOld:
	unistore["storeInfo"]["revision"] += 1

# Write unistore to file
with open("twlmenu-themes.unistore", "w", encoding="utf8") as file:
	file.write(json.dumps(unistore, sort_keys=True))
