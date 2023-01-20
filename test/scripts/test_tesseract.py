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

# We import the necessary packages
#import the needed packages
import cv2
import os,argparse
import pytesseract
from PIL import Image
import numpy as np

# pytesseract.pytesseract.tesseract_cmd = 'D:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'

# We then Construct an Argument Parser
ap=argparse.ArgumentParser()
ap.add_argument("-i","--image",
				required=True,
				help="Path to the image folder")
ap.add_argument("-p","--pre_processor",
				default="thresh",
				help="the preprocessor usage")
args=vars(ap.parse_args())

# We then read the image with text
images=cv2.imread(args["image"])

# convert to grayscale image
gray=cv2.cvtColor(images, cv2.COLOR_BGR2GRAY)

# checking whether thresh or blur
if args["pre_processor"] == "thresh":
	cv2.threshold(gray, 0,255,cv2.THRESH_BINARY| cv2.THRESH_OTSU)[1]
if args["pre_processor"] == "blur":
	cv2.medianBlur(gray, 3)
	
# memory usage with image i.e. adding image to memory
filename = "{}.jpg".format(os.getpid())
cv2.imwrite(filename, gray)

custom_oem_psm_config = r'--psm 5'
text = pytesseract.image_to_string(Image.open(filename), lang='jpn_vert', config=custom_oem_psm_config)


# text = pytesseract.image_to_data(Image.open(filename), \
# 								lang='jpn_vert', config=custom_oem_psm_config, output_type='data.frame')

# conf = text['conf'].to_numpy()
# conf_avg = conf[conf != -1].mean()

print (conf, conf_avg)

os.remove(filename)
print(text)
