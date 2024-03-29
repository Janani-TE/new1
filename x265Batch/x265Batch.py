# Copyright (C) 2015 Mahesh Pittala <mahesh@multicorewareinc.com>
#
# This software may be used and distributed according to the terms of the
# GNU General Public License version 2 or any later version. See COPYING

import os
import subprocess as sub
import time, datetime
import shutil
import glob
import sys
import platform
import re
header = {}
CWD = os.getcwd()
path = {}
osname = platform.system()
try:
    from paths_cfg import my_sequences, my_bitstreams, my_system, my_hardware
    from paths_cfg import my_RAMDISK, my_compareFPS, my_csvupload
	
    # support ~/repos/x265 syntax
    my_sequences = os.path.expanduser(my_sequences)
    my_bitstreams = os.path.expanduser(my_bitstreams)
except ImportError, e:
    print 'Copy paths_cfg.py.example to paths_cfg.py and edit the file as necessary'
    sys.exit(1)

try:
    from paths_cfg import feature
except ImportError, e:
    feature = 'empty'

try:
    from paths_cfg import encoder_binary_name
except ImportError, e:
    encoder_binary_name = 'x265'
	
try:
    from paths_cfg import lib_path
except ImportError, e:
    lib_path = ''

try:
    from paths_cfg import ffmpeg_feature
except ImportError, e:
    ffmpeg_feature = False	

try:
    from paths_cfg import my_RAMDiskpath
    my_RAMDiskpath = os.path.expanduser(my_RAMDiskpath)
except ImportError, e:
    print 'failed to import variables, if u want to run with ram disk then you must set path, defaulting to None', e
    my_RAMDiskpath = None

try:
    from paths_cfg import my_email_from, my_email_to, my_smtp_pwd, my_smtp_host, my_smtp_port
except ImportError, e:
    print '** `my_email_*` not defined, defaulting to None'
    my_email_from, my_email_to, my_smtp_pwd = None, None, None

try:
    from paths_cfg import Decodebitstream
except ImportError, e:
    print '** `Decodebitstream*` not defined, defaulting to None'
    Decodebitstream = None

try:
    from paths_cfg import my_comparequalitymetrics
except ImportError, e:
    print '** `my_comparequalitymetrics*` not defined, defaulting to None'
    my_comparequalitymetrics = None

try:
    from paths_cfg import my_ftp_url, my_ftp_user, my_ftp_pass, my_ftp_path_stable, my_ftp_path_default, my_ftp_path_stableold, my_ftp_path_defaultold
except ImportError, e:
    print '** `my_email_*` not defined, defaulting to None'
    my_ftp_url, my_ftp_user, my_ftp_pass, my_ftp_path_stable, my_ftp_path_default, my_ftp_path_stableold, my_ftp_path_defaultold = None, None, None, None, None, None, None

featureFlag, featurecount =  False, 0
featurebitrate, featuremaxrates, featurebufsizes, featurecrf = [], [], [], []

