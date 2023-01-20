import cv2
import os
from tqdm import tqdm

class TextDetection():
    def __init__(self, args):
        self.contourSize = args.contour_size
        self.args = args
    
    ### text cropping rectangle
    def text_detect(self, img, ele_size=(8,2)): #
        #https://github.com/qzane/text-detection
        if len(img.shape) == 3:
            img = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
        img_sobel = cv2.Sobel(img,cv2.CV_8U,1,0) #same as default,None,3,1,0,cv2.BORDER_DEFAULT)
        img_threshold = cv2.threshold(img_sobel, 0, 255, cv2.THRESH_OTSU+cv2.THRESH_BINARY)
        element = cv2.getStructuringElement(cv2.MORPH_RECT, ele_size)
        # do a close (dilation followed by erosion) to close up small holes in the mask
        img_threshold_morp = cv2.morphologyEx(img_threshold[1], cv2.MORPH_CLOSE, element)
        
        contours, hierarchy = cv2.findContours(img_threshold_morp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # image, contours, hierarchy = cv2.findContours(img_threshold_morp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        noiseSizeParam = int(ele_size[0]/3)
        contours = [i for i in contours if i.shape[0] > noiseSizeParam** 2]     
        Rect = [cv2.boundingRect(i) for i in contours] # no padding   
        RectP = [(max(int(i[0]-noiseSizeParam),0),max(int(i[1]-noiseSizeParam),0),\
            min(int(i[0]+i[2]+noiseSizeParam),img.shape[1]),min(int(i[1]+i[3]+noiseSizeParam), img.shape[0])) for i in Rect]       #with padding, box  x1,y1,x2,y2 

        return RectP, Rect

    def textDetect(self, imgPath, textOnlyFolder):
        """Detect and separate all segmented texts into blocks of texts

        Args:
            imgPath: file path for the original image (raw manga)
            textOnlyFolder: directory for the text-only image

        Returns:
            rectList: list of rectangle specifying the location for each block of text
        """
        fileName = os.path.basename(imgPath)
        img = cv2.imread(os.path.join(textOnlyFolder, fileName))
        rectP,rect = self.text_detect(img, ele_size=(int(img.shape[0]*self.contourSize),int(img.shape[0]*self.contourSize)))  #x,y
        rectList = [rectP,rect]
            
        return rectList



    def post_process(self, text_box_list, text_mask, seg_engine):
        pass

        # go through the boxes, use Tesseract OCR confidence to assess whether they contain real texts

        # based on the new boxes, update the text mask, then inpaint the original image.

        # return the updated list of text boxes, which will be subsequently OCR-ed and translated
