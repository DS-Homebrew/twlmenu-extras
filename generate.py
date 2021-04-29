#!/usr/bin/env python3

import datetime
import git
import glob
import io
import json
import os
from PIL import Image, ImageDraw
import py7zr
import sys
import urllib.parse
import yaml

# No py 2
if(sys.version_info.major != 3):
	print("This is Python %d!\nPlease use Python 3!" % sys.version_info.major)
	exit()

# Convert names to lowercase alphanumeric + underscore and hyphen
def webName(name):
	name = name.lower()
	out = ""
	for letter in name:
		if letter in "abcdefghijklmnopqrstuvwxyz0123456789-_.":
			out += letter
		elif letter == " ":
			out += "-"
	return out

def getTheme(path):
	if "3dsmenu/" in path:
		return "Nintendo 3DS"
	elif "akmenu/" in path:
		return "Wood UI"
	elif "dsimenu/" in path:
		return "Nintendo DSi"
	elif "r4menu/" in path:
		return "R4 Original"
	elif "unlaunch/" in path:
		return "Unlaunch"
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
if os.path.exists("twlmenu-skins.unistore"):
	with open("twlmenu-skins.unistore", "r", encoding="utf8") as file:
		unistoreOld = json.load(file)

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
for file in ["3ds.png", "dsi.png", "r4.png"]:
	with Image.open(open(os.path.join("unistore", "icons", file), "rb")) as icon:
		if not os.path.exists(os.path.join("unistore", "temp")):
			os.mkdir(os.path.join("unistore", "temp"))

		icon.thumbnail((48, 48))
		icon.save(os.path.join("unistore", "temp", str(iconIndex) + ".png"))
		icons.append(str(iconIndex) + ".png")
		iconIndex += 1

# Auth header
header = None
if len(sys.argv) > 1:
	header = {"Authorization": "token " + sys.argv[1]}

# Get skin files
files = [f for f in glob.glob("_nds/TWiLightMenu/*menu/themes/*.7z")]
files += [f for f in glob.glob("_nds/TWiLightMenu/unlaunch/backgrounds/*.gif")]

