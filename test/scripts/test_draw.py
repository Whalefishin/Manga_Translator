
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


from text_draw import TextDraw
from manga_translator import parse_arguments
import pickle


args = parse_arguments()

textDraw = TextDraw(args, args.font_style, args.font_size)

f = open('test/textBoxList', 'rb')
textBoxList = pickle.load(f)
textList_trans = ['What do you say?', 'Thank you!', 'Home', 'Comment', 'Home', \
    "I've done my strength as the master of hiring me down!", 'Home', '...', 'Home', \
    'Home', 'Test JPN: だから僕と付き合って正解だったろ？', '...', '!', 'Test emoji: ♥♥♪']
# textList_trans_chinese = ['What do you say?', 'Thank you!', 'Home', 'Comment', 'Home', \
# "I've done my strength as the master of hiring me down!", 'Home', '...', 'Home', \
# 'Home', 'Home', '...', '!', 'Home']
fileName = 'test/inpainted.PNG'


textDraw.drawTextToImage(fileName, textBoxList, textList_trans, 'test', 'test/results')


print ("Done")