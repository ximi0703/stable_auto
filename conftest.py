#!/usr/bin/env python
# -*- coding:utf-8 -*-
import logging
import operator
import os
import re
import shutil
import subprocess
import threading
import time
import uuid

import allure
import pytest
import uiautomator2 as u2
import wda as wda

from common.utils import ReadConfig, Util
from common.logger import setup_logger
from common.logger2 import Logger

flag_log = True


def stream_reader(stream, mylogger):
    while flag_log:
        try:
            mylogger.info('%s', stream.readline().decode().strip())
        except Exception as e:
            mylogger.info(e)

#
# def check_error(driver):
#     u2_base_file = r"C:\Users\chuanwen.peng\.uiautomator2\cache"
#     while True:
#         time.sleep(50)
#         if "com.github.uiautomator" in driver.current_app().get("package"):
#             logging.info("出现白屏！")
#             driver.press("back")
#         try:
#             if os.listdir(u2_base_file):
#                 logging.info("删除u2缓存文件!")
#                 for file in os.listdir(u2_base_file):
#                     shutil.rmtree(os.path.join(u2_base_file, file))
#         except Exception as e:
#             logging.error(e)
#
#
# def uninstall_u2(driver):
#     while True:
#         time.sleep(1200)
#         logging.info("间隔20min删除u2app")
#         driver.app_uninstall("com.github.uiautomator")
#         driver.app_uninstall("com.github.uiautomator.test")


