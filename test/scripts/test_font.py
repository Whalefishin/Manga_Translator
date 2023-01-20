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

def text(output_path):
    font_size = 16
    image = Image.new("RGB", (200, 200), "green")
    draw = ImageDraw.Draw(image)
    # font = ImageFont.load_default()
    # font = ImageFont.truetype('lib_/fonts/Gidole-Regular.ttf', font_size)
    font = ImageFont.truetype('lib_/fonts/LibreBaskerville-Regular.ttf', font_size)
    draw.text((10, 10), "Hello from", font=font)
    draw.text((10, 25), "Pillow", font=font)
    image.save(output_path)

if __name__ == "__main__":
    text("test/results/text_draw.jpg")