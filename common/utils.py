#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
# @Author   : chuanwen.peng
# @Time     : 2023/3/13 13:52
# @File     : utils.py
# @Project  : StabilityTest
"""
import ctypes
import inspect
import os
import platform
import re
import time

import uiautomator2 as u2
import subprocess
import configparser
import json
import logging

from common.logger import setup_logger


def _async_raise(tid, exctype):
    """raises the exception, performs cleanup if needed"""
    tid = ctypes.c_long(tid)
    if not inspect.isclass(exctype):
        exctype = type(exctype)
    res = ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, ctypes.py_object(exctype))
    if res == 0:
        raise ValueError("invalid thread id")
    elif res != 1:
        # """if it returns a number greater than one, you're in trouble,
        # and you should call it again with exc=NULL to revert the effect"""
        ctypes.pythonapi.PyThreadState_SetAsyncExc(tid, None)
        raise SystemError("PyThreadState_SetAsyncExc failed")


def stop_thread(thread):
    _async_raise(thread.ident, SystemExit)


def log_detection(device, project_dir, func_stack):
    setup_logger(project_dir, func_stack)
    logcat_path = os.path.join(project_dir, "report", func_stack, "logcat")
    if not os.path.exists(logcat_path):
        os.makedirs(logcat_path)
    logcat_filename = os.path.join(logcat_path,
                                   time.strftime("%m%d_%H%M%S", time.localtime(time.time())) + ".txt")
    logcat_file = open(logcat_filename, "w", errors="ignore")
    os.system("adb -s %s logcat -c" % device)
    pop_log = subprocess.Popen(["adb", "-s", device, "logcat", "-v", "time"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)  # 启动logcat捕获日志
    logging.info("start capturing log: %s", str(logcat_file))
    while pop_log.poll() is None:
        buff = pop_log.stdout.readline().decode('utf-8')
        # todo 判断日志中的关键字
        check_err_log(buff)
        # if "调用互联发送消息id" in buff:
        #     logging.error(buff.strip())
        try:
            logcat_file.write(buff)
        except UnicodeEncodeError as e:
            logging.error(e)
    logcat_file.close()
    pop_log.terminate()  # 停止日志捕获
    logging.info("stop capturing log")


# def check_err_log(line):
#     if re.findall(BaseCashEmnu.SYSTEM_ANR, line):
#         logging.error("存在SYSTEM_ANR错误:" + line)
    # if re.findall(BaseCashEmnu.ANR, line):
    #     logging.error("存在anr错误:" + line)
    # if re.findall(BaseCashEmnu.CRASH, line):
    #     logging.error("存在crash错误:" + line)
    # if re.findall(BaseCashEmnu.ACCESSERROR, line):
    #     logging.error("存在违法访问错误:" + line)
    # if re.findall(BaseCashEmnu.MEMORYERROR, line):
    #     logging.error("存在内存不足错误:" + line)
    # if re.findall(BaseCashEmnu.FLOWERROR, line):
    #     logging.error("存在堆栈溢出错误:" + line)
    # if re.findall(BaseCashEmnu.IOException, line):
    #     logging.error("存在输入输出异常错误:" + line)
    # if re.findall(BaseCashEmnu.SQLException, line):
    #     logging.error("存在操作数据库异常错误:" + line)
    # if re.findall(BaseCashEmnu.NumberFormatException, line):
    #     logging.error("存在字符串转换为数字异常错误:" + line)
    # if re.findall(BaseCashEmnu.FileNotFoundException, line):
    #     logging.error("存在文件未找到错误:" + line)
    # if re.findall(BaseCashEmnu.EOFException, line):
    #     logging.error("存在文件已结束异常错误:" + line)
    # if re.findall(BaseCashEmnu.SecurityException, line):
    #     logging.error("存在违背安全原则错误:" + line)
    # if re.findall(BaseCashEmnu.ArrayIndexOutOfBoundsException, line):
    #     logging.error("存在数组下标越界错误:" + line)
    # if re.findall(BaseCashEmnu.NegativeArrayException, line):
    #     logging.error("存在数组负下标错误:" + line)
    # if re.findall(BaseCashEmnu.ClassCastException, line):
    #     logging.error("存在类型强制转换错误:" + line)
    # if re.findall(BaseCashEmnu.NullPointerException, line):
    #     logging.error("存在空指针错误:" + line)
    # if re.findall(BaseCashEmnu.ArithmeticException, line):
    #     logging.error("存在算术异常错误:" + line)


class Util:
    def __init__(self):
        pass

    def install(self, devices, path):
        """
        安装apk文件
        :return:
        """
        # adb install 安装错误常见列表
        errors = {'INSTALL_FAILED_ALREADY_EXISTS': '程序已经存在',
                  'INSTALL_DEVICES_NOT_FOUND': '找不到设备',
                  'INSTALL_FAILED_DEVICE_OFFLINE': '设备离线',
                  'INSTALL_FAILED_INVALID_APK': '无效的APK',
                  'INSTALL_FAILED_INVALID_URI': '无效的链接',
                  'INSTALL_FAILED_INSUFFICIENT_STORAGE': '没有足够的存储空间',
                  'INSTALL_FAILED_DUPLICATE_PACKAGE': '已存在同名程序',
                  'INSTALL_FAILED_NO_SHARED_USER': '要求的共享用户不存在',
                  'INSTALL_FAILED_UPDATE_INCOMPATIBLE': '版本不能共存',
                  'INSTALL_FAILED_SHARED_USER_INCOMPATIBLE': '需求的共享用户签名错误',
                  'INSTALL_FAILED_MISSING_SHARED_LIBRARY': '需求的共享库已丢失',
                  'INSTALL_FAILED_REPLACE_COULDNT_DELETE': '需求的共享库无效',
                  'INSTALL_FAILED_DEXOPT': 'dex优化验证失败',
                  'INSTALL_FAILED_DEVICE_NOSPACE': '手机存储空间不足导致apk拷贝失败',
                  'INSTALL_FAILED_DEVICE_COPY_FAILED': '文件拷贝失败',
                  'INSTALL_FAILED_OLDER_SDK': '系统版本过旧',
                  'INSTALL_FAILED_CONFLICTING_PROVIDER': '存在同名的内容提供者',
                  'INSTALL_FAILED_NEWER_SDK': '系统版本过新',
                  'INSTALL_FAILED_TEST_ONLY': '调用者不被允许测试的测试程序',
                  'INSTALL_FAILED_CPU_ABI_INCOMPATIBLE': '包含的本机代码不兼容',
                  'CPU_ABIINSTALL_FAILED_MISSING_FEATURE': '使用了一个无效的特性',
                  'INSTALL_FAILED_CONTAINER_ERROR': 'SD卡访问失败',
                  'INSTALL_FAILED_INVALID_INSTALL_LOCATION': '无效的安装路径',
                  'INSTALL_FAILED_MEDIA_UNAVAILABLE': 'SD卡不存在',
                  'INSTALL_FAILED_INTERNAL_ERROR': '系统问题导致安装失败',
                  'INSTALL_PARSE_FAILED_NO_CERTIFICATES': '文件未通过认证 >> 设置开启未知来源',
                  'INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES': '文件认证不一致 >> 先卸载原来的再安装',
                  'INSTALL_FAILED_INVALID_ZIP_FILE': '非法的zip文件 >> 先卸载原来的再安装',
                  'INSTALL_CANCELED_BY_USER': '需要用户确认才可进行安装',
                  'INSTALL_FAILED_VERIFICATION_FAILURE': '验证失败 >> 尝试重启手机',
                  'DEFAULT': '未知错误'
                  }
        print('Installing...')
        l = os.popen("adb -s %s install -r %s" % (devices, path)).read()
        if 'Success' in l:
            print('Install Success')
        if 'Failure' in l:
            reg = re.compile('\\[(.+?)\\]')
            key = re.findall(reg, l)[0]
            try:
                print('Install Failure >> %s' % errors[key])
            except KeyError:
                print('Install Failure >> %s' % key)
        return 1 if [i for i in l.split() if "Success" in i] else 0

    def get_network_state(self, devices):
        """
        设备是否连上互联网
        :return:
        """
        return 0 if subprocess.Popen('adb -s %s shell ping -w 1 www.baidu.com' % devices, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, shell=True).stderr.readlines() else 1

    def close_wear_detect(self, glass_serial):
        print("关闭佩戴检测服务")
        self.dev_root(glass_serial)
        os.system('adb -s %s shell "setprop persist.hw.wear.bp_support false"' % glass_serial)
        self.dev_reboot(glass_serial)

    def device_unlock(self, serial):
        # if not serial.info.get('screenOn'):
        #     serial.screen_off()
        while serial.info.get("currentPackageName") == 'com.android.systemui':
            # serial.unlock()
            serial.screen_on()
            serial.swipe(0.5, 0.9, 0.5, 0.1)
            time.sleep(0.5)

    def dev_lock_time(self, device):
        os.system('adb -s %s shell settings put system screen_off_timeout 1800000' % device)

    def dev_unlock(self, device):
        self.dev_root(device.serial)
        if not device.info['screenOn']:
            device.press("power")
            device.swipe(0.3, 0.9, 0.9, 0.1)
            # TODO 源码无以下这行，原因是手机滑动之后会有延迟，需增加超时机制
            time.sleep(1)

    def connect_wifi(self, device, path="common/adb-join-wifi.apk"):
        self.dev_root(device)
        install_status = self.install(device, path)
        if install_status:
            os.system(
                "adb -s %s shell am start -n com.steinwurf.adbjoinwifi/.MainActivity --esn connect -e ssid XR@Ruijie-5G -e password_type WPA -e password xjsd@123456" % device)
            time.sleep(2)
            # if not self.wifi_connect_status(device):
            u2.connect(device).app_stop("com.steinwurf.adbjoinwifi")

    def wifi_connect_status(self, device):
        logging.info("---------------------获取wifi连接状态： %s------------------------" % device)
        p = os.popen('adb -s %s shell settings get global wifi_on' % device)

        status = 1 if "1" in p.readline()[0] else 0
        if status:
            logging.info("---------------------获取wifi接状态： 开------------------------")
        else:
            logging.info("---------------------获取wifi接状态： 关------------------------")
        return status

    def bt_connect_status(self, device):
        p = os.popen('adb -s %s shell settings get global bluetooth_on' % device)

        status = 1 if "1" in p.readline()[0] else 0
        if status:
            logging.info("---------------------获取bluetooth接状态： 开------------------------")
        else:
            logging.info("---------------------获取bluetooth接状态： 关------------------------")
        return status

    def dev_root(self, serial):
        root_status = "adbd is already running as root" in [i.strip() for i in
                                                            os.popen("adb -s %s root" % serial).readlines()]
        if not root_status:
            time.sleep(3)
            root_status = "adbd is already running as root" in [i.strip() for i in
                                                                os.popen("adb -s %s root" % serial).readlines()]
        logging.info("---------------------root设备： %s成功------------------------" % serial)
        return root_status

    def dev_reboot(self, serial):
        os.system("adb -s %s reboot" % serial)
        time.sleep(40)
        root_status = 1 if serial in os.popen("adb devices").read() else 0
        while not root_status:
            time.sleep(5)
            root_status = 1 if serial in os.popen("adb devices").read() else 0
        logging.info("---------------------reboot设备： %s成功------------------------" % serial)
        return root_status

    def device_status(self, serial):
        """设备是否在线"""
        root_status = 1 if [i for i in os.popen("adb devices").readlines() if serial in i and "device" in i] else 0
        if not root_status:
            time.sleep(5)
            root_status = 1 if [i for i in os.popen("adb devices").readlines() if serial in i and "device" in i] else 0
        logging.info("---------------------device设备： %s成功------------------------" % serial)
        return root_status

    def simulate_wear(self, glass_serial):
        """模拟佩戴"""
        self.dev_root(glass_serial)
        os.system('adb -s %s shell "am broadcast -a com.upup.debug.WEAR_STATE_CHANGED --ei state 1"' % glass_serial)
        time.sleep(0.5)


class AdbTools(object):
    """
    ADB工具类
    """

    def __init__(self, device_id=''):
        self.__system = platform.system()
        self.__find = ''
        self.__command = ''
        self.__device_id = device_id
        self.__get_find()
        self.__check_adb()
        self.__connection_devices()

    def __get_find(self):
        """
        判断系统类型，windows使用findstr，linux使用grep
        :return:
        """
        if self.__system is "Windows":
            self.__find = "findstr"
        else:
            self.__find = "grep"

    def __check_adb(self):
        """
        检查adb
        判断是否设置环境变量ANDROID_HOME
        :return:
        """
        # if "ANDROID_HOME" in os.environ:
        if "platform-tools" in os.environ.get("PATH") or "platform-tools" in os.environ.get("ANDROID_HOME"):
            if self.__system == "Windows":
                # path = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", "adb.exe")
                base_path = [i for i in os.environ["PATH"].split(";") if "platform-tools" in i][0]
                path = os.path.join(base_path, "adb.exe")
                if os.path.exists(path):
                    self.__command = path
                else:
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])
            else:
                base_path = [i for i in os.environ.get("PATH").split(":") if "adb" in i][0]
                # path = os.path.join(base_path, "adb")
                # path = os.path.join(os.environ["ANDROID_HOME"], "platform-tools", "adb")
                if os.path.exists(base_path):
                    self.__command = base_path
                else:
                    raise EnvironmentError(
                        "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])
        else:
            raise EnvironmentError(
                "Adb not found in $ANDROID_HOME path: %s." % os.environ["ANDROID_HOME"])

    def check_pkg(self, package_name):
        """
        检查应用是否安装
        :return:
        """
        if self.__system is "Windows":
            pid_command = self.shell("pm list packages | %s %s$" % (self.__find, package_name)).read()
            if pid_command:
                return True
            else:
                return False
        else:
            pid_command = self.shell("pm list packages | %s -w %s" % (self.__find, package_name)).read()
            if pid_command:
                return True
            else:
                return False

    def __connection_devices(self):
        """
        连接指定设备，单个设备可不传device_id
        :return:
        """
        if self.__device_id == "":
            return
        self.__device_id = "-s %s" % self.__device_id

    def adb(self, args):
        """
        执行adb命令
        :param args:参数
        :return:
        """
        cmd = "%s %s %s" % (self.__command, self.__device_id, str(args))
        # print(cmd)
        return os.popen(cmd)

    def shell(self, args):
        """
        执行adb shell命令
        :param args:参数
        :return:
        """
        cmd = "%s %s shell %s" % (self.__command, self.__device_id, str(args))
        # print(cmd)
        return os.popen(cmd)

    def mkdir(self, path):
        """
        创建目录
        :param path: 路径
        :return:
        """
        return self.shell('mkdir %s' % path)

    def get_devices(self):
        """
        获取设备列表
        :return:
        """
        l = self.adb('devices').readlines()
        return [i.split()[0] for i in l if 'devices' not in i and len(i) > 5]

    def get_current_application(self):
        """
        获取当前运行的应用信息
        :return:
        """
        return self.shell(r'dumpsys window w | %s / | %s name=' % (self.__find, self.__find)).read()

    def get_current_package(self):
        """
        获取当前运行app包名
        :return:
        """
        reg = re.compile(r'name=(.+?)/')
        return re.findall(reg, self.get_current_application())[0]

    def get_current_activity(self):
        """
        获取当前运行activity
        :return: package/activity
        """
        reg = re.compile(r'name=(.+?)\)')
        return re.findall(reg, self.get_current_application())[0]

    def __get_process(self, package_name):
        """
        获取进程信息
        :param package_name:
        :return:
        """
        if self.__system is "Windows":
            pid_command = self.shell("ps | %s %s$" % (self.__find, package_name)).read()
        else:
            pid_command = self.shell("ps | %s -w %s" % (self.__find, package_name)).read()
        return pid_command

    def process_exists(self, package_name):
        """
        返回进程是否存在
        :param package_name:
        :return:
        """
        process = self.__get_process(package_name)
        return package_name in process

    def get_pid(self, package_name):
        """
        获取pid
        :return:
        """
        pid_command = self.__get_process(package_name)
        if pid_command == '':
            print("The process doesn't exist.")
            return pid_command

        req = re.compile(r"\d+")
        result = str(pid_command).split()
        result.remove(result[0])
        return req.findall(" ".join(result))[0]

    def get_uid(self, pid):
        """
        获取uid
        :param pid:
        :return:
        """
        result = self.shell("cat /proc/%s/status" % pid).readlines()
        for i in result:
            if 'uid' in i.lower():
                return i.split()[1]

    def get_flow_data_tcp(self, uid):
        """
        获取应用tcp流量
        :return:(接收, 发送)
        """
        tcp_rcv = self.shell("cat proc/uid_stat/%s/tcp_rcv" % uid).read().split()[0]
        tcp_snd = self.shell("cat proc/uid_stat/%s/tcp_snd" % uid).read().split()[0]
        return tcp_rcv, tcp_snd

    def get_flow_data_all(self, uid):
        """
        获取应用流量全部数据
        包含该应用多个进程的所有数据 tcp udp等
        (rx_bytes, tx_bytes) >> (接收, 发送)
        :param uid:
        :return:list(dict)
        """
        all_data = []
        d = {}
        data = self.shell("cat /proc/net/xt_qtaguid/stats | %s %s" % (self.__find, uid)).readlines()
        for i in data:
            if not i.startswith('\n'):
                item = i.strip().split()
                d['idx'] = item[0]
                d['iface'] = item[1]
                d['acct_tag_hex'] = item[2]
                d['uid_tag_int'] = item[3]
                d['cnt_set'] = item[4]
                d['rx_bytes'] = item[5]
                d['rx_packets'] = item[6]
                d['tx_bytes'] = item[7]
                d['tx_packets'] = item[8]
                d['rx_tcp_bytes'] = item[9]
                d['rx_tcp_packets'] = item[10]
                d['rx_udp_bytes'] = item[11]
                d['rx_udp_packets'] = item[12]
                d['rx_other_bytes'] = item[13]
                d['rx_other_packets'] = item[14]
                d['tx_tcp_bytes'] = item[15]
                d['tx_tcp_packets'] = item[16]
                d['tx_udp_bytes'] = item[17]
                d['tx_udp_packets'] = item[18]
                d['tx_other_bytes'] = item[19]
                d['tx_other_packets'] = item[20]

                all_data.append(d)
                d = {}
        return all_data

    @staticmethod
    def dump_apk(path):
        """
        dump apk文件
        :param path: apk路径
        :return:
        """
        # 检查build-tools是否添加到环境变量中
        # 需要用到里面的aapt命令
        l = os.environ['PATH'].split(';')
        build_tools = False
        for i in l:
            if 'build-tools' in i:
                build_tools = True
        if not build_tools:
            raise EnvironmentError("ANDROID_HOME BUILD-TOOLS COMMAND NOT FOUND.\nPlease set the environment variable.")
        return os.popen('aapt dump badging %s' % (path,))

    @staticmethod
    def dump_xml(path, filename):
        """
        dump apk xml文件
        :return:
        """
        return os.popen('aapt dump xmlstrings %s %s' % (path, filename))

    def uiautomator_dump(self):
        """
        获取屏幕uiautomator xml文件
        :return:
        """
        return self.shell('uiautomator dump').read().split()[-1]

    def pull(self, source, target):
        """
        从手机端拉取文件到电脑端
        :return:
        """
        self.adb('pull %s %s' % (source, target))

    def push(self, source, target):
        """
        从电脑端推送文件到手机端
        :param source:
        :param target:
        :return:
        """
        self.adb('push %s %s' % (source, target))

    def remove(self, path):
        """
        从手机端删除文件
        :return:
        """
        self.shell('rm %s' % (path,))

    def clear_app_data(self, package):
        """
        清理应用数据
        :return:
        """
        self.shell('pm clear %s' % (package,))

    def install(self, path):
        """
        安装apk文件
        :return:
        """
        # adb install 安装错误常见列表
        errors = {'INSTALL_FAILED_ALREADY_EXISTS': '程序已经存在',
                  'INSTALL_DEVICES_NOT_FOUND': '找不到设备',
                  'INSTALL_FAILED_DEVICE_OFFLINE': '设备离线',
                  'INSTALL_FAILED_INVALID_APK': '无效的APK',
                  'INSTALL_FAILED_INVALID_URI': '无效的链接',
                  'INSTALL_FAILED_INSUFFICIENT_STORAGE': '没有足够的存储空间',
                  'INSTALL_FAILED_DUPLICATE_PACKAGE': '已存在同名程序',
                  'INSTALL_FAILED_NO_SHARED_USER': '要求的共享用户不存在',
                  'INSTALL_FAILED_UPDATE_INCOMPATIBLE': '版本不能共存',
                  'INSTALL_FAILED_SHARED_USER_INCOMPATIBLE': '需求的共享用户签名错误',
                  'INSTALL_FAILED_MISSING_SHARED_LIBRARY': '需求的共享库已丢失',
                  'INSTALL_FAILED_REPLACE_COULDNT_DELETE': '需求的共享库无效',
                  'INSTALL_FAILED_DEXOPT': 'dex优化验证失败',
                  'INSTALL_FAILED_DEVICE_NOSPACE': '手机存储空间不足导致apk拷贝失败',
                  'INSTALL_FAILED_DEVICE_COPY_FAILED': '文件拷贝失败',
                  'INSTALL_FAILED_OLDER_SDK': '系统版本过旧',
                  'INSTALL_FAILED_CONFLICTING_PROVIDER': '存在同名的内容提供者',
                  'INSTALL_FAILED_NEWER_SDK': '系统版本过新',
                  'INSTALL_FAILED_TEST_ONLY': '调用者不被允许测试的测试程序',
                  'INSTALL_FAILED_CPU_ABI_INCOMPATIBLE': '包含的本机代码不兼容',
                  'CPU_ABIINSTALL_FAILED_MISSING_FEATURE': '使用了一个无效的特性',
                  'INSTALL_FAILED_CONTAINER_ERROR': 'SD卡访问失败',
                  'INSTALL_FAILED_INVALID_INSTALL_LOCATION': '无效的安装路径',
                  'INSTALL_FAILED_MEDIA_UNAVAILABLE': 'SD卡不存在',
                  'INSTALL_FAILED_INTERNAL_ERROR': '系统问题导致安装失败',
                  'INSTALL_PARSE_FAILED_NO_CERTIFICATES': '文件未通过认证 >> 设置开启未知来源',
                  'INSTALL_PARSE_FAILED_INCONSISTENT_CERTIFICATES': '文件认证不一致 >> 先卸载原来的再安装',
                  'INSTALL_FAILED_INVALID_ZIP_FILE': '非法的zip文件 >> 先卸载原来的再安装',
                  'INSTALL_CANCELED_BY_USER': '需要用户确认才可进行安装',
                  'INSTALL_FAILED_VERIFICATION_FAILURE': '验证失败 >> 尝试重启手机',
                  'DEFAULT': '未知错误'
                  }
        print('Installing...')
        l = self.adb('install -r %s' % (path,)).read()
        if 'Success' in l:
            print('Install Success')
        if 'Failure' in l:
            reg = re.compile('\\[(.+?)\\]')
            key = re.findall(reg, l)[0]
            try:
                print('Install Failure >> %s' % errors[key])
            except KeyError:
                print('Install Failure >> %s' % key)
        return 1 if [i for i in l.split() if "Success" in i] else 0

    def uninstall(self, package):
        """
        卸载apk
        :param package: 包名
        :return:
        """
        print('Uninstalling...')
        l = self.adb('uninstall %s' % (package,)).read()
        print(l)

    def get_cache_logcat(self):
        """
        导出缓存日志
        :return:
        """
        return self.adb('logcat -v time -d')

    def get_crash_logcat(self):
        """
        导出崩溃日志
        :return:
        """
        return self.adb('logcat -v time -d | %s AndroidRuntime' % (self.__find,))

    def clear_cache_logcat(self):
        """
        清理缓存区日志
        :return:
        """
        self.adb('logcat -c')

    def get_device_time(self):
        """
        获取设备时间
        :return:
        """
        return self.shell('date').read().strip()

    def ls(self, command):
        """
        shell ls命令
        :return:
        """
        return self.shell('ls %s' % (command,)).readlines()

    def file_exists(self, target):
        """
        判断文件在目标路径是否存在
        :return:
        """
        l = self.ls(target)
        for i in l:
            if i.strip() == target:
                return True
        return False

    def is_install(self, target_app):
        """
        判断目标app在设备上是否已安装
        :param target_app: 目标app包名
        :return: bool
        """
        return target_app in self.shell('pm list packages %s' % (target_app,)).read()

    def get_device_model(self):
        """
        获取设备型号
        :return:
        """
        return self.shell('getprop ro.product.model').read().strip()

    def get_device_id(self):
        """
        获取设备id
        :return:
        """
        return self.adb('get-serialno').read().strip()

    def get_device_android_version(self):
        """
        获取设备Android版本
        :return:
        """
        return self.shell('getprop ro.build.version.release').read().strip()

    def get_device_sdk_version(self):
        """
        获取设备SDK版本
        :return:
        """
        return self.shell('getprop ro.build.version.sdk').read().strip()

    def get_device_mac_address(self):
        """
        获取设备MAC地址
        :return:
        """
        return self.shell('cat /sys/class/net/wlan0/address').read().strip()

    def get_device_ip_address(self):
        """
        获取设备IP地址
        pass: 适用WIFI 蜂窝数据
        :return:
        """
        if not self.get_wifi_state() and not self.get_data_state():
            return
        l = self.shell('ip addr | %s global' % self.__find).read()
        reg = re.compile(r'\d+.\d+.\d+.\d+')
        return re.findall(reg, l)[0]

    def get_device_imei(self):
        """
        获取设备IMEI
        :return:
        """
        sdk = self.get_device_sdk_version()
        # Android 5.0以下方法
        if int(sdk) < 21:
            l = self.shell('dumpsys iphonesubinfo').read()
            reg = re.compile('[0-9]{15}')
            return re.findall(reg, l)[0]
        elif self.root():
            l = self.shell('service call iphonesubinfo 1').read()
            print(l)
            print(re.findall(re.compile("'.+?'"), l))
            imei = ''
            for i in re.findall(re.compile("'.+?'"), l):
                imei += i.replace('.', '').replace("'", '').replace(' ', '')
            return imei
        else:
            print('The device not root.')
            return ''

    def check_sim_card(self):
        """
        检查设备SIM卡
        :return:
        """
        return len(self.shell('getprop | %s gsm.operator.alpha]' % self.__find).read().strip().split()[-1]) > 2

    def get_device_operators(self):
        """
        获取运营商
        :return:
        """
        return self.shell('getprop | %s gsm.operator.alpha]' % self.__find).read().strip().split()[-1]

    def get_device_state(self):
        """
        获取设备状态
        :return:
        """
        return self.adb('get-state').read().strip()

    def get_display_state(self):
        """
        获取屏幕状态
        :return: 亮屏/灭屏
        """
        l = self.shell('dumpsys power').readlines()
        for i in l:
            if 'mScreenOn=' in i:
                return i.split()[-1] == 'mScreenOn=true'
            if 'Display Power' in i:
                return 'ON' in i.split('=')[-1].upper()

    def get_screen_normal_size(self):
        """
        获取设备屏幕分辨率 >> 标配
        :return:
        """
        return self.shell('wm size').read().strip().split()[-1].split('x')

    def get_screen_reality_size(self):
        """
        获取设备屏幕分辨率 >> 实际分辨率
        :return:
        """
        x = 0
        y = 0
        l = self.shell(r'getevent -p | %s -e "0"' % self.__find).readlines()
        for n in l:
            if len(n.split()) > 0:
                if n.split()[0] == '0035':
                    x = int(n.split()[7].split(',')[0])
                elif n.split()[0] == '0036':
                    y = int(n.split()[7].split(',')[0])
        return x, y

    def get_device_interior_sdcard(self):
        """
        获取内部SD卡空间
        :return: (path,total,used,free,block)
        """
        return self.shell(r'df | %s /mnt/shell/emulated' % self.__find).read().strip().split()

    def get_device_external_sdcard(self):
        """
        获取外部SD卡空间
        :return: (path,total,used,free,block)
        """
        return self.shell('df | %s /storage' % self.__find).read().strip().split()

    def __fill_rom(self, path, stream, count):
        """
        填充数据
        :param path: 填充地址
        :param stream: 填充流大小
        :param count: 填充次数
        :return:
        """
        self.shell('dd if=/dev/zero of=%s bs=%s count=%s' % (path, stream, count)).read().strip()

    def fill_interior_sdcard(self, filename, size):
        """
        填充内置SD卡
        :param filename: 文件名
        :param size: 填充大小，单位byte
        :return:
        """
        if size > 10485760:  # 10m
            self.__fill_rom('sdcard/%s' % filename, 10485760, size / 10485760)
        else:
            self.__fill_rom('sdcard/%s' % filename, size, 1)

    def fill_external_sdcard(self, filename, size):
        """
        填充外置SD卡
        :param filename: 文件名
        :param size: 填充大小，单位byte
        :return:
        """
        path = self.get_device_external_sdcard()[0]
        if size > 10485760:  # 10m
            self.__fill_rom('%s/%s' % (path, filename), 10485760, size / 10485760)
        else:
            self.__fill_rom('%s/%s' % (path, filename), size, 1)

    def kill_process(self, pid):
        """
        杀死进程
        pass: 一般需要权限不推荐使用
        :return:
        """
        return self.shell('kill %s' % pid).read().strip()

    def quit_app(self, package):
        """
        退出应用
        :return:
        """
        return self.shell('am force-stop %s' % package).read().strip()

    def reboot(self):
        """
        重启设备
        :return:
        """
        self.adb('reboot')

    def recovery(self):
        """
        重启设备并进入recovery模式
        :return:
        """
        self.adb('reboot recovery')

    def fastboot(self):
        """
        重启设备并进入fastboot模式
        :return:
        """
        self.adb('reboot bootloader')

    def root(self):
        """
        获取root状态
        :return:
        """
        return 'not found' not in self.shell('su -c ls -l /data/').read().strip()

    def wifi(self, power):
        """
        开启/关闭wifi
        pass: 需要root权限
        :return:
        """
        if not self.root():
            print('The device not root.')
            return
        if power:
            self.shell('su -c svc wifi enable').read().strip()
        else:
            self.shell('su -c svc wifi disable').read().strip()

    def data(self, power):
        """
        开启/关闭蜂窝数据
        pass: 需要root权限
        :return:
        """
        if not self.root():
            print('The device not root.')
            return
        if power:
            self.shell('su -c svc data enable').read().strip()
        else:
            self.shell('su -c svc data disable').read().strip()

    def get_wifi_state(self):
        """
        获取WiFi连接状态
        :return:
        """
        return 'enabled' in self.shell('dumpsys wifi | %s ^Wi-Fi' % self.__find).read().strip()

    def get_data_state(self, devices):
        """
        获取移动网络连接状态
        :return:
        """
        return '2' in self.shell('dumpsys telephony.registry | %s mDataConnectionState' % self.__find).read().strip()

    def get_network_state(self, devices):
        """
        设备是否连上互联网
        :return:
        """
        return 0 if subprocess.Popen('adb -s %s shell ping -w 1 www.baidu.com' % devices, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).stderr.readlines() else 1
        # return 'unknown host' not in self.shell('ping -w 1 www.baidu.com').read().strip()

    def get_wifi_password_list(self):
        """
        获取WIFI密码列表
        :return:
        """
        if not self.root():
            print('The device not root.')
            return []
        l = re.findall(re.compile(r'ssid=".+?"\s{3}psk=".+?"'), self.shell('su -c cat /data/misc/wifi/*.conf').read())
        return [re.findall(re.compile('".+?"'), i) for i in l]

    def call(self, number):
        """
        拨打电话
        :param number:
        :return:
        """
        self.shell('am start -a android.intent.action.CALL -d tel:%s' % number)

    def open_url(self, url):
        """
        打开网页
        :return:
        """
        self.shell('am start -a android.intent.action.VIEW -d %s' % url)

    def start_application(self, component):
        """
        启动一个应用
        e.g: com.android.settings/com.android.settings.Settings
        """
        self.shell("am start -n %s" % component)

    def send_keyevent(self, keycode):
        """
        发送一个按键事件
        https://developer.android.com/reference/android/view/KeyEvent.html
        :return:
        """
        self.shell('input keyevent %s' % keycode)

    def rotation_screen(self, param):
        """
        旋转屏幕
        :param param: 0 >> 纵向，禁止自动旋转; 1 >> 自动旋转
        :return:
        """
        self.shell('/system_framework/bin/content insert --uri content://settings/system_framework --bind '
                   'name:s:accelerometer_rotation --bind value:i:%s' % param)

    def instrument(self, command):
        """
        启动instrument app
        :param command: 命令
        :return:
        """
        return self.shell('am instrument %s' % command).read()

    def export_apk(self, package, target_path='', timeout=5000):
        """
        从设备导出应用
        :param timeout: 超时时间
        :param target_path: 导出后apk存储路径
        :param package: 包名
        :return:
        """
        num = 0
        if target_path == '':
            self.adb('pull /data/app/%s-1/base.apk %s' % (package, os.path.expanduser('~')))
            while 1:
                num += 1
                if num <= timeout:
                    if os.path.exists(os.path.join(os.path.expanduser('~'), 'base.apk')):
                        os.rename(os.path.join(os.path.expanduser('~'), 'base.apk'),
                                  os.path.join(os.path.expanduser('~'), '%s.apk' % package))

        else:
            self.adb('pull /data/app/%s-1/base.apk %s' % (package, target_path))
            while 1:
                num += 1
                if num <= timeout:
                    if os.path.exists(os.path.join(os.path.expanduser('~'), 'base.apk')):
                        os.rename(os.path.join(os.path.expanduser('~'), 'base.apk'),
                                  os.path.join(os.path.expanduser('~'), '%s.apk' % package))


class ReadConfig:
    """ 读取配置的类 """

    #
    # __instance = None
    #
    # def __new__(cls, *args, **kwargs):
    #     if not cls.__instance:
    #         cls.__instance = super(ReadConfig, cls).__new__(cls, *args, **kwargs)
    #     return cls.__instance

    def __init__(self, root_dir=os.getcwd()):
        self.cf = configparser.ConfigParser()
        self.root_config_path = os.path.join(root_dir, "config.ini")
        self.cf.read(self.root_config_path, "utf-8")
        if root_dir.split(os.path.sep)[-1] == "StressTest" or root_dir.split(os.path.sep)[-1] == "Stable_XR":
            # if root_dir.split(os.path.sep)[-1] == "MTBF" or root_dir.split(os.path.sep)[-1] == "StressTest":
            devices_list = eval(self.cf.get("DEVICE", "devices_list"))
            # self.drive_list = [u2.connect(i) for i in devices_list]
            self.drive_list = [i for i in devices_list]
            # todo 错误日志
            keys = [i[0] for i in self.cf.items("ERROR") if not i[0].startswith("i_")]
            values = [i[1] for i in self.cf.items("ERROR") if not i[0].startswith("i_")]
            self.error_log = dict(zip(keys, values))
        else:
            try:
                for item in self.cf.sections():
                    if "PACKAGE" in item:
                        self.package_name = eval(self.cf.get("PACKAGE", "package_name"))
                    elif "ELEMENT" in item:
                        self.element_list = self.cf.items("ELEMENT")
                        elements = [i[0] for i in self.cf.items("ELEMENT")]
                        values = [eval(i[1]) for i in self.cf.items("ELEMENT")]
                        self.element_dict = dict(zip(elements, values))
                    elif "COMMAND" in item:
                        self.order_list = self.cf.items("COMMAND")
                        orders = [i[0] for i in self.cf.items("COMMAND")]
                        values = [eval(i[1]) for i in self.cf.items("COMMAND")]
                        self.order_dict = dict(zip(orders, values))
            except configparser.NoSectionError as e:
                logging.error(e)

    # @property
    def get_platform(self, app_name) -> str:
        pkg_config_path = os.path.join(app_name, "config.ini")
        self.cf.read(pkg_config_path, "utf-8")
        platform = self.cf.get("DRIVER", "platform")
        return platform.lower()

    # @property
    def get_implicitly_wait(self, app_name) -> float:
        pkg_config_path = os.path.join(app_name, "config.ini")
        self.cf.read(pkg_config_path, "utf-8")
        implicitly_wait = self.cf.get("DRIVER", "implicitly_wait")
        return float(implicitly_wait)

    # @property
    def get_check_error_toast(self, app_name) -> bool:
        pkg_config_path = os.path.join(app_name, "config.ini")
        self.cf.read(pkg_config_path, "utf-8")
        check_error_toast = self.cf.get("DRIVER", "check_error_toast")
        return True if check_error_toast.lower() == "true" else False

    # @property
    def get_package_name(self, app_name) -> list:
        pkg_config_path = os.path.join(app_name, "common.ini")
        self.cf.read(pkg_config_path, "utf-8")
        package_name = self.cf.get(self.get_platform(app_name).upper(), "package_name")
        return json.loads(package_name)

    # @property
    def get_popup_elements(self, app_name) -> list:
        pkg_config_path = os.path.join(app_name, "common.ini")
        self.cf.read(pkg_config_path, "utf-8")
        popup_elements = self.cf.get(self.get_platform(app_name).upper(), "popup_element")
        return json.loads(popup_elements)

    @property
    def get_env(self) -> str:
        self.cf.read(self.root_config_path, "utf-8")
        env = self.cf.get("ENVIRONMENT", "env")
        return env.lower()

    @property
    def get_region(self) -> str:
        self.cf.read(self.root_config_path, "utf-8")
        region = self.cf.get("ENVIRONMENT", "region")
        return region.lower()

    @property
    def get_project_dir(self):
        return str(self.root_dir)


if __name__ == '__main__':
    # r = ReadConfig(os.getcwd())
    Util().connect_wifi("1000190131J00021")