@pytest.fixture(scope="session")
def driver(request):
    # TODO 获取配置文件路径
    global app_name
    app_name = request.param.get("app_name")
    config_r = ReadConfig(os.path.join(os.getcwd(), "StressTest", app_name))
    devices = request.param.get("devices")
    setup_logger(os.getcwd(), devices + "_" + app_name)
    error_logs = request.param.get("errors")
    os.system('adb -s %s root' % devices)
    os.system('adb -s %s shell dumpsys battery set usb 0' % devices)
    os.system('adb -s %s shell dumpsys battery set ac 0' % devices)
    # TODO 关闭佩戴检测
    # Util().close_wear_detect(devices)
    # Util().dev_root(devices)
    # Util().simulate_wear(devices)
    driver = u2.connect(devices)  # 连接设备(usb只能插入单个设备)
    if len([i for i in driver.app_list() if 'uiautomator' in i]) < 2:
        # 初始化apk多设备
        logging.error("u2初始化安装")
        os.system(r"python -m uiautomator2 init")
        time.sleep(15)
    try:
        max_retry = 3
        # u2出现问题
        while not driver.uiautomator.running() and max_retry > 0:
            os.system(f"adb -s {driver.serial} shell curl  -X POST  http://127.0.0.1:7912/uiautomator")
            # os.system(f"adb -s {driver.serial} shell am instrument -w -r -e debug false -e class com.github.uiautomator.stub.Stub \
            #    com.github.uiautomator.test/android.support.test.runner.AndroidJUnitRunner")
            time.sleep(5)
            print(f"重试第{4 - max_retry}")
            max_retry -= 1
        logging.info("u2此时状态" + str(driver.uiautomator.running()))
        # #  atx出现问题
        # os.system(f"adb -s {phone_serial_no} shell /data/local/tmp/atx-agent server -d --stop")
        # log.error("初始化atx")
        # time.sleep(12)  # 时间要足够长才保证重启成功
    except Exception as e:
        #  atx出现问题
        os.system(f"adb -s {driver.serial} shell /data/local/tmp/atx-agent server -d --stop")
        logging.error("后台重启atx第二次")
        time.sleep(12)  # 时间要足够长才保证重启成功
        # 重试五次
        max_retry = 3
        # u2出现问题
        while not driver.uiautomator.running() and max_retry > 0:
            os.system(f"adb -s {driver.serial} shell curl  -X POST  http://127.0.0.1:7912/uiautomator")
            # os.system(f"adb -s {driver.serial} shell am instrument -w -r -e debug false -e class com.github.uiautomator.stub.Stub \
            #    com.github.uiautomator.test/android.support.test.runner.AndroidJUnitRunner")
            time.sleep(5)
            print(f"重试第{4 - max_retry}")
            max_retry -= 1
        print("u2此时状态" + str(driver.uiautomator.running()))
    # driver.settings["operation_delay"] = (0.2, 0.2)  # 操作后的延迟，(0, 0)表示操作前等待0s，操作后等待0s
    # driver.settings['operation_delay_methods'] = ['click', 'swipe', 'drag', 'press']
    logcat_path = os.path.join(os.getcwd(), "report", devices + "_" + app_name, "logcat")
    if not os.path.exists(logcat_path):
        os.makedirs(logcat_path)
    logcat_filename = os.path.join(logcat_path, time.strftime("%m%d_%H%M%S",
                                                              time.localtime(time.time())) + ".txt")
    logcat_file = open(logcat_filename, "w")
    os.system("adb -s %s logcat -c" % driver._serial)
    pop_log = subprocess.Popen(["adb", "-s", driver._serial, "logcat", "-v", "threadtime"],
                               stdout=logcat_file,
                               stderr=subprocess.PIPE)  # 启动logcat捕获日志
    logging.info("start capturing log: %s", str(logcat_file))
    Util().device_unlock(driver)
    # get_hci_log(devices)
    # get_wlan_log(devices)
    screen_off_timeout = os.popen('adb -s %s shell settings get system screen_off_timeout' % devices).read().strip()
    if screen_off_timeout != '1800000':
        os.system('adb -s %s shell settings put system screen_off_timeout 1800000' % devices)
    # with driver.watch_context(builtin=True) as ctx:
    # # ctx.when("^(下载|更新)").when("取消").click()  # 当同时出现（下载 或 更新）和 取消 按钮时，点击取消
    # ctx.when("跳过%").click()
    # ctx.when("暂不升级").click()
    # ctx.when("允许").click()
    # ctx.when("继续").click()
    # ctx.when("每次开启").click()
    # # todo 由于眼镜很多崩溃问题阻塞，所以出现崩溃就重启应用
    # ctx.when("关闭应用").click()
    # ctx.when("创建").when("取消").click()
    # ctx.when("恢复").when("取消").click()
    # ctx.wait_stable(seconds=1.5)  # 开启弹窗监控，并等待界面稳定（两个弹窗检查周期内没有弹窗代表稳定）
    yield driver, config_r
    driver.set_fastinput_ime(False)  # 关闭自动化定制的输入法
    logcat_file.close()
    pop_log.terminate()  # 停止日志捕获
    logging.info("stop capturing log")
    # todo sc_log抓取
    file_path = os.path.join(os.getcwd(), "report", driver.serial + "_" + app_name, "sc_log")
    file_name = time.strftime('%Y_%m_%d_%H_%M', time.localtime(time.time())) + "_" + app_name
    cmd = "%s %s %s" % (
        os.path.join(os.path.abspath(os.getcwd()), "scLogTools", "get_log.bat"), driver.serial,
        os.path.join(file_path, file_name))
    # os.system(cmd)
    time.sleep(2)
    logging.info("已抓取sclog日志")
    os.system('adb -s %s shell dumpsys battery set usb 1' % devices)
    os.system('adb -s %s shell dumpsys battery set ac 1' % devices)
    # os.system("adb -s %s shell input keyevent 82" % devices)
    # time.sleep(1)
    # status = driver(text="万象桌面").exists
    # while not status:
    #     driver.keyevent("21")
    #     time.sleep(1)
    #     status = driver(text="万象桌面").exists
    # os.system('adb -s %s shell settings put system screen_off_timeout %s' % (devices, screen_off_timeout))
    # driver.screen_off()  # 息屏