class Test:
    def __init__(self):
        self.my_sequences = my_sequences
        self.my_bitstreams = my_bitstreams
        self.my_RAMDISK = my_RAMDISK
        self.my_RAMDiskpath = my_RAMDiskpath

        self.inputsequences_path = ''
        self.outputfile_path = ''
        self.first = True
        self.seq = ''

        self.cwd = ''
        self.finalcsv = 'x265Benchmark_aux.csv'
        self.fullcommandlines = 'fullcommandlines_autogen.txt'
        self.goldendir = ''
        self.resultdir = ''

        self.sequences = set()
        self.commands = open(self.fullcommandlines, 'w')
        self.nowdate = datetime.datetime.now().strftime('log-%y%m%d%H%M%S')
        self.start_time = datetime.datetime.now()
        self.logfname = '%s.txt' % (self.nowdate)
        self.logfp = open(os.path.join(self.resultdir, self.logfname), 'wb')

        self.branch = ''
        self.tag = ''
        self.cfg = ''
        self.cli = ''
        self.iter = 1
        self.out = False

        self.video = ''
        self.preset = ''
        self.abr = ''
        self.cqp = ''
        self.crf = ''
        self.vbvbufsize = ''
        self.vbvmaxrate = ''
        self.fps = ''
        self.avg = []
        self.rev = ''
        self.feature = ''
        self.tableheader = r'<tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th><th>{4}</th><th>{5}</th><th>{6}</th><th>{7}</th><th>{8}</th><th>{9}</th><th>{10}</th><th>{11}</th><th>{12}</th><th>{13}</th><th>{14}</th></tr>'\
                                   .format('Video',
                                   'Feature',
                                   'Preset',
                                   'ABR',
                                   'CQP',
                                   'CRF',
                                   'vbv-bufsize',
                                   'vbv-maxrate',
                                   'golden tip',
                                   'current tip',
                                   'Golden SSIM(dB)',
                                   'Current SSIM(dB)',
                                   'harmonicmean of golden FPS',
                                   'harmonicmean of current FPS', 
                                   '% of increase with current FPS')

        self.tableheaderforQuality = r'<tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th><th>{4}</th><th>{5}</th><th>{6}</th><th>{7}</th><th>{8}</th><th>{9}</th><th>{10}</th><th>{11}</th></tr>'\
                                   .format('Video',
                                   'Feature',
                                   'Preset',
                                   'ABR',
                                   'golden tip',
                                   'current tip',
                                   'previous bitrate',
                                   'previous SSIM(db)',
                                   'current bitrate',
                                   'current SSIM(db)',
                                   '(BD-SSIM)average difference in ssim',
                                   '(BD-Rate)percentage of bit rate saved')

        self.table = ['<htm><body><table border="1">']

    def ramdisk(self):
        if self.my_RAMDISK == True:
            self.inputsequences_path = self.my_RAMDiskpath
            self.outputfile_path = self.my_RAMDiskpath
            if osname == 'Linux':
                os.system("sudo rm -rf " + self.my_RAMDiskpath)
        else:
            self.inputsequences_path = self.my_sequences
            self.outputfile_path = self.my_bitstreams

    def parse(self, arg, index):
        try:
            if arg == '--tag':
                self.tag = sys.argv[index+1]
                self.finalcsv = self.tag + '_aux.csv'
            elif arg == '--cfg':
                self.cfg = sys.argv[index+1]
            elif arg == '--iter':
                self.iter = int(sys.argv[index+1])
            elif arg == '--branch':
                self.branch = sys.argv[index+1]
            elif arg == '--mailid':
                my_email_to = sys.argv[index+1]
            elif arg == '--discardout':
                self.out = True
            elif arg == '--':
                self.cli = sys.argv[index+1:]
                if not os.name == 'nt':
                    os.system('chmod 555 '+ sys.argv[index+1])
                self.cli = ' '.join(self.cli)
            elif arg == '-h' or arg == '--help':
                print sys.argv[0], '[OPTIONS]\n'
                print '\t-h/--help              show this help'
                print '\t   --cfg <string>      locate the file which is having commandlines'
                print '\t   --tag <string>      specific name for your test, default NULL (optional)'
                print '\t   --iter <N>          N times to run the command line, default 1 (optional)'
                print '\t   --branch <string>   binary built from stable\default branch, default NULL (optional)'
                print '\t   --mailid <string>   receiver mail id to get the results, default NULL (optional)'
                print '\t   --discardout        to not to generate outputs, default set to my_bitstreams in conf.py'
                print '\t   -- <string>         binary and additional encoder options'
                print '\t\n\n for full information please read the readme.md file'
                sys.exit(0)
        except IndexError as e:
            print('Run -h\--help for a list of options')
            sys.exit(1)

    def setup_workingdir(self):
        if my_compareFPS == True or my_comparequalitymetrics == True:
            self.goldendir = 'goldencsv' + self.branch
            if not os.path.exists(os.path.join(self.cwd, self.goldendir)):
                os.mkdir(os.path.join(self.cwd, self.goldendir))

        if not os.path.exists(os.path.join(self.cwd, self.my_bitstreams)):
            os.mkdir(os.path.join(self.cwd, self.my_bitstreams))

        if not os.path.exists(os.path.join(self.cwd, "Results" + self.branch)):
            os.mkdir(os.path.join(self.cwd, "Results" + self.branch))

        self.resultdir = os.path.join(self.cwd, "Results" + self.branch, datetime.datetime.now().strftime('%y-%m-%d-%H%M%S'))
        if not os.path.exists(self.resultdir):
            os.mkdir(self.resultdir)

    def prepare_commands(self):
        global csv_filename
        with open(self.cfg) as f:
            csv_filename = (self.tag if self.tag != '' else 'x265Benchmark') + '.csv'
            for cmd in f:
                for i in range(self.iter):
                    if (ffmpeg_feature == True):
                        output_files = ''
                        ffmpegcommand = (self.cli).split('--psnr ')[0]
                        if feature in cmd:
                            cmd_string = cmd                        
                            if '}' in cmd:
                                numStrm = cmd_string.count('}')
                                k = 0;
                                final_command = cmd_string.split('{')[0]
                                while (k < numStrm):
                                    crflist, bitratelist = [], []                               
                                    linesplit = cmd_string.split('}')[0].split('{')[1]
                                    k = k+1;
                                    if (k < numStrm):
                                        cmd_string = cmd_string.split('}')[1]
                                    if 'crf=' in linesplit:
                                        list = linesplit.split('(crf=')[1].split(')')[0]
                                        for l in list.split (','):
                                            crflist.append(l)
                                        linesplit = linesplit.replace('(', '')
                                        linesplit = linesplit.replace(')', '')
                                        csv_file=':csv='
                                        for i in range(len(crflist)):
                                            csv_file += os.path.join(self.resultdir,(self.tag if self.tag != '' else 'x265Benchmark')+'.csv,')
                                        csv_file = csv_file[:-1]
                                        csv_file += ':csv-log-level=0:'
                                        linesplit += csv_file
                                    elif 'bitrate=' in linesplit:
                                        list = linesplit.split('(bitrate=')[1].split(')')[0]
                                        for l in list.split (','):
                                            bitratelist.append(l)
                                        linesplit = linesplit.replace('(', '')
                                        linesplit = linesplit.replace(')', '')
                                        csv_file=':csv='
                                        for i in range(len(bitratelist)):
                                            csv_file += os.path.join(self.resultdir,(self.tag if self.tag != '' else 'x265Benchmark')+'.csv,')
                                        csv_file = csv_file[:-1]
                                        csv_file += ':csv-log-level=0:'
                                        linesplit += csv_file
                                    final_command += linesplit
                                final_command = final_command[:-1]
                                final_command += '" -uhdkit-bitstreams '
                                final_command += cmd.split('-uhdkit-bitstreams')[1]
                                final_command = final_command.replace('{', '')
                                final_command = final_command.replace('}', '')
                                final_command = final_command.replace('(', '')
                                final_command = final_command.replace(')', '')
                            else:
                                bitratelist, crflist = [], []
                                cmd_string = cmd
                                if 'bitrate=' in cmd:
                                    list = cmd.split('[bitrate=')[1].split(']')[0]
                                    for l in list.split(','):
                                        bitratelist.append(l)
                                    csv_file=':csv='
                                    for i in range(len(bitratelist)):
                                        csv_file += os.path.join(self.resultdir,(self.tag if self.tag != '' else 'x265Benchmark')+'.csv,')
                                    csv_file = csv_file[:-1]
                                    final_command = cmd_string.split('[')[0]
                                    final_command += cmd_string.split(']')[0].split('[')[1]
                                    final_command += csv_file
                                    final_command += ':csv-log-level=0'
                                    final_command += cmd_string.split(']')[1]
                                elif 'crf=' in cmd:
                                    list = cmd.split('[crf=')[1].split(']')[0]
                                    for l in list.split(','):
                                        crflist.append(l)
                                    csv_file=':csv='
                                    for i in range(len(crflist)):
                                        csv_file += os.path.join(self.resultdir,(self.tag if self.tag != '' else 'x265Benchmark')+'.csv,')
                                    csv_file = csv_file[:-1]
                                    final_command = cmd_string.split('[')[0]
                                    final_command += cmd_string.split(']')[0].split('[')[1]
                                    final_command += csv_file
                                    final_command += ':csv-log-level=0'
                                    final_command += cmd_string.split(']')[1]
                                final_command = final_command.replace('[', '')
                                final_command = final_command.replace(']', '')
                            
                            self.commands.write(' '.join([ffmpegcommand ,\
                                                        '-i', os.path.join(self.inputsequences_path,  final_command.strip('"\r\n'))
                                                        ,output_files if not self.out == True else ' -f null /dev/null' if osname == 'Linux' else ' -f null /dev/null '
                                                        ,'\n']))
                        else:
                            output_files = ''
                            ffmpegcommand = (self.cli).split('--psnr ')[0]
                            if cmd[-1] == '"':
                                cmd = cmd[:-1]
                            elif cmd[-2] == '"':
                                cmd = cmd[:-2]
                            self.commands.write(''.join([ffmpegcommand ,\
                                                    '-i ', os.path.join(self.inputsequences_path,  cmd.strip('"\r\n')),
                                                    ':csv=',  os.path.join(self.resultdir, (self.tag if self.tag != '' else 'x265Benchmark') + '.csv"'),
                                                    output_files if not self.out == True else ' -f null /dev/null' if osname == 'Linux' else ' -f null /dev/null '
                                                    ,'\n']))
                    elif feature in cmd:
                        commandline = cmd.split('[')[0]
                        commandline += cmd.split('[')[1].split(']')[0]
                        bitrates = cmd.split('--bitrate ')[1].split(']')[0]
                        bitrate_list = []
                        bitrate_list = bitrates.split(',')
                        no_of_bitrates = len(bitrate_list)
                        csv_files = ''
                        output_files = ''
                        for i  in bitrate_list:
                            csv_files += os.path.join(self.resultdir,(self.tag if self.tag != '' else 'x265Benchmark')+'.csv,')
                            output_files += os.path.join(self.outputfile_path, self.tag + i + '.hevc,')
                        csv_files = csv_files[:-1]							
                        output_files =  output_files[:-1]
                        self.commands.write(' '.join([self.cli,\
                                                    '--input', os.path.join(self.inputsequences_path, commandline), 
                                                    '--csv',  csv_files,
                                                    '-o ',
                                                    output_files if not self.out == True else '//dev//null' if osname == 'Linux' else 'nul'
                                                    ,'\n']))					
                    else:
                        self.commands.write(' '.join([self.cli,\
                                                    '--input', os.path.join(self.inputsequences_path, cmd.strip('\r\n')), 
                                                    '--csv',  os.path.join(self.resultdir, csv_filename), 
                                                    '-o ',
                                                    os.path.join(self.outputfile_path, ''.join(cmd.strip('\r\n').split(' '))) + self.tag + '.hevc' if not self.out == True else '//dev//null' if osname == 'Linux' else 'nul'
                                                    , '\n']))
                self.sequences.add(cmd.split(' ')[0])

        for file in glob.glob("..//AWSsetup//*.txt"):
            if '_commands.txt' in file:
                with open(file) as f:
                    for cmd in f:
                        if cmd and not cmd.startswith('#') and not cmd.startswith('\n'):
                            for i in range(self.iter):
                                self.commands.write(' '.join([self.cli,\
                                                            '--input', os.path.join(self.inputsequences_path, cmd.strip('\r\n')), 
                                                            '--csv',  os.path.join(self.resultdir, csv_filename), 
                                                            '-o ',
                                                            os.path.join(self.outputfile_path, ''.join(cmd.strip('\r\n').split(' '))) + self.tag + '.hevc'  if not self.out == True else '//dev//null' if osname == 'Linux' else 'nul'
                                                            , '\n']))
                            self.sequences.add(cmd.split(' ')[0])
        self.commands.close()

    def setup(self, cmd):
        for i in range(len(self.sequences)):
            if list(self.sequences)[i] in cmd:
                if self.my_RAMDISK == True:
                    if not list(self.sequences)[i] == self.seq:
                        if self.first == True:
                            self.first = False
                        else:
                            try:
                                os.remove(os.path.join(self.inputsequences_path, self.seq))
                                shutil.move(os.path.join(self.outputfile_path, '.'), os.path.join(self.my_bitstreams, datetime.datetime.now().strftime('bitstreams-%y%m%d%H%M%S')))
                            except (shutil.Error, OSError), e:
                                pass
                        shutil.copy(os.path.join(self.my_sequences, list(self.sequences)[i]), os.path.join(self.inputsequences_path, list(self.sequences)[i]))
                        self.seq = list(self.sequences)[i]            

    def remove_movefiles(self):
        try:
            os.remove(os.path.join(self.inputsequences_path, self.seq))
            shutil.move(os.path.join(self.outputfile_path, '.'), os.path.join(self.my_bitstreams, datetime.datetime.now().strftime('bitstreams-%y%m%d%H%M%S')))
        except (shutil.Error, OSError), e:
            pass				

    def parsecsv(self, tok, index, cmdline):
        commandline = cmdline[10]
        if tok == '--input' or (ffmpeg_feature == True and tok == '-i'):
            self.video = os.path.basename(cmdline[index + 1])
        elif tok == '-p' or tok == '--preset'  or (ffmpeg_feature == True and tok == '-preset'):
            self.preset = cmdline[index + 1]
        if ffmpeg_feature == True:
            if feature in commandline:
                if 'bitrate' in commandline:
                    self.abr = commandline.split('bitrate=')[1].split(':')[0]
                if 'crf' in commandline:
                    self.crf = commandline.split('crf=')[1].split(':')[0]
                if 'vbv-bufsize' in commandline:
                    self.vbvbufsize = commandline.split('vbv-bufsize=')[1].split(':')[0]
                if 'vbv-maxrate' in commandline:
                    self.vbvmaxrate = commandline.split('vbv-maxrate=')[1].split(':')[0]
                if 'feature' in commandline:
                    self.feature = commandline.split('feature=')[1].split(':')[0]
            else:
                params = re.split(',|\:|\=', tok)
                if ('bitrate' in params or 'qp' in params or 'crf' in params or 'vbv-bufsize' in params or 'vbv-maxtrate' in params):
                    m = 0
                    for param in params:
                        if param == 'bitrate':
                            self.abr = params[m + 1]
                        if param == 'qp':
                            self.cqp = params[m + 1]
                        if param == 'crf':
                            self.crf = params[m + 1]
                        if param == 'vbv-bufsize':
                            self.vbvbufsize = params[m + 1]
                        if param == 'vbv-maxrate':
                            self.vbvmaxrate = params[m + 1]
                        if param == 'feature':
                            self.feature = params[m + 1]
                        m = m + 1
        else:
			if tok == '--bitrate':
				self.abr = cmdline[index + 1]
			elif tok == '-q' or tok == '--qp':
				self.cqp = cmdline[index + 1]
			elif tok == '--crf':
				self.crf = cmdline[index + 1]
			elif tok == '--vbv-bufsize':
				self.vbvbufsize = cmdline[index + 1]
			elif tok == '--vbv-maxrate':
				self.vbvmaxrate = cmdline[index + 1]
			elif tok == '--feature':
				self.feature = cmdline[index + 1]		
			
