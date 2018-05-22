#!/usr/bin/env python

# Copyright (C) 2016 Mahesh Pittala <mahesh@multicorewareinc.com>,
# Aasai Priya <aasai@multicorewareinc.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version. See COPYING

import os
import sys
import utils
import shlex

try:
    from conf import encoder_binary_name
except ImportError, e:
    encoder_binary_name = 'x265'

def arrangecli_MC(seq, command, always, extras, ffmpegpath, build):
    if 'ffmpeg' in command:
        pipe = '-|'
        ffmpeg = 'ffmpeg'
        ffmpegformat = command.split('-i ')[1].split('-|')[0]
        options = command.split('-|')[1]
        final_command = [ffmpegpath]
        final_command.append('-i')
        final_command.append(seq)
        final_command.extend(shlex.split(ffmpegformat))
        final_command.append(pipe)
        final_command.append(build)
        final_command.extend(shlex.split(options))
        final_command.extend(extras)
        final_command.append('-o')
        return final_command
    fullCommand = str(command)
    numStrm = fullCommand.count('}')
    k=0
    commandslist = []
    final_command = always
    final_command += ' '
    final_command += fullCommand.split('{')[0]
    cmd_string = fullCommand.split('}')
    while k<numStrm:
        #cmd = cmd_string.split('[')[1].split(']')[0]
        cmd = cmd_string[k].split('{')[1];
        cmd_stream = cmd
        cmd = cmd.replace('[ ', '')
        cmd = cmd.replace(' ]', '')
        cmd = cmd.replace(' ;', '')
        final_command += cmd
        k=k+1     
        bitrates, vbvmaxrates, vbvbufsizes, crf, crfmax, crfmin = [], [], [], [], [], []
        tchash = []
        if '--vbv-bufsize ' in cmd_stream:
            list = cmd_stream.split('--vbv-bufsize ')[1].split(' ')[0]
            for l in list.split (','):
                vbvbufsizes.append(l)
            cmd = cmd.replace('--vbv-bufsize ', '')
            cmd = cmd.replace(list, '')
        if '--vbv-maxrate ' in cmd_stream:
            list = cmd_stream.split('--vbv-maxrate ')[1].split(' ')[0]
            for l in list.split (','):
                vbvmaxrates.append(l)
            cmd = cmd.replace('--vbv-maxrate ', '')
            cmd = cmd.replace(list, '')
        if '--crf-max' in cmd_stream:
            list =  cmd_stream.split('--crf-max ')[1].split(' ')[0]
            for l in list.split (','):
                crfmax.append(l)
            cmd = cmd.replace('--crf-max ', '')
            cmd = cmd.replace(list, '')
        if '--crf-min' in cmd_stream:
            list =  cmd_stream.split('--crf-min ')[1].split(' ')[0]
            for l in list.split (','):
                crfmin.append(l)
            cmd = cmd.replace('--crf-min ', '')
            cmd = cmd.replace(list, '')
        if '--bitrate' in cmd_stream:
            list = cmd_stream.split('--bitrate ')[1].split(' ')[0]
            for l in list.split (','):
                bitrates.append(l)
            cmd = cmd.replace('--bitrate ', '')
            cmd = cmd.replace(list, '')
            cnt = 0
            for i in range(len(bitrates)):
                command = cmd
                command += ' --bitrate '
                command += str(bitrates[i])
                if vbvbufsizes and vbvbufsizes[i]:
                    command +=  ' --vbv-bufsize '
                    command +=  str(vbvbufsizes[i])
                if vbvmaxrates and vbvmaxrates[i]:
                    command +=  ' --vbv-maxrate '
                    command +=  str(vbvmaxrates[i])
                command = command.replace('; ','')
                command = command.replace('[ ','')
                command = command.replace(' ]','')
                command += ' '
                commandslist.append(command)
                testhash = utils.testcasehash(seq, command)
                tchash.append(testhash)
                utils.testhashlist.append(testhash)
        if '--crf' in cmd_stream:
            list = cmd_stream.split('--crf ')[1].split(' ')[0]
            for l in list.split (','):
                crf.append(l)
            cmd = cmd.replace('--crf ', '')
            cmd = cmd.replace(list, '')            
            for i in range(len(crf)):
                command = cmd
                command = ' --crf '
                command += str(crf[i])
                if crfmax and crfmax[i]:
                    command +=  ' --crf-max '
                    command +=  str(crfmax[i])
                if crfmin and crfmin[i]:
                    command +=  ' --crf-min '
                    command +=  str(crfmin[i])
                if vbvbufsizes and vbvbufsizes[i]:
                    command +=  ' --vbv-bufsize '
                    command +=  str(vbvbufsizes[i])
                if vbvmaxrates and vbvmaxrates[i]:
                    command +=  ' --vbv-maxrate '
                    command +=  str(vbvmaxrates[i])
                command = command.replace(';','')
                command = command.replace('[ ','')
                command = command.replace(' ]','')
                command += ' '
                commandslist.append(command)
                testhash = utils.testcasehash(seq, command)
                tchash.append(testhash)
                utils.testhashlist.append(testhash)
        final_command += ' -o '
        if encoder_binary_name == 'x264' or '--codec "x264"' in final_command:
            final_command += '.h264,'.join(tchash)
            final_command += '.h264'	
        else:
            final_command += '.hevc,'.join(tchash)
            final_command += '.hevc'

        csv_filenames = ''
        for i in tchash:
            csv_filenames += i
            csv_filenames += '.csv,'
        csv_filenames = csv_filenames[:-1]
        final_command += ' --csv '
        final_command += csv_filenames  

        if '--codec "x264"' in final_command:
            yuv_filenames = ''
            for i in tchash:
                yuv_filenames += 'x264-output_'+ i +'.yuv,'
            yuv_filenames = yuv_filenames[:-1]
            final_command += ' --dump-yuv '
            final_command += yuv_filenames          

        if '--recon=recon.y4m' in extras:
            recon_filenames = ''
            for i in tchash:
                recon_filenames += i
                recon_filenames += '.y4m,'
            recon_filenames = recon_filenames[:-1]
            final_command += ' --recon='
            final_command += recon_filenames
        elif '--recon=recon.yuv' in extras:
            recon_filenames = ''
            for i in tchash:
                recon_filenames += i
                recon_filenames += '.yuv,'
            recon_filenames = recon_filenames[:-1]
            final_command += ' --recon='
            final_command += recon_filenames
    final_command += ' '
    final_command += ' '.join(extras)
    return final_command

