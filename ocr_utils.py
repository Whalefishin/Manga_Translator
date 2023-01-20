#! /usr/bin/env python3

# Adapted from: https://github.com/nyorem/python-japanese-ocr/blob/master/main.py


import cv2
from multiprocessing import Pool, cpu_count
import numpy as np
import os
import sys
import time
import pytesseract

nthreads = 6
assert nthreads < cpu_count()

# Binarize an image
def binarize(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
    return binary

# Find the contours (rectangles) of text in an image
def find_contours_text(img, kernel_size, verbose=False, sort_key=None):
    # binarize
    binary = binarize(img)

    # dilation
    kernel = np.ones(kernel_size, dtype=np.uint8)
    dilation = cv2.dilate(binary, kernel, iterations=1)
    if verbose:
        cv2.imshow("dilation", dilation)
        cv2.waitKey(0)

    # find contours
    # _, ctrs, _ = cv2.findContours(dilation.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ctrs, _ = cv2.findContours(dilation.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if sort_key is None:
        sort_key = lambda ctr: cv2.boundingRect(ctr)[0]
    sorted_ctrs = sorted(ctrs, key=sort_key)

    return sorted_ctrs

# Draw contours (rectanglers) over a given image
def draw_contours(ctrs, img, w_rect=2, fname=None, verbose=False):
    img_contours = img.copy()
    for i, ctr in enumerate(ctrs):
        x, y, w, h = cv2.boundingRect(ctr)
        cv2.rectangle(img_contours, (x, y), (x + w, y + h), (0, 255, 0), w_rect)
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(img_contours, str(i), (x + w//2, y + h//2), font, 1, (0, 0, 255), 1, cv2.LINE_AA)
        # cv2.putText(img_contours, str(x), (x + w//4, y + h//4), font, 1, (255, 0, 0), 5, cv2.LINE_AA)
    if fname is not None:
        cv2.imwrite(fname, img_contours)
    if verbose:
        cv2.imshow("contours", img_contours)
        cv2.waitKey(0)

# Get the rectangular box corresponding to a contour
def get_rect(img, ctr):
    x, y, w, h = cv2.boundingRect(ctr)
    return img[y:y+h, x:x+w]

# Find big sections of text in an image
def find_sections(img, verbose=False, dirname="results"):
    img_h, img_w = img.shape[:2]

    binary = binarize(img)
    if verbose:
        cv2.imshow("binary", binary)
        cv2.waitKey(0)

    sections = []
    size = (10, 100)

    # # Crop the image a little to avoid outliers on the side of the page
    # offsets = (2, 20)
    # img = img[offsets[0]:-offsets[0], offsets[1]:-offsets[1]]

    sort_key = lambda ctr: cv2.boundingRect(ctr)[1]
    ctrs = find_contours_text(img, size, verbose=verbose, sort_key=sort_key)
    draw_contours(ctrs, img, w_rect=2, verbose=verbose)
    ii = 0
    for ctr in ctrs:
        _, _, w, h = cv2.boundingRect(ctr)
        ratio_w, ratio_h = w / img_w, h / img_h
        if ratio_h > 0.1:
        # if ratio_w > 0.25:
            section = get_rect(img, ctr)
            sections.append(section)
            cv2.imwrite("{}/section{}.png".format(dirname, ii), section)
            ii += 1

    return sections

# Sort contours left from right, top to bottom
def sort_contours(ctrs):
    threshold = 10

    # Find columns (sort by x)
    ctrs = sorted(ctrs, key=lambda ctr: -cv2.boundingRect(ctr)[0])
    cols = []
    col = []
    prev = cv2.boundingRect(ctrs[0])[0]
    for i, ctr in enumerate(ctrs):
        x, _, _, _ = cv2.boundingRect(ctr)
        if abs(x - prev) >= threshold:
            cols.append(col)
            col = []
        col.append(i)
        prev = x
    if col:
        cols.append(col)

    # Sort rectangles in columns (sort by y)
    sorted_ctrs = []
    for col in cols:
        col_ctrs = [ ctrs[i] for i in col ]
        sorted_col_ctrs = sorted(col_ctrs, key=lambda ctr: cv2.boundingRect(ctr)[1])
        sorted_ctrs.append(sorted_col_ctrs)

    sorted_ctrs = flatten(sorted_ctrs)

    return sorted_ctrs

# Flatten a list of lists
def flatten(lst):
    return [item for sublist in lst for item in sublist]

# Find elements of text inside a section
def find_text(section, verbose=False, section_idx=None, dirname="results"):
    binary = binarize(section)
    if section_idx is None:
        section_idx = np.random.randint(10)

    if verbose:
        cv2.imshow("input_section", binary)

    # TODO: automate finding text width
    text_width = 35
    size = (text_width // 2, 10)

    ctrs = find_contours_text(section, size, verbose=verbose, sort_key=None)
    ctrs = sort_contours(ctrs)

    fname = "{}/section{}_annotated.png".format(dirname, section_idx)
    draw_contours(ctrs, section, w_rect=2, fname=fname, verbose=verbose)

    text = []
    txt_boxes = []
    for i, ctr in enumerate(ctrs):
        x, y, w, h = cv2.boundingRect(ctr)
        if w <= 30:
            continue
        text.append(ctr)

        txt = get_rect(section, ctr)
        txt_boxes.append(txt)
        section_dirname = "{}/section{}".format(dirname, section_idx)
        if not os.path.isdir(section_dirname):
            os.mkdir(section_dirname)
        cv2.imwrite("{}/section{}/text{}.png".format(dirname, section_idx, i), txt)

    return txt_boxes

# Find elements of text inside a section
def find_text_lines(img, verbose=False):
    binary = binarize(img)

    # TODO: automate finding text width
    text_width = 35
    size = (text_width // 2, 10)

    ctrs = find_contours_text(img, size, verbose=verbose, sort_key=None)
    ctrs = sort_contours(ctrs)

    # fname = "{}/section{}_annotated.png".format(dirname, section_idx)
    draw_contours(ctrs, img, w_rect=2, verbose=verbose)

    text = []
    txt_boxes = []
    for i, ctr in enumerate(ctrs):
        x, y, w, h = cv2.boundingRect(ctr)
        if w <= 30:
            continue
        text.append(ctr)

        txt = get_rect(img, ctr)
        txt_boxes.append(txt)
        # section_dirname = "{}/section{}".format(dirname, section_idx)
        # if not os.path.isdir(section_dirname):
        #     os.mkdir(section_dirname)
        # cv2.imwrite("{}/section{}/text{}.png".format(dirname, section_idx, i), txt)

    return txt_boxes

# Find text in an image
def analyse_image(img, verbose=False, dirname="results", multi_section=False):
    if multi_section:
        sections = find_sections(img, verbose=verbose, dirname=dirname)
        txt_boxes = []
        for i, section in enumerate(sections):
           txt_boxes += find_text(section, verbose=verbose, section_idx=i, dirname=dirname)
    else:
       txt_boxes = find_text_lines(img)

    # return sections
    return txt_boxes

# OCR on an image (filename)
def do_ocr(img):
    assert os.path.isfile(img)
    num = os.path.splitext(os.path.basename(img))[0][4:]
    print(img)
    # cmd = "tesseract {} stdout -l jpn_vert --psm 5 2> /dev/null".format(img)
    # txt = os.popen(cmd).read()
    # custom_oem_psm_config = r'--psm 5 2'
    custom_oem_psm_config = r'--psm 5'
    txt = pytesseract.image_to_string(img, lang='jpn_vert', config=custom_oem_psm_config)
    # txt = pytesseract.image_to_string(img, lang='jpn_vert')
    return (num, txt)

# Delete a directory if it exists
def remove_dir(dirname):
    if os.path.isdir(dirname):
        import shutil
        shutil.rmtree(dirname)

# Get all the files recursively in a directory
def get_files(dirname):
    assert os.path.isdir(dirname)

    files_dict = {}

    for _, dirs, _ in os.walk(dirname):
        for d in dirs:
            for root, _, files in os.walk(os.path.join(dirname, d)):
                for file in files:
                    fname = os.path.join(root, file)
                    if d not in files_dict.keys():
                        files_dict[d] = []
                    files_dict[d].append(fname)

    return files_dict

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Input image", type=str)
    parser.add_argument("--ocr", help="Doing OCR", action="store_true")
    parser.add_argument("-v", "--verbose", help="Verbose", action="store_true")
    args = parser.parse_args()

    ocr = args.ocr
    verbose = args.verbose
    fname = args.image

    assert os.path.isfile(fname), "Image {} does not exist".format(fname)
    dirname = "results_{}".format(os.path.splitext(os.path.basename(fname))[0])

    if not ocr:
        print("Analyzing image: {}...".format(fname))
        print("Saving results to: {}".format(dirname))
        remove_dir(dirname)
        os.mkdir(dirname)

        img = cv2.imread(fname)
        _ = analyse_image(img, verbose=verbose, dirname=dirname)
        print("Analysis done")
    else:
        print("Doing OCR...")
        files_dict = get_files(dirname)
        # print (files_dict)

        text_dict = {}
        for k in files_dict.keys():
            text_dict[k] = []

        for d in files_dict.keys():
            files = files_dict[d]
            print(d)
            with Pool(nthreads) as pool:
                text_dict[d] = pool.map(do_ocr, files)
            # for f in files:
            #     do_ocr(f)

        # print(text_dict)
        for d in text_dict.keys():
            txt_fname = os.path.join(dirname, d + ".txt")
            # with open(txt_fname, "w") as f:
            with open(txt_fname, "w", encoding='utf8') as f:
                sorted_text = sorted(text_dict[d], key=lambda v: int(v[0]))
                for (i, txt) in sorted_text:
                    txt = txt.replace("\x0c", "")
                    f.write("line{}: {}".format(i, txt))

        f.close()
        print("OCR done")
