#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Author   : chuanwen.peng
# @Time     : 2023/3/24 14:34
# @File     : main.py
# @Project  : Stable_XR
"""
import os
import time

'''
刷机脚本
'''
if __name__ == '__main__':
    # todo 判断设备属性
    check_devices = [i for i in os.popen("adb devices").readlines() if "device" in i and "attached" not in i]
    if check_devices > 1:
        print("连接设备大于1台！请选择对应的设备！")
        device_list = [i.split()[0] for i in [i for i in os.popen("adb devices").readlines() if "device\n" in i]]
        for devi in device_list:
            print(devi)
        device_index = int(input("请选择需要刷机的设备序号（1， 2， 3）："))
        serial = device_list[device_index - 1]
    elif len(check_devices) == 1:
        check_devices = [i for i in os.popen("adb devices").readlines() if "device" in i and "attached" not in i]
        serial = check_devices[0]
    else:
        print("请检查设备是否连接！")
    model_name = "mars" if "meizu" in os.popen("adb -s %s shell getprop ro.product.model" % serial).readlines()[
        0].lower() else "star"
    print("当前连接设备为: %s" % model_name)
    if "mars" in model_name:
        branch = "Mars_QTF10_XR"
        zip_name = "out_image"
    else:
        branch = "daily"
        zip_name = "star"
    debug_type = input("请输入需要刷机的版本是user还是debug： ")
    version_name = input("请输入需要刷机的版本: ")
    if "debug" in debug_type:
        debug_type = "userdebug"
    version_path = os.path.join("/home/chuanwenpeng/workspace/smoketest_glass/", model_name, branch, debug_type)
    firmware_list = os.listdir(version_path)
    firmware_list_new = sorted(os.listdir(version_path),
                               key=lambda x: os.path.getmtime(os.path.join(version_path, x)), reverse=True)
    flag = True
    firmware_list_new2 = [i for i in firmware_list_new if i.endswith('.7z')]
    for name in firmware_list_new2:
        if version_name in name:
            flag = False
            print("当前选择的版本为：%s" % name)
            # todo 复制过来
            file_path = os.path.join(version_path, name)
            print("正在复制刷机包")
            os.system("cp %s ." % file_path)
            time.sleep(1)
            # 解压
            print("正在解压包")
            os.system("7z x %s -o%s" % (name, zip_name))
            print("正在进入bootloader")
            os.system("adb -s %s reboot bootloader" % serial)
            time.sleep(18)
            # 开始刷机
            if model_name == "mars":
                zip_path = os.path.join(os.getcwd(), zip_name, "out_image", "flashall-erase-userdata.sh")
                qiehuan_path = os.path.join(os.getcwd(), zip_name, "out_image")
            else:
                zip_path = os.path.join(os.getcwd(), zip_name, "flashall-erase-userdata.sh")
                qiehuan_path = os.path.join(os.getcwd(), zip_name)
            os.chdir(qiehuan_path)
            time.sleep(2)
            os.system("/bin/bash %s" % zip_path)
            # 删除压缩包和文件
            os.chdir("/home/update_firmware")
            print("当前位置: %s" % os.getcwd())
            print("压缩包位置: %s" % os.path.join(os.getcwd(), zip_name))
            print("压缩： %s" % name)
            os.system("rm -rf %s" % os.path.join(os.getcwd(), zip_name))
            time.sleep(1)
            os.system("rm -rf %s" % name)
            time.sleep(1)
            break
    if flag:
        print("列表下没有选择的版本，请确保每日构建版本已成功下载！")