def Bjontegaardmetric(ssim1,bitrate1,ssim2,bitrate2):

        import math
        import numpy
        R1 = []
        R2 = []
        SSIM1 = []
        SSIM2 = []
        string1 = "" 
        string2 = ""
        plot1 = []
        plot2 = []

        bitrate1 = [float(field) for field in bitrate1]
        bitrate2 = [float(field) for field in bitrate2]
        ssim1 = [float(field) for field in ssim1]
        ssim2 = [float(field) for field in ssim2]
        

        R1=[math.log(num) for num in bitrate1]
        R2=[math.log(num) for num in bitrate2]
        
        #dssim mode
        p1 = numpy.polyfit(R1,ssim1,3)
        p2 = numpy.polyfit(R2,ssim2,3)

        min_int = max([min(R1),min(R2)])
        max_int = min([max(R1),max(R2)])

        p_int1 = numpy.polyint(p1)
        p_int2 = numpy.polyint(p2)

        int1 = numpy.polyval(p_int1, max_int) - numpy.polyval(p_int1, min_int)
        int2 = numpy.polyval(p_int2, max_int) - numpy.polyval(p_int2, min_int)

        #calculates the average difference in ssim
        avg_diff = (int2 - int1) / (max_int - min_int)
        print 'RESULT DSSIM:',avg_diff

        #rate mode
        p1 = numpy.polyfit(ssim1,R1,3);
        p2 = numpy.polyfit(ssim2,R2,3);

        min_int = max([ min(ssim1), min(ssim2) ]);
        max_int = min([ max(ssim1), max(ssim2) ]);

        p_int1 = numpy.polyint(p1);
        p_int2 = numpy.polyint(p2);

        int1 = numpy.polyval(p_int1, max_int) - numpy.polyval(p_int1, min_int);
        int2 = numpy.polyval(p_int2, max_int) - numpy.polyval(p_int2, min_int);

        #calculates the percentage of bit rate saved
        avg_exp_diff = (int2-int1)/(max_int-min_int);
        avg_diff1 = (math.exp(avg_exp_diff)-1)*100;
        print 'RESULT RATE:',avg_diff1
        
        return avg_diff, avg_diff1

