# configure all the variables beginning with my_, then you will be able to run the test script
# system description
my_system = 'System: '
my_hardware = 'Hardware: '

# locate the paths
my_sequences     = r''
my_bitstreams    = r''

# are you created enough RAM disk? if True, then give path
my_RAMDISK          = False
my_RAMDiskpath      = r'/mnt/RAMDISK'
ffmpeg_feature      = False #Set True for ffmpeg performance test
lib_path            = r'' #set path installation path of the binary
encoder_binary_name = ''  #Set encoder_binary_name
feature             = ''  #Set feature name to parse commandline differently

# compare current test performance results with golden (previous) test results
my_compareFPS = False

# compare current test quality metrics with golden (previous) metrics by calculaying BD-Rate, BD-SSIM 
my_comparequalitymetrics = False

# email the compared test results
my_email_from   = ''
my_email_to     = ''
my_smtp_pwd     = ''
my_smtp_host    = 'smtp.gmail.com'
my_smtp_port    = 587


# upload csv files on egnyte(This is for automation of tests)
# here password should be base64 encoded
my_csvupload            = False
my_ftp_url              = ''
my_ftp_user             = ''
my_ftp_pass             = ''
my_ftp_path_stable      = ''
my_ftp_path_default     = ''
my_ftp_path_stableold   = ''
my_ftp_path_defaultold  = ''
