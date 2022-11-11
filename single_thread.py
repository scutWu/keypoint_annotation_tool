# -*- coding : utf-8-*-

import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import mediapipe as mp
import json
import cv2
import os
from shutil import rmtree
from PIL import Image, ImageTk
import math
import time
import ctypes
# from mpl_toolkits import mplot3d
# import  matplotlib.pyplot as plt
# import keyboard


class LabelTool:
    def __init__(self, master):
        self.parent = master
        self.parent.title('手部关键点自动标注微调工具软件')
        self.parent.geometry('880x820')
        # self.parent_canvas = tk.Canvas(self.parent, width=880, height=820, scrollregion=(0, 0, 880, 820))
        # self.parent_canvas.pack(fill='both', expand=True)
        self.frame = tk.Frame(self.parent, takefocus=True)
        self.frame.pack(fill='both', expand=True)

        # entry定义
        self.entry_list = [tk.Entry(self.frame, takefocus=False) for i in range(42)]
        self.entry_content = [tk.StringVar() for i in range(42)]  # 当前帧的关键点
        for i in range(42):
            self.entry_list[i].config(textvariable=self.entry_content[i])

        # 参数定义
        self.videoPath = ''  # 选中的视频的路径
        self.current = 0  # 当前帧（当前帧current与显示的帧序号i的关系是：i = current + 1）
        self.start = False  # 是否开始处理视频
        self.rad = 3.0  # 关键点半径
        self.image_height = 680
        self.image_width = 360
        self.original_height = 0
        self.original_width = 0
        self.frame_count = 0
        self.frame_rate = 0.0
        self.filename = ''
        self.detect = 'all'  # 三种取值：all、partial、none，分别代表全部帧检测到关键点、部分帧检测到关键点、所有帧都没检测到关键点
        self.fail_frame = []  # 没检测到关键点的帧序号
        self.first = 0  # 起始帧位置，初始为0
        self.ddl = 0
        self.step = tk.IntVar()  # 键盘控制关键点移动的步长
        self.step.set(4)
        self.gr_label = []
        self.keypoint_data_new = []
        self.img = []  # 缓存每一帧图片，内存换时间
        self.show = True  # true时显示当前关键点，false时不显示

        # radiobutton定义
        self.index = tk.IntVar()
        self.index.set(21)  # 21代表没有选中
        self.rb = [tk.Radiobutton(self.frame, text="", value=i, font=("Helvetica", 5), variable=self.index
                                  , command=self.frame.focus_set, takefocus=False) for i in range(22)]
        self.gr = tk.IntVar()
        self.gr.set(3)  # 0代表过渡帧(默认)，1代表张开，2代表握紧，3代表没有选中
        text = ["过渡帧", "伸掌起始帧", "握拳起始帧", ""]
        self.rb1 = [tk.Radiobutton(self.frame, text=text[i], value=i, variable=self.gr, font=1,
                                   indicatoron=True, command=self.on_rb1, takefocus=False) for i in range(4)]
        self.work_state = tk.IntVar()
        self.work_state.set(0)  # 0代表标数据（输入是视频），1代表检测标的数据质量（输入是视频+json）
        self.work_state_ = 0  # 在选择视频后，由该变量决定软件的工作状态。（设置该变量的目的是：在开放选择工作状态的情况下，保证软件的工作状态统一
        text = ['标注', '检查']
        self.rb2 = [tk.Radiobutton(self.frame, text=text[i], value=i, variable=self.work_state,
                                   font=1, command=self.on_rb2, takefocus=False) for i in range(2)]
        self.rb3_value = tk.IntVar()
        self.rb3_value.set(0)  # 0当前帧，1后一帧，2后两帧，-1前一帧，-2前两帧, -3不显示所有坐标
        text = ['N', '-2', '-1', '0', '1', '2']
        self.rb3 = [tk.Radiobutton(self.frame, text=text[i + 3], value=i, variable=self.rb3_value,
                                   command=self.on_rb3) for i in range(-3, 3)]

        # checkbutton定义
        self.cb_content = tk.IntVar()
        self.cb = tk.Checkbutton(self.frame, text="辅助网格线", font=200, variable=self.cb_content,
                                 command=self.on_cb, takefocus=False)
        self.complex = tk.IntVar()  # 复杂场景，0代表简单场景，1代表复杂场景, 初始为简单场景
        self.complex.set(0)
        self.complex_type = []
        self.cb1 = tk.Checkbutton(self.frame, text="复杂场景", font=200, variable=self.complex,
                                  command=self.create_complex_window)
        # self.cb2 = tk.Checkbutton(self.frame, text="人脸", font=200, variable=self.cb5_value[1])  # 人脸，已弃用
        self.cb3_value = tk.IntVar()  # 是否选定初始帧，0代表未选定，1代表已选定
        self.cb3_value.set(0)
        self.cb3 = tk.Checkbutton(self.frame, text="十秒视频起始帧：" + "未标注",
                                  font=200, variable=self.cb3_value, command=self.on_cb3, takefocus=False)

        # 二级界面复杂类型变量定义，由二级界面的checkbutton绑定,其中cb5_value[1]代表人脸
        self.cb5_value = [tk.IntVar() for i in range(11)]
        for i in range(11):
            self.cb5_value[i].set(0)

        # button定义
        # self.bt = tk.Button(self.frame, text="更改json输出路径", command=self.change_output_path)
        self.bt0 = tk.Button(self.frame, text="选择视频", command=self.select_path)
        self.bt1 = tk.Button(self.frame, text="test", command=self.mytest)
        self.bt2 = tk.Button(self.frame, text="重置当前帧坐标", command=self.reset_coordinate, takefocus=False)
        self.bt3 = tk.Button(self.frame, text="上一帧图像", command=self.previous_image, takefocus=False)
        self.bt4 = tk.Button(self.frame, text="下一帧图像", command=self.next_image, takefocus=False)
        self.bt5 = tk.Button(self.frame, text="保存输出文件和视频", command=self.save_file)
        # self.bt6 = tk.Button(self.frame, text="使用说明", command=self.info)
        # self.bt7 = tk.Button(self.frame, text="更改默认输入路径", command=self.change_input_path)
        # self.bt8 = tk.Button(self.frame, text='更改视频输出路径', command=self.change_video_path)
        self.bt9 = tk.Button(self.frame, text='更改软件配置', command=self.config_software, takefocus=False)

        # label定义
        self.label1 = tk.Label(self.frame, font=200, text="帧序号：" + "0/0")
        self.label2 = tk.Label(self.frame, font=200, text="视频编号：")
        # self.label3 = tk.Label(self.frame, font=200)  # 输出路径。已弃用
        self.label8 = tk.Label(self.frame, font=150, text="", background="red")
        self.label9 = tk.Label(self.frame, font=200, text="帧率：")
        self.label10 = tk.Label(self.frame, font=200, text="")

        # 两个画布定义
        self.panel0 = tk.Canvas(self.frame, bg="lightgrey", height=740, width=420)
        self.panel = tk.Canvas(self.frame, bg="lightgrey", height=680, width=360)

        # 创建scrollbar，有bug
        # self.sb = tk.Scrollbar(self.frame)
        # self.sb.pack(side='right', fill='y')
        # self.sb.config(command=self.parent_canvas.yview)
        # self.parent_canvas.config(yscrollcommand=self.sb.set)
        # self.parent_canvas.create_window(0, 0, window=self.frame)

        # 输入输出路径定义、创建默认文件夹和path.json
        self.output_path = tk.StringVar()
        self.input_path = tk.StringVar()
        self.video_path = tk.StringVar()
        self.create_init_folder()

        # 绑定函数
        self.panel.bind("<Button-1>", self.on_click)
        self.frame.bind("<KeyPress>", self.on_keyboard)
        self.frame.bind("<Button-1>", self.focus_on_frame)
        self.frame.focus_set()
        # entry绑定回调函数
        for i in range(42):
            self.entry_content[i].trace_variable("w", self.callback_entry)
        self.index.trace('w', self.callback_index)
        self.after_id = self.panel.after(600, self.focus_on_current_index)

        # 设置布局
        self.layout()

    def layout(self):
        # entry_list（关键点坐标）、rb（关键点index）、label（关键点说明label）
        # 第一部分
        j = 0
        for i in range(0, 10):
            self.entry_list[i].place(x=520 + 80 * (i % 2), y=80 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=470, y=80 + 20 * i)
                j += 1
                la = tk.Label(self.frame, text=str(j), bg="red")
                la.place(x=495, y=80 + 20 * i)
        # 第二部分
        # j = 5
        for i in range(10, 18):
            self.entry_list[i].place(x=520 + 80 * (i % 2), y=91 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=470, y=91 + 20 * i)
                j += 1
                la = tk.Label(self.frame, text=str(j - 5), bg="green")
                la.place(x=495, y=91 + 20 * i)
        # 第三部分
        # j = 9
        for i in range(18, 26):
            self.entry_list[i].place(x=520 + 80 * (i % 2), y=102 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=470, y=102 + 20 * i)
                j += 1
                la = tk.Label(self.frame, text=str(j - 9), bg="yellow")
                la.place(x=495, y=102 + 20 * i)
        # 第四部分
        # j = 13
        for i in range(26, 34):
            self.entry_list[i].place(x=720 + 80 * (i % 2), y=0 - 440 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=675, y=0 - 440 + 20 * i)
                j += 1
                la = tk.Label(self.frame, text=str(j - 13), bg="cyan")
                la.place(x=700, y=0 - 440 + 20 * i)
        # 第五部分
        # j = 17
        for i in range(34, 42):
            self.entry_list[i].place(x=720 + 80 * (i % 2), y=-390 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=675, y=0 - 390 + 20 * i)
                j += 1
                la = tk.Label(self.frame, text=str(j - 17), bg="pink")
                la.place(x=700, y=0 - 390 + 20 * i)

        # radiobutton布局
        for i in range(3):
            self.rb1[i].place(x=470, y=650 + 35 * i)
        for i in range(2):
            self.rb2[i].place(x=720 + 70 * i, y=5)
        for i in range(6):
            self.rb3[i].place(x=665 + 35 * i, y=480)

        # checkbutton布局
        self.cb.place(x=470, y=770)  # 辅助网格线
        self.cb1.place(x=750, y=35)  # 复杂场景
        self.cb3.place(x=20, y=30)  # 十秒视频起始帧

        # button布局
        self.bt0.place(x=700, y=530, width=140, height=31)  # 选择视频
        self.bt2.place(x=700, y=570, width=140, height=31)  # 重置当前帧坐标
        self.bt3.place(x=700, y=610, width=140, height=31)  # 上一帧图像
        self.bt4.place(x=700, y=650, width=140, height=31)  # 下一帧图像
        # self.bt1.place(x=700, y=690, width=140, height=31)  # test
        self.bt5.place(x=700, y=730, width=140, height=31)  # 保存输出文件和视频
        # self.bt.place(x=710, y=730, width=140, height=31)  # 更改json输出路径
        # self.bt8.place(x=710, y=690, width=140, height=31)  # 更改视频输出路径
        # self.bt7.place(x=710, y=770, width=140, height=31)  # 更改默认输入路径
        self.bt9.place(x=700, y=770, width=140, height=31)  # 修改软件配置

        # label布局
        self.label1.place(x=240, y=5)  # 帧序号
        self.label2.place(x=20, y=5)  # 视频编号
        self.label9.place(x=440, y=5)  # 帧率
        self.label10.place(x=470, y=620)  # gr提示信息
        tk.Label(self.frame, text="工作状态：", font=1).place(x=620, y=5)

        # 画布布局
        self.panel0.place(x=20, y=60, anchor="nw")  # 底层画布
        self.panel.place(x=50, y=90, anchor="nw")  # 顶层画布

    def create_init_folder(self):
        if not os.path.exists('./output'):  # 初始输出文件夹
            os.mkdir('./output')
        if not os.path.exists('./processed_video'):
            os.mkdir('./processed_video')
        if not os.path.exists('./processed_video/1'):
            os.mkdir('./processed_video/1')
        if not os.path.exists('./processed_video/2'):
            os.mkdir('./processed_video/2')
        if not os.path.exists('./path.json'):
            with open('./path.json', 'w') as file:
                path = os.getcwd()
                path = path.replace('\\', '/')
                json_file = dict(input_path=".", output_path=path + '/output', video_path=path + '/processed_video')
                json.dump(json_file, file)
        with open('./path.json', 'r') as file:
            json_file = json.load(file)
            self.output_path.set(json_file['output_path'])
            self.input_path.set(json_file['input_path'])
            self.video_path.set(json_file['video_path'])

    def on_rb2(self):
        if self.work_state.get() == 0:
            self.bt0.config(text='选择视频')
        elif self.work_state.get() == 1:
            self.bt0.config(text='选择视频和json')

    def calculate_gr_count(self):
        gt = len(self.gr_label) // 2
        d = []
        t = []
        zuida = 0
        zuixiao = 10000
        for i in range(self.first - 1, self.first + int(10 * self.frame_rate) - 1):
            temp = math.sqrt(math.pow(self.keypoint_data_new[i][1] * self.original_width -
                                      self.keypoint_data_new[i][17] * self.original_width, 2) +
                             math.pow(self.keypoint_data_new[i][2] * self.original_height -
                                      self.keypoint_data_new[i][18] * self.original_height, 2))
            d.append(temp)
            # t.append(self.keypoint_data[i][0])
            if temp > zuida:
                zuida = temp
            if temp < zuixiao:
                zuixiao = temp
            # print("dis[" + str(t[i]) + "] = " + str(d[i]))
        mean = (zuida + zuixiao) / 2
        count = 0
        for i in range(int(10 * self.frame_rate - 1)):  # 所有帧
            if not (d[i] > mean and d[i + 1] > mean):
                if not (d[i] < mean and d[i + 1] < mean):
                    count += 1
        pd = int(count / 2)
        if gt == pd:
            print('Congratulation!', 'gt = ' + str(gt) + ', pd = ' + str(pd))
        else:
            print('Aoh!', 'gt = ' + str(gt) + ', pd = ' + str(pd))

    def focus_on_frame(self, event):
        self.frame.focus_set()

    def when_destroy(self, event):
        self.cb1.config(state=tk.ACTIVE)
        # print("111", event)
        value = ['a1', 'a2', 'a3', 'a4', 'b1', 'b2', 'c1', 'c2', 'd', 'e', 'f']
        self.complex_type = []
        for i in range(11):
            if self.cb5_value[i].get() == 1:
                self.complex_type.append(value[i])
        if len(self.complex_type) > 0:
            self.complex.set(1)
        else:
            self.complex.set(0)
        # print('complex:', self.complex.get(), ', complex_type:', self.complex_type)

    def create_complex_window(self):
        top = tk.Toplevel()
        top.title('选择复杂场景类型')
        top.geometry('640x490')
        self.cb1.config(state=tk.DISABLED)
        text = ['(1)手部颜色和背景颜色相近', '(2)背景出现人脸', '(3)背景出现医生的手', '(4)背景目标较多较复杂',
                '(1)过近', '(2)过远', '(1)光线过暗', '(2)光线过亮', '(d)模糊、像素低的视频', '(e)手掌与屏幕不平行：过于前倾、后倾或侧倾',
                '(f)抓握不标准：不能完全张开手掌、为追求速度而不完全张开手掌']
        label_text = ['(a)complex background', '(b)手与屏幕距离问题', '(c)光线问题导致手与背景难以分辨']
        # 绑定了self.cb5_value数组，因此每次打开子窗口能自动显示目前标记复杂场景类别
        cb5 = [tk.Checkbutton(top, text=text[i], variable=self.cb5_value[i], font=1) for i in range(11)]
        label1 = tk.Label(top, text=label_text[0], font=1)
        label1.place(x=10, y=10)
        label1.bind('<Destroy>', self.when_destroy)
        for i in range(4):
            cb5[i].place(x=40, y=40 + 30 * i)
        tk.Label(top, text=label_text[1], font=1).place(x=10, y=170)
        for i in range(2):
            cb5[i + 4].place(x=40, y=200 + 30 * i)
        tk.Label(top, text=label_text[2], font=1).place(x=10, y=270)
        for i in range(2):
            cb5[i + 6].place(x=40, y=300 + 30 * i)
        for i in range(3):
            cb5[i + 8].place(x=10, y=370 + 40 * i)

    def config_software(self):
        top = tk.Toplevel()
        top.title('修改配置')
        top.geometry('640x460')
        top.wm_attributes('-topmost', 1)
        tk.Button(top, text='更改默认视频输入路径', command=self.change_input_path).place(x=20, y=8, width=140, height=31)
        tk.Entry(top, textvariable=self.input_path, state=tk.DISABLED).place(x=180, y=8, width=420, height=31)
        tk.Button(top, text='更改默认json输出路径', command=self.change_output_path).place(x=20, y=58, width=140, height=31)
        tk.Entry(top, textvariable=self.output_path, state=tk.DISABLED).place(x=180, y=58, width=420, height=31)
        tk.Button(top, text='更改默认视频输出路径', command=self.change_video_path).place(x=20, y=108, width=140, height=31)
        tk.Entry(top, textvariable=self.video_path, state=tk.DISABLED).place(x=180, y=108, width=420, height=31)
        tk.Label(top, text='关键点移动步长：', font=1).place(x=20, y=158)
        rb = [tk.Radiobutton(top, text=str(i), value=i, variable=self.step) for i in range(2, 9)]
        for i in range(7):
            rb[i].place(x=180 + 45 * i, y=158)

    def clear_rb(self):
        # self.rb[self.index.get()].deselect()
        self.rb[21].select()

    # 响应键盘专用
    def click_cb3(self):
        if self.start:
            if self.cb3_value.get() == 1:
                self.cb3.deselect()
            elif self.cb3_value.get() == 0:
                self.cb3.select()
            self.on_cb3()

    def on_cb3(self):
        if self.start:
            if self.cb3_value.get() == 1:
                self.first = self.current + 1
                if self.work_state_ == 1:
                    if self.is_raw_video == 'yes':
                        with open(self.path_to_json, 'r') as file:
                            data = json.load(file)
                        if self.first != data['original_index']:
                            tk.messagebox.showinfo('提示', '标注了新的十秒视频起始帧，在点击保存按钮时，将生成新的十秒视频')
                            self.bt5.config(text='保存输出文件和视频')
                        else:
                            self.bt5.config(text='保存输出文件')
                jieshu = self.first + int(10 * self.frame_rate) - 1
                if jieshu > self.frame_count:
                    tk.messagebox.showwarning('提示', '十秒视频的起始帧过大，结束帧 > 总帧数')
                    self.cb3.deselect()
                else:
                    # print(self.first, jieshu)
                    self.cb3.config(text="十秒视频起始帧：" + str(self.first) + "，结束帧：" + str(jieshu))
            else:
                self.cb3.config(text="十秒视频起始帧：" + "请在第 " + str(self.ddl) + ' 帧及之前标注')

    def clear_rb1(self):
        self.rb1[3].select()

    def on_keyboard(self, event):
        if self.start:
            # print(event, event.keycode, event.keysym, event.char)  # 根据这行代码来确定自己的按键信息
            if event.keysym == 'Return':
                self.next_image()
                return
            elif event.char == '0' or event.char == 'k' or event.char == 'K':
                self.previous_image()
                return
            elif event.char == '6' or event.char == ']':
                self.reset_coordinate()
                return
            elif event.char == '5' or event.char == '[':
                self.click_cb3()
                return
            elif event.char == '1' or event.char == 'l' or event.char == 'L':  # 过渡帧
                self.rb1[0].select()
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为过渡")
                return
            elif event.char == '2' or event.char == ';':  # 伸掌起始帧
                self.rb1[1].select()
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为伸掌")
                return
            elif event.char == '3' or event.char == "'":  # 握拳起始帧
                self.rb1[2].select()
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为握拳")
                return
            i = self.index.get()
            if i != 21:
                if event.char == ' ' or event.char == 'e' or event.char == 'E':  # 空格或e：index加一
                    if i < 20:
                        self.index.set(i + 1)
                    else:
                        self.index.set(0)
                elif event.char == 'q' or event.char == 'Q':  # 按下q，index减一
                    if i != 0:
                        self.index.set(i - 1)
                    else:
                        self.index.set(20)
                elif event.char == 'f' or event.char == 'F':  # 按下f，跳段
                    if i < 4:
                        self.index.set(i + 5)
                    elif i == 4:
                        self.index.set(8)
                    elif i > 16:
                        self.index.set(i - 17)
                    else:
                        self.index.set(i + 4)
                elif event.char == 'a' or event.char == 'A' or event.keycode == 37:  # 向左
                    self.entry_content[2 * i].set(str(int(self.entry_content[2 * i].get()) - self.step.get()))
                elif event.char == 'w' or event.char == 'W' or event.keycode == 38:  # 向上
                    self.entry_content[2 * i + 1].set(str(int(self.entry_content[2 * i + 1].get()) - self.step.get()))
                elif event.char == 's' or event.char == 'S' or event.keycode == 40:  # 向下
                    self.entry_content[2 * i + 1].set(str(int(self.entry_content[2 * i + 1].get()) + self.step.get()))
                elif event.char == 'd' or event.char == 'D' or event.keycode == 39:  # 向右
                    self.entry_content[2 * i].set(str(int(self.entry_content[2 * i].get()) + self.step.get()))

    # 响应鼠标点击
    def on_click(self, event):
        if self.start:
            i = self.index.get()
            if i != 21:
                # print(self.index.get(), type(event.x), event.y)
                self.entry_content[2 * i].set(event.x)
                self.entry_content[2 * i + 1].set(event.y)

    def mytest(self):
        # ax = plt.axes(projection="3d")
        # z = [[], [], [], [], []]
        # x = [[], [], [], [], []]
        # y = [[], [], [], [], []]
        # for i in range(50):
        #     z[0].append(self.keypoint_data[i][0])
        #     x[0].append(self.keypoint_data[i][1])
        #     y[0].append(self.keypoint_data[i][2])
        # for j in range(4):
        #     for i in range(50):
        #         z[j + 1].append(self.keypoint_data[i][0])
        #         x[j + 1].append(self.keypoint_data[i][11 + j * 2] * self.original_width)
        #         y[j + 1].append(self.keypoint_data[i][12 + j * 2] * self.original_height)
        # color = ["red", "green", "yellow", "blue", "pink"]
        # for i in range(5):
        #     ax.plot3D(x[i], y[i], z[i], color[i])
        # ax.set_xlabel("X Axes")
        # ax.set_ylabel("Y Axes")
        # ax.set_zlabel("Z Axes")
        # plt.show()

        # 计算抓握次数
        # d = []
        # t = []
        # zuida = 0
        # zuixiao = 10000
        # for i in range(self.frame_count):
        #     temp = math.sqrt(math.pow(self.keypoint_data[i][1] * self.original_width -
        #                               self.keypoint_data[i][17] * self.original_width, 2) +
        #                      math.pow(self.keypoint_data[i][2] * self.original_height -
        #                               self.keypoint_data[i][18] * self.original_height, 2))
        #     d.append(temp)
        #     t.append(self.keypoint_data[i][0])
        #     if temp > zuida:
        #         zuida = temp
        #     if temp < zuixiao:
        #         zuixiao = temp
        #     print("dis[" + str(t[i]) + "] = " + str(d[i]))
        # mean = (zuida + zuixiao) / 2
        # flag = 0  # 0 down, 1 up
        # count = 0
        # for i in range(self.frame_count - 1):  # 所有帧
        #     if not (d[i] > mean and d[i + 1] > mean):
        #         if not (d[i] < mean and d[i + 1] < mean):
        #             count += 1
        # count = int(count / 2)
        # print("count = " + str(count))
        # plt.ylabel("distance")
        # plt.xlabel("frame")
        # plt.plot(t, d)
        # d1 = [(zuida + zuixiao) / 2, (zuida + zuixiao) / 2]
        # t1 = [1, self.frame_count]
        # plt.plot(t1, d1, linestyle="--")
        # plt.show()

        # 生成20帧的视频
        # path = tk.filedialog.askopenfilename()
        # if path != '':
        #     cap = cv2.VideoCapture(path)
        #     mfps = cap.get(5)
        #     print(mfps)
        #     mfps = self.process_frame_rate(mfps)
        #     print(mfps)
        #     w = int(cap.get(3))
        #     h = int(cap.get(4))
        #     path, name = os.path.split(path)
        #     filename, suffix = os.path.splitext(name)
        #     out_path = self.video_path + '/' + filename  + suffix
        #     mfourcc = cv2.VideoWriter_fourcc(*'mp4v')
        #     dim = (w, h)
        #     writer = cv2.VideoWriter(out_path, mfourcc, mfps, dim)
        #     print(int(cap.get(7)))
        #     i = 0
        #     while cap.isOpened():
        #         success, image = cap.read()
        #         if not success:
        #             # print(i, mfps)
        #             print("Ignoring empty camera frame.")
        #             break
        #         if i < 20:
        #             writer.write(image)
        #         else:
        #             print(i, mfps)
        #             print('end')
        #             break
        #         i += 1
        pass
        # self.cal_time()
        # print(self.parent.winfo_screenwidth(), self.parent.winfo_screenheight())


    def cal_time(self):
        st = time.time()
        for i in range(self.frame_count - 1):
            self.next_image()
        et = time.time()
        print('time: ' + str(et - st))

    def on_rb1(self):
        if self.start:
            if self.gr.get() == 1:
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为张开")
            elif self.gr.get() == 2:
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为握紧")
            elif self.gr.get() == 0:
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为过渡")

    def write_path_file(self):
        with open('./path.json', 'w') as file:
            json_file = dict(input_path=self.input_path.get(), output_path=self.output_path.get(),
                             video_path=self.video_path.get())
            json.dump(json_file, file)

    def change_output_path(self):
        path = tk.filedialog.askdirectory(initialdir=self.output_path.get())
        if path != '':
            self.output_path.set(path)
            self.write_path_file()

    def change_video_path(self):
        path = tk.filedialog.askdirectory(initialdir=self.video_path.get())
        if path != '':
            self.video_path.set(path)
            self.write_path_file()
            if not os.path.exists(self.video_path.get() + '/1'):
                os.mkdir(self.video_path.get() + '/1')
            if not os.path.exists(self.video_path.get() + '/2'):
                os.mkdir(self.video_path.get() + '/2')

    def change_input_path(self):
        path = tk.filedialog.askdirectory(initialdir=self.input_path.get())
        if path != '':
            self.input_path.set(path)
            self.write_path_file()

    def select_path(self):
        if self.work_state.get() == 0:  # 标注
            path_ = tk.filedialog.askopenfilename(initialdir=self.input_path.get())
            if path_ != "":
                self.reset()
                self.videoPath = path_
                self.process_by_mediapipe()
                self.work_state_ = 0
                self.label8.config(text='该帧无landmark')

        elif self.work_state.get() == 1:  # 检查
            self.is_raw_video = tkinter.messagebox.askquestion('输入视频类型', '选择的是原始视频（非裁剪后的视频）吗？')  # 该变量仅在检查状态下生效
            if self.is_raw_video == 'yes':
                path_to_video = tk.filedialog.askopenfilename(title='选择视频', initialdir=self.input_path.get())
            else:
                path_to_video = tk.filedialog.askopenfilename(title='选择视频', initialdir=self.video_path.get() + '/1/')
            if path_to_video == '':
                return
            # json文件的地址，该变量仅在检查状态下生效
            self.path_to_json = tk.filedialog.askopenfilename(title='选择json文件', initialdir=self.output_path.get())
            if self.path_to_json == '':
                return
            # 判断所选视频和json是否对应
            _, name = os.path.split(path_to_video)
            video_name, suffix = os.path.splitext(name)
            _, name = os.path.split(self.path_to_json)
            json_name, suffix = os.path.splitext(name)
            if video_name == json_name.split('_')[0]:
                self.reset()
                self.videoPath = path_to_video
                self.process_with_annotationInfo()
                self.work_state_ = 1
                self.label8.config(text='该帧在原json中被舍弃')
            else:
                tk.messagebox.showwarning('提示', '所选视频与json不对应')

    def on_cb(self):
        if self.cb_content.get() == 1:
            self.coordinate_line()
        else:
            self.panel.delete("line")
            self.panel0.delete("coord")

    def reset_coordinate(self):
        if self.start:
            for i in range(42):
                if (i % 2) == 0:
                    self.entry_content[i].set(str(int(self.keypoint_data[self.current][i + 1] * self.image_width)))
                else:
                    self.entry_content[i].set(str(int(self.keypoint_data[self.current][i + 1] * self.image_height)))
        else:
            tk.messagebox.showwarning("提示", "先点击选择视频~")
        self.frame.focus_set()

    # 保存每一帧的关键点坐标、过渡or张开or握紧
    def save_coordinate(self):
        if self.start:
            self.keypoint_data_new[self.current][0] = self.gr.get()
            for i in range(42):
                if (i % 2) == 0:
                    temp = float(self.entry_content[i].get()) / self.image_width
                else:
                    temp = float(self.entry_content[i].get()) / self.image_height
                self.keypoint_data_new[self.current][i + 1] = temp
            self.process[self.current] = True  # 当前帧已处理
            # print("saving " + str(self.current + 1))
            return True

    def load_image(self):
        # imagePath = "./video2img/" + str(self.current + 1) + '.jpg'
        # pil_image = Image.open(imagePath)
        # pil_image = Image.fromarray(self.img[self.current][..., ::-1])  # bgr转rgb的第二种方法，不调用opencv接口
        pil_image = Image.fromarray(self.img[self.current])  # bgr转rgb的第一种方法：需要调用opencv2接口
        self.tkimg = ImageTk.PhotoImage(pil_image)
        self.panel.create_image(2, 2, image=self.tkimg, anchor="nw")
        self.set_entry_content()
        self.when_no_landmark()
        self.config_rb3()
        self.process[self.current] = False
        # self.clear_rb()
        self.rb[6].select()
        self.frame.focus_set()
        self.label1.config(text="帧序号：" + str(self.current + 1) + "/" + str(self.frame_count))

    def when_no_landmark(self):
        if self.exist[self.current]:
            self.label8.place_forget()
        else:
            self.label8.place(x=770, y=465, anchor='center')

    def config_rb3(self):
        self.rb3_value.set(0)
        if 2 < self.current < self.frame_count - 3:
            pass
        elif self.current == 0:
            self.rb3[1].config(state=tk.DISABLED)
            self.rb3[2].config(state=tk.DISABLED)
        elif self.current == 1:
            self.rb3[1].config(state=tk.DISABLED)
            self.rb3[2].config(state=tk.ACTIVE)
        elif self.current == 2:
            self.rb3[1].config(state=tk.ACTIVE)
        elif self.current == self.frame_count - 3:
            self.rb3[5].config(state=tk.ACTIVE)
        elif self.current == self.frame_count - 2:
            self.rb3[4].config(state=tk.ACTIVE)
            self.rb3[5].config(state=tk.DISABLED)
        elif self.current == self.frame_count - 1:
            self.rb3[4].config(state=tk.DISABLED)
            self.rb3[5].config(state=tk.DISABLED)

    # 点击rb3，把临近帧的关键点信息复制到该帧
    def on_rb3(self):
        if self.start:
            if self.rb3_value.get() == -3:
                for i in range(42):
                    self.entry_content[i].set(str(0))
            else:
                j = self.current + self.rb3_value.get()
                for i in range(42):
                    if (i % 2) == 0:
                        self.entry_content[i].set(str(int(self.keypoint_data_new[j][i + 1] * self.image_width)))
                    else:
                        self.entry_content[i].set(str(int(self.keypoint_data_new[j][i + 1] * self.image_height)))

    # 设置entry的值
    def set_entry_content(self):
        if not self.process[self.current]:  # 未处理过的
            temp = int(self.keypoint_data[self.current][0])
            self.rb1[temp].select()
            for i in range(42):
                if (i % 2) == 0:
                    self.entry_content[i].set(str(int(self.keypoint_data[self.current][i + 1] * self.image_width)))
                else:
                    self.entry_content[i].set(str(int(self.keypoint_data[self.current][i + 1] * self.image_height)))
        else:  # 处理过的
            temp = int(self.keypoint_data_new[self.current][0])
            self.rb1[temp].select()
            for i in range(42):
                if (i % 2) == 0:
                    self.entry_content[i].set(str(int(self.keypoint_data_new[self.current][i + 1] * self.image_width)))
                else:
                    self.entry_content[i].set(str(int(self.keypoint_data_new[self.current][i + 1] * self.image_height)))

    def callback_index(self, *args):
        if self.start:
            for i in range(21):
                self.new_show_coordinate(i)

    def callback_entry(self, var, index, mode):
        if self.start:
            temp_str = "".join(list(filter(str.isdigit, var)))
            i = int(temp_str)
            index_ = i // 2
            # print("var = " + str(var), " i = " + str(i))
            temp_cont = self.entry_content[i - 0].get()  # entry_content前面有0个tk变量
            # print("entry_content[" + str(i - 0) + "] = " + temp_cont)
            if temp_cont.replace("-", "").isdigit() and temp_cont != "":
                # print(temp_cont)
                # self.show_coordinate()
                self.new_show_coordinate(index_)

    def new_show_coordinate(self, index_):
        self.panel.delete('a' + str(index_))  # tag为纯数字识别不了- -
        temp = []
        if self.entry_content[2 * index_].get() != '':
            temp.append(float(self.entry_content[2 * index_].get()))
        else:
            return
        if self.entry_content[2 * index_ + 1].get() != '':
            temp.append(float(self.entry_content[2 * index_ + 1].get()))
        else:
            return
        color = ['red', 'green', 'yellow', 'cyan', 'pink', '']
        offset = [1, -4, -8, -12, -16]
        if index_ < 5:
            finger = 0
        else:
            finger = (index_ - 1) // 4
        self.panel.create_oval(temp[0] - self.rad, temp[1] - self.rad, temp[0] + self.rad, temp[1] + self.rad,
                               fill=color[finger], tags='a' + str(index_))
        self.panel.create_text(temp[0] + self.rad + 3.0, temp[1], text=str(index_ + offset[finger]),
                               tags='a' + str(index_))
        self.panel.tag_raise("line")

    def focus_on_current_index(self):
        if self.start:
            if not self.show:
                self.panel.delete('a' + str(self.index.get()))
                self.show = True
            else:
                self.entry_content[2 * self.index.get()].set(self.entry_content[2 * self.index.get()].get())
                self.show = False
            self.after_id = self.frame.after(600, self.focus_on_current_index)
        else:
            self.frame.after_cancel(self.after_id)
        # print(datetime.datetime.now(), self.after_id)

    # 祭奠死去的函数
    # 从entry中获取关键点坐标，并绘制坐标点
    def show_coordinate(self):
        self.panel.delete("label")
        temp_coord = [[0.0 for j in range(2)] for i in range(21)]
        j = 0
        for i in range(42):
            value = self.entry_content[i].get()
            if value == "":
                continue
            if (i % 2) == 0:
                temp_coord[j][0] = float(value)
            else:
                temp_coord[j][1] = float(value)
                j = j + 1

        # 绘制关键点， tags为label
        for i in range(5):
            self.panel.create_oval(temp_coord[i][0] - self.rad, temp_coord[i][1] - self.rad,
                                   temp_coord[i][0] + self.rad, temp_coord[i][1] + self.rad,
                                   fill="red", tags="label")
            self.panel.create_text(temp_coord[i][0] + self.rad + 3, temp_coord[i][1], text=str(i + 1),
                                   tags="label")
        for i in range(5, 9):
            self.panel.create_oval(temp_coord[i][0] - self.rad, temp_coord[i][1] - self.rad,
                                   temp_coord[i][0] + self.rad, temp_coord[i][1] + self.rad,
                                   fill="green", tags="label")
            self.panel.create_text(temp_coord[i][0] + self.rad + 3, temp_coord[i][1], text=str(i - 4),
                                   tags="label")
        for i in range(9, 13):
            self.panel.create_oval(temp_coord[i][0] - self.rad, temp_coord[i][1] - self.rad,
                                   temp_coord[i][0] + self.rad, temp_coord[i][1] + self.rad,
                                   fill="yellow", tags="label")
            self.panel.create_text(temp_coord[i][0] + self.rad + 3, temp_coord[i][1], text=str(i - 8),
                                   tags="label")
        for i in range(13, 17):
            self.panel.create_oval(temp_coord[i][0] - self.rad, temp_coord[i][1] - self.rad,
                                   temp_coord[i][0] + self.rad, temp_coord[i][1] + self.rad,
                                   fill="cyan", tags="label")
            self.panel.create_text(temp_coord[i][0] + self.rad + 3, temp_coord[i][1], text=str(i - 12),
                                   tags="label")
        for i in range(17, 21):
            self.panel.create_oval(temp_coord[i][0] - self.rad, temp_coord[i][1] - self.rad,
                                   temp_coord[i][0] + self.rad, temp_coord[i][1] + self.rad,
                                   fill="pink", tags="label")
            self.panel.create_text(temp_coord[i][0] + self.rad + 3, temp_coord[i][1], text=str(i - 16),
                                   tags="label")

        self.panel.tag_raise("line")

    def coordinate_line(self):
        # 网格线
        for i in range(7):
            self.panel.create_line(60 * i, 0, 60 * i, 680, fill="grey", tags="line")
        # self.panel.create_line(360, 0, 360, 680, fill="grey", tags="line")
        for i in range(14):
            self.panel.create_line(0, 50 * i, 360, 50 * i, fill="grey", tags="line")
        self.panel.create_line(0, 680, 360, 680, tags="line")
        self.panel0.create_line(29, 29, 409, 29, tags="coord", arrow=tk.LAST)
        self.panel0.create_line(29, 29, 29, 729, tags="coord", arrow=tk.LAST)

        # 坐标
        self.panel0.create_text(20, 20, text="0", tags="coord")
        for i in range(6):
            self.panel0.create_text(30 + 60 * (i + 1), 20, text=str(60 + 60 * i), tags="coord")
        for i in range(13):
            self.panel0.create_text(16, 30 + 50 + 50 * i, text=str(50 + 50 * i), tags="coord")
        self.panel0.create_text(16, 710, text="680", tags="coord")

    def reset(self):
        self.panel.delete("all")
        self.start = False
        self.current = 0
        self.keypoint_data_new = []
        for i in range(42):
            self.entry_list[i].delete(0, tk.END)
        self.label2.config(text="视频编号：")
        self.label1.config(text="帧序号：0/0")
        self.clear_rb()
        self.clear_rb1()
        self.label9.config(text="帧率：")
        self.label10.config(text="")
        self.label8.place_forget()
        self.detect = 'all'
        self.fail_frame = []
        self.cb1.deselect()
        # self.cb2.deselect()
        self.cb3.deselect()
        self.cb3.config(text="十秒视频起始帧：" + "未标注")
        # self.cb4.deselect()
        # self.last_gr_label = 0
        self.complex_type = []
        for i in range(11):
            self.cb5_value[i].set(0)
        self.bt5.config(text='保存输出文件和视频')
        self.gr_label = []
        self.img = []

    def jump_to(self, index_):
        if self.start:
            if not 0 < index_ <= self.frame_count:
                tk.messagebox.showwarning('提示', '请输入范围内的帧序号')
                return
            if not self.process[self.current]:
                if not self.save_coordinate():
                    return
            self.current = index_ - 1
            self.load_image()

    def next_image(self):
        if self.start:
            if not self.process[self.current]:
                if not self.save_coordinate():
                    return
            # print("cur = " + str(self.current))
            # print("count = " + str(self.frame_count))
            if (self.current + 1) < self.frame_count:
                self.current = self.current + 1
                self.load_image()
            else:
                tk.messagebox.showinfo("提示", "该视频已处理完成，请点击’保存输出文件‘按钮")
            # print(self.current + 1, self.process[self.current])
        else:
            tk.messagebox.showwarning("提示", "先点击选择视频~")

    def check(self):
        # 检查是否选择了十秒视频起始帧
        if self.cb3_value.get() == 0:
            jump = tk.messagebox.askquestion('保存失败', '还未选择十秒视频的起始帧，是否跳到第1帧')
            if jump == 'yes':
                self.jump_to(1)
            return False
        # 检查是否过一遍视频
        for i in range(self.first - 1, self.first + int(10 * self.frame_rate) - 1):
            if not self.process[i]:
                jump = tk.messagebox.askquestion('保存失败', '第' + str(i + 1) + '帧未处理，是否跳到第' + str(i + 1) + '帧')
                if jump == 'yes':
                    self.jump_to(i + 1)
                return False
        # 检查是否标注了错误的伸掌（握拳）
        flag = 0  # 1张开，2握拳
        for i in range(self.first - 1, self.first + int(10 * self.frame_rate) - 1):
            if self.keypoint_data_new[i][0] != 0:
                if self.keypoint_data_new[i][0] == flag:
                    jump = tk.messagebox.askquestion('保存失败', '在第 ' + str(self.gr_label[-1][0]) + ' 帧和第 ' +
                                                     str(i + 1) + ' 帧标注了连续的伸掌（握拳），是否跳到第' +
                                                     str(self.gr_label[-1][0]) + '帧')
                    if jump == 'yes':
                        self.jump_to(self.gr_label[-1][0])
                    return False
                else:
                    self.gr_label.append([i + 1, self.keypoint_data_new[i][0]])  # 第一项是帧序号，第二项是张开、握紧label
                    flag = self.keypoint_data_new[i][0]
        # print(self.gr_label)
        return True

    def get_json_filename(self):
        if self.work_state_ == 0:
            return self.filename
        elif self.work_state_ == 1:
            count = 0
            for item in os.listdir(self.output_path.get()):
                if self.filename in item:
                    count += 1
            return self.filename + '_v' + str(count)

    def write_json(self):
        json_name = self.get_json_filename()
        name = tk.filedialog.asksaveasfilename(title=u"保存文件", initialdir=self.output_path.get(),
                                               initialfile=json_name, filetypes=[("json", ".json")])
        if name == '':
            tk.messagebox.showwarning("提示", "未保存成功，请点击保存输出文件按钮")
            return False
        num = int(10 * self.frame_rate)
        begin = self.first
        mlabel = self.keypoint_data_new[(self.first - 1):(self.first + int(10 * self.frame_rate) - 1)]
        # 标注状态
        if self.work_state_ == 0:
            new_fail_frame = []
            for index in range(len(self.fail_frame)):
                if (self.fail_frame[index] - self.first) >= 0:
                    if self.fail_frame[index] < self.first + num:
                        new_fail_frame.append(self.fail_frame[index] - self.first + 1)
            if len(new_fail_frame) == num:
                self.detect = 'none'
            elif len(new_fail_frame) == 0:
                self.detect = 'all'
            else:
                self.detect = 'partial'
        # 检查状态
        elif self.work_state_ == 1:
            if self.is_raw_video == 'no':
                with open(self.path_to_json, 'r') as file:
                    data = json.load(file)
                begin = data['original_index']

        json_file = dict(name=self.filename, frame_num=num, frame_rate=self.frame_rate,
                         width=self.original_width, height=self.original_height,
                         original_index=begin, is_detected=self.detect,
                         has_face=self.cb5_value[1].get(), is_complex=self.complex.get(),
                         complex_type=self.complex_type,
                         label=mlabel)
        with open(name + ".json", "w") as file:
            json.dump(json_file, file)
        print("write json file successfully!")
        return True

    def generate_video(self, gType):
        if gType == 1: # 生成裁剪后的视频 1
            outpath = self.video_path.get() + '/1/' + self.filename + '.mp4'
            dim = (self.original_width, self.original_height)
            writer = cv2.VideoWriter(outpath, cv2.VideoWriter_fourcc(*'mp4v'), self.frame_rate, dim)
            # print(path, cv2.VideoWriter_fourcc(*'mp4v'), self.frame_rate, dim)
            for i in range(self.first, self.first + int(10 * self.frame_rate)):
                # print(1, i)
                # if i != self.first:
                #     keyboard.wait('d')
                # imgBGR = cv2.imread('./img2video/' + str(i) + '.jpg', cv2.COLOR_RGB2BGR)
                imgRGB = cv2.imread('./img2video/' + str(i) + '.jpg', cv2.COLOR_BGR2RGB)
                # cv2.imshow('BGR', imgBGR)
                cv2.imshow('Video1 is being generated', imgRGB)
                writer.write(imgRGB)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cv2.destroyWindow('Video1 is being generated')
            print('generate video 1 successfully!')

        elif gType == 2:  # 生成裁剪后的视频 2
            cap = cv2.VideoCapture(self.videoPath)
            outpath = self.video_path.get() + '/2/' + self.filename + '.mp4'
            dim = (self.original_width, self.original_height)
            writer2 = cv2.VideoWriter(outpath, cv2.VideoWriter_fourcc(*'mp4v'), self.frame_rate, dim)
            i = 1
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    # print("Ignoring empty camera frame.")
                    break
                if self.first <= i < self.first + int(self.frame_rate * 10):
                    # print(2, i)
                    cv2.imshow('Video2 is being generated', image)
                    writer2.write(image)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                i += 1
            cv2.destroyWindow('Video2 is being generated')
            print('generate video 2 successfully!')
        else:
            return

    def save_file(self):
        if self.start:
            if not self.save_coordinate():
                return
            if not self.check():
                return

            # 标注状态
            if self.work_state_ == 0:
                # 写入json文件
                if not self.write_json():
                    return
                # 生成十秒视频
                self.generate_video(1)
                self.generate_video(2)

            # 检查状态
            elif self.work_state_ == 1:
                with open(self.path_to_json, 'r') as file:
                    data = json.load(file)
                need_new_json = tk.messagebox.askquestion('', '是否生成新的json文件？如果目录下有同名文件，可能会覆盖原始文件')
                if need_new_json == 'yes':
                    if not self.write_json():
                        return
                # 如果更改了十秒视频起始帧，则生成新的视频
                if self.is_raw_video == 'yes':
                    if self.first != data['original_index']:
                        # tk.messagebox.showinfo('提示', '标注了新的十秒视频起始帧，将生成新的视频')
                        self.generate_video(1)
                        self.generate_video(2)

            # self.calculate_gr_count()
            self.reset()
            tk.messagebox.showinfo("提示", "json写入成功，请等待视频生成完毕后，点击选择视频按钮，处理下一个视频，辛苦啦")
        else:
            tk.messagebox.showwarning("提示", "先点击选择视频")

    def previous_image(self):
        if self.current > 0:
            if not self.process[self.current]:
                if not self.save_coordinate():
                    return
            self.current = self.current - 1
            self.load_image()
            # print(self.current + 1, self.process[self.current])
        else:
            tk.messagebox.showwarning("提示", "前面真的没有图像帧了~")

    def get_frame_rate(self, fps):
        temp = round(fps, 2)
        temp = str(int(100 * temp))
        while len(temp) < 4:
            temp = list(temp)
            temp.append('0')
            temp = ''.join(temp)
            # print(temp)
        if int(temp[3]) > 4:
            temp = int(temp) // 10
            result = (temp + 1) * 10
        else:
            result = temp
        result = float(result)
        # print('before processed: ' + str(self.frame_rate))
        # print('after processed: ' + str(round(result / 100, 1)))
        return round(result / 100, 1)

    def process_with_annotationInfo(self):
        with open(self.path_to_json, 'r') as file:
            data = json.load(file)
        cap = cv2.VideoCapture(self.videoPath)
        self.frame_count = int(cap.get(7))  # 视频总帧数
        self.frame_rate = cap.get(5)
        self.frame_rate = self.get_frame_rate(self.frame_rate)

        if self.is_raw_video == 'yes':
            self.first = data['original_index']  # first与current的对应关系：first领先current 1
            self.keypoint_data = [[0.0 for j in range(43)] for i in range(self.frame_count)]  # 原始关键点数据
            self.process = [False for i in range(self.frame_count)]
            self.exist = [False for i in range(self.frame_count)]
            j = 0
            for i in range(data['original_index'] - 1, data['original_index'] + int(10 * self.frame_rate) - 1):
                self.keypoint_data[i] = data['label'][j][:]
                j += 1
                self.exist[i] = True

            # 创建img2video文件夹。处理raw视频可能需要新生成视频
            if not os.path.exists('./img2video'):
                os.mkdir('./img2video')
            else:
                rmtree('./img2video')
                os.mkdir('./img2video')
        else:
            self.ddl = 1
            self.first = 1
            self.keypoint_data = data['label'][:]  # 原始关键点数据
            self.process = [False for i in range(data['frame_num'])]
            self.exist = [True for i in range(data['frame_num'])]

        # 将原始关键点数据深拷贝至
        for i in range(self.frame_count):
            temp = self.keypoint_data[i][:]
            self.keypoint_data_new.append(temp)

        self.bt5.config(text='保存输出文件')  # 在检查状态下，除非标注了新的十秒视频起始帧，否则不生成新的视频
        path, name = os.path.split(self.videoPath)
        self.filename, suffix = os.path.splitext(name)
        self.label2.config(text="视频编号：" + self.filename)
        self.label9.config(text="帧率：" + str(self.frame_rate))
        self.cb3_value.set(1)  # 十秒视频起始帧默认已标注
        jieshu = self.first + int(10 * self.frame_rate) - 1
        self.cb3.config(text="十秒视频起始帧：" + str(self.first) + "，结束帧：" + str(jieshu))
        self.detect = data['is_detected']
        complex_dict = {
            'a1': 0,
            'a2': 1,
            'a3': 2,
            'a4': 3,
            'b1': 4,
            'b2': 5,
            'c1': 6,
            'c2': 7,
            'd': 8,
            'e': 9,
            'f': 10
        }
        try:
            self.complex_type = data['complex_type'][:]
        except KeyError:
            self.complex_type = []
        if len(self.complex_type) == 0:
            self.complex.set(0)
        else:
            self.complex.set(1)
            for item in self.complex_type:
                self.cb5_value[complex_dict[item]].set(1)

        # 创建video2img文件夹
        # if not os.path.exists('./video2img'):
        #     os.mkdir('./video2img')
        # else:
        #     rmtree('./video2img')
        #     os.mkdir('./video2img')

        # opencv处理视频
        i = 0
        while cap.isOpened():
            success, image = cap.read()
            if not success:
                break

            dim = (self.image_width, self.image_height)
            if image.shape[0] != self.image_height or image.shape[1] != self.image_width:
                resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
                # cv2.imwrite('./video2img/' + str(i + 1) + '.jpg', resized)
                self.img.append(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
            else:
                # cv2.imwrite('./video2img/' + str(i + 1) + '.jpg', image)
                self.img.append(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            if self.is_raw_video == 'yes':
                cv2.imwrite('./img2video/' + str(i + 1) + '.jpg', image)
            if i == 0:
                self.original_height, self.original_width, c = image.shape

            cv2.namedWindow('Processing', 0)
            cv2.resizeWindow('Processing', 360, 680)
            cv2.imshow('Processing', image)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            i += 1

        if len(self.img) != self.frame_count:
            if not self.is_raw_video:
                tk.messagebox.showwarning('警告', '生成视频的总帧数有丢失')
                self.reset()
                return
            else:
                self.frame_count = len(self.img)

        if self.is_raw_video == 'yes':
            self.ddl = self.frame_count - int(10 * self.frame_rate) + 1
            if self.ddl < 1:
                tk.messagebox.showwarning('提示', '视频总帧数不够')

        cv2.destroyAllWindows()
        cap.release()
        self.start = True
        self.after_id = self.panel.after(600, self.focus_on_current_index)
        self.load_image()

    def process_by_mediapipe(self):
        # mp.solutions.drawing_utils用于绘制
        mp_drawing = mp.solutions.drawing_utils
        # 参数：1、颜色，2、线条粗细，3、点的半径
        DrawingSpec_point = mp_drawing.DrawingSpec((0, 255, 0), 1, 1)
        DrawingSpec_line = mp_drawing.DrawingSpec((0, 0, 255), 1, 1)
        # mp.solutions.hands，是人的手
        mp_hands = mp.solutions.hands
        # 参数：1、是否检测静态图片，2、手的数量，3、检测阈值，4、跟踪阈值
        hands_mode = mp_hands.Hands(max_num_hands=1)

        cap = cv2.VideoCapture(self.videoPath)
        # print(type(path), path)
        self.frame_count = int(cap.get(7))  # 视频总帧数. opencv似乎会丢掉重复的帧，因此该值不一定准确
        self.frame_rate = cap.get(5)
        self.frame_rate = self.get_frame_rate(self.frame_rate)
        self.label9.config(text="帧率：" + str(self.frame_rate))
        self.keypoint_data = [[0.0 for j in range(43)] for i in range(self.frame_count)]  # 原始关键点数据
        self.process = [False for i in range(self.frame_count)]
        self.exist = [True for i in range(self.frame_count)]
        i = 0

        # 创建video2img文件夹
        # if not os.path.exists('./video2img'):
        #     os.mkdir('./video2img')
        # else:
        #     rmtree('./video2img')
        #     os.mkdir('./video2img')

        # 创建img2video文件夹
        if not os.path.exists('./img2video'):
            os.mkdir('./img2video')
        else:
            rmtree('./img2video')
            os.mkdir('./img2video')

        while True:
            # if i != 0:
            #     keyboard.wait('d')
            success, image = cap.read()
            if not success:
                # print("Ignoring empty camera frame.")
                break

            # cv2.imwrite('./video2img/'+str(i+1)+'.jpg', image)
            # 尺寸调整为360*680
            dim = (self.image_width, self.image_height)
            if image.shape[0] != self.image_height or image.shape[1] != self.image_width:
                resized = cv2.resize(image, dim, interpolation=cv2.INTER_AREA)
                # cv2.imwrite('./video2img/' + str(i + 1) + '.jpg', resized)
                self.img.append(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB))
            else:
                # cv2.imwrite('./video2img/' + str(i + 1) + '.jpg', image)
                self.img.append(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            cv2.imwrite('./img2video/' + str(i + 1) + '.jpg', image)

            image1 = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # image2 = image.copy()

            # 处理RGB图像
            results = hands_mode.process(image1)
            i = i + 1
            # print("i = "+str(i), results.multi_hand_landmarks, test)

            self.original_height, self.original_width, c = image.shape  # get image shape
            # print(str(image_width)+" "+str(image_height))

            if results.multi_hand_landmarks == None:
                self.keypoint_data[i - 1][0] = 0  # 默认都是过度帧
                self.exist[i - 1] = False
                # tk.messagebox.showwarning("提示", "该帧无landmark，勿重置坐标点")
                self.fail_frame.append(i)
            else:
                # iterate on all detected hand landmarks
                for hand_landmarks in results.multi_hand_landmarks:
                    # we can get points using mp_hands
                    self.keypoint_data[i - 1][0] = 0  # 默认都是过度帧
                    self.keypoint_data[i - 1][1] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x, 3)
                    self.keypoint_data[i - 1][2] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y, 3)
                    self.keypoint_data[i - 1][3] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_CMC].x, 3)
                    self.keypoint_data[i - 1][4] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_CMC].y, 3)
                    self.keypoint_data[i - 1][5] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP].x, 3)
                    self.keypoint_data[i - 1][6] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP].y, 3)
                    self.keypoint_data[i - 1][7] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].x, 3)
                    self.keypoint_data[i - 1][8] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].y, 3)
                    self.keypoint_data[i - 1][9] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x, 3)
                    self.keypoint_data[i - 1][10] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y, 3)
                    self.keypoint_data[i - 1][11] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].x, 3)
                    self.keypoint_data[i - 1][12] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y, 3)
                    self.keypoint_data[i - 1][13] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].x, 3)
                    self.keypoint_data[i - 1][14] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y, 3)
                    self.keypoint_data[i - 1][15] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].x, 3)
                    self.keypoint_data[i - 1][16] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].y, 3)
                    self.keypoint_data[i - 1][17] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x, 3)
                    self.keypoint_data[i - 1][18] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y, 3)
                    self.keypoint_data[i - 1][19] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x, 3)
                    self.keypoint_data[i - 1][20] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y, 3)
                    self.keypoint_data[i - 1][21] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].x, 3)
                    self.keypoint_data[i - 1][22] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y, 3)
                    self.keypoint_data[i - 1][23] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].x, 3)
                    self.keypoint_data[i - 1][24] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].y, 3)
                    self.keypoint_data[i - 1][25] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x, 3)
                    self.keypoint_data[i - 1][26] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y, 3)
                    self.keypoint_data[i - 1][27] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].x, 3)
                    self.keypoint_data[i - 1][28] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y, 3)
                    self.keypoint_data[i - 1][29] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].x, 3)
                    self.keypoint_data[i - 1][30] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y, 3)
                    self.keypoint_data[i - 1][31] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_DIP].x, 3)
                    self.keypoint_data[i - 1][32] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_DIP].y, 3)
                    self.keypoint_data[i - 1][33] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].x, 3)
                    self.keypoint_data[i - 1][34] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y, 3)
                    self.keypoint_data[i - 1][35] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].x, 3)
                    self.keypoint_data[i - 1][36] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].y, 3)
                    self.keypoint_data[i - 1][37] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].x, 3)
                    self.keypoint_data[i - 1][38] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y, 3)
                    self.keypoint_data[i - 1][39] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_DIP].x, 3)
                    self.keypoint_data[i - 1][40] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_DIP].y, 3)
                    self.keypoint_data[i - 1][41] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].x, 3)
                    self.keypoint_data[i - 1][42] = round(
                        hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y, 3)

            # 绘制
            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    mp_drawing.draw_landmarks(
                        image, hand_landmarks, mp_hands.HAND_CONNECTIONS, DrawingSpec_point, DrawingSpec_line)

            cv2.namedWindow('Processing', 0)
            cv2.resizeWindow('Processing', 360, 680)
            cv2.imshow('Processing', image)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        if len(self.img) != self.frame_count:  # 读取视频丢帧时
            self.frame_count = len(self.img)
        self.ddl = self.frame_count - int(10 * self.frame_rate) + 1
        if self.ddl < 1:
            tk.messagebox.showwarning('提示', '视频总帧数不够')

        # 将原始关键点数据深拷贝至
        for i in range(self.frame_count):
            temp = self.keypoint_data[i][:]
            self.keypoint_data_new.append(temp)

        path, name = os.path.split(self.videoPath)
        self.filename, suffix = os.path.splitext(name)
        self.label2.config(text="视频编号：" + self.filename)
        self.cb3.config(text="十秒视频起始帧：" + "请在第 " + str(self.ddl) + ' 帧及之前标注')

        # 计算detect的值
        if len(self.fail_frame) == self.frame_count:
            self.detect = 'none'
        elif len(self.fail_frame) > 0:
            self.detect = 'partial'
        print(self.filename, 'detect: ' + self.detect, ', fail frame:', self.fail_frame)

        hands_mode.close()
        cv2.destroyAllWindows()
        cap.release()
        self.start = True
        self.after_id = self.frame.after(600, self.focus_on_current_index)
        self.load_image()


if __name__ == '__main__':
    root = tk.Tk()
    tool = LabelTool(root)
    # ctypes.windll.shcore.SetProcessDpiAwareness(1)
    root.mainloop()
