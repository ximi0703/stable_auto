#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy as np
from PIL import Image

from .error import TemplateInputError


def generate_result(middle_point, pypts, confi):
    """Format the result: 定义图像识别结果格式."""
    ret = dict(result=middle_point,
               rectangle=pypts,
               confidence=confi)
    return ret


def check_image_valid(im_source, im_search):
    """Check if the input images valid or not."""
    if im_source is not None and im_source.any() and im_search is not None and im_search.any():
        return True
    else:
        return False


def check_source_larger_than_search(im_source, im_search):
    """检查图像识别的输入."""
    # 图像格式, 确保输入图像为指定的矩阵格式:
    # 图像大小, 检查截图宽、高是否大于了截屏的宽、高:
    h_search, w_search = im_search.shape[:2]
    h_source, w_source = im_source.shape[:2]
    if h_search > h_source or w_search > w_source:
        raise TemplateInputError("error: in template match, found im_search bigger than im_source.")


def img_mat_rgb_2_gray(img_mat):
    """
    Turn img_mat into gray_scale, so that template match can figure the img data.
    "print(type(im_search[0][0])")  can check the pixel type.
    """
    assert isinstance(img_mat[0][0], np.ndarray), "input must be instance of np.ndarray"
    return cv2.cvtColor(img_mat, cv2.COLOR_BGR2GRAY)


def img_2_string(img):
    _, png = cv2.imencode('.png', img)
    return png.tostring()


def string_2_img(pngstr):
    nparr = np.frombuffer(pngstr, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def pil_2_cv2(pil_image):
    open_cv_image = np.array(pil_image)
    # Convert RGB to BGR (method-1):
    open_cv_image = cv2.cvtColor(open_cv_image, cv2.COLOR_RGB2BGR)
    # Convert RGB to BGR (method-2):
    # b, g, r = cv2.split(open_cv_image)
    # open_cv_image = cv2.merge([r, g, b])
    return open_cv_image


def cv2_2_pil(cv2_image):
    cv2_im = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
    pil_im = Image.fromarray(cv2_im)
    return pil_im


def compress_image(pil_img, path, quality, max_size=None):
    """
    Save the picture and compress

    :param pil_img: PIL image
    :param path: save path
    :param quality: the image quality, integer in range [1, 99]
    :param max_size: the maximum size of the picture, e.g 1200
    :return:
    """
    if max_size:
        # The picture will be saved in a size <= max_size*max_size
        pil_img.thumbnail((max_size, max_size), Image.ANTIALIAS)
    quality = int(round(quality))
    if quality <= 0 or quality >= 100:
        raise Exception("SNAPSHOT_QUALITY (" + str(quality) + ") should be an integer in the range [1,99]")
    pil_img.save(path, quality=quality, optimize=True)


def cocos_min_strategy(w, h, sch_resolution, src_resolution, design_resolution=(960, 640)):
    """图像缩放规则: COCOS中的MIN策略."""
    # 输入参数: w-h待缩放图像的宽高，sch_resolution为待缩放图像的来源分辨率
    #           src_resolution 待适配屏幕的分辨率  design_resolution 软件的设计分辨率
    # 需要分别算出对设计分辨率的缩放比，进而算出src\sch有效缩放比。
    scale_sch = min(1.0 * sch_resolution[0] / design_resolution[0], 1.0 * sch_resolution[1] / design_resolution[1])
    scale_src = min(1.0 * src_resolution[0] / design_resolution[0], 1.0 * src_resolution[1] / design_resolution[1])
    scale = scale_src / scale_sch
    h_re, w_re = int(h * scale), int(w * scale)
    return w_re, h_re


class TargetPos(object):
    """
    点击目标图片的不同位置，默认为中心点0
    1 2 3
    4 0 6
    7 8 9
    """
    LEFTUP, UP, RIGHTUP = 1, 2, 3
    LEFT, MID, RIGHT = 4, 5, 6
    LEFTDOWN, DOWN, RIGHTDOWN = 7, 8, 9

    def getXY(self, cvret, pos):
        if pos == 0 or pos == self.MID:
            return cvret["result"]
        rect = cvret.get("rectangle")
        if not rect:
            print("could not get rectangle, use mid point instead")
            return cvret["result"]
        w = rect[2][0] - rect[0][0]
        h = rect[2][1] - rect[0][1]
        if pos == self.LEFTUP:
            return rect[0]
        elif pos == self.LEFTDOWN:
            return rect[1]
        elif pos == self.RIGHTDOWN:
            return rect[2]
        elif pos == self.RIGHTUP:
            return rect[3]
        elif pos == self.LEFT:
            return rect[0][0], rect[0][1] + h / 2
        elif pos == self.UP:
            return rect[0][0] + w / 2, rect[0][1]
        elif pos == self.RIGHT:
            return rect[2][0], rect[2][1] - h / 2
        elif pos == self.DOWN:
            return rect[2][0] - w / 2, rect[2][1]
        else:
            print("invalid target_pos:%s, use mid point instead" % pos)
            return cvret["result"]
