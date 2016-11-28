#FPS Tool

##实现需求：
动画FPS测试。

直接运行FPStest.py即可，按需添加参数，参数说明参见下方脚本说明。

##脚本说明：
1. 参数说明；
	* -o：操作类型，只有三种类型，LR（左右滑动）、UD（上下滑动）、DU（下上滑动）；
	* -c：测试次数，默认30次；
	* -h：帮助信息。
2. 脚本原理：
	* 通过gfxinfo获取每帧耗时用以计算FPS，需打开被测设备的“GPS呈现分析”开关;
	* 执行操作时每秒计算一次动画帧率，并在终端上输出计算，并于操作脚本执行完后计算最终平均FPS结果；
	* 结果均在终端输出，无保留本地文件。