@pytest.fixture(scope="package")
def driver1(request):
    # TODO 获取配置文件路径
    app_name = request.param.get("app_name")
    devices = request.param.get("devices")
    os.system('adb -s %s root' % devices)
    driver = u2.connect(devices)  # 连接设备(usb只能插入单个设备)
    if len([i for i in driver.app_list() if 'uiautomator' in i]) < 2:
        # 初始化apk多设备
        logging.error("u2初始化安装")
        os.system(r"python -m uiautomator2 init")
        time.sleep(15)
    try:
        max_retry = 3
        # u2出现问题
        while not driver.uiautomator.running() and max_retry > 0:
            os.system(f"adb -s {driver.serial} shell curl  -X POST  http://127.0.0.1:7912/uiautomator")
            # os.system(f"adb -s {driver.serial} shell am instrument -w -r -e debug false -e class com.github.uiautomator.stub.Stub \
            #    com.github.uiautomator.test/android.support.test.runner.AndroidJUnitRunner")
            time.sleep(5)
            print(f"重试第{4 - max_retry}")
            max_retry -= 1
        logging.info("u2此时状态" + str(driver.uiautomator.running()))
        # #  atx出现问题
        # os.system(f"adb -s {phone_serial_no} shell /data/local/tmp/atx-agent server -d --stop")
        # log.error("初始化atx")
        # time.sleep(12)  # 时间要足够长才保证重启成功
    except Exception as e:
        #  atx出现问题
        os.system(f"adb -s {driver.serial} shell /data/local/tmp/atx-agent server -d --stop")
        logging.error("后台重启atx第二次")
        time.sleep(12)  # 时间要足够长才保证重启成功
        # 重试五次
        max_retry = 3
        # u2出现问题
        while not driver.uiautomator.running() and max_retry > 0:
            os.system(f"adb -s {driver.serial} shell curl  -X POST  http://127.0.0.1:7912/uiautomator")
            # os.system(f"adb -s {driver.serial} shell am instrument -w -r -e debug false -e class com.github.uiautomator.stub.Stub \
            #    com.github.uiautomator.test/android.support.test.runner.AndroidJUnitRunner")
            time.sleep(5)
            print(f"重试第{4 - max_retry}")
            max_retry -= 1
        print("u2此时状态" + str(driver.uiautomator.running()))
    # driver.settings["operation_delay"] = (0.2, 0.2)  # 操作后的延迟，(0, 0)表示操作前等待0s，操作后等待0s
    # driver.settings['operation_delay_methods'] = ['click', 'swipe', 'drag', 'press']
    logcat_path = os.path.join(os.getcwd(), "report", devices + "_" + app_name, "logcat")
    if not os.path.exists(logcat_path):
        os.makedirs(logcat_path)
    myloggers = Logger('TestMyLog', logcat_path)
    mylogger = myloggers.getlog()
    foo_proc = subprocess.Popen(["adb", "-s", driver.serial, "logcat", "-v", "threadtime"], stdout=subprocess.PIPE)

    thread = threading.Thread(target=stream_reader, args=(foo_proc.stdout, mylogger,))
    thread.setDaemon(True)
    thread.start()
    logging.info("start capturing log: %s", str(logcat_path))

    # thread_u2 = threading.Thread(target=check_error, args=(driver,))
    # thread_u2.setDaemon(True)
    # thread_u2.start()
    # logging.info("u2 error check running")
    #
    # thread_u2 = threading.Thread(target=uninstall_u2, args=(driver,))
    # thread_u2.setDaemon(True)
    # thread_u2.start()
    # logging.info("u2 uninstall check running")

    Util().device_unlock(driver)
    driver.app_start("com.meizu.logreport")
    # todo mars设备抓取日志
    start_log = 'adb -s %s shell am broadcast  -a com.meizu.logreport.adb_cmd --ei action 1 --es type "recording,bluetooth,wifi,audio,modem" --receiver-include-background' % devices
    end_log = 'adb -s %s shell am broadcast  -a com.meizu.logreport.adb_cmd --ei action 0 --es type "recording,bluetooth,wifi,audio,modem" --receiver-include-background' % devices
    # subprocess.Popen(start_log, shell=True)
    # logging.info("开始抓取mars日志（recording,bluetooth,wifi,audio,modem）")

    screen_off_timeout = os.popen('adb -s %s shell settings get system screen_off_timeout' % devices).read().strip()
    if screen_off_timeout != '1800000':
        os.system('adb -s %s shell settings put system screen_off_timeout 1800000' % devices)
    # with driver.watch_context(builtin=True) as ctx:
        # # ctx.when("^(下载|更新)").when("取消").click()  # 当同时出现（下载 或 更新）和 取消 按钮时，点击取消
        # ctx.when("跳过%").click()
        # ctx.when("暂不更新").click()
        # ctx.when("允许").click()
        # ctx.when("仅在使用时允许").click()
        # ctx.when("同意并继续").click()
        # ctx.when("我知道了").click()
        # ctx.when("暂不更新").click()
        # ctx.when("同意").click()
        # ctx.when("继续").click()
        # ctx.when("每次开启").click()
        # ctx.when("刷新一下").click()
        # ctx.when("点击重新加载").click()
        # # ctx.when("请开启“星纪AR通知使用”权限").when("去开启").click()
        # ctx.when("创建").when("取消").click()
        # ctx.when("恢复").when("取消").click()
        # ctx.wait_stable(seconds=1.5)  # 开启弹窗监控，并等待界面稳定（两个弹窗检查周期内没有弹窗代表稳定）
    yield driver, app_name
    # logging.info("停止抓取mars日志（recording,bluetooth,wifi,audio,modem）")
    # subprocess.Popen(end_log, shell=True)
    driver.set_fastinput_ime(False)  # 关闭自动化定制的输入法
    # time.sleep(60)
    global flag_log
    flag_log = False
    foo_proc.terminate()  # 停止日志捕获
    logging.info("stop capturing log")
    # logging.info("-------------------开始抓取mars日志------------------------")
    # os.system("adb -s %s pull sdcard/Android/log %s" % (
    #     devices, os.path.join(os.getcwd(), "report", devices + "_" + app_name)))
    # time.sleep(3)
    # logging.info("-------------------抓取mars日志完成------------------------")
    # todo 小米需要注释下面
    # driver.press("home")
    # os.system('adb -s %s shell settings put system screen_off_timeout %s' % (devices, screen_off_timeout))
    # driver.screen_off()  # 息屏


