#!/usr/bin/env python3

import re
import textwrap

from argparse import ArgumentParser, FileType


def processLine(line: str, indent: int) -> str:
	"""Cleans up a line if it can"""

	line = line.rstrip()

	# Reduce indent
	if len(line) > 32 and len(line.strip()) <= 32 and lineIndent(line) != indent:
		line = line.strip()
		line = (" " * ((32 - len(line)) // 2)) + line
	elif lineIndent(line) > 4:
		line = re.sub("^ +", lambda x: x[0][:len(x[0]) // 4], line)

	# A horizontal rule, just cut it
	if isHr(line) == 1:
		line = line[:32]

	return line

def isArt(line: str) -> float:
	"""Returns the percentage of the line that seems like art"""

	return len(re.findall(r"[_\-=+~*:;|/\\^@#\[\],.'\" ]", line)) / len(line) if len(line) > 0 else 0

def isHr(line: str) -> float:
	"""Retruns the percentage of the line that seems like a horizontal rule"""

	return len(re.findall(r"[\-=+~*: ]*", line)[0]) / len(line) if len(line) > 0 else 0

def isBullet(line: str) -> int:
	"""Returns the length of the bullet if the line looks like a bullet"""

	match = re.findall(r"^ {0,8}(?:[0-9i]+(?:st|nd|rd|th)?(?:[.)]| -)|[-*=+•])+ ?", line)
	return len(match[0]) if len(match) > 0 else 0

def lineIndent(line: str) -> int:
	"""Returns the indent of a line"""

	return len(re.findall("^ *", line)[0])


parser = ArgumentParser(description="Wraps a text file to 32 columns, doing its best to preserve ASCII formatting")
parser.add_argument("input", type=str, help="input file")
parser.add_argument("output", type=str, help="output file")
parser.add_argument("-s", "--silent", action="store_true", help="don't print output")
parser.add_argument("-e", "--encoding", type=str, default="Windows 1252", help="encoding of the files")

args = parser.parse_args()

with open(args.input, encoding=args.encoding) as f:
	input = f.read().split("\n")

grouped = []

temp = []
indent = 0
lineCount = 1
lastArt = 0
for i, line in enumerate(input):
	line = processLine(line, indent)

	# Group together if indentation matches and it seems like a paragraph
	if lineIndent(line) == indent and not isBullet(line) and isArt(line) <= .75 and line != "":
		temp.append(line)
	else:
		if len(temp) > 0:
			if max(len(x) for x in temp) > 32 and isArt("".join(temp)) <= .75:
				temp = textwrap.fill(re.sub(r"\s+", " ", "\n".join(temp)).strip(), 32, initial_indent=" " * lineIndent(temp[0]), subsequent_indent=" " * (isBullet(temp[0]) or lineIndent(temp[0])))
			else:
				temp = "\n".join([x[:32] for x in temp])
				if not args.silent and isArt(temp) > .75:
					print(f"Warning: Probably ASCII art at line {lineCount}")
			grouped.append(temp)
			lineCount += len(re.findall("\n", temp)) + 1

		if line == "" or isArt(line) > .75:
			if not args.silent and line != "" and isHr(line) <= .5:
				if i - 1 != lastArt:
					print(f"Warning: Probably ASCII art at line {lineCount}")
				lastArt = i

			grouped.append(line[:32])
			lineCount += 1
			temp = []
			indent = 0
		else:
			temp = [line]
			indent = lineIndent(line) + isBullet(line)

if len(temp) > 0:
	if max(len(x) for x in temp) > 32:
		temp = textwrap.fill("\n".join(temp), 32, initial_indent=" " * (indent * 32 // 80))
	else:
		temp = "\n".join(temp)
	grouped.append(temp)

with open(args.output, "w", encoding=args.encoding) as f:
	f.write("\n".join(grouped))