def harmonic_mean(nums):
    geomean = reduce(lambda x, y: x*y, nums)**(1.0/len(nums))
    arithmean = float(sum(nums)/len(nums))
    return float((geomean**2)/arithmean)

def email_results(test, f1, f2):
    if not (my_email_from and my_email_to and my_smtp_pwd):
        return

    import smtplib
    from email.mime.text import MIMEText
    from email.MIMEMultipart import MIMEMultipart
    from email.encoders import encode_base64
    from email.mime.image import MIMEImage

    duration = str(datetime.datetime.now() - test.start_time).split('.')[0]

    msg = MIMEMultipart()
    body = MIMEText(my_system)
    msg.attach(body)
    body = MIMEText(my_hardware)
    msg.attach(body)	
    body = MIMEText("Test Duration(H:M:S) = {0}".format(duration) + ''.join(test.table), 'html')
    msg.attach(body)
    text0 = MIMEImage(open(f1, 'rb').read(), _subtype="csv")
    text0.add_header('Content-Disposition', 'attachment', filename=os.path.basename(f1))
    msg.attach(text0)
    text1 = MIMEImage(open(f2, 'rb').read(), _subtype="csv")
    text1.add_header('Content-Disposition', 'attachment', filename=os.path.basename(f2))
    msg.attach(text1)
    if type(my_email_to) is str:
        msg['To'] = my_email_to
    else:
        msg['To'] = ", ".join(my_email_to)
    
    msg['From'] = my_email_from
    data = [platform.system(), '-', test.tag, 'Quality Regression' if my_comparequalitymetrics else 'Performance Regression', '-', test.branch]
    msg['Subject'] = ' '.join(data)

    session = smtplib.SMTP(my_smtp_host, my_smtp_port)
    try:
        session.ehlo()
        session.starttls()
        session.ehlo()
        session.login(my_email_from, my_smtp_pwd.decode('base64'))
        session.sendmail(my_email_from, my_email_to, msg.as_string())
    except smtplib.SMTPException, e:
        print 'Unable to send email', e
    finally:
        session.quit()

