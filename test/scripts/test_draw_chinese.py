import sys
import os
# getting the name of the directory
# where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(os.path.dirname(current))
 
# adding the parent directory to
# the sys.path.
sys.path.append(parent)

from PIL import Image, ImageDraw, ImageFont

font_size = 32
font = ImageFont.truetype('lib_/fonts/FZHT.TTF', font_size)
im = Image.new('RGBA', (100, 100), (0, 0, 0, 0))
draw = ImageDraw.Draw(im)
# draw.text((0, 0), '我和你', 'black', font, direction='ttb')
# draw.text((0, 0), '我和你', 'white', font)
for i,c in enumerate('你说什么'):
    draw.text((0, i*font_size), c, 'white', font)
im.save('test/results/draw_chinese.png')
