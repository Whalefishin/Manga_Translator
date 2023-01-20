from PIL import Image, ImageFont, ImageDraw  
import textwrap              
from tqdm import tqdm
import os

class TextDraw():
    def __init__(self, args, fontStyle, fontSize):
        self.fontStyle = fontStyle
        self.fontSize = fontSize
        self.args = args
        self.lang = args.target_lang
    
    def getFont(self, font_size):
      """ loads the specified font in a particular size

      Args:
          font_size (int): size of the font used

      Returns:
          font
      """
      if self.fontStyle == 'baskerville':
        font = ImageFont.truetype('lib_/fonts/LibreBaskerville-Regular.ttf', font_size)
      elif self.fontStyle == 'gidole':
        font = ImageFont.truetype('lib_/fonts/Gidole-Regular.ttf', font_size)
      elif self.fontStyle == 'komika':
        font = ImageFont.truetype('lib_/fonts/komika-hand.ttf', font_size)
      elif self.fontStyle == 'komika_merged':
        font = ImageFont.truetype('lib_/fonts/Komika_merged.ttf', font_size)
      elif self.fontStyle == 'emoji':
        font = ImageFont.truetype('lib_/fonts/NotoEmoji.ttf', font_size)
      elif self.fontStyle == 'NotoSans':
        font = ImageFont.truetype('lib_/fonts/NotoSansSC-Regular.otf', font_size)
      elif self.fontStyle == 'FZHT':
        font = ImageFont.truetype('lib_/fonts/FZHT.TTF', font_size)
      else:
        font = ImageFont.load_default()

      return font

    def determine_font_size(self, w_box, h_box, w_img):
      """determine the font size and adjustments to the box size

      Args:
          w_box (float): width of the text box
          h_box (float): height of the text box
          w_img (float): width of the entire image

      Returns:
          w_box, font_size: adjusted text box width, computed font size
      """

      # NOTE: these are rough estimates. They may require additional tuning.
      default_size = int(w_img * 0.012)
      min_letters_per_line = 5
      max_letters_per_line = 20

      # this block deals with font size being too big for the box
      # first, check whether the box is thin, possibly with only a single line of vertical text
      if w_box // default_size < min_letters_per_line: 
        # hacky solution: use the height of the box as an estimate for how much 
        # space we need to allow for words
        w_box = max(w_box, h_box // 2)
      
      # the default size may be too small for some huge boxes
      # in this case, scale the font up
      font_size = max(default_size, w_box // max_letters_per_line)
      
      return w_box, font_size

    def drawText(self, imgPath, rect, textList):
      """Draw text on the text-less manga image on the location specified by rect

      Args:
          imgPath: file path for the textless manga
          rect: specifies the dimensions of the textbox. Format: (x,y,w,h), where (x,y) is the top left corner.
          textList: list of translated texts to draw

      Returns:
          img: manga page with translated texts
      """
      img = Image.open(imgPath)
      draw = ImageDraw.Draw(img)
      # we draw a thin layer of white around the texts, so that they're 
      # visually isolated from the background drawings if they happen to overlap.
      shadowcolor = (255,255,255)
      strokeSize = 2

      for text, (x,y,w,h) in zip(textList, rect):
        if text == "": continue

        if self.lang == 'english':
          # determine font size
          if self.fontSize != 0:
            fontSize = self.fontSize # use the manually set font size
          else:
            w, fontSize = self.determine_font_size(w, h, img.size[1])
          imageFont = self.getFont(fontSize)
          # enlarge the text box horizontally so that Roman letters fit a bit better
          w *= self.args.text_pad_ratio
          # shift the left side to the left so the enlargement is shared equally between left and right
          x -= max(0, (self.args.text_pad_ratio - 1) * w // 2)

          # check for illegal characters, which may happen for some translators
          # if not text.isascii(): continue
          # split text to fit into box
          for line in textwrap.wrap(text, width=w//fontSize+1, break_long_words=self.args.break_long_words):   
            # draw border
            draw.text((x-strokeSize, y), line, font=imageFont, fill=shadowcolor)
            draw.text((x+strokeSize, y), line, font=imageFont, fill=shadowcolor)
            draw.text((x, y-strokeSize), line, font=imageFont, fill=shadowcolor)
            draw.text((x, y+strokeSize), line, font=imageFont, fill=shadowcolor)
            # draw thicker border
            draw.text((x-strokeSize, y-strokeSize), line, font=imageFont, fill=shadowcolor)
            draw.text((x+strokeSize, y-strokeSize), line, font=imageFont, fill=shadowcolor)
            draw.text((x-strokeSize, y+strokeSize), line, font=imageFont, fill=shadowcolor)
            draw.text((x+strokeSize, y+strokeSize), line, font=imageFont, fill=shadowcolor)
            #draw text
            draw.text((x, y), line, font=imageFont, fill=(0, 0, 0))  #black

            y += fontSize + strokeSize
        elif self.lang == 'chinese_simplified':
          # # determine font size
          # if self.fontSize != 0:
          #   fontSize = self.fontSize # use the manually set font size
          # else:
          #   w, fontSize = self.determine_font_size(w, h, img.size[1])
          # imageFont = self.getFont(fontSize)

          # # enlarge the text box horizontally so that Roman letters fit a bit better
          # w *= self.args.text_pad_ratio
          # # shift the left side to the left so the enlargement is shared equally between left and right
          # x -= max(0, (self.args.text_pad_ratio - 1) * w // 2)

          # no need to do the adjustments to box dimensions because chinese tends to
          # take up less space and we'll also draw it vertically, so it will likely fit. 
          fontSize = int(img.size[1] * 0.018)
          imageFont = self.getFont(fontSize)
          # ideally, we start drawing on the top right corner if the text box is perfectly identified
          # in practice, we go back a bit to the left from the top right corner and start there.
          x_curr_pos = x + w - int(w // 3) 
          y_curr_pos = y
          y_lim = y + h
          for c in text:
            # draw thin border
            draw.text((x_curr_pos - strokeSize, y_curr_pos), c, font=imageFont, fill=shadowcolor)
            draw.text((x_curr_pos + strokeSize, y_curr_pos), c, font=imageFont, fill=shadowcolor)
            draw.text((x_curr_pos, y_curr_pos-strokeSize), c, font=imageFont, fill=shadowcolor)
            draw.text((x_curr_pos, y_curr_pos+strokeSize), c, font=imageFont, fill=shadowcolor)
            # draw thicker border
            draw.text((x_curr_pos - strokeSize, y_curr_pos-strokeSize), c, font=imageFont, fill=shadowcolor)
            draw.text((x_curr_pos + strokeSize, y_curr_pos-strokeSize), c, font=imageFont, fill=shadowcolor)
            draw.text((x_curr_pos - strokeSize, y_curr_pos+strokeSize), c, font=imageFont, fill=shadowcolor)
            draw.text((x_curr_pos + strokeSize, y_curr_pos+strokeSize), c, font=imageFont, fill=shadowcolor)
            # draw text in black
            draw.text((x_curr_pos, y_curr_pos), c, font=imageFont, fill=(0, 0, 0))

            y_curr_pos += fontSize + strokeSize
            if y_curr_pos >= y_lim: # switch to the next vertical line on the left
              y_curr_pos = y
              x_curr_pos = x_curr_pos - (fontSize + strokeSize)
        else:
          raise NotImplementedError()

      return img

    def drawTextToImage(self, imgPath, textBoxList, textListList_trans, inpaintedFolder, transalatedFolder):
      """A wrapper for drawText() that saves the image with drawn translated texts.

      Args:
          imgPath: file name for the textless image
          textBoxList: list of text boxes 
          textListList_trans: list of translated texts
          inpaintedFolder: directory to find the textless image
          transalatedFolder: directory to save the translated image
      """
      fileName = os.path.basename(imgPath)
      rectP, rect = textBoxList
      im = self.drawText(os.path.join(inpaintedFolder, fileName), rect, textListList_trans)
      im.save(os.path.join(transalatedFolder, fileName)) 
        
        