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
print (parent)

from PIL import Image
import pytesseract
from manga_ocr import MangaOcr

mocr = MangaOcr()
text = mocr('test/dirty2.png')
print (text)

custom_oem_psm_config = r'--psm 5'
text = pytesseract.image_to_string(Image.open(filename), lang='jpn_vert', config=custom_oem_psm_config)
