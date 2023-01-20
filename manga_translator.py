from folder_manager import FolderManager
from text_segmentation import TextSegmenation, TextSegmenationDetection
# from text_detection import TextDetection
from text_ocr import TextOcr
from text_translate import TextTranslator
from text_draw import TextDraw
import argparse
import os
import pickle
from tqdm import tqdm
import time
import threading
import glob

def parse_arguments():
    parser = argparse.ArgumentParser()

    # meta
    parser.add_argument('--raw_dir',          type=str, default='./test/orig_page', \
                                                help='The directory containing the raw manga')
    parser.add_argument('--result_root_dir',  type=str, default='./results', \
                                                help='The main folder containing all translation results.')
    parser.add_argument('--result_name',      type=str, default='test', \
                                                help='The subfolder containing the translation results. For example, this can be the manga name.')
    parser.add_argument('--verbose',          action='store_true', default=False, help='whether to display and save additional outputs for debugging')
    parser.add_argument('--overwrite',        action='store_true', default=False, help='whether to overwrite the result folder if one already exists.')
    
    # segmentation
    parser.add_argument('--seg_engine',           type=str, default='manga_seg', choices=['sickzil', 'manga_seg'], help='name of the segmentation model used.')
    parser.add_argument('--mask_dilation_radius', type=int, default=4, help='Bigger = more aggressive dilation = we capture a larger neighborhood around the mask')
    parser.add_argument('--manga_seg_load_cpu',   action='store_true', default=False, help='Whether to load the Manga-text-segmentation model on CPU. Enable if you run out of VRAM')

    # detection
    # parser.add_argument('--txt_box_postprocess', type=lambda x: (str(x).lower() == 'true'), default=False, help='Whether to post process the text box detected.')
    parser.add_argument('--contour_size',     type=float, default=0.025, help='used to determine text boxes in the detector')

    # OCR
    parser.add_argument('--OCR_engine',       type=str, default='manga_ocr', choices=['tesseract', 'manga_ocr'], help='name of the OCR model used.')
    parser.add_argument('--conf_filter',      type=lambda x: (str(x).lower() == 'true'), default=True, help='Whether to filter out OCR outputs by confidence levels from e.g. Tesseract')
    parser.add_argument('--conf_filter_thres',type=float, default=40., help='used to determine text boxes in the detector')

    # tranlation
    parser.add_argument('--translator',       type=str, default='argos', choices=['argos', 'google', 'eztrans'], help='name of the translation model used')
    parser.add_argument('--font_style',       type=str, default='komika', \
                                                choices=['default', 'gidole', 'baskerville', 'komika',\
                                                         'NotoSans', 'FZHT', 'emoji', 'komika_merged'], help='name of the font used')
    parser.add_argument('--font_size',        type=int, default=0, help='0 means picking a size automatically based on text bubble sizes')
    parser.add_argument('--source_lang',      type=str, default='japanese', choices=['japanese'], help='name of the source language, i.e., one that is on the raw manga.')
    parser.add_argument('--target_lang',      type=str, default='english', choices=['english', 'chinese_simplified'], help='language you wish to translate to')

    # formatter
    parser.add_argument('--break_long_words', type=lambda x: (str(x).lower() == 'true'), default=False, help='break long words into multiple lines in the formatter')
    parser.add_argument('--text_pad_ratio',   type=float, default=1.0, help='ratio to widen the text box in the formatter')


    args = parser.parse_args()

    return args


class MangaTranslator():
    def __init__(self, args):
        self.args = args
        # for directory management
        self.folder = FolderManager(args)
        # initialize different modules
        # self.textSegmentation = TextSegmenation(args.seg_engine, args)
        # self.textDetection    = TextDetection(args)
        self.text_seg_detector = TextSegmenationDetection(args.seg_engine, args)
        self.textOcr          = TextOcr(args, self.folder.OCR_folder, args.OCR_engine)
        self.textTranslator   = TextTranslator(args, args.translator, self.folder.OCR_folder)
        self.textDraw         = TextDraw(args, args.font_style, args.font_size)

        # self.textPostProcessor = TestPostProcessor(args, self.folder.inpaintedFolder, \
        #                                             self.textSegmentation, self.textDection)

        
    def run(self):
        # get all the manga files to be translated
        oriFileList = glob.glob(self.args.raw_dir + '/*')
        # process by page
        for fileName in tqdm(oriFileList): 
            self.processTranslationTask(fileName)
        
        print ("All done!")
        

    def processTranslationTask(self, fileName):
        # text segmentation
        # print ("================== Started segmentation ==================")
        # # the outputs here are two images: one in the text-only folder with all the segmented texts
        # # the second in the inpainted folder, which is the text-less original manga, with some inpainting 
        # # done to minimize damage to the background.
        # textMask = self.textSegmentation.segmentPage(fileName, self.folder.inpaintedFolder, self.folder.textOnlyFolder)
        # print ("================== Finished segmentation ==================")

        # # text detection
        # print ("================== Started text box detection ==================")
        # textBoxList = self.textDetection.textDetect(fileName, self.folder.textOnlyFolder)
        # print ("================== Finished text box detection ==================")

        # # post-processing for segmentation and detection results
        # print ("================== Started segmentation postprocessing ==================")
        # # outputs the final list of text boxes we will OCR
        # textBoxList = self.textDetection(fileName, textBoxList, textMask, self.textSegmentation)
        # print ("================== Finished segmentation postprocessing ==================")

        textBoxList = self.text_seg_detector.segment_and_detect(fileName, \
                                    self.folder.inpaintedFolder, self.folder.textOnlyFolder)

        # text ocr
        print ("================== Started OCR ==================")
        textList = self.textOcr.getTextFromImg(fileName, textBoxList, self.folder.textOnlyFolder)
        print ("================== Finished OCR ==================")

        # text translation
        print ("================== Started Translation ==================")
        textList_trans = self.textTranslator.translate(textList)
        print ("================== Finished Translation ==================")
        
        # text draw
        print ("================== Started rendering the translated page ==================")
        self.textDraw.drawTextToImage(fileName, textBoxList, textList_trans, \
            self.folder.inpaintedFolder, self.folder.transalatedFolder)
        print ("================== Finished rendering the translated page ==================")


if __name__ == "__main__":
    args = parse_arguments()
    mangaTranslator = MangaTranslator(args)
    mangaTranslator.run()
        


