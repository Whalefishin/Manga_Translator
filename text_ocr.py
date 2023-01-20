from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import io
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import pickle
from tqdm import tqdm
import cv2
import re
import subprocess
import pytesseract
from manga_ocr import MangaOcr
import PIL.Image
from ocr_utils import analyse_image
import numpy as np

class TextOcr():
    def __init__(self, args, OCR_folder, ocrType):
        self.service=None
        self.ocrType=ocrType
        self.OCR_folder = OCR_folder
        self.args = args
        if self.ocrType == 'manga_ocr':
            self.mocr = MangaOcr()

    def getTextTesseractOcr(self, img, txt_idx=0, fname='1'):
        """Use Tesseract to OCR texts

        Args:
            img: image of the cropped text box to be OCR-ed
            txt_idx (int, optional): idx for the text line, only used in debug outputs. Defaults to 0.

        Returns:
            text: OCR results
        """

        # break text boxes into individual lines to improve OCR results
        text_lines = analyse_image(img) 
        text = ''
        text_list = [] # used in debug mode
        for line in text_lines:
            custom_oem_psm_config = r'--psm 5' # important Tesseract option for vertical texts
            text_ocr = pytesseract.image_to_string(line, lang='jpn_vert', config=custom_oem_psm_config)
            text_ocr = self.filterText(text_ocr)
            text += text_ocr
            text_list.append(text_ocr)

        if self.args.verbose: # debugging outputs
            cv2.imwrite(os.path.join(self.OCR_folder, 'text{}.png'.format(txt_idx)), img)
            for i, t in enumerate(text_lines):
                save_dir = os.path.join(self.OCR_folder, 'text{}_line{}.png'.format(txt_idx, str(i)))
                log_dir = os.path.join(self.OCR_folder, 'log.txt')
                cv2.imwrite(save_dir, t)
                with open(log_dir, 'a', encoding='utf8') as f:
                    f.write('text {} line {} reads: {} \n'.format(txt_idx, str(i), text_list[i]))

                f.close()

        return text
    
    def getTextMangaOcr(self, img, txt_idx=0, fname='1'):
        """Use Manga-OCR to detect texts

        Args:
            img: image of the cropped text box to be OCR-ed
            txt_idx (int, optional): idx for the text line, only used in debug outputs. Defaults to 0.

        Returns:
            text: OCR results
        """
        image = PIL.Image.fromarray(img)
        text = self.mocr(image)

        # Idea: have some type of sanity check that the img contains to be texts at all
        # because manga-ocr will decipher texts even if there are none.
        # NOTE: manga-ocr doesn't provide a confidence measure for its outputs
        # so we borrow the average confidence from Tesseract on the same img
        if self.args.conf_filter:
            custom_oem_psm_config = r'--psm 5' # important Tesseract option for vertical texts
            text_Tes = pytesseract.image_to_data(image, lang='jpn_vert', config=custom_oem_psm_config, \
                                                output_type='data.frame')
            conf = text_Tes['conf'].to_numpy()
            conf_avg = conf[conf != -1].mean()

            # if Tesseract has low confidence on the output, which typically
            # happens if the image has no text, or if the texts are written in some 
            # nonconventional script (typically some onomatopoeia).
            # In this case, we do not OCR it for downstream translation
            if np.isnan(conf_avg) or conf_avg < self.args.conf_filter_thres:
                text = ''

        if self.args.verbose:
            cv2.imwrite(os.path.join(self.OCR_folder, '{}_text{}.png'.format(fname, txt_idx)), img)
            save_dir = os.path.join(self.OCR_folder, '{}_text{}.png'.format(fname, txt_idx))
            log_dir = os.path.join(self.OCR_folder, 'log.txt')
            cv2.imwrite(save_dir, img)
            with open(log_dir, 'a', encoding='utf8') as f:
                if self.args.conf_filter:
                    f.write('Image {}, text {} reads: {}; Tesseract conf: {:.2f} \n'.format(fname, txt_idx, text, conf_avg))
                else:
                    f.write('Image {}, text {} reads: {} \n'.format(fname, txt_idx, text))
            f.close()

        return text

    def getTextFromImg(self, imgPath, rectList, textOnlyFolder):
        """OCR all the texts from the given image and text locations on the image

        Args:
            imgPath: file path for the image to OCR
            rectList: list of rectangles that specifies text locations
            textOnlyFolder: directory to read the segmentation results (image of only texts) 

        Returns:
            textList: list of texts OCR-ed from the input image
        """
        fileName = os.path.basename(imgPath)
        img = cv2.imread(os.path.join(textOnlyFolder, fileName))
        textList = []
        rectP, rect = rectList
        for i, r in enumerate(rectP): 
            x1, y1, x2, y2 = r
            # Cropping the text block for giving input to OCR 
            cropped = img[y1: y2, x1: x2] 
            # OCR
            if self.ocrType == "tesseract":
                text = self.getTextTesseractOcr(cropped, txt_idx=i, fname=fileName)
            elif self.ocrType == 'manga_ocr':
                text = self.getTextMangaOcr(cropped, txt_idx=i, fname=fileName)
            else:
                raise NotImplementedError()
            
            textList += [text]
        
        return textList
        
 