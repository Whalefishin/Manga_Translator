import os
originalWorkingPath=os.getcwd()
import sys
sys.path.append("./lib_/sickzil_machine/src")
sys.path.insert(0, './lib_/manga_text_segmentation/code')
from fastai.vision import *
from dataset import *
import tensorflow as tf
import core
import imgio
import utils.fp as fp
import cv2
from tqdm import tqdm
import consts
import tensorflow as tf
from skimage.morphology import square
import fastai
import pytesseract

class TextSegmenationDetection():
    def __init__(self, engine, args):
        self.args = args
        self.seg_engine = TextSegmenation(engine, args)
        self.detector   = TextDetection(args)


    def segment_and_detect(self, imgPath, outputInpaintedPath, outputTextOnlyPath):

        fileName = os.path.basename(imgPath)
        save_path_text_only_img = os.path.join(outputTextOnlyPath, fileName)
        save_path_inpainted_img = os.path.join(outputInpaintedPath, fileName)
        # inpaint to get textless image
        oriImage = imgio.load(imgPath, imgio.IMAGE) # L x W x C

        print ("================== Started segmentation ==================")
        txt_mask = self.seg_engine.segmentPage(imgPath, outputInpaintedPath, outputTextOnlyPath)
        print ("================== Finished segmentation ==================")
        print ("================== Started text box detection ==================")
        txt_mask, textOnlyImage, txt_boxes = self.detector.text_detect(txt_mask, oriImage)
        print ("================== Finished text box detection ==================")

        # get the image of segmented texts and save the images
        # textOnlyImage = cv2.bitwise_and(oriImage, txt_mask)
        # textOnlyImage[txt_mask==0] = 255
        imgio.save(save_path_text_only_img, textOnlyImage)
        # we inpaint the textless image, in case the text cropping took out some drawings
        inpaintedImage = self.seg_engine.inpaint_image(oriImage, txt_mask)
        imgio.save(save_path_inpainted_img, inpaintedImage)

        return txt_boxes



