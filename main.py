#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Author   : chuanwen.peng
# @Time     : 2023/3/6 16:55
# @File     : main.py
# @Project  : StabilityTest
"""
import argparse
import logging
import os
import shutil
import sys
import time

import pytest
from connect_glass import connect_main

from common.utils import Util, ReadConfig


def local_run(app_name):
    args = [os.path.join(app_name, "StressTest/teleprompter/test_teleprompter.py"), "-m M", "--alluredir",
            "/report/raw_data/", "--clean-alluredir"]
    # args = [app_name[0]]
    pytest.main(args)


def generate_report():
    report_path = os.path.join("report",
                               "html_report_" + time.strftime("%Y-%m-%d-%H-%M-%S", time.localtime(time.time())))
    os.system("allure generate " + "/report/raw_data/ -o " + report_path)
    return report_path


def open_report(report_path):
    # windows TODO 判断平台在linux会出错
    os.system("allure open %s -p 2022" % report_path)
    # os.system("nohup allure open %s -p 2022 &" % report_path)


def alter(file):
    new_data = []
    with open(file, 'r+', encoding='utf-8') as f:
        filedata = f.readlines()
        for line in filedata:
            if "wifi_verbose_logging_enabled" in line:
                line = line.replace('false', 'true')
            new_data.append(line)
    with open(file, 'w', encoding='utf-8') as f:
        for line in new_data:
            f.write(line)


def get_wlan_log(serial):
    Util().dev_root(serial)
    wifi_path = os.path.join(os.getcwd(), "WifiConfigStore.xml")
    if os.path.exists(wifi_path):
        os.remove(wifi_path)
    # TODO 获取build文件
    print("开始获取wifi配置文件")
    os.system(
        "adb -s %s shell cat data/misc/apexdata/com.android.wifi/WifiConfigStore.xml > WifiConfigStore.xml" % serial)
    while not os.path.exists(wifi_path):
        time.sleep(3)
        print("重试获取wifi配置文件")
        os.system(
            "adb -s %s shell cat data/misc/apexdata/com.android.wifi/WifiConfigStore.xml > WifiConfigStore.xml" % serial)
    print("完成获取wifi配置文件")
    file_name = os.path.join(os.getcwd(), wifi_path)
    # TODO 判断当前服务状态
    with open(wifi_path, 'r+', encoding='utf-8') as f:
        filedata = f.readlines()
        for line in filedata:
            if 'name="wifi_verbose_logging_enabled"' in line:
                alter(file=file_name)
                status = 1 if "error" in os.popen(
                    "adb -s %s push %s data/misc/apexdata/com.android.wifi/WifiConfigStore.xml" % (
                        serial, file_name)).read() else 0
                while status:
                    print("重试文件传输")
                    os.system("adb -s %s push %s data/misc/apexdata/com.android.wifi/WifiConfigStore.xml" % (
                        serial, file_name))
                    time.sleep(5)
                    status = 1 if "error" in os.popen(
                        "adb -s %s push %s system/WifiConfigStore.xml" % (serial, file_name)).read() else 0
                print("文件传输成功")
                logging.info("已经打开wlan详细日志")


def get_hci_log(serial):
    Util().dev_root(serial)
    os.system("adb -s %s shell setprop persist.bluetooth.btsnooplogmode full" % serial)
    time.sleep(3)
    os.system("adb -s %s shell setprop persist.vendor.service.bdroid.soclog true" % serial)
    time.sleep(3)
    os.system("adb -s %s shell svc bluetooth  disable" % serial)
    time.sleep(3)
    os.system("adb -s %s shell svc bluetooth enable" % serial)
    time.sleep(20)
    logging.info("已经打开hci详细日志")


def check_hci(serial):
    if "full" not in os.popen("adb -s %s shell getprop persist.bluetooth.btsnooplogmode" % serial).readlines()[0]:
        logging.info("正在打开%s设备的hci详细日志" % device)
        get_hci_log(device)
        logging.info("正在打开%s设备的wlan详细日志" % device)
        get_wlan_log(device)
        Util().dev_reboot(serial)
        Util().dev_root(serial)
    else:
        print("已经打开HCI日志！！！删除以前的日志")
        logging.info("已经打开HCI日志！！！删除以前的日志")
        os.system("adb -s %s root" % serial)
        time.sleep(2)
        # todo 删除手机
        model_name = "mars" if "meizu" in os.popen("adb -s %s shell getprop ro.product.model" % serial).readlines()[
            0].lower() else "star"
        if "mars" in model_name:
            logging.info("删除手机sdcard/Android/log/下文件")
            os.system("adb -s %s shell rm -rf sdcard/Android/log/*" % serial)
            time.sleep(2)
        else:
            logging.info("删除眼镜/data/vendor/wifi/wlan_logs/下文件")
            os.system("adb -s %s shell rm -rf sdcard/Android/log/*" % serial)
            time.sleep(2)
            os.system("adb -s %s shell rm -rf /data/misc/bluetooth/logs/*" % serial)
            time.sleep(2)


if __name__ == '__main__':
    # 删除之前的报告
    if os.path.exists("report"):
        shutil.rmtree("report")
    devices_list = ReadConfig().drive_list
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', type=str)
    args = parser.parse_args()
    if len(devices_list) >= 2:
        print('--------正在执行刷机互联流程---------')
        # connect_main(args.p)
    else:
        print('--------当前连接设备不足两台---------')
        os.system("kill -9 %s" % args.p)
        sys.exit()
    for device in devices_list:
        logging.info("正在打开%s设备的hci&wifi详细日志" % device)
        # check_hci(device)
    module_name = os.path.join(os.getcwd())
    local_run(module_name)
    report_path = generate_report()
    print("report location: %s" % report_path)
    open_report(report_path)
