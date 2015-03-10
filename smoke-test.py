#!/usr/bin/env python

import sys
import shutil

import utils

# setup will call sys.exit() if it determines the tests are unable to continue
utils.setup(sys.argv)

if utils.run_make:
    errors = utils.buildall()
    if errors:
        print errors
        sys.exit(1)

if utils.run_bench:
    errors = utils.testharness()
    if errors:
        print errors
        sys.exit(1)

from conf import my_builds
encoders = my_builds.keys()

sequences = [
    'RaceHorses_416x240_30_10bit.yuv',
    'big_buck_bunny_360p24.y4m',
    'washdc_422_ntsc.y4m',
    'old_town_cross_444_720p50.y4m',
    'crowd_run_1080p50.y4m'
]

configs = [
    ['--preset=superfast', '-f50', '--hash=1'],
    ['--preset=medium', '-f50', '--hash=1'],
]

extras = ['--psnr', '--ssim']

rev = utils.hgversion()
lastgood = utils.findlastgood(rev)
print 'testing revision %s, validating against %s\n' % (rev, lastgood)

log = ''
for key in encoders:
    desc = utils.describeEnvironment(key)
    for seq in sequences:
        for cfg in configs:
            log += utils.runtest(key, lastgood, rev, seq, cfg, extras, desc)
            print

if log:
    # TODO: file log or email
    print log
