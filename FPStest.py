# -*- coding: utf-8 -*-
import os, platform, re, time, subprocess, FPS_script
from optparse import OptionParser


# 判断系统平台;
if platform.system() == 'Windows':
    seek = 'findstr'
else:
    seek = 'grep'

# 设置测试前提条件, 执行脚本、 开关状态等;
def setup(method):
    scriptFiles_exist = os.popen('adb shell ls /sdcard/').read()
    if 'monkeyTest_UD.txt' not in scriptFiles_exist:
        FPS_script.main()
    if method == 'gfx':
        # 检查GPU呈现分析开关状态;
        get_gfxSwitch = os.popen('adb shell getprop debug.hwui.profile').read()
        if 'true' in get_gfxSwitch or 'visual_bars' in get_gfxSwitch:
            print u'通过gfxinfo取值, 测试开始...\n'
        else:
            print u'无法获取帧率数据, 请打开“开发者选项-GPU呈现模式分析”开关, 脚本退出。'
            exit()
    else:
        print u'通过surfaceFlinger取值, 测试开始...\n'

# 获取processName, windowName;
def getprocess():
    getWindow = os.popen('adb shell dumpsys window | ' + seek + ' mCurrentFocus').readline().split()[-1]
    processName = getWindow.split(r'/')[0]
    windowName = getWindow[:-1]
    return processName, windowName

# 获取手机垂直同步时间;
def get_vsync_time(method):
    vsyncTime = 0
    get_vsyncTime_command = 'adb shell dumpsys SurfaceFlinger | %s refresh=' %seek
    get_vsyncTime = os.popen(get_vsyncTime_command).read().split(',')
    for line in get_vsyncTime:
        if 'refresh' in line:
            if method == 'gfx':
                vsyncTime = round(float(line.split('=')[1]) / 1000000, 2)
            else:
                vsyncTime = round(float(line.split('=')[1]) / 1000000)
    # print 'vsynTime:', vsyncTime
    return vsyncTime

def monkey_command():
    monkeyCommand = ''
    usage = 'FPStest.py [-o <LR, UD, DU>][-c <count>][-m <method>]'
    # 参数解析;
    parser = OptionParser(usage)
    parser.add_option('-o', dest = 'operateType', help = u'操作类型, LR左右滑动, UD上下滑动, DU下上滑动;')
    parser.add_option('-c', dest = 'count', default = '30', help = u'操作次数, 默认30次;')
    parser.add_option('-m', dest = 'method', default = 'gfx', help = u'测试方法, gfx、surface, 默认为gfx;')
    (options, args) = parser.parse_args()
    operateType = options.operateType
    count = options.count
    method = options.method
    # 判断测试次数参数是否为数字类型;
    try:
        int(count)
    except:
        parser.print_help()
        exit()
    # 判断操作类型输入值;
    if operateType == 'UD' or operateType == 'ud':
        monkeyCommand = 'adb shell monkey -f /sdcard/monkeyTest_UD.txt %s' %count
    elif operateType == 'DU' or operateType == 'du':
        monkeyCommand = 'adb shell monkey -f /sdcard/monkeyTest_DU.txt %s' %count
    elif operateType == 'LR' or operateType == 'lr':
        monkeyCommand = 'adb shell monkey -f /sdcard/monkeyTest_LR.txt %s' %count
    else:
        parser.print_help()
        exit()
    # 判断测试方法输入值;
    if method == 'gfx' or method == 'surface':
        pass
    else:
        parser.print_help()
        exit()
    return monkeyCommand, method

def FPS_data_collection(method):
    processName, windowName = getprocess()
    if method == 'gfx':
        # 通过gfxinfo命令取值;
        if 'StatusBar' in processName:
            gfxinfo_command = 'adb shell dumpsys gfxinfo com.android.systemui'
        else:
            gfxinfo_command = 'adb shell dumpsys gfxinfo %s' %processName
        os.popen(gfxinfo_command)
        time.sleep(1)
        gfxinfo = os.popen(gfxinfo_command).readlines()
        # 每帧耗时计算;
        frameList_gfx = []
        for gfxinfo_str in gfxinfo:
            frame_1st_split = re.findall( r'\d*\W\d\d[\t\r]', gfxinfo_str )
            if len(frame_1st_split) > 1:
                frame_1st = []
                for i in frame_1st_split:
                    frame_1st.append(float(i.replace( r'\t', '').replace( r'\r', '')))
                frame_1st_time = round(sum(frame_1st), 2)
                frameList_gfx.append(frame_1st_time)
        # print frameList_gfx
        return frameList_gfx
    else:
        # 通过surfaceFlinger命令取值;
        surfaceFlinger_timeList = []
        os.popen('adb shell dumpsys SurfaceFlinger --latency-clear')
        time.sleep(1)
        surfaceFlinger_all = os.popen('adb shell dumpsys SurfaceFlinger --latency ' + windowName).readlines()
        for surface_line in surfaceFlinger_all[1:-1]:
            # 过滤空值, 获取第二列的值;
            if len(surface_line) > 10:
                surfaceFlinger_timeList.append(surface_line.split()[1])
        # 计算单帧耗时,第二列数据后一数据与前一数据的差;
        framesList_surface = []
        for i in range(len(surfaceFlinger_timeList)):
            if i != len(surfaceFlinger_timeList) - 1:
                timing = int(surfaceFlinger_timeList[i+1]) - int(surfaceFlinger_timeList[i])
                # 纳秒换算毫秒;
                framesTime = round(timing / 1000000.00, 2)
                framesList_surface.append(framesTime)
        # print framesList_surface
        return framesList_surface

# FPS计算;
def FPS_count(method, vsyncTime):
    frameList = FPS_data_collection(method)
    frame_count = len(frameList)
    # frameList不为空, 进行运算;
    if frame_count > 0:
        jank_count = 0
        vsync_overtime = 0
        for frame_time in frameList:
            if frame_time > vsyncTime:
                jank_count += 1
                if frame_time % vsyncTime == 0:
                    vsync_overtime += int(frame_time / vsyncTime) - 1
                else:
                    vsync_overtime += int(frame_time / vsyncTime)
        fps = round(frame_count * 60.0 / (frame_count + vsync_overtime), 2)
        return fps, jank_count, vsync_overtime, frame_count

def monkey_run():
    # FPS_script.wait_for_device()
    retry = 0
    monkeyCommand, method = monkey_command()
    setup(method)
    vsyncTime = get_vsync_time(method)
    monkeyRun = subprocess.Popen(monkeyCommand, shell = True)
    time.sleep(1)
    fps_list = []
    jank_list = []
    frame_all = []
    returncode = monkeyRun.poll()
    while returncode is None:
        try:
            fps, jank, vsync, frame_count = FPS_count(method, vsyncTime)
            fps_list.append(fps)
            jank_list.append(jank)
            frame_all.append(frame_count)
            print u'FPS值:', fps
            print u'掉帧数:', jank
            print u'垂直同步超时区间:', vsync
            print u'总帧数:', frame_count
            print '-------------------------------'
        except:
            retry += 1
            if retry == 3:
                print u'取值失败, 建议更换测试方法进行尝试。'
                exit()
        returncode = monkeyRun.poll()
    fps_avg = round(sum(fps_list) / len(fps_list), 2)
    jank_percent = round(float(sum(jank_list)) / sum(frame_all) * 100, 2)
    print u'平均FPS值:', fps_avg
    print u'掉帧率: %s%%' %jank_percent

if __name__ == '__main__':
    monkey_run()