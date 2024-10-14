#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
# @Author   : chuanwen.peng
# @Time     : 2022/4/15 14:21
# @File     : base_page.py
# @Project  : Glass_UI
"""

import logging
import os
import re
import time
import uuid
from typing import Union

import allure
import uiautomator2
import wda
from cached_property import cached_property
from uiautomator2 import UiObject, UiObjectNotFoundError, Device
from uiautomator2.exceptions import XPathElementNotFoundError
from uiautomator2.xpath import XPathSelector

from common.aircv import TargetNotFoundError
from common.utils import ReadConfig
from common.image import ImageX


class BasePage(object):
    """页面元素操作基类"""

    # 查找元素失败重试计数器
    _err_counter = 0
    # 最大重试次数
    _MAX_RETRY_TIMES = 1

    def __init__(self, driver: Union[Device, wda.Client], platform):
        self.driver = driver
        self.platform = ReadConfig().get_platform(platform)
        self.implicitly_wait = ReadConfig().get_implicitly_wait(platform)
        self.check_error_toast = ReadConfig().get_check_error_toast(platform)

    def find_element(self, retry_times=_MAX_RETRY_TIMES, index=0, **locator):
        """
        定位元素，支持以下参数：

        Android:
            text, textContains, textMatches, textStartsWith
            className, classNameMatches
            description, descriptionContains, descriptionMatches, descriptionStartsWith
            checkable, checked, clickable, longClickable
            scrollable, enabled,focusable, focused, selected
            packageName, packageNameMatches
            resourceId, resourceIdMatches
            index, instance
        以上的参数都可以单独或组合使用，以下的只能单独使用
            child, left, right ,up ,down
            xpath
            image
        iOS:
            className
            name, nameContains, nameMatches
            label, labelContains
            value, valueContains
            visible, enabled
            index (index 必须与label，value等结合使用)
        以上的参数都可以单独(index除外)或组合使用，以下的只能单独使用
            id
            child
            xpath
            predicate
            classChain
            image
        """
        try:
            elements = None
            if "image" in locator.keys():
                return self.image.wait(locator["image"], timeout=self.implicitly_wait)
            if self.platform == "android":
                if "xpath" in locator.keys():
                    elements = self.driver.xpath(locator["xpath"])
                    if len(elements.all()) == 0:
                        elements.get()
                    elif len(elements.all()) > 1:
                        logging.warning("More than one element was found, please reselect the element positioning "
                                        "conditions --> %s", str(locator))
                else:
                    if "child" in locator.keys():
                        child_list = locator["child"]
                        elements = self.driver(**self.handle_resourceId(**child_list[0]))
                        for child in child_list[1:]:
                            elements = elements.child(**self.handle_resourceId(**child))
                    elif "left" in locator.keys():
                        child_list = locator["left"]
                        elements = self.driver(**self.handle_resourceId(**child_list[0])).left(
                            **self.handle_resourceId(**child_list[1]))
                    elif "right" in locator.keys():
                        child_list = locator["right"]
                        elements = self.driver(**self.handle_resourceId(**child_list[0])).right(
                            **self.handle_resourceId(**child_list[1]))
                    elif "up" in locator.keys():
                        child_list = locator["up"]
                        elements = self.driver(**self.handle_resourceId(**child_list[0])).up(
                            **self.handle_resourceId(**child_list[1]))
                    elif "down" in locator.keys():
                        child_list = locator["down"]
                        elements = self.driver(**self.handle_resourceId(**child_list[0])).down(
                            **self.handle_resourceId(**child_list[1]))
                    else:
                        elements = self.driver(**self.handle_resourceId(**locator))[index]
                    if len(elements) == 0:
                        elements.must_wait()
                    elif len(elements) > 1:
                        logging.warning("More than one element was found, please reselect the element positioning "
                                        "conditions --> %s", str(locator))
            elif self.platform == "ios":
                if "child" in locator.keys():
                    child_list = locator["child"]
                    elements = self.driver(**child_list[0])
                    for child in child_list[1:]:
                        elements = elements.child(**child)
                else:
                    elements = self.driver(**locator)
                if len(elements.count()) == 0:
                    elements.wait()
                elif len(elements.count()) > 1:
                    logging.warning("More than one element was found, please reselect the element positioning "
                                    "conditions --> %s", str(locator))
            self._err_counter = 0
            return elements
        except (XPathElementNotFoundError, UiObjectNotFoundError, wda.WDAElementNotFoundError, TargetNotFoundError):
            self._err_counter += 1
            if self._err_counter > retry_times:
                logging.error("element %s was not found", str(locator))
                assert False, "element {} was not found".format(str(locator))
            else:
                logging.info("try to find element %s again[%i]", str(locator), self._err_counter)
                return self.find_element(**locator)

    def find_element_and_click(self, check_toast=True, ignore_toast=None, index=0, **locator):
        """
        定位元素并点击(默认检查异常toast提示)
        find element and perform click
        Args:
            check_toast (bool): 默认检查toast,表示此处可能会有异常的情况发生；若正常场景也会弹成功之类的toast，请添加忽略内容
            ignore_toast (str): 需要忽略的正常toast提示
            index (int): 元素索引，适用于定位到多个重复的元素的场景，xpath,child,left,right,up,down不支持
        """
        logging.info("click element: %s", str(locator))
        if "image" in locator.keys():
            x, y = self.find_element(**locator)
            self.driver.click(x, y)
        # elif "xpath" or "child" or "left" or "right" or "up" or "down" in locator.keys():
        elif "xpath" in locator.keys() or "child" in locator.keys() or "left" in locator.keys() or "right" in locator.keys() or "up" in locator.keys() or "down" in locator.keys():
            self.find_element(**locator).click()
        else:
            self.find_element(**locator)[index].click()
        if self.platform == "ios":
            check_toast = False  # iOS没有原生toast组件，这里跳过不进行校验
        if (check_toast and self.check_error_toast) is False:
            assert True
        else:
            toast = self.get_toast(wait_timeout=2)
            logging.info("check toast: %s", str(toast))
            if (toast is None) or (toast == ignore_toast):
                assert True
            else:
                self.take_screenshot("报错截图")
                assert False, "报错toast：{}".format(toast)

    def find_element_and_long_click(self, duration: float = 1.0, **locator):
        """
        定位元素并长按
        find element and perform long click

        Args:
            duration (float): seconds of pressed
        """
        logging.info("long click element: %s", str(locator))
        if self.platform == "android":
            if "image" in locator.keys():
                x, y = self.find_element(**locator)
                self.driver.long_click(x, y, duration=duration)
            elif "xpath" in locator.keys():
                # xpath没有定义duration参数
                self.find_element(**locator).long_click()
            else:
                self.find_element(**locator).long_click(duration=duration)
        elif self.platform == "ios":
            self.find_element(**locator).get().tap_hold(duration=duration)

    def find_element_and_input(self, plaintext=None, **locator):
        """
        定位元素并输入文本
        find element and perform input

        Args:
            plaintext: unencrypted plaintext
        """
        logging.info("input plaintext: %s", str(plaintext))
        element = self.find_element(**locator)
        if type(element) is UiObject:
            element.clear_text()
            element.send_keys(plaintext)
        elif type(element) is XPathSelector:
            element.set_text(plaintext)
        elif type(element) is wda.Selector:
            element.get().clear_text()
            element.get().set_text(plaintext)

    def find_element_and_swipe(self, direction, steps: int = 10, scale: float = 0.8, **locator):
        """
        定位元素并滑动(以元素自身的边为基准，从元素的中间或一边滑动到另一边)
        performs the swipe action on the UiObject or XMLElement or wda.Element.

        Args:
            direction (str): one of ("left", "right", "up", "down")
            steps (int): for android UiObject, move steps, one step is about 5ms
            scale: for android XPath, means percent of swipe, range (0, 1.0);
                   for iOS, 1.0 means, element (width or height) multiply 1.0
        """
        logging.info("swipe element: %s", str(locator))
        element = self.find_element(**locator)
        if type(element) is UiObject:
            element.swipe(direction, steps)  # Swipe from the center of the UiObject to its edge
        elif type(element) is XPathSelector:
            element.get().swipe(direction, scale)  # Swipe from one edge to another edge
        elif type(element) is wda.Selector:
            element.get().scroll(direction, scale)

    def find_element_and_drag(self, *coordinate, **locator):
        """
        定位元素并拖动(暂不支持xpath元素/图片/iOS)
        drag the UiObject towards another point

        Args:
            coordinate (tuple): target coordinate (x,y)
        Raise:
            TypeError
        """
        logging.info("drag element: %s", str(locator))
        element = self.find_element(**locator)
        if type(element) is UiObject:
            element.drag_to(*coordinate, duration=0.25)
        else:
            logging.error("Drag action is not supported for XMLElement/image/iOS")
            raise TypeError

    def assert_element_exist(self, **locator):
        """ 断言元素存在，不存在则报错 """
        if self.find_element(**locator) is not None:
            logging.info("check element exist: %s %s", str(locator), "True")
            assert True

    def check_element_existence(self, timeout=5, **locator):
        """ 检查元素存在性"""
        if self.driver(**locator).exists(timeout=timeout):
            logging.info("check element exist: %s %s", str(locator), "True")
            return True
        else:
            logging.info("check element exist: %s %s", str(locator), "False")
            return False

    def assert_text_non_exist(self, plaintext: str):
        """ 断言文字在当前页面不存在(模糊匹配)，存在则报错"""
        if self.platform == "android":
            ok = True
            source = self.driver.dump_hierarchy()
            sel = self.driver.xpath("%" + str(plaintext) + "%", source=source)
            if sel.exists:
                ok = False
            logging.info("assert non-exist text: {} --> {}".format(plaintext, ok))
            assert ok, "current page does exist {}".format(plaintext)
        elif self.platform == "ios":
            # todo ios待适配
            pass

    def assert_text_exist(self, plaintext: str):
        """ 断言文字在当前页面存在(模糊匹配)，不存在则报错"""
        if self.platform == "android":
            ok = True
            self.driver.sleep(1.5)
            source = self.driver.dump_hierarchy()
            sel = self.driver.xpath("%" + str(plaintext) + "%", source=source)
            if not sel.exists:
                ok = False
            logging.info("assert exist text: {} --> {}".format(plaintext, ok))
            assert ok, "current page does not exist {}".format(plaintext)
        elif self.platform == "ios":
            # todo ios待适配
            pass

    def assert_text_exist_strict(self, plaintext: str):
        """ 断言文字在当前页面存在(精确匹配)，不存在则报错"""
        if self.platform == "android":
            ok = True
            self.driver.sleep(1.5)
            source = self.driver.dump_hierarchy()
            sel = self.driver.xpath(str(plaintext), source=source)
            if not sel.exists:
                ok = False
            logging.info("assert exist text: {} --> {}".format(plaintext, ok))
            assert ok, "current page does not exist {}".format(plaintext)
        elif self.platform == "ios":
            # todo ios待适配
            pass

    def check_text_existance(self, plaintext: str):
        """ 检查当前界面是否包含指定文字(模糊匹配) """
        if self.platform == "android":
            ok = True
            self.driver.sleep(1.5)
            source = self.driver.dump_hierarchy()
            sel = self.driver.xpath("%" + str(plaintext) + "%", source=source)
            if not sel.exists:
                ok = False
            logging.info("check exist text: {} --> {}".format(plaintext, ok))
            return ok
        elif self.platform == "ios":
            # todo ios待适配
            pass

    def check_blank_screen(self):
        """ 检查是否白屏 """
        return self.image.blank_detection()

    def wait_until_element_gone(self, timeout=300, **locator):
        """ 等待指定的元素消失 """
        logging.info("start wait until element %s disappear", str(locator))
        gone = self.find_element(**locator).wait_gone(timeout)
        if gone:
            logging.info("element %s disappear", str(locator))
            assert True
        else:
            assert False, "waiting timeout"

    def swipe_screen(self, direction, scale: float = 0.7):
        """
        滑动屏幕(手指滑动的方向)
        swipe the screen in a certain area

        Args:
            direction (str): one of "left", "right", "up", "bottom"
            scale (float): percent of swipe, range (0, 1.0]; useless for ios
        """
        logging.info("swipe %s screen", str(direction))
        if self.platform == "android":
            self.driver.swipe_ext(direction, scale)
        elif self.platform == "ios":
            if direction == "up":
                self.driver.swipe_up()
            if direction == "down":
                self.driver.swipe_down()
            if direction == "left":
                self.driver.swipe_left()
            if direction == "right":
                self.driver.swipe_right()

    def scroll_until_element_appear(self, retry_times=_MAX_RETRY_TIMES, **locator):
        """
        滚动屏幕直到出现指定的元素
        scroll up the whole screen until target element founded
        """
        logging.info("scroll until element %s appear", str(locator))
        try:
            if self.platform == "android":
                if "xpath" in locator.keys():
                    self.driver.xpath.scroll_to(locator["xpath"])
                else:
                    self.driver(scrollable=True).scroll.to(**locator)
            elif self.platform == "ios":
                self.driver(**locator).get().scroll()
            self._err_counter = 0
        except (XPathElementNotFoundError, UiObjectNotFoundError, wda.WDAElementNotFoundError):
            self._err_counter += 1
            if self._err_counter > retry_times:
                logging.error("element %s was not found", str(locator))
                assert False, "element {} was not found".format(str(locator))
            else:
                logging.info("try to find element %s again[%i]", str(locator), self._err_counter)
                return self.scroll_until_element_appear(**locator)

    def scroll_to_boundary(self, boundary: str = "end", speed: str = "fast"):
        """
        滚动屏幕到应用的边界(顶部或底部)
        perform fling/scroll on the specific ui object(scrollable)

        Args:
            boundary (str): one of "end", "beginning"
            speed (str): one of "fast", "slow"
        """
        logging.info("scroll to %s", str(boundary))
        if self.platform == "android":
            if boundary == "end":
                if speed == "fast":
                    self.driver(scrollable=True).fling.toEnd()
                elif speed == "slow":
                    self.driver(scrollable=True).scroll.toEnd()
            elif boundary == "beginning":
                if speed == "fast":
                    self.driver(scrollable=True).fling.toBeginning()
                elif speed == "slow":
                    self.driver(scrollable=True).scroll.toBeginning()
        elif self.platform == "ios":
            logging.warning("avoid using this method for ios.")
            if boundary == "end":
                for i in range(5):
                    self.driver.swipe_up()  # wda未提供滑动到底部的接口，临时用这个替代，尽量避免ios用这个方法
            elif boundary == "beginning":
                self.driver.double_tap(2, 2)
        self.sleep(0.5)

    def press_key(self, key):
        """
        按键操作(物理/虚拟)
        Android:
            home, back, left, right, up, down, center, menu, search, enter,
            delete(or del), recent(recent apps), volume_up, volume_down,
            volume_mute, camera, power.
        iOS:
            home, volumeUp, volumeDown
        """
        logging.info("press %s key", str(key))
        self.driver.press(key)

    def open_notification(self):
        """ 打开通知栏 """
        logging.info("open notification")
        if self.platform == "android":
            self.driver.open_notification()
        elif self.platform == "ios":
            w, h = self.driver.window_size()
            self.driver.swipe(1, 1, 1, h)

    def open_quick_settings(self):
        """ 打开快速设置栏 """
        logging.info("open quick settings")
        if self.platform == "android":
            self.driver.open_quick_settings()
        elif self.platform == "ios":
            logging.warning("only support opening quick settings for iphone X,11,12 series")
            w, h = self.driver.window_size()
            self.driver.swipe(w, 1, w, h // 2)

    def get_toast(self, wait_timeout=5):
        """ 获取toast """
        if self.platform == "android":
            self.driver.toast.reset()
            return self.driver.toast.get_message(wait_timeout=wait_timeout)
        elif self.platform == "ios":
            logging.warning("does not support getting toast for ios temporarily.")
            return None

    def take_screenshot(self, name="截图") -> str:
        """ 屏幕截图 """
        screenshot_path = os.path.join(ReadConfig().get_project_dir, "report", "screenshot")
        if not os.path.exists(screenshot_path):
            os.makedirs(screenshot_path)
        filename = os.path.join(screenshot_path, str(uuid.uuid1()) + ".png")
        self.driver.screenshot(filename)
        logging.info("take screenshot: %s", str(filename))
        with allure.step("进行截图"):
            allure.attach.file(filename, name + " " + time.strftime("%m-%d %H:%M:%S", time.localtime()) + " "
                               + str(filename), allure.attachment_type.PNG)  # 添加截图到报告中
        return filename

    def sleep(self, seconds):
        """ 在当前页面等待 """
        logging.info("sleep %.1fs", seconds)
        self.driver.sleep(seconds)

    @cached_property
    def image(self):
        return ImageX(self.driver)

    def handle_resourceId(self, **kwargs):
        """ 处理resourceId """
        if "resourceId" in kwargs.keys():
            if re.match("(\w+\.){0,}\w+:id\/\w+", kwargs["resourceId"]) is None:
                app_current = self.driver.app_current()
                kwargs["resourceId"] = app_current["package"] + ":id/" + kwargs["resourceId"]
        return kwargs


if __name__ == '__main__':
    d1 = uiautomator2.connect("1000190131J00021")
    phone_page = BasePage("1000190131J00021", r"D:\XRwork\Stable_XR\StressTest\mixed_scene")
    d = {"resourceId": "com.upuphone.star.launcher:id/iv_battery_bg"}
    d = {'resourceId': "com.upuphone.star.launcher:id/iv_battery_bg"}
    phone_page.check_element_existence(**d)