def encode(test): 
    with open(test.fullcommandlines) as lines:
        for cmd in lines:
            if(ffmpeg_feature == True):
                os.environ["LD_LIBRARY_PATH"]=lib_path		
            test.setup(cmd)
            print('encoding...', cmd)
            ret = sub.Popen(cmd, shell=True, stderr=test.logfp, stdout=test.logfp)
            if ret.wait() != 0:
                print("\n Encoding failed: %s \n" %cmd)
            # sleep for 10 seconds to release the resource completely....
            time.sleep(10)

def writetoken(cmdline, test, final, count):
    global featureFlag, featurecount, featurebitrate, featuremaxrates, featurebufsizes, featurecrf
    command = cmdline[10]
    for i in range(len(cmdline)):
        test.parsecsv(cmdline[i], i, cmdline)
    if test.preset == '':
        test.preset = 'medium'
    if test.crf == '':
        test.crf = '28'
    if feature in command:
        if featureFlag == False and featurecount == 0:
            bitrates, maxrates, bufsizes, crf = [], [], [], []
            featurecount = count
            featureFlag = True
            if 'bitrate' in command:
                featurebitrate = (test.abr).split(",")
            if 'vbv-bufsize' in command:
                featurebufsizes = (test.vbvbufsize).split(",")
            if 'vbv-maxrate' in command:
                featuremaxrates = (test.vbvmaxrate).split(",")
            if 'crf' in command:
                featurecrf = (test.crf).split(",")

        if (featurecount > 0 and featureFlag == True) :
            if featurebitrate and featurebufsizes and featuremaxrates:
                final.write(''.join(','.join([test.video, test.feature, test.preset, featurebitrate.pop(0), test.cqp, test.crf, featurebufsizes.pop(0), featuremaxrates.pop(0)])))
            elif featurebitrate and not featurebufsizes and not featuremaxrates:
                final.write(''.join(','.join([test.video, test.feature, test.preset, featurebitrate.pop(0), test.cqp, test.crf, test.vbvbufsize, test.vbvmaxrate])))
            elif featurecrf and featurebufsizes and featuremaxrates:
                final.write(''.join(','.join([test.video, test.feature, test.preset, test.abr, test.cqp, featurecrf.pop(0), featurebufsizes.pop(0), featuremaxrates.pop(0)])))
            elif featurecrf and not featurebufsizes and not featuremaxrates:
                final.write(''.join(','.join([test.video, test.feature, test.preset, test.abr, test.cqp, featurecrf.pop(0), test.vbvbufsize, test.vbvmaxrate])))
            featurecount = (featurecount - 1)
            if (featurecount == 0):
                featureFlag = False

    else:
        final.write(''.join(','.join([test.video, test.feature, test.preset, test.abr, test.cqp, test.crf, test.vbvbufsize, test.vbvmaxrate])))