# def _add_screenshot(driver, app_name):
#     """ 添加截图 """
#     screenshot_path = os.path.join(os.getcwd(), "report", driver.serial + "_" + app_name, "screenshot")
#     if not os.path.exists(screenshot_path):
#         os.makedirs(screenshot_path)
#     filename = os.path.join(screenshot_path, str(uuid.uuid1()) + ".png")
#     driver.screenshot(filename)  # 截图
#     logging.info("take screenshot: %s", str(filename))
#     allure.attach.file(filename, "失败截图 " + time.strftime("%m-%d %H:%M:%S", time.localtime()) + " " + str(filename),
#                        allure.attachment_type.PNG)  # 添加截图到报告中


# @pytest.hookimpl(tryfirst=True, hookwrapper=True)
# def pytest_runtest_makereport(item):
#     outcome = yield
#     rep = outcome.get_result()
#     if rep.when == "call" and rep.failed:
#         for i in item.funcargs:
#             if i != "request":
#                 if isinstance(item.funcargs[i][0], u2.Device) or isinstance(item.funcargs[i][0], wda.Client):
#                     _add_screenshot(item.funcargs[i][0], item.funcargs["request"].path.parent.name)


def pytest_collection_modifyitems(session, items):
    print("收集到的测试用例:%s" % items)
    # first_case = [i for i in items if "test_on_off_screen" in i.name][0]
    # items.remove(first_case)
    # items.insert(0, first_case)
    print("整理后的测试用例:%s" % items)
