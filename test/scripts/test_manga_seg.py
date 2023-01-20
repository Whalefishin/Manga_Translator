import os
import sys
from fastai.vision import *

current = os.path.dirname(os.path.realpath(__file__))
 
# Getting the parent directory name
# where the current directory is present.
parent = os.path.dirname(os.path.dirname(current))

sys.path.append(parent + "/lib_/manga_text_segmentation/code")
sys.path.append(parent + "/lib_/sickzil_machine/src")

from dataset import *
import core
import imgio



model = load_learner('lib_/models', 'manga_txt_model.pkl')
     
# im = open_image('lib_/manga_text_segmentation/images/AisazuNihaIrarenai-009.jpg')
im = open_image('test/orig_page/Capture.PNG')
pred = model.predict(im)[0]
     
im.show(figsize=(10, 10))
pred.show(figsize=(10, 10)) # get the image with pred.data
im.show(y=pred, figsize=(22, 22), alpha=0.8)

#save prediction to use with sickzil
m = unpad_tensor(pred.px, im.px.shape) # 1 x L x W
mask = m[0] # L x W

#sickzil works better if we dilate the mask a bit
mask = binary_dilation(mask)

# img = torch.ones(im.px.shape) * 255
# img[1][mask == 1] = 0
# img[2][mask == 1] = 0

# i = Im.fromarray(image2np(img).astype(np.uint8))
# i.putalpha(Im.fromarray((mask == 1).astype(np.uint8) * 255)) # not sure if we need this

# i.save('results/sickzil-009.png', format='PNG')

img = torch.ones(im.px.shape) * 255
a = img.permute(1,2,0) # L x W x C
a[mask==1] = 0
a_img = Im.fromarray(image2np(a.permute(2,0,1)).astype(np.uint8))
a_img.save('test/results/sickzil_black.png', format='PNG')

m = -m.repeat(3,1,1).permute(1,2,0) + 255 # L x W x C
img_orig = im.px.permute(1,2,0)    # L x W x C
torch.cuda.empty_cache()
inpaintedImage = core.inpainted(img_orig, m) 
# inpaintedImage = cv2.inpaint(img_orig, m) 
imgio.save('test/results/inpainted_manga_txt.png', inpaintedImage)



# oriImage = imgio.load('test/capture.PNG', imgio.IMAGE)
# # m_1 = -imgio.load('test_results/sickzil_txt.PNG', imgio.IMAGE) + 255
# m_1 = imgio.mask2segmap(-imgio.load('test_results/sickzil_txt.PNG', imgio.IMAGE) + 255)
# inpaintedImage = core.inpainted(oriImage, m_1) 
# imgio.save('test_results/inpainted.png', inpaintedImage)
