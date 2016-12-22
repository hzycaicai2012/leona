#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import types

import leona.util


class Adb(object):
    """Adb命令的帮助类
    """
    __serialNum = None

    def __init__(self, serial_num):
        self.__serialNum = serial_num
        self.__cmd = 'adb -s %s ' % self.__serialNum

    def exec_cmd(self, cmd, timeout=60, output_file=None):
        """同步执行adb命令
        """
        cmd_str = self.__cmd + cmd
        ret_code, output = leona.util.Cmd.run(cmd_str, timeout=timeout, output_file=output_file)
        return ret_code, output

    def exec_cmd_async(self, cmd, timeout=-1, output_callback=None, shell=False):
        """异步执行adb命令
        """
        cmd_str = self.__cmd + cmd
        handle, output = leona.util.Cmd.async(cmd_str, timeout=timeout,
                output_callback=output_callback, shell=shell)
        return handle, output

    def uninstall_with_output(self, package, output_file=None):
        """卸载应用
        """
        return self.exec_cmd('uninstall %s' % package, timeout=60, output_file=output_file)

    def uninstall(self, package, output_file=None):
        """卸载应用
        """
        return self.exec_cmd('uninstall %s' % package, timeout=60, output_file=output_file)

    def push(self, local_path, dev_path):
        """推送本地文件到设备
        """
        self.exec_cmd('push "%s" %s' % (local_path, dev_path))

    def pull(self, dev_path, local_path):
        """从设备拉取文件到本地
        """
        self.exec_cmd('pull %s "%s"' % (dev_path, local_path))

    def click(self, x, y):
        """点击操作
        """
        self.exec_cmd('shell input tap %s %s' % (x, y))

    def swipe(self, start_x, start_y, end_x, end_y, duration=500):
        """点击操作
        """
        self.exec_cmd('shell input %s %s %s %s %s' % (start_x, start_y, end_x, end_y, duration))

    def screen_shot(self, local_path):
        """截屏并保存到本地文件
        """
        remote_screenshot_file = '/data/local/tmp/mtc_screenshot_for_cv.png'
        ret, output = self.exec_cmd('shell screencap -p %s' % remote_screenshot_file)
        if ret == 0:
            self.pull(remote_screenshot_file, local_path)

    def start_app(self, app_name, main_activity):
        """启动应用
        """
        self.exec_cmd('shell am start -n %s/%s' % (app_name, main_activity))

    def broadcast(self, action):
        self.exec_cmd('shell am broadcast -a %s' % action)

    def stop_app(self, app_name):
        """停止应用
        """
        self.exec_cmd('shell am force-stop %s' % app_name)

    def logcat_clean(self):
        """logcat -c
        """
        self.exec_cmd('logcat -c')
