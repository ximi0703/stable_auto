# -*- coding: utf-8 -*-
from common import project_dir
from common.aircv.utils import cocos_min_strategy
import os


class Settings(object):

    LOG_DIR = os.path.join(project_dir, "report", "screen_log")
    RESIZE_METHOD = staticmethod(cocos_min_strategy)
    CVSTRATEGY = ["surf", "tpl", "brisk"]  # keypoint matching: kaze/brisk/akaze/orb, contrib: sift/surf/brief
    KEYPOINT_MATCHING_PREDICTION = True
    THRESHOLD = 0.8  # [0, 1]
    THRESHOLD_STRICT = None  # dedicated parameter for assert_exists
    OPDELAY = 0.1
    FIND_TIMEOUT = 20
    FIND_TIMEOUT_TMP = 3
    PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "")  # for ``using`` other script
    SNAPSHOT_QUALITY = 10  # 1-100 https://pillow.readthedocs.io/en/5.1.x/handbook/image-file-formats.html#jpeg
    # Image compression size, e.g. 1200, means that the size of the screenshot does not exceed 1200*1200
    IMAGE_MAXSIZE = os.environ.get("IMAGE_MAXSIZE", None)
