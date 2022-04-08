#!/usr/bin/env python3

# Requirements:
# pip3 install libscrc pillow

"""
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""

from argparse import ArgumentParser, FileType
from io import SEEK_CUR
from libscrc import modbus
from PIL import Image
from struct import unpack


def bannergif(rom, output):
	"""Extracts a DS(i) ROM's icon to an image"""

	# Load version and check checksums
	version, _, _, _, dsiChecksum = unpack("<HHHHH", rom.read(10))

	if version & 0x100:
		rom.seek(0x1240)
		data = rom.read(0x1180)
		if dsiChecksum != modbus(data):
			print("Warning: DSi icon checksum failed, using DS icon")
			version &= ~0x100

	rom.seek(0)

	# Load banner data
	bitmaps = []
	palettes = []
	animation = []
	if version == 0x103:  # DSi (animated)
		# Read frame bitmaps
		rom.seek(0x1240, SEEK_CUR)
		for _ in range(8):
			bitmap = [0] * 32 * 32
			for ty in range(4):
				for tx in range(4):
					for y in range(8):
						for x in range(4):
							byte = unpack("B", rom.read(1))[0]
							bitmap[((ty * 8 + y) * 32) + tx * 8 + x * 2] = byte & 0xF
							bitmap[((ty * 8 + y) * 32) + tx * 8 + x * 2 + 1] = byte >> 4
			bitmaps.append(bitmap)

		# Read palettes
		for _ in range(8):
			palette = [0] * 256 * 3  # Pillow wants a 256 color palette with RGB separated
			for i in range(0x10):
				color = unpack("<H", rom.read(2))[0]
				palette[i * 3] = round((color & 0x1F) * 255 / 31)
				palette[i * 3 + 1] = round(((color >> 5) & 0x1F) * 255 / 31)
				palette[i * 3 + 2] = round(((color >> 10) & 0x1F) * 255 / 31)
			palettes.append(palette)

		# Read animation sequence
		for i in range(0x40):
			value = unpack("<H", rom.read(2))[0]
			animation.append({
				"vflip": True if value & (1 << 15) else False,
				"hflip": True if value & (1 << 14) else False,
				"palette": (value >> 11) & 7,
				"bitmap": (value >> 8) & 7,
				"duration": value & 0xFF
			})
	else:  # DS
		# Read bitmap
		rom.seek(0x20, SEEK_CUR)
		bitmap = [0] * 32 * 32
		for ty in range(4):
			for tx in range(4):
				for y in range(8):
					for x in range(4):
						byte = unpack("B", rom.read(1))[0]
						bitmap[((ty * 8 + y) * 32) + tx * 8 + x * 2] = byte & 0xF
						bitmap[((ty * 8 + y) * 32) + tx * 8 + x * 2 + 1] = byte >> 4
		bitmaps.append(bitmap)

		# Read palette
		palette = [0] * 256 * 3  # Pillow wants a 256 color palette with RGB separated
		for i in range(0x10):
			color = unpack("<H", rom.read(2))[0]
			palette[i * 3] = round((color & 0x1F) * 255 / 31)
			palette[i * 3 + 1] = round(((color >> 5) & 0x1F) * 255 / 31)
			palette[i * 3 + 2] = round(((color >> 10) & 0x1F) * 255 / 31)
		palettes.append(palette)

		# No animation, just show the first frame as there's only one
		animation = [{
			"vflip": False,
			"hflip": False,
			"palette": 0,
			"bitmap": 0,
			"duration": 1
		}]

	# Convert to Pillow image
	images = []
	delays = []
	for i, frame in enumerate(animation):
		# Animation ends when the animation u16 is 0, since it's split here
		# for ease of use checking just the duration should be fine
		if frame["duration"] == 0 and i > 0:
			break

		# 32x32 Paletted image
		img = Image.frombytes("P", (32, 32), bytes(bitmaps[frame["bitmap"]]))
		img.putpalette(palettes[frame["palette"]])

		# Flip the image if needed
		if(frame["hflip"]):
			img = img.transpose(Image.FLIP_LEFT_RIGHT)
		if(frame["vflip"]):
			img = img.transpose(Image.FLIP_TOP_BOTTOM)

		# Add it to the output list
		images.append(img)
		# The 'duration' is in frames (1/60th of a second), Pillow wants
		# miliseconds. (though GIFs are actually centiseconds)
		# Also, basically all GIF viewers will wait longer if the delay is
		# under 20 miliseconds, so use that as the minimum. If you want
		# more accurate timing you'll need a different output format.
		delays.append(max(frame["duration"] * 1000 // 60, 20))

	# Fix delay alignment, GIFs want it 1 frame after
	delays = delays[-1:] + delays[:-1]

	# Save output image
	images[0].save(output, save_all=True, append_images=images[1:], duration=delays, loop=0, optimize=False)


if __name__ == "__main__":
	parser = ArgumentParser(description="Extracts a DS(i) ROM's icon to an image")
	parser.add_argument("input", metavar="input.nds", type=FileType("rb"), help="DS ROM")
	parser.add_argument("-o", "--output", metavar="output.gif", default="output.gif", type=str, help="output image")

	args = parser.parse_args()

	bannergif(args.input, args.output)