class TextDetection():
    def __init__(self, args):
        self.contourSize = args.contour_size
        self.args = args
    
    ### text cropping rectangle
    def text_detect(self, txt_mask, img_orig):
        ele_size = (int(txt_mask.shape[0] * self.contourSize), int(txt_mask.shape[0] * self.contourSize))
        #https://github.com/qzane/text-detection
        if len(txt_mask.shape) == 3:
            img = cv2.cvtColor(txt_mask,cv2.COLOR_BGR2GRAY)
        else:
            img = txt_mask
        img_sobel = cv2.Sobel(img, cv2.CV_8U,1, 0) #same as default,None,3,1,0,cv2.BORDER_DEFAULT)
        img_threshold = cv2.threshold(img_sobel, 0, 255, cv2.THRESH_OTSU+cv2.THRESH_BINARY)
        element = cv2.getStructuringElement(cv2.MORPH_RECT, ele_size)
        # do a close (dilation followed by erosion) to close up small holes in the mask
        img_threshold_morp = cv2.morphologyEx(img_threshold[1], cv2.MORPH_CLOSE, element)
        
        contours, hierarchy = cv2.findContours(img_threshold_morp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # image, contours, hierarchy = cv2.findContours(img_threshold_morp, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        
        noiseSizeParam = int(ele_size[0]/3)
        contours = [c for c in contours if c.shape[0] > noiseSizeParam** 2]     
        Rect = [cv2.boundingRect(i) for i in contours] # no padding   
        RectP = [(max(int(i[0]-noiseSizeParam),0),max(int(i[1]-noiseSizeParam),0),\
            min(int(i[0]+i[2]+noiseSizeParam),img.shape[1]),min(int(i[1]+i[3]+noiseSizeParam), img.shape[0])) for i in Rect]       #with padding, box  x1,y1,x2,y2 

        # Post processing
        # go through the boxes, use Tesseract OCR confidence to assess whether they contain real texts.
        # Based on the new boxes, update the text mask, which is used to inpaint the original image.
        textOnlyImage = cv2.bitwise_and(img_orig, txt_mask)
        textOnlyImage[txt_mask==0] = 255
        if self.args.conf_filter:
            I_keep = []
            custom_oem_psm_config = r'--psm 5' # important Tesseract option for vertical texts
            for i,r in enumerate(RectP):
                x1, y1, x2, y2 = r
                # Cropping the text block for giving input to OCR 
                cropped = textOnlyImage[y1: y2, x1: x2] 
                text_Tes = pytesseract.image_to_data(cropped, lang='jpn_vert', config=custom_oem_psm_config, \
                                                    output_type='data.frame')
                conf = text_Tes['conf'].to_numpy()
                conf_avg = conf[conf != -1].mean()

                # if Tesseract has low confidence on the output, which typically
                # happens if the image has no text, or if the texts are written in some 
                # nonconventional script (typically some onomatopoeia).
                # In this case, we do not OCR it for downstream translation
                if not np.isnan(conf_avg) and conf_avg > self.args.conf_filter_thres:
                    I_keep.append(i)

            # keep the boxes that actually contain texts
            contours = [contours[i] for i in I_keep]
            Rect     = [Rect[i] for i in I_keep]
            RectP    = [RectP[i] for i in I_keep]

            # adjust the masks so to match the new boxes
            mask_new = np.zeros(txt_mask.shape, np.uint8)
            mask_new = cv2.drawContours(mask_new, contours, -1, (255,255,255), -1)
            txt_mask = cv2.bitwise_and(mask_new, txt_mask)
            textOnlyImage = cv2.bitwise_and(img_orig, txt_mask)
            textOnlyImage[txt_mask==0] = 255

        return txt_mask, textOnlyImage, [RectP, Rect]

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
        rectP,rect = self.text_detect(img,ele_size=(int(img.shape[0]*self.contourSize),int(img.shape[0]*self.contourSize)))  #x,y
        rectList = [rectP,rect]
            
        return rectList



class TextSegmenation():
    def __init__(self, engine, args):
        self.engine = engine
        self.args = args
        if args.manga_seg_load_cpu:
            fastai.core.defaults.device = torch.device("cpu")
    
    def imgpath2mask(self, imgpath):
        return fp.go(
            imgpath,
            lambda path: imgio.load(path, imgio.NDARR),     
            core.segmap,
            imgio.segmap2mask)

    def resize(self, imgPath):
        img = cv2.imread(imgPath) 
        if self.engine == 'sickzil':
            # text resize by 1000px height 
            size = 1000
            if img.shape[0] > size:
                img = cv2.resize(img, (int(size*img.shape[1]/img.shape[0]), size), interpolation = cv2.INTER_AREA)
                cv2.imwrite(imgPath, img) 
        elif self.engine == 'manga_seg':
            # the model seems to require the input image to have even numbers as dimensions
            # could be a minor bug on their side. We'll just reshape the images so that this is true
            if img.shape[0] % 2 != 0 and img.shape[1] % 2 != 0:
                img = cv2.resize(img, (img.shape[1]-1, img.shape[0]-1), interpolation = cv2.INTER_AREA)
            elif img.shape[1] % 2 != 0:
                img = cv2.resize(img, (img.shape[1]-1, img.shape[0]), interpolation = cv2.INTER_AREA)   
            elif img.shape[0] % 2 != 0:
                img = cv2.resize(img, (img.shape[1], img.shape[0]-1), interpolation = cv2.INTER_AREA)  
            cv2.imwrite(imgPath, img) 
        else:
            raise NotImplementedError()
            
    def segmentPage(self, imgPath, outputInpaintedPath, outputTextOnlyPath):
        """Segments the texts from the drawings on a manga page with the specified model

        Args:
            imgPath: file path of the original manga page
            outputInpaintedPath: directory to save the manga page with texts cropped out
            outputTextOnlyPath: directory to save the image of the cropped out texts

        """
        fileName = os.path.basename(imgPath)
        save_path_text_only_img = os.path.join(outputTextOnlyPath, fileName)
        save_path_inpainted_img = os.path.join(outputInpaintedPath, fileName)
        # preprocess the image size
        # for example, sickzil has poor quality on high resolution image, so we downsize it if necessary
        self.resize(imgPath) 

        if self.engine == 'sickzil':
            # sickzil has poor quality on high resolution image, so we downsize it if necessary
            # self.resize(imgPath) 
            # oriImage = imgio.load(imgPath, imgio.IMAGE) # L x W x C
            maskImage  = imgio.mask2segmap(self.imgpath2mask(imgPath))       # mask image : L x W x C
            # we also inpaint the textless image, in case the text cropping took out some drawings
            # inpaintedImage = core.inpainted(oriImage, maskImage)             # no-text image

        elif self.engine == 'manga_seg':
            im = open_image(imgPath)
            model = load_learner('./lib_/models', 'manga_txt_model.pkl')
            # segmentation
            pred = model.predict(im)[0]
            mask = unpad_tensor(pred.px, im.px.shape)[0] # L x W
            # add a small dilation to buff up the masks so that we cover the texts
            if self.args.mask_dilation_radius == 0:
                mask = binary_dilation(mask)
            else:
                mask = binary_dilation(mask, footprint=square(self.args.mask_dilation_radius))
            # img is the real mask used
            img = torch.ones(im.px.shape) * 255
            img = img.permute(1,2,0) # L x W x C
            # NOTE: you don't have to release the GPU cache if you have enough GPU memory to go around
            torch.cuda.empty_cache()
            img[mask==1] = 0
            # invert img to get the mask. 
            # In a perfect world, the mask should perfectly lay on top of  all the texts on the page.
            # In practice, some non-texts may also be masked, and we have slightly dilated the mask
            # to make sure it covers a tubular neighborhood around the texts, so that we don't miss
            # thin strokes, etc.
            maskImage = (-img + 255).numpy().astype(np.uint8)
            
        else:
            raise NotImplementedError()

        # # save output images
        # # If we wish to do some post-processing, defer saving output images until that's finished.
        # if not self.args.txt_box_postprocess:
        #     oriImage = imgio.load(imgPath, imgio.IMAGE) # L x W x C
        #     # get the image of segmented texts and save the images
        #     textOnlyImage = cv2.bitwise_and(oriImage, maskImage) 
        #     textOnlyImage[maskImage==0] = 255
        #     imgio.save(save_path_text_only_img, textOnlyImage)
        #     # we inpaint the textless image, in case the text cropping took out some drawings
        #     inpaintedImage = self.inpaint_image(oriImage, maskImage)
        #     imgio.save(save_path_inpainted_img, inpaintedImage)

        return maskImage
    
    def inpaint_image(self, original, mask):
        return core.inpainted(original, mask)