#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import shutil
import time
import uuid

from .service import Adb
from .service import MtcCv


class Leona(object):
    """
    test sdk main class, provide control api such as click according to image
    """
    ICON_DIR = "icons"
    SCREEN_DIR = "screens"

    def __init__(self, serial_num, base_path):
        self.serial_num = serial_num
        self.base_path = base_path
        self.control = self.adb = Adb(serial_num)
        self.icon_path = os.path.join(self.base_path, Leona.ICON_DIR)
        self.scene_path = None
        self.prepare_work_dir()
        self.screen_image_patten = 'screen_shot_%s.png'

    def prepare_work_dir(self):
        self.scene_path = self.create_dir(Leona.SCREEN_DIR)

    def create_dir(self, dir_name):
        result_dir = os.path.join(self.base_path, dir_name)
        if os.path.exists(result_dir):
            shutil.rmtree(result_dir, ignore_errors=True)
            time.sleep(3)  # 重要
            shutil.rmtree(result_dir, ignore_errors=True)
            time.sleep(3)  # 重要
            os.makedirs(result_dir, mode=0750)
        else:
            os.makedirs(result_dir, mode=0750)
        return result_dir

    def press_back(self):
        self.send_key_event(4)

    def press_home(self):
        self.send_key_event(3)

    def input_text(self, text):
        self.adb.exec_cmd('shell input text "%s"', text)

    def send_key_event(self, event_code):
        """
        send key evnet to device, such as back, home
        """
        self.adb.exec_cmd("shell input keyevent %s", event_code)

    def click_by_img(self, object_path):
        object_path = os.path.join(self.icon_path, object_path)
        if not os.path.exists(object_path):
            return
        retry_count = 3
        while retry_count > 0:
            start = time.time()
            screen_shot_path = os.path.join(self.scene_path, self.screen_image_patten % uuid.uuid1())
            self.adb.screen_shot(screen_shot_path)
            im_search = MtcCv.read_image(object_path)
            im_source = MtcCv.read_image(screen_shot_path)
            height, width, channels = im_source.shape
            new_width = 648
            new_height = (height * 1.0 / width) * new_width
            radio = (width * 1.0 / new_width)
            im_source = MtcCv.resize_image(im_source, new_width, new_height)
            print "search begins:", object_path, time.time() - start
            result_point = MtcCv.find_sift(im_source=im_source, im_search=im_search)
            if result_point is None:
                result_point = MtcCv.find_template(im_source, im_search)
            print "search ends:", time.time() - start
            if result_point is not None:
                print int(result_point['result'][0] * radio), int(result_point['result'][1] * radio)
                self.adb.click(int(result_point['result'][0] * radio), int(result_point['result'][1] * radio))
                print "click end", time.time() - start
                break
            else:
                retry_count -= 1
                time.sleep(2)
                print "can not find:", time.time() - start

    def start_app(self, package_name, start_activity):
        self.adb.start_app(package_name, start_activity)

    def input_text(self, text):
        self.adb.input_text()
