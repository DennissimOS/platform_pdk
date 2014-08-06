# Copyright 2014 The Android Open Source Project
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import its.image
import its.device
import its.objects
import its.target
import os.path
import numpy
import pylab
import matplotlib
import matplotlib.pyplot

def main():
    """Take long bursts of images and check that they're all identical.

    Assumes a static scene. Can be used to idenfity if there are sporadic
    frames that are processed differently or have artifacts. Uses manual
    capture settings.
    """
    NAME = os.path.basename(__file__).split(".")[0]

    BURST_LEN = 50
    BURSTS = 10
    FRAMES = BURST_LEN * BURSTS

    DELTA_THRESH = 0.1

    with its.device.ItsSession() as cam:

        # Capture at the smallest resolution.
        props = cam.get_camera_properties()
        _, fmt = its.objects.get_fastest_manual_capture_settings(props)
        e, s = its.target.get_target_exposure_combos(cam)["minSensitivity"]
        req = its.objects.manual_capture_request(s, e)
        w,h = fmt["width"], fmt["height"]

        # Converge 3A prior to capture.
        cam.do_3a()

        # Capture bursts of YUV shots.
        # Build a 4D array, which is an array of all RGB images.
        imgs = numpy.empty([FRAMES,h,w,3])
        for j in range(BURSTS):
            caps = cam.do_capture([req]*BURST_LEN, [fmt])
            for i,cap in enumerate(caps):
                n = j*BURST_LEN + i
                imgs[n] = its.image.convert_capture_to_rgb_image(cap)

        # Dump all images.
        print "Dumping images"
        for i in range(FRAMES):
            its.image.write_image(imgs[i], "%s_frame%03d.jpg"%(NAME,i))

        # The mean image.
        img_mean = imgs.mean(0)
        its.image.write_image(img_mean, "%s_mean.jpg"%(NAME))

        # Compute the deltas of each image from the mean image; this test
        # passes if none of the deltas are large.
        print "Computing frame differences"
        delta_maxes = []
        for i in range(FRAMES):
            deltas = (imgs[i] - img_mean).reshape(h*w*3)
            delta_max_pos = numpy.max(deltas)
            delta_max_neg = numpy.min(deltas)
            delta_maxes.append(max(abs(delta_max_pos), abs(delta_max_neg)))
        max_delta_max = max(delta_maxes)
        print "Frame %d has largest diff %f" % (
                delta_maxes.index(max_delta_max), max_delta_max)
        assert(max_delta_max < DELTA_THRESH)

if __name__ == '__main__':
    main()