# Generate UniStore entries
for skin in files:
	# Skip Wood UI for now
	if(getTheme(skin) == "Wood UI"):
		continue

	info = {}
	updated = datetime.datetime.utcfromtimestamp(0)
	skinName = skin[skin.rfind("/")+1:skin.rfind(".")]

	if skin[-2:] == "7z":
		with py7zr.SevenZipFile(skin) as a:
			updated = lastUpdated(a)
	else:
		updated = datetime.datetime.utcfromtimestamp(git.Repo(".").blame("HEAD", skin)[0][0].committed_date)

	if os.path.exists(os.path.join(skin[:skin.rfind("/")], "meta", skinName, "info.json")):
		with open(os.path.join(skin[:skin.rfind("/")], "meta", skinName, "info.json")) as file:
			info = json.load(file)
	elif os.path.exists(os.path.join(skin[:skin.rfind("/")], "_meta.json")):
		with open(os.path.join(skin[:skin.rfind("/")], "_meta.json")) as file:
			j = json.load(file)
			if skinName in j:
				info = j[skinName]

	screenshots = []
	if os.path.exists(os.path.join(skin[:skin.rfind("/")], "meta", skinName, "screenshots")):
		dirlist = os.listdir((os.path.join(skin[:skin.rfind("/")], "meta", skinName, "screenshots")))
		dirlist.sort()
		for screenshot in dirlist:
			if screenshot[-3:] == "png":
				screenshots.append({
					"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin[:skin.rfind("/")] + "/meta/" + urllib.parse.quote(skinName) + "/screenshots/" + screenshot,
					"description": screenshot[:screenshot.rfind(".")].capitalize().replace("-", " ")
				})
	elif skin[-3:] == "gif":
		screenshots.append({
			"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin,
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

	if (not "unistore_exclude" in info or info["unistore_exclude"] == False) and (not getTheme(skin) == "Unlaunch"):
		# Make icon for UniStore
		if os.path.exists(os.path.join(skin[:skin.rfind("/")], "meta", skinName, "icon.png")):
			with Image.open(open(os.path.join(skin[:skin.rfind("/")], "meta", skinName, "icon.png"), "rb")) as icon:
				if not os.path.exists(os.path.join("unistore", "temp")):
					os.mkdir(os.path.join("unistore", "temp"))

				icon.thumbnail((48, 48))
				icon.save(os.path.join("unistore", "temp", str(iconIndex) + ".png"))
				icons.append(str(iconIndex) + ".png")
				skinInfo["icon_index"] = iconIndex
				iconIndex += 1

		# Add entry to UniStore
		unistore["storeContent"].append({
			"info": skinInfo,
			info["title"] if "title" in info else skinName: [
				{
					"type": "downloadFile",
					"file": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + urllib.parse.quote(skin),
					"output": "sdmc:/" + skinName + ".7z",
					"message": "Downloading " + info["title"] if "title" in info else skinName + "..."
				},
				{
					"type": "extractFile",
					"file": "sdmc:/" + skinName + ".7z",
					"input": skinName + "/",
					"output": "sdmc:/" + skin[:-3] + "/",
					"message": "Extracting " + info["title"] if "title" in info else skinName + "..."
				},
				{
					"type": "deleteFile",
					"file": "sdmc:/" + skinName + ".7z",
					"message": "Deleting " + skinName + ".7z..."
				}
			]
		})

	# Website file
	web = skinInfo.copy()
	web["layout"] = "app"
	web["updated"] = updated.strftime("%Y-%m-%dT%H:%M:%SZ")
	web["systems"] = [web["console"]]
	web["downloads"] = {skin[skin.rfind("/") + 1:]: {
		"url": "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin,
		"size": os.path.getsize(skin)
		}}
	if skin[-3:] == "gif":
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin
	elif web["icon_index"] < 3:
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/unistore/icons/" + ["3ds", "dsi", "r4", "ak"][web["icon_index"]] + ".png"
	else:
		web["icon"] = "https://raw.githubusercontent.com/DS-Homebrew/twlmenu-extras/master/" + skin[:skin.rfind("/")] + "/meta/" + urllib.parse.quote(skinName) + "/icon.png"
	web["image"] = web["icon"]
	web.pop("icon_index")
	if "title" in web:
		if not os.path.exists(os.path.join("docs", "_" + webName(web["console"]))):
			os.mkdir(os.path.join("docs", "_" + webName(web["console"])))
		with open(os.path.join("docs", "_" + webName(web["console"]), webName(web["title"]) + ".md"), "w", encoding="utf8") as file:
			file.write("---\n" + yaml.dump(web) + "---\n")

	for category in web["category"]:
		if not os.path.exists(os.path.join("docs", webName(web["console"]))):
			os.mkdir(os.path.join("docs", webName(web["console"])))
		with open(os.path.join("docs", webName(web["console"]), category + ".md"), "w", encoding="utf8") as file:
			file.write(f"---\nlayout: cards\ntitle: {getTheme(skin)} - {category}\nsystem: {webName(web['console'])}\ncategory: {category}\n---")

# Make t3x
with open(os.path.join("unistore", "temp", "icons.t3s"), "w", encoding="utf8") as file:
	file.write("--atlas -f rgba -z auto\n\n")
	for icon in icons:
		file.write(icon + "\n")
os.system("tex3ds -i " + os.path.join("unistore", "temp", "icons.t3s") + " -o " + os.path.join("unistore", "twlmenu-skins.t3x"))

# Increment revision if not the same
if unistore != unistoreOld:
	unistore["storeInfo"]["revision"] += 1

# Write unistore to file
with open(os.path.join("unistore", "twlmenu-skins.unistore"), "w", encoding="utf8") as file:
	file.write(json.dumps(unistore, sort_keys=True))
