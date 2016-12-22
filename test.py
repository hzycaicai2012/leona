#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Author:  hzsunshx
# Created: 2015-03-23 14:42

"""
sift
"""

import sys
import os
import leona
import time

if __name__ == '__main__':
    print sys.argv
    base_path = os.path.abspath(os.path.dirname(sys.argv[0]))
    d = leona.Leona(sys.argv[1], base_path)
    d.start_app("com.psbc.house", "com.psbc.house.activity.LoadingActivity")
    time.sleep(5)
    d.click_by_img("change_city.jpg")
    time.sleep(2)
    d.click_by_img("jiangsu_city.jpg")
    time.sleep(2)
    d.click_by_img("mall.jpg")
    time.sleep(2)
    d.click_by_img("phone_fee.jpg")
    time.sleep(2)
    d.click_by_img("mobile_10_fee.jpg")
    time.sleep(2)
    d.click_by_img("back_btn.jpg")
    time.sleep(2)
    d.click_by_img("game_money.jpg")
    time.sleep(2)
    d.click_by_img("game_money_exchange.jpg")
    time.sleep(2)
    d.click_by_img("back_btn.jpg")
    time.sleep(2)