def regeneratecsv(test):
    global encoder_binary_version, csv_filename
    csvheader = True
    csvlist = glob.glob(os.path.join(test.resultdir, '*.csv'))
    final = open(os.path.join(test.resultdir, test.finalcsv), 'w')
    if encoder_binary_name == 'x265' or encoder_binary_name == 'x264':
        for csv in csvlist:
            with open(csv) as lines:
                bitrates, maxrates, bufsizes = [], [], [] 
                for line in lines:
                    tokens = line.split(', ')
                    cmdline = tokens[0].split()
                    if cmdline[0] == 'Command,':
                        if csvheader == True:
                            final.write(' Video, Feature, Preset, ABR, CQP, CRF, vbv-bufsize, vbv-maxrate')							
                            csvheader = False
                        else:
                            continue
                    else:
                        writetoken(cmdline, test, final, 0)
                        test.preset = test.abr = test.cqp = test.crf = test.vbvbufsize = test.vbvmaxrate = test.feature = ''

                    for j in range(len(tokens)):
                        a = tokens[j].replace(",",".")
                        final.write(',')
                        final.write(a)				

    else:
        currentTestCsv = open(os.path.join(test.resultdir, csv_filename), 'r')
        writeline=''
        start_line = ''
        count = 0
        currentTestCsvLines = currentTestCsv.readlines()
        start_line = currentTestCsvLines[0]	
        tokens = start_line.split(', ')
        cmdline = tokens[0].split()
        encoder_binary_version = currentTestCsvLines[4]
        if cmdline[0] == 'Command':
            if csvheader == True:
                final.write(' Video, Feature, Preset, ABR, CQP, CRF, vbv-bufsize, vbv-maxrate')
                csvheader = False		
                for j in range(len(tokens)):
                    a = tokens[j].replace(",",".")
                    if '\n' in a:
                        a = tokens[j].replace("\n",",")				
                    final.write(',')
                    final.write(a)  
                final.write('Encoder Version\n')
        for line in range(1, len(currentTestCsvLines), 4):
            bitratelist, crflist = [], []
            writeline = currentTestCsvLines[line]
            tokens = writeline .split(', ')
            cmdline = tokens[0].split()
            if feature in cmdline[10]:
                if 'bitrate=' in cmdline[10]:
                    list = cmdline[10].split('bitrate=')[1].split(':')[0]
                    for l in list.split (','):
                        bitratelist.append(l)
                    count = len(bitratelist)
                if 'crf=' in cmdline[10]:
                    list = cmdline[10].split('crf=')[1].split(':')[0]
                    for l in list.split (','):
                        crflist.append(l)
                    count = len(crflist)
                writetoken(cmdline,test, final, count)
            else:
                writetoken(cmdline,test, final, 0)
            test.preset = test.abr = test.cqp = test.crf = test.vbvbufsize = test.vbvmaxrate = test.feature = ''
            for j in range(len(tokens)):
                a = tokens[j].replace(",",".")
                final.write(',')
                if '\n' in a:
                    a = tokens[j].replace("\n",",")
                final.write(a)
            final.write(encoder_binary_version)					
    final.close()
			
			
def compare(test):
    if not os.path.exists(os.path.join(test.resultdir, test.finalcsv)) or not os.path.exists(os.path.join(test.cwd, test.goldendir, test.finalcsv)):
        print('csv file does not exist to compare', os.path.join(test.resultdir, test.finalcsv), os.path.exists(os.path.join(test.cwd, test.goldendir, test.finalcsv)))
        if os.path.exists(os.path.join(test.resultdir, test.finalcsv)):
            shutil.copy(os.path.join(test.resultdir, test.finalcsv), os.path.join(test.cwd, test.goldendir, test.finalcsv))
        return

    import operator
    temp_list = []
    temp_dict = {}
    current = open(os.path.join(test.resultdir, test.finalcsv), 'r')
    golden = open(os.path.join(test.goldendir, test.finalcsv), 'r')
    current_csvlines = current.readlines()
    golden_csvlines = golden.readlines()
    golden_ssim = ''
    current_ssim = ''
    if len(current_csvlines) == len(golden_csvlines):
        test.table.append(test.tableheader)
        for i in range(1, len(golden_csvlines), test.iter):
            tok = golden_csvlines[i].split(',')
            version_len = len(tok)
            test.video, test.feature, test.preset, test.abr, test.cqp, test.rev, test.crf, test.vbvbufsize, test.vbvmaxrate = tok[0], tok[1], tok[2], tok[3], tok[4], tok[version_len-1], tok[5], tok[6], tok[7]
            for j in range(test.iter):
                tok = golden_csvlines[i+j].split(',')		
                test.avg.append(float(tok[11]))
            golden_ssim = tok[18]
            test.fps = "%.2f" % harmonic_mean(test.avg)
            test.avg = []

            tok = current_csvlines[i].split(',')
            if tok[0] == test.video and tok[1] == test.feature and tok[2] == test.preset and tok[3] == test.abr and tok[4] == test.cqp and tok[5] == test.crf and tok[6] == test.vbvbufsize and tok[7] == test.vbvmaxrate:
                version_len_cur = len(tok)
                for j in range(test.iter):
                    tok = current_csvlines[i+j].split(',')
                    test.avg.append(float(tok[11]))
                current_ssim = tok[18]
                fps = "%.2f" % harmonic_mean(test.avg)
                test.avg = []
                perc_increase = float("%.2f" %(100 * ((float(fps) - float(test.fps)) / float(test.fps))))
                temp_dict['fps'] = perc_increase
                temp_dict['cmd'] = r'<tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th><th>{4}</th><th>{5}</th><th>{6}</th><th>{7}</th><th>{8}</th><th>{9}</th><th>{10}</th><th>{11}</th><th>{12}</th><th>{13}</th><th>{14}</th></tr>'\
                                    .format(test.video, 
                                            test.feature,
                                            test.preset, 
                                            test.abr, 
                                            test.cqp, 
                                            test.crf, 
                                            test.vbvbufsize, 
                                            test.vbvmaxrate, 
                                            test.rev.strip('\r\n'), 
                                            tok[version_len_cur-1].strip('\r\n'),
                                            golden_ssim,
                                            current_ssim,
                                            str(test.fps), 
                                            str(fps), 
                                            perc_increase)
                temp_list.append(temp_dict)
                temp_dict = {}
                test.preset = test.abr = test.cqp = test.crf = test.vbvbufsize = test.vbvmaxrate = ''

        sorted_table = sorted(temp_list, key=operator.itemgetter('fps'))
        for list in sorted_table:
            test.table.append(list['cmd'])
        test.table.append('</table></body></html>')
        email_results(test, os.path.join(test.resultdir, test.finalcsv), os.path.join(test.cwd, test.goldendir, test.finalcsv))

    current.close()
    golden.close()
    os.remove(os.path.join(test.cwd, test.goldendir, test.finalcsv))
    shutil.copy(os.path.join(test.resultdir, test.finalcsv), os.path.join(test.cwd, test.goldendir, test.finalcsv))