def arrangecli(seq, command, always, extras, ffmpegpath, build):
    if 'ffmpeg' in command:
        pipe = '-|'
        ffmpeg = 'ffmpeg'
        ffmpegformat = command.split('-i ')[1].split('-|')[0]
        options = command.split('-|')[1]
        final_command = [ffmpegpath]
        final_command.append('-i')
        final_command.append(seq)
        final_command.extend(shlex.split(ffmpegformat))
        final_command.append(pipe)
        final_command.append(build)
        final_command.extend(shlex.split(options))
        final_command.extend(extras)
        final_command.append('-o')
        return final_command

    cmd_string = str(command)
    f = cmd_string.split('[')[0]
    cmd = cmd_string.split('[')[1].split(']')[0]
    commandslist = []
    bitrates, vbvmaxrates, vbvbufsizes, crf, crfmax, crfmin = [], [], [], [], [], []
    if '--bitrate ' in cmd:
        list = cmd.split('--bitrate ')[1].split(' ')[0]
        for l in list.split (','):
            bitrates.append(l)
        cmd_string = cmd_string.replace('--bitrate', '')
        cmd_string = cmd_string.replace(list, '')
    if '--vbv-bufsize ' in cmd:
        list = cmd.split('--vbv-bufsize ')[1].split(' ')[0]
        for l in list.split (','):
            vbvbufsizes.append(l)
        cmd_string = cmd_string.replace('--vbv-bufsize', '')
        cmd_string = cmd_string.replace(list, '')
    if '--vbv-maxrate ' in cmd:
        list = cmd.split('--vbv-maxrate ')[1].split(' ')[0]
        for l in list.split (','):
            vbvmaxrates.append(l)
        cmd_string = cmd_string.replace('--vbv-maxrate', '')
        cmd_string = cmd_string.replace(list, '')
    if '--crf' in cmd:
        list = cmd.split('--crf ')[1].split(' ')[0]
        for l in list.split (','):
            crf.append(l)
        cmd_string = cmd_string.replace('--crf', '')
        cmd_string = cmd_string.replace(list, '')
    if '--crf-max' in cmd:
        list =  cmd.split('--crf-max ')[1].split(' ')[0]
        for l in list.split (','):
            crfmax.append(l)
        cmd_string = cmd_string.replace('--crf-max', '')
        cmd_string = cmd_string.replace(list, '')
    if '--crf-min' in cmd:
        list =  cmd.split('--crf-min ')[1].split(' ')[0]
        for l in list.split (','):
            crfmin.append(l)
        cmd_string = cmd_string.replace('--crf-min', '')
        cmd_string = cmd_string.replace(list, '')
    if '--bitrate' in cmd:
        for i in range(len(bitrates)):
            command = '--bitrate '
            command += str(bitrates[i])
            if vbvbufsizes and vbvbufsizes[i]:
                command +=  ' --vbv-bufsize '
                command +=  str(vbvbufsizes[i])
            if vbvmaxrates and vbvmaxrates[i]:
                command +=  ' --vbv-maxrate '
                command +=  str(vbvmaxrates[i])
            command += ' '
            command += cmd_string.strip(';').strip('[').strip(']')
            command += ' '
            command += always
            commandslist.append(command)
            testhash = utils.testcasehash(seq, command)
            utils.testhashlist.append(testhash)
    if '--crf' in cmd:
        for i in range(len(crf)):
            command = '--crf '
            command += str(crf[i])
            if crfmax and crfmax[i]:
                command +=  ' --crf-max '
                command +=  str(crfmax[i])
            if crfmin and crfmin[i]:
                command +=  ' --crf-min '
                command +=  str(crfmin[i])
            if vbvbufsizes and vbvbufsizes[i]:
                command +=  ' --vbv-bufsize '
                command +=  str(vbvbufsizes[i])
            if vbvmaxrates and vbvmaxrates[i]:
                command +=  ' --vbv-maxrate '
                command +=  str(vbvmaxrates[i])
            command += ' '
            command += cmd_string.strip(';').strip('[').strip(']')
            command += ' '
            command += always
            commandslist.append(command)
            testhash = utils.testcasehash(seq, command)
            utils.testhashlist.append(testhash)
    final_command = f
    final_command += ' '
    final_command += cmd.replace(';', '').strip('[').strip(']')
    final_command += ' '
    final_command += always
    final_command += ' -o '
    if encoder_binary_name == 'x264' or '--codec "x264"' in command:
        final_command += '.h264,'.join(utils.testhashlist)
        final_command += '.h264'	
    else:
        final_command += '.hevc,'.join(utils.testhashlist)
        final_command += '.hevc'
    if '--csv=test.csv' in extras or '--recon=recon.y4m' in extras or '--recon=recon.yuv' in extras:
        return final_command
    else:
        final_command += ' '
        final_command += ' '.join(extras)

    if '--csv=test.csv' in extras:
        csv_filenames = ''
        for i in utils.testhashlist:
            csv_filenames += i
            csv_filenames += '.csv,'
        csv_filenames = csv_filenames[:-1]
        final_command += ' --csv '
        final_command += csv_filenames
    elif '--recon=recon.y4m' in extras:
        recon_filenames = ''
        for i in utils.testhashlist:
            recon_filenames += i
            recon_filenames += '.y4m,'
        recon_filenames = recon_filenames[:-1]
        final_command += ' --recon='
        final_command += recon_filenames
    elif '--recon=recon.yuv' in extras:
        recon_filenames = ''
        for i in utils.testhashlist:
            recon_filenames += i
            recon_filenames += '.yuv,'
        recon_filenames = recon_filenames[:-1]
        final_command += ' --recon='
        final_command += recon_filenames
    return final_command
