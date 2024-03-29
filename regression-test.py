#!/usr/bin/env python

# Copyright (C) 2015 Steve Borho <steve@borho.org>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version. See COPYING

import os
import sys
import shutil
from subprocess import Popen, PIPE
import utils

# setup will call sys.exit() if it determines the tests are unable to continue
if "--save-load-test" in sys.argv:
    utils.setup(sys.argv, 'save-load-tests.txt', '', False)
else:
    utils.setup(sys.argv, 'regression-tests.txt', '', False)

from conf import my_builds, my_machine_name, my_sequences, my_x265_source
from utils import logger, find_executable

try:
    from conf import my_upload
except ImportError, e:
    print 'failed to import my_upload'
    my_upload = False

try:
    from conf import csv_feature
except ImportError, e:
    print 'failed to import csv_feature'
    csv_feature = False

try:
    from conf import my_patchlocation, my_ftp_location
except ImportError, e:
    print 'failed to import  my_patchlocation, my_ftp_location'
my_patchrevision = ''

try:
    from conf import encoder_binary_name
except ImportError, e:
    print 'failed to import encoder_binary_name'	
    encoder_binary_name = 'x265'
	
# do not use debug builds for long-running tests
debugs = [key for key in my_builds if 'debug' in my_builds[key][3]]
for k in debugs:
    del my_builds[k]

utils.buildall()
if logger.errors:
    # send results to mail
    logger.email_results()
    sys.exit(1)

always = '--no-info --hash=1'
hasffplay = find_executable('ffplay')

try:

    cumulative_count = 0
    for key in my_builds:
        tests = utils.parsetestfile(key, False)
        cumulative_count += logger.testcountlline(len(tests))	
		
    logger.settestcount(cumulative_count)

    for build in my_builds:
        logger.setbuild(build)
        tests = utils.parsetestfile(key, False)
        for seq, command in tests:
            if '--codec "x264"' in command:
                alwaysforx264 = ''
                extras = ['--psnr', '--ssim']
                utils.runtest(build, seq, command, alwaysforx264, extras)
                continue
            if 'ffplay' in command and not hasffplay:
                continue
            if encoder_binary_name == 'x265':
                extras = ['--psnr', '--ssim', utils.getspotcheck(command)]
            else:
                extras = ['--psnr', '--ssim']
            utils.runtest(build, seq, command, always, extras)

    if logger.errors:
        # send results to mail
        logger.email_results()
        sys.exit(1)
    else:
        # send results to mail
        logger.email_results()
    # rebuild without debug options and upload binaries on egnyte
    logs = open(os.path.join(utils.encoder_binary_name, logger.logfname),'r')
    fatalerror = False
    for line in logs:
         if 'encoder error reported' in line or 'DECODE ERRORS' in line  or 'Validation failed' in line or 'encoder warning reported' in line:
             fatalerror = True

    if fatalerror == False and my_upload:
        for key, v in my_upload.iteritems():
            buildoption = []
            buildoption.append(v[0])
            buildoption.append(v[1])
            buildoption.append(v[2])
            buildoption.append(v[3].replace('debug', '').replace('checked', '').replace('tests', '').replace('warn', '').replace('reldeb', '').replace('noasm','').replace('static',''))
            buildoption.append(v[4])
            my_upload[key] = tuple(buildoption)
        utils.buildall(None, my_upload)
        if logger.errors:
            sys.exit(1)
        utils.upload_binaries()
        if logger.errors:
            sys.exit(1)
            
        # here it applies specific patch and shares libraries
        if csv_feature == True:
            cmd = ''.join(["hg import ", my_patchlocation])
            p = Popen(cmd, cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
            my_patchrevision = utils.hgversion(my_x265_source)
            if p.returncode:
                logger.write('\nfailed to apply patch\n')
                p = Popen("hg revert --all", cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
                p = Popen("hg clean", cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
                cmd = ''.join(["hg strip ", my_patchrevision])
                p = Popen(cmd, cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
            else:
                utils.buildall(None, my_upload)
                extras = ['--psnr', '--ssim', '--csv-log-level=3', '--csv=test.csv', '--frames=10']
                cmd = ''.join(["hg strip ", my_patchrevision])
                p = Popen(cmd, cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
                for build in my_upload:
                    logger.setbuild(build)
                    for seq, command in tests:
                        utils.runtest(build, seq, command, always, extras)
            utils.upload_binaries(my_ftp_location)
except KeyboardInterrupt:
    print 'Caught CTRL+C, exiting'
finally:
    print 'clean the repo'
    if csv_feature == True:
        p = Popen("hg revert --all", cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
        p = Popen("hg clean", cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
        cmd = ''.join(["hg strip ", my_patchrevision])
        p = Popen(cmd, cwd=my_x265_source, stdout=PIPE, stderr=PIPE)