def comparequality(test):
    if not os.path.exists(os.path.join(test.resultdir, test.finalcsv)) or not os.path.exists(os.path.join(test.cwd, test.goldendir, test.finalcsv)):
        print('csv file does not exist to compare', os.path.join(test.resultdir, test.finalcsv), os.path.exists(os.path.join(test.cwd, test.goldendir, test.finalcsv)))
        if os.path.exists(os.path.join(test.resultdir, test.finalcsv)):
            shutil.copy(os.path.join(test.resultdir, test.finalcsv), os.path.join(test.cwd, test.goldendir, test.finalcsv))
        return

    import operator
    temp_list = []
    temp_dict = {}
    ssim1 = []
    ssim2 = []
    bitrate1 = []
    bitrate2 = []
    abr = []
    current = open(os.path.join(test.resultdir, test.finalcsv), 'r')
    golden = open(os.path.join(test.goldendir, test.finalcsv), 'r')
    current_csvlines = current.readlines()
    golden_csvlines = golden.readlines()
    if len(current_csvlines) == len(golden_csvlines):
        test.table.append(test.tableheaderforQuality)
        for i in range(1, len(golden_csvlines), 4):
            tok = golden_csvlines[i].split(',')
            version_len = len(tok)
            test.video, test.feature, test.preset, test.rev = tok[0], tok[1], tok[2], tok[version_len-1]
            for j in range(4):
                tok = golden_csvlines[i+j].split(',')
                ssim1.append("{0:.4f}".format(float(tok[18])))
                bitrate1.append("{0:.2f}".format(float(tok[12])))
                abr.append(tok[3])

            tok = current_csvlines[i].split(',')
            if tok[0] == test.video and tok[2] == test.preset and tok[1] == test.feature:
                for j in range(4):
                    tok = current_csvlines[i+j].split(',')
                    ssim2.append("{0:.4f}".format(float(tok[18])))
                    bitrate2.append("{0:.2f}".format(float(tok[12])))

                dssim, rate = Bjontegaardmetric(ssim1,bitrate1,ssim2,bitrate2)
                
                temp_dict['cmd'] = r'<tr><th>{0}</th><th>{1}</th><th>{2}</th><th>{3}</th><th>{4}</th><th>{5}</th><th>{6}</th><th>{7}</th><th>{8}</th><th>{9}</th><th>{10}</th><th>{11}</th></tr>'\
                                    .format(test.video,
                                            test.feature,
                                            test.preset, 
                                            abr, 
                                            test.rev.strip('\r\n'), 
                                            tok[version_len-1].strip('\r\n'),
                                            str(bitrate1), 
                                            str(ssim1),
                                            str(bitrate2), 
                                            str(ssim2),
                                            "{0:.4f}".format(dssim),
                                            repr("{0:.2f}".format(rate)))
                temp_list.append(temp_dict)
                temp_dict = {}
                test.preset = ''
                abr = []
                ssim1 = []
                bitrate1 = []
                ssim2 = []
                bitrate2 = []

        for list in temp_list:
            test.table.append(list['cmd'])
        test.table.append('</table></body></html>')
        email_results(test, os.path.join(test.resultdir, test.finalcsv), os.path.join(test.cwd, test.goldendir, test.finalcsv))

    current.close()
    golden.close()
    os.remove(os.path.join(test.cwd, test.goldendir, test.finalcsv))
    shutil.copy(os.path.join(test.resultdir, test.finalcsv), os.path.join(test.cwd, test.goldendir, test.finalcsv))

def upload_csv(test):
    if not (my_ftp_url and my_ftp_user and my_ftp_pass and my_ftp_path_stable and my_ftp_path_default and my_ftp_path_defaultold and my_ftp_path_stableold):
        return

    now  = time.strftime("%Y-%m-%d-%H-%M-%S")
    import ftplib
    try:
        ftp = ftplib.FTP(my_ftp_url)
        ftp.login(my_ftp_user, my_ftp_pass.decode('base64'))
        if test.branch == 'default':
            ftp.cwd(my_ftp_path_default)
            fp = open(os.path.join(test.resultdir, test.finalcsv),'rb')
            ftp.storbinary('STOR ' + test.finalcsv,fp)
            ftp.cwd('./')
            ftp.cwd(my_ftp_path_defaultold)            
            ftp.storbinary('STOR ' + '_'.join([now, test.finalcsv]) ,fp)
        else:
            ftp.cwd(my_ftp_path_stable)
            fp = open(os.path.join(test.resultdir, test.finalcsv),'rb')
            ftp.storbinary('STOR ' + test.finalcsv,fp)
            ftp.cwd('./')
            ftp.cwd(my_ftp_path_stableold)            
            ftp.storbinary('STOR ' +'_'.join([now, test.finalcsv]),fp)
    except ftplib.all_errors, e:
        print "ftp failed", e
