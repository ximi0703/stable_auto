rem 批处理不行，自己复制出来一行行运行即可
@echo off
chcp 65001
set APK=%1
echo APK路径为：%APK%
adb root
adb push %APK% /data/local/tmp
adb shell chmod 755 /data/local/tmp/atx-agent
adb shell /data/local/tmp/atx-agent server -d --stop
rem  需要手动同意atx u2安装
ping -n 5 127.0.0.1 >nul
python -m uiautomator2 init

