#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re

import cv2
import numpy as np


class MtcCv(object):
    """参考aircv的opencv辅助类
    """

    @staticmethod
    def read_image(filename):
        '''wrap of cv2.imread
        '''
        im = cv2.imread(filename)
        if im is None:
            raise RuntimeError("file: '%s' not exists" % filename)
        return im

    @staticmethod
    def resize_image(im_source, new_width, new_height):
        return cv2.resize(im_source, (int(new_width), int(new_height)))

    @staticmethod
    def find_template(im_source, im_search, threshold=0.5):
        '''return find location, if not found; return None
        '''
        result = MtcCv.find_all_template(im_source, im_search, threshold, 1)
        return result[0] if result else None

    @staticmethod
    def find_all_template(im_source, im_search, threshold=0.5, max_count=0):
        '''Locate image position with cv2.templateFind
        '''
        # method = cv2.TM_CCORR_NORMED
        # method = cv2.TM_SQDIFF_NORMED
        method = cv2.TM_CCOEFF_NORMED
        s_gray = cv2.cvtColor(im_search, cv2.COLOR_BGR2GRAY)
        i_gray = cv2.cvtColor(im_source, cv2.COLOR_BGR2GRAY)
        res = cv2.matchTemplate(i_gray, s_gray, method)
        w, h = im_search.shape[1], im_search.shape[0]

        result = []
        while True:
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                top_left = min_loc
            else:
                top_left = max_loc
            if max_val < threshold:
                break
            # calculator middle point
            middle_point = (top_left[0] + w / 2, top_left[1] + h / 2)
            result.append(dict(
                result=middle_point,
                rectangle=(top_left, (top_left[0], top_left[1] + h), (top_left[0] + w, top_left[1]),
                           (top_left[0] + w, top_left[1] + h)),
                confidence=max_val
            ))
            if max_count and len(result) >= max_count:
                break
            cv2.floodFill(res, None, max_loc, (-1000,), max_val - threshold + 0.1, 1, flags=cv2.FLOODFILL_FIXED_RANGE)
        return result

    @staticmethod
    def find_sift(im_source, im_search, threshold=0.4):
        '''SIFT特征点匹配
        '''
        res = MtcCv.find_all_sift(im_source, im_search, threshold, max_count=1)
        if not res:
            return None
        return res[0]

    FLANN_INDEX_KDTREE = 0

    @staticmethod
    def find_all_sift(im_source, im_search, threshold=0.4, max_count=0):
        '''使用sift算法进行多个相同元素的查找
        '''
        sift = cv2.SIFT(edgeThreshold=100)
        flann = cv2.FlannBasedMatcher({'algorithm': MtcCv.FLANN_INDEX_KDTREE, 'trees': 5}, dict(checks=50))

        kp_sch, des_sch = sift.detectAndCompute(im_search, None)
        min_match_count = len(kp_sch) * threshold
        if len(kp_sch) < min_match_count:
            return None

        kp_src, des_src = sift.detectAndCompute(im_source, None)
        if len(kp_src) < min_match_count:
            return None

        result = []
        while True:
            matches = flann.knnMatch(des_sch, des_src, k=2)
            good = []
            for m, n in matches:
                if m.distance < 0.9 * n.distance:
                    good.append(m)

            if len(good) < min_match_count:
                break

            sch_pts = np.float32([kp_sch[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
            img_pts = np.float32([kp_src[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)

            if len(sch_pts) < 4 or len(img_pts) < 4:
                break

            M, mask = cv2.findHomography(sch_pts, img_pts, cv2.RANSAC, 5.0)
            matches_mask = mask.ravel().tolist()

            h, w = im_search.shape[:2]
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)
            dst = cv2.perspectiveTransform(pts, M)

            pypts = []
            for npt in dst.astype(int).tolist():
                pypts.append(tuple(npt[0]))

            lt, br = pypts[0], pypts[2]
            middle_point = (lt[0] + br[0]) / 2, (lt[1] + br[1]) / 2

            result.append(dict(
                result=middle_point,
                rectangle=pypts,
                confidence=(matches_mask.count(1), len(good))  # min(1.0 * matches_mask.count(1) / 10, 1.0)
            ))

            if max_count and len(result) >= max_count:
                break

            qindexes, tindexes = [], []
            for m in good:
                qindexes.append(m.queryIdx)  # need to remove from kp_sch
                tindexes.append(m.trainIdx)  # need to remove from kp_img

            def filter_index(indexes, arr):
                r = np.ndarray(0, np.float32)
                for i, item in enumerate(arr):
                    if i not in qindexes:
                        r = np.append(r, item)
                return r

            kp_src = filter_index(tindexes, kp_src)
            des_src = filter_index(tindexes, des_src)

        return result

    @staticmethod
    def find_all(im_source, im_search, max_count=0):
        result = MtcCv.find_all_template(im_source, im_search, max_count=max_count)
        if not result:
            result = MtcCv.find_all_sift(im_source, im_search, max_count=max_count)
        if not result:
            return []
        return [match["result"] for match in result]

    @staticmethod
    def find(im_source, im_search):
        '''Only find maximum one object
        '''
        r = MtcCv.find_all(im_source, im_search, max_count=1)
        return r[0] if r else None