def Decodebitstreams_runssim(self):
    global headerhandle
    global header_numberofrows
    global header
    global path

    ssim_log=open(os.getcwd()+"//log//ssimlog.txt","w")
    hevcfiles = os.listdir(self.my_bitstreams)
    for bitstream in hevcfiles:
            dirpath = os.path.join(os.getcwd(),"decodedfiles")
            rename=bitstream.replace(".hevc", ".yuv")
            for n in range(header_numberofrows):
                    if headerhandle.cell(n, 0).value in bitstream:
                        header['video']=str(headerhandle.cell(n, 0).value)
                        header['width']=str(headerhandle.cell(n, 1).value)
                        header['height']=str(headerhandle.cell(n, 2).value)
                        header['fps']=str(headerhandle.cell(n, 3).value)
                        header['frames']=str(headerhandle.cell(n, 4).value)
            if 'ultrafast' in rename or 'superfast' in rename:
                command = path['ssim']+" "+ path['UHDcode']+" "+"-b "+os.path.join(self.my_bitstreams,bitstream)+" -o "+os.path.join(os.getcwd(),"decodedfiles","out.yuv")+" --parallel 4 -el "+"--input"+" "+path['input_sequences']+"//"+header['video']+".yuv "+"--frames "+header['frames']+" "+"--maxcusize 64"+" "+"--csv "+dirpath+"/"+rename+"_ssim.csv "+"--width "+header['width']+" "+"--height "+header['height']
            else:
                command = path['ssim']+" "+ path['UHDcode']+" "+"-b "+os.path.join(self.my_bitstreams,bitstream)+" -o "+os.path.join(os.getcwd(),"decodedfiles","out.yuv")+" --parallel 4 -el "+"--input"+" "+path['input_sequences']+"//"+header['video']+".yuv "+"--frames "+header['frames']+" "+"--maxcusize 32"+" "+"--csv "+dirpath+"/"+rename+"_ssim.csv "+"--width "+header['width']+" "+"--height "+header['height']
            print command
            ret=sub.Popen(command, shell=True, stderr=ssim_log, stdout=ssim_log)
            if ret.wait()!=0:
                print("error while running ssim tool")
    ssim_log.close()
    shutil.copy(os.path.join(self.resultdir,'x265Benchmark.csv'),'../plotgraphs')

def main():
    # create object
    test = Test()
    test.cwd = os.getcwd()

    # setup ramdisk path if created
    test.ramdisk()

    # parse the arguments
    for i in range(len(sys.argv)):
        test.parse(sys.argv[i], i)
    if not test.cfg:
        test.cfg = 'commands.conf.txt'

    # set up working directory
    test.setup_workingdir()

    # prepare command lines to run
    test.prepare_commands()

    # run the encoder
    encode(test)

    # remove video and move bitstreams from ramdisk
    test.remove_movefiles()

    # close the encoder log file
    test.logfp.close()

    # add extra columns for video, preset and rate control options in csv
    if not Decodebitstream:
        regeneratecsv(test)

    if my_compareFPS == True:
        compare(test)    # compare current test results with golden(previous) test results
    elif my_comparequalitymetrics == True:
        try:
            import numpy
        except ImportError, e:
            os.system("yum install -y numpy")
        comparequality(test) # compare current test quality metrics with golden (previous) metrics by calculaying BD-Rate, BD-SSIM

    # upload csv file on egnyte
    if my_csvupload == True:
        upload_csv(test)
    # Decoding and comparing the ssim value
    if Decodebitstream == True:
        import xlrd
        global headerhandle
        global header_numberofrows
        for folder in ["decodedfiles","log"]:
            if os.path.exists(folder):
                if not os.path.exists(folder+"//older"):
                    os.mkdir(folder+"//older")
            else:
                os.mkdir(folder)
        if not os.path.exists(os.path.join(os.getcwd(),"HeaderInfo.xls")):
            print "HeaderInfo.xls is missing"
            exit(0)
        wb = xlrd.open_workbook(test.cwd+"//HeaderInfo.xls")
        config = wb.sheet_by_name('Configuration')
        config_numberofrows=config.nrows
        headerhandle = wb.sheet_by_name('HeaderInfo')
        header_numberofrows=headerhandle.nrows
        for i in range(config_numberofrows):
            if config.cell(i, 0).value=='input_sequences':
                path['input_sequences']=str(config.cell(i, 1).value)
            elif config.cell(i, 0).value=='ssim':
                path['ssim']=str(config.cell(i, 1).value)
            elif config.cell(i, 0).value=='UHDcode':
                path['UHDcode']=str(config.cell(i, 1).value)
        Decodebitstreams_runssim(test)
        os.chdir('../plotgraphs')
        os.system("python plot.py")

if __name__ == "__main__":
    main()
