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
# from mpl_toolkits import mplot3d
# import  matplotlib.pyplot as plt
# import keyboard


class LabelTool():
    def __init__(self, master):
        self.parent = master
        self.parent.title('手部关键点自动标注微调工具软件')
        self.parent.geometry('880x820')
        # self.parent_canvas = tk.Canvas(self.parent, width=880, height=820, scrollregion=(0, 0, 880, 820))
        # self.parent_canvas.pack(fill='both', expand=True)
        self.frame = tk.Frame(self.parent)
        self.frame.pack(fill='both', expand=True)

        # self.keypoints = [tk.StringVar() for i in range(42)]  # 当前帧的关键点
        self.current = 0  # 当前帧
        self.entry_list = [tk.Entry(self.frame) for i in range(42)]
        self.entry_content = [tk.StringVar() for i in range(42)]  # 当前帧的关键点
        # vcmd = (self.frame.register(self.validate), '%P')
        for i in range(42):
            self.entry_list[i].config(textvariable=self.entry_content[i])
            # self.entry_list[i].config(validate="key", validatecommand=vcmd)
        self.start = False  # 是否开始处理视频
        self.rad = 3.0  # 关键点半径
        self.image_height = 680
        self.image_width = 360
        self.detect = 'all'  # 三种取值：all、partial、none，分别代表全部帧检测到关键点、部分帧检测到关键点、所有帧都没检测到关键点
        self.fail_frame = []  # 没检测到关键点的帧序号
        self.complex = tk.IntVar()  # 复杂场景，0代表简单场景，1代表复杂场景, 初始为简单场景
        self.complex.set(0)
        self.complex_type = []
        self.cb5_value = [tk.IntVar() for i in range(11)]
        for i in range(11):
            self.cb5_value[i].set(0)
        # self.complex_ma = tk.IntVar()  # 运动分析任务的复杂场景，0代表简单场景，1代表复杂场景, 初始为简单场景. 已弃用
        # self.complex_ma.set(0)
        # self.face = tk.IntVar()  # 0代表无人脸出现。1代表有人脸出现。 已启用，由cb5_value[1]表示
        # self.face.set(0)
        self.cb3_value = tk.IntVar()  # 是否选定初始帧，0代表未选定，1代表已选定
        self.cb3_value.set(0)
        self.first = 0  # 起始帧位置，初始为0
        self.step = 3  # 键盘控制关键点移动的步长

        # 选择哪一个关键点
        self.index = tk.IntVar()
        self.index.set(21)  # 21代表没有选中
        self.rb = [tk.Radiobutton(self.frame, text="", value=i, font=100, variable=self.index
                                  , command=self.frame.focus_set) for i in range(22)]

        # 标注张开和握拳
        self.gr = tk.IntVar()
        self.gr.set(3)  # 0代表过渡帧(默认)，1代表张开，2代表握紧，3代表没有选中
        # self.last_gr_label = 0  # 初始为0，1代表上一次标注为张开，2代表上一次标注为握紧。该值的目的是防止连续两次标注为张开或握紧
        rb1_text = ["过渡帧", "伸掌起始帧", "握拳起始帧", ""]
        self.rb1 = [tk.Radiobutton(self.frame, text=rb1_text[i], value=i, variable=self.gr, font=1,
                                   indicatoron=True, command=self.show_tip) for i in range(4)]
        for i in range(3):
            self.rb1[i].place(x=470, y=650 + 35 * i)
            # self.rb1[i].pack()

        # 布局
        # 第一部分
        j = 0
        for i in range(0, 10):
            self.entry_list[i].place(x=520 + 80 * (i % 2), y=80 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=470, y=80+20*i)
                j += 1
                la = tk.Label(self.frame, text=str(j), bg="red")
                la.place(x=495, y=80+20*i)
        # 第二部分
        # j = 5
        for i in range(10, 18):
            self.entry_list[i].place(x=520 + 80 * (i % 2), y=91 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=470, y=91+20*i)
                j += 1
                la = tk.Label(self.frame, text=str(j-5), bg="green")
                la.place(x=495, y=91+20*i)
        # 第三部分
        # j = 9
        for i in range(18, 26):
            self.entry_list[i].place(x=520 + 80 * (i % 2), y=102 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=470, y=102 + 20 * i)
                j += 1
                la = tk.Label(self.frame, text=str(j-9), bg="yellow")
                la.place(x=495, y=102 + 20 * i)
        # 第四部分
        # j = 13
        for i in range(26, 34):
            self.entry_list[i].place(x=720 + 80 * (i % 2), y=0 - 440 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=675, y=0-440+20*i)
                j += 1
                la = tk.Label(self.frame, text=str(j-13), bg="cyan")
                la.place(x=700, y=0-440+20*i)
        # 第五部分
        # j = 17
        for i in range(34, 42):
            self.entry_list[i].place(x=720 + 80 * (i % 2), y=-390 + 20 * (i - (i % 2)), width=60, height=16)
            if (i % 2) == 0:
                self.rb[j].place(x=675, y=0-390+20*i)
                j += 1
                la = tk.Label(self.frame, text=str(j-17), bg="pink")
                la.place(x=700, y=0-390+20*i)

        self.videoPath = tk.StringVar()
        self.bt = tk.Button(self.frame, text="更改json输出路径", command=self.change_output_path)
        self.bt.place(x=710, y=730, width=140, height=31)
        self.bt0 = tk.Button(self.frame, text="选择视频", command=self.select_path)
        self.bt0.place(x=710, y=450, width=140, height=31)
        self.bt1 = tk.Button(self.frame, text="test", command=self.mytest)
        # self.bt1.place(x=710, y=610, width=140, height=31)
        self.bt2 = tk.Button(self.frame, text="重置当前帧坐标", command=self.reset_coordinate)
        self.bt2.place(x=710, y=490, width=140, height=31)
        self.bt3 = tk.Button(self.frame, text="上一帧图像", command=self.previous_image)
        self.bt3.place(x=710, y=530, width=140, height=31)
        self.bt4 = tk.Button(self.frame, text="下一帧图像", command=self.next_image)
        self.bt4.place(x=710, y=570, width=140, height=31)
        self.bt5 = tk.Button(self.frame, text="保存输出文件和视频", command=self.save_file)
        self.bt5.place(x=710, y=650, width=140, height=31)
        # self.bt6 = tk.Button(self.frame, text="使用说明", command=self.info)
        # self.bt6.place(x=810, y=12, width=58, height=30)
        self.bt7 = tk.Button(self.frame, text="更改默认输入路径", command=self.change_input_path)
        self.bt7.place(x=710, y=770, width=140, height=31)
        self.bt8 = tk.Button(self.frame, text='更改视频输出路径', command=self.change_video_path)
        self.bt8.place(x=710, y=690, width=140, height=31)

        self.label1 = tk.Label(self.frame, font=200, text="帧序号：" + "0/0")
        self.label1.place(x=240, y=5)
        self.label2 = tk.Label(self.frame, font=200, text="视频编号：")
        self.label2.place(x=20, y=5)
        self.label3 = tk.Label(self.frame, font=200)
        # self.label3.place(x=20, y=30)
        # self.label4 = tk.Label(self.frame, font=200, text="横坐标")
        # self.label4.place(x=515, y=52)
        # self.label5 = tk.Label(self.frame, font=200, text="纵坐标")
        # self.label5.place(x=595, y=52)
        # self.label6 = tk.Label(self.frame, font=200, text="横坐标")
        # self.label6.place(x=715, y=52)
        # self.label7 = tk.Label(self.frame, font=200, text="纵坐标")
        # self.label7.place(x=795, y=52)
        self.label8 = tk.Label(self.frame, font=150, text="该帧无landmark,勿重置坐标", background="red")
        # self.label8.place(x=450, y=690)
        # self.label8.place_forget()
        self.label9 = tk.Label(self.frame, font=200, text="帧率：")
        self.label9.place(x=440, y=5)
        self.label10 = tk.Label(self.frame, font=200, text="")
        self.label10.place(x=470, y=620)

        self.panel0 = tk.Canvas(self.frame, bg="lightgrey", height=740, width=420)
        self.panel0.place(x=20, y=60, anchor="nw")
        self.panel = tk.Canvas(self.frame, bg="lightgrey", height=680, width=360)
        self.panel.place(x=50, y=90, anchor="nw")
        self.panel.bind("<Button-1>", self.on_click)
        self.frame.bind("<KeyPress>", self.on_keyboard)
        self.frame.bind("<Button-1>", self.focus_on_frame)
        self.frame.focus_set()

        self.cb_content = tk.IntVar()
        self.cb = tk.Checkbutton(self.frame, text="辅助网格线", font=200, variable=self.cb_content,
                                 command=self.on_checkbutton)
        self.cb.place(x=470, y=770)
        self.cb1 = tk.Checkbutton(self.frame, text="复杂场景", font=200, variable=self.complex,
                                  command=self.create_complex_window)
        self.cb1.place(x=750, y=12)
        # self.cb2 = tk.Checkbutton(self.frame, text="人脸", font=200, variable=self.cb5_value[1])
        # self.cb2.place(x=765, y=32)
        self.cb3 = tk.Checkbutton(self.frame, text="十秒视频起始帧：" + "未标注",
                                  font=200, variable=self.cb3_value, command=self.on_cb3)
        self.cb3.place(x=20, y=30)
        # self.cb4 = tk.Checkbutton(self.frame, text='复杂场景（运动分析）', font=200, variable=self.complex_ma)
        # self.cb4.place(x=655, y=5)

        # 创建scrollbar，有bug
        # self.sb = tk.Scrollbar(self.frame)
        # self.sb.pack(side='right', fill='y')
        # self.sb.config(command=self.parent_canvas.yview)
        # self.parent_canvas.config(yscrollcommand=self.sb.set)
        # self.parent_canvas.create_window(0, 0, window=self.frame)

        # 创建默认文件夹和path.json
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
            self.output_path = json_file['output_path']
            self.input_path = json_file['input_path']
            self.video_path = json_file['video_path']
        self.label3.config(text="默认输出路径：" + self.output_path)

    def calculate_gr_count(self):
        gt = len(self.gr_label) // 2
        d = []
        t = []
        zuida = 0
        zuixiao = 10000
        for i in range(self.first - 1, self.first + int(10 * self.frame_rate) - 1):
            temp = math.sqrt(math.pow(self.keypoint_data_new[i][1] * self.oringinal_width -
                                      self.keypoint_data_new[i][17] * self.oringinal_width, 2) +
                             math.pow(self.keypoint_data_new[i][2] * self.oringinal_hight -
                                      self.keypoint_data_new[i][18] * self.oringinal_hight, 2))
            d.append(temp)
            # t.append(self.keypoint_data[i][0])
            if temp > zuida:
                zuida = temp
            if temp < zuixiao:
                zuixiao = temp
            # print("dis[" + str(t[i]) + "] = " + str(d[i]))
        mean = (zuida + zuixiao) / 2
        count = 0
        for i in range(self.frame_count - 1):  # 所有帧
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
        print('complex: ', self.complex.get(), 'complex_type: ', self.complex_type)

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
            cb5[i].place(x=40, y=40+30*i)
        tk.Label(top, text=label_text[1], font=1).place(x=10, y=170)
        for i in range(2):
            cb5[i + 4].place(x=40, y=200+30*i)
        tk.Label(top, text=label_text[2], font=1).place(x=10, y=270)
        for i in range(2):
            cb5[i + 6].place(x=40, y=300+30*i)
        for i in range(3):
            cb5[i + 8].place(x=10, y=370+40*i)

    def clear_radiobutton(self):
        # self.rb[self.index.get()].deselect()
        self.rb[21].select()
        # print(self.index.get())

    def on_cb3(self):
        if self.start:
            if self.cb3_value.get() == 1:
                self.first = self.current + 1
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
            i = self.index.get()
            if i != 21:
                if event.keycode == 65 or event.keycode == 37:
                    self.entry_content[2 * i].set(str(int(self.entry_content[2 * i].get()) - self.step))
                elif event.keycode == 87 or event.keycode == 38:
                    self.entry_content[2 * i + 1].set(str(int(self.entry_content[2 * i + 1].get()) - self.step))
                elif event.keycode == 83 or event.keycode == 40:
                    self.entry_content[2 * i + 1].set(str(int(self.entry_content[2 * i + 1].get()) + self.step))
                elif event.keycode == 68 or event.keycode == 39:
                    self.entry_content[2 * i].set(str(int(self.entry_content[2 * i].get()) + self.step))

    # 响应鼠标点击
    def on_click(self, event):
        if self.start:
            i = self.index.get()
            if i != 21:
                # print(self.index.get(), type(event.x), event.y)
                self.entry_content[2 * i].set(event.x)
                self.entry_content[2 * i + 1].set(event.y)
                # self.show_coordinate()

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
        #         x[j + 1].append(self.keypoint_data[i][11 + j * 2] * self.oringinal_width)
        #         y[j + 1].append(self.keypoint_data[i][12 + j * 2] * self.oringinal_hight)
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
        #     temp = math.sqrt(math.pow(self.keypoint_data[i][1] * self.oringinal_width -
        #                               self.keypoint_data[i][17] * self.oringinal_width, 2) +
        #                      math.pow(self.keypoint_data[i][2] * self.oringinal_hight -
        #                               self.keypoint_data[i][18] * self.oringinal_hight, 2))
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


        path = tk.filedialog.askopenfilename()
        if path != '':
            cap = cv2.VideoCapture(path)
            mfps = cap.get(5)
            print(mfps)
            mfps = self.process_frame_rate(mfps)
            print(mfps)
            w = int(cap.get(3))
            h = int(cap.get(4))
            path, name = os.path.split(path)
            filename, suffix = os.path.splitext(name)
            out_path = self.video_path + '/' + filename  + suffix
            mfourcc = cv2.VideoWriter_fourcc(*'mp4v')
            dim = (w, h)
            writer = cv2.VideoWriter(out_path, mfourcc, mfps, dim)
            print(int(cap.get(7)))
            i = 0
            while cap.isOpened():
                success, image = cap.read()
                if not success:
                    # print(i, mfps)
                    print("Ignoring empty camera frame.")
                    break
                if i < 20:
                    writer.write(image)
                else:
                    print(i, mfps)
                    print('end')
                    break
                i += 1
        pass

    def info(self):
        tk.messagebox.showinfo("帮助", "重要提示：\n"
                                     "软件的所在目录的路径不可以存在中文字符，否则软件无法正常工作。\n"
                                     "解决方法：把包含软件的文件夹移动至不存在中文字符的目录，点击”生成快捷方式.bat“。\n\n"
                                     "软件使用帮助：\n"
                                     "第一步：点击选择视频按钮，选择要处理的视频。\n"
                                     "第二步：通过修改坐标值修改相应的关键点坐标信息。\n"
                                     "第三步：处理完一帧后，点击下一帧图像，软件会自动保存该帧信息。\n"
                                     "第四步：处理完所有帧，点击保存输出文件按钮，可以修改输出路径和文件名。\n\n"
                                     "其他：\n"
                                     "默认输出文件名为视频编号.json，默认输出路径为 C:\labeltool\output \n "
                                     "可通过更改默认输出路径按钮修改默认输出路径，也可以在保存输出文件时指定。\n"
                                     "一个视频处理完后，可点击选择视频开始处理下一视频。\n"
                                     "辛苦啦~")

    # 错误case1：一个帧内标注一次握紧，再标注为过渡，last_gr_label会设置为2
    # 错误case2：一个帧内标注一次握紧，，再标注为过渡，再标注为握紧，last_gr_label会设置为2
    def show_tip(self):
        if self.start:
            if self.gr.get() == 1:
                # if self.gr.get() != self.last_gr_label:
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为张开")
                #     self.last_gr_label = 1
                # else:
                #     tk.messagebox.showwarning('警告', '标注错误：连续标注两个伸掌起始帧，请检查之前的标注')
                #     self.rb1[0].select()
            elif self.gr.get() == 2:
                # if self.gr.get() != self.last_gr_label:
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为握紧")
                #     self.last_gr_label = 2
                # else:
                #     tk.messagebox.showwarning('警告', '标注错误：连续标注两个握拳起始帧，请检查之前的标注')
                #     self.rb1[0].select()
            elif self.gr.get() == 0:
                self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为过渡")
                pass

    def write_path_file(self):
        with open('./path.json', 'w') as file:
            json_file = dict(input_path=self.input_path, output_path=self.output_path, video_path=self.video_path)
            json.dump(json_file, file)

    def change_output_path(self):
        path = tk.filedialog.askdirectory(initialdir=self.output_path)
        if path != '':
            self.output_path = path
            self.label3.config(text="默认输出路径：" + self.output_path)
            self.write_path_file()

    def change_video_path(self):
        path = tk.filedialog.askdirectory(initialdir=self.video_path)
        if path != '':
            self.video_path = path
            self.write_path_file()
            if not os.path.exists(self.video_path + '/1'):
                os.mkdir(self.video_path + '/1')
            if not os.path.exists(self.video_path + '/2'):
                os.mkdir(self.video_path + '/2')

    def change_input_path(self):
        path = tk.filedialog.askdirectory(initialdir=self.input_path)
        if path != '':
            self.input_path = path
            self.write_path_file()

    def select_path(self):
        # if not self.start:
        path_ = tk.filedialog.askopenfilename(initialdir=self.input_path)
        # 通过replace函数替换绝对文件地址中的/来使文件可被程序读取
        # 注意：\\转义后为\，所以\\\\转义后为\\
        # print("path_ = " + path_)
        # path_ = path_.replace("/", "\\")
        if path_ != "":
            self.reset()
            self.videoPath.set(path_)
            # print(self.videoPath.get())
            self.video_test(self.videoPath.get())
        else:
            pass
            # tk.messagebox.showwarning("提示", "该视频还没处理完")

    def on_checkbutton(self):
        if self.cb_content.get() == 1:
            self.coordinate_line()
        else:
            self.panel.delete("line")
            self.panel0.delete("coord")

    def callback_test(self, var, index, mode):
        if self.start:
            temp_str = "".join(list(filter(str.isdigit, var)))
            i = int(temp_str)
            # print("var = " + str(var))
            # print("i = " + str(i))
            temp_cont = self.entry_content[i].get()
            # print("entry_content[" + str(i) + "] = " + temp_cont)
            if temp_cont.replace("-", "").isdigit() and temp_cont != "":
                # print("show")
                # print(temp_cont)
                self.show_coordinate()

    def reset_coordinate(self):
        if self.start:
            for i in range(42):
                if (i % 2) == 0:
                    self.entry_content[i].set(str(int(self.keypoint_data[self.current][i + 1] * self.image_width)))
                else:
                    self.entry_content[i].set(str(int(self.keypoint_data[self.current][i + 1] * self.image_height)))
            self.show_coordinate()
        else:
            tk.messagebox.showwarning("提示", "先点击选择视频~")
        self.frame.focus_set()

    # 保存每一帧的关键点坐标、过渡or张开or握紧
    def save_coordinate(self):
        if self.start:
            # bug：连续点击上一帧
            # if self.gr.get() == 1 or self.gr.get() == 2:
            #     for i in range(self.current):
            #         if self.keypoint_data_new[self.current - 1 - i][0] != 0:
            #             self.last_gr_label = self.keypoint_data_new[self.current - 1 - i][0]
            #             print('last_gr_label:', self.last_gr_label)
            #             break
            #     if self.last_gr_label != self.gr.get():
            #         self.keypoint_data_new[self.current][0] = self.gr.get()
            #         if self.gr.get() == 1:
            #             self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为张开")
            #         else:
            #             self.label10.config(text="最近标注第" + str(self.current + 1) + "帧为握紧")
            #     else:
            #         if self.gr.get() == 1:
            #             tk.messagebox.showwarning('警告', '连续标注两个伸掌起始帧，请检查之前的标注')
            #         else:
            #             tk.messagebox.showwarning('警告', '连续标注两个握拳起始帧，请检查之前的标注')
            #         return False

            self.keypoint_data_new[self.current][0] = self.gr.get()
            for i in range(42):
                if (i % 2) == 0:
                    temp = float(self.entry_content[i].get()) / self.image_width
                else:
                    temp = float(self.entry_content[i].get()) / self.image_height
                self.keypoint_data_new[self.current][i + 1] = temp
            self.process[self.current] = True  # 当前帧已处理
            print("saving " + str(self.current + 1))
            return True


    def load_image(self):
        imagePath = "./video2img/" + str(self.current + 1) + '.jpg'
        pil_image = Image.open(imagePath)
        self.tkimg = ImageTk.PhotoImage(pil_image)
        self.panel.create_image(2, 2, image=self.tkimg, anchor="nw")
        self.set_entry_content()
        self.show_coordinate()
        self.process[self.current] = False
        self.clear_radiobutton()
        if self.exist[self.current]:
            self.label8.place_forget()
        else:
            self.label8.place(x=440, y=35)
        self.frame.focus_set()

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
                if(i % 2) == 0:
                    self.entry_content[i].set(str(int(self.keypoint_data_new[self.current][i + 1] * self.image_width)))
                else:
                    self.entry_content[i].set(str(int(self.keypoint_data_new[self.current][i + 1] * self.image_height)))

    # 从entry中获取关键点坐标，并绘制坐标点
    def show_coordinate(self):
        self.panel.delete("label")
        temp_coord = [[0.0 for j in range(2)] for i in range(21)]
        j = 0
        for i in range(42):
            value = self.entry_content[i].get()
            if value == "":
                continue
            if(i % 2) == 0:
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

        # 帧数label
        self.label1.config(text="帧序号：" + str(self.current + 1) + "/" + str(self.frame_count))

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
        for i in range(42):
            self.entry_list[i].delete(0, tk.END)
        self.label2.config(text="视频编号：")
        self.label1.config(text="帧序号：0/0")
        self.clear_radiobutton()
        self.clear_rb1()
        self.label9.config(text="帧率：")
        self.label10.config(text="")
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
        if self.cb3_value.get() == 0:
            tk.messagebox.showwarning('提示', '还未选择十秒视频的起始帧')
            return False
        flag = 0  # 1张开，2握拳
        self.gr_label = []
        for i in range(self.frame_count):
            if self.keypoint_data_new[i][0] != 0:
                if self.keypoint_data_new[i][0] == flag:
                    tk.messagebox.showwarning('警告', '在第 ' + str(self.gr_label[-1][0]) + ' 帧和第 '
                                              + str(i + 1) + ' 帧标注了连续的伸掌（握拳），请修正后再点击保存按钮')
                    return False
                else:
                    self.gr_label.append([i + 1, self.keypoint_data_new[i][0]])  # 第一项是帧序号，第二项是张开、握紧label
                    flag = self.keypoint_data_new[i][0]
        # print(self.gr_label)
        return True

    def save_file(self):
        if self.start:
            if self.current + 1 >= self.first + int(10 * self.frame_rate) - 1:
                if not self.save_coordinate():
                    return
                if not self.check():
                    return

                # 写入json文件
                name = tk.filedialog.asksaveasfilename(title=u"保存文件", initialdir=self.output_path,
                                                       initialfile=self.filename, filetypes=[("json", ".json")])
                if name == '':
                    tk.messagebox.showwarning("提示", "未保存成功，请点击保存输出文件按钮")
                    return
                num = int(10 * self.frame_rate)
                # mlabel = [[0.0 for j in range(43)] for i in range(num)]
                mlabel = self.keypoint_data_new[(self.first - 1):(self.first + int(10 * self.frame_rate) - 1)]
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
                json_file = dict(name=self.filename, frame_num=num, frame_rate=self.frame_rate,
                                 width=self.oringinal_width, height=self.oringinal_hight,
                                 original_index=self.first, is_detected=self.detect,
                                 has_face=self.cb5_value[1].get(), is_complex=self.complex.get(),
                                 complex_type=self.complex_type,
                                 label=mlabel)
                with open(name + ".json", "w") as file:
                    json.dump(json_file, file)
                print("write json file success 2")

                # 生成裁剪后的视频 1
                path = self.video_path + '/1/' + self.filename + '.mp4'
                dim = (self.oringinal_width, self.oringinal_hight)
                writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), self.frame_rate, dim)
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
                cv2.destroyAllWindows()

                # 生成裁剪后的视频 2
                cap = cv2.VideoCapture(self.videoPath.get())
                path = self.video_path + '/2/' + self.filename + '.mp4'
                writer2 = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), self.frame_rate, dim)
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
                cv2.destroyAllWindows()

                self.calculate_gr_count()
                self.reset()
                tk.messagebox.showinfo("提示", "该视频已处理完成，点击选择视频按钮，处理下一个视频，辛苦啦")
            else:
                tk.messagebox.showwarning("提示", "还没到最后一帧~")
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

    def process_frame_rate(self, fps):
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

    def video_test(self, path):
        # mp.solutions.drawing_utils用于绘制
        mp_drawing = mp.solutions.drawing_utils

        # 参数：1、颜色，2、线条粗细，3、点的半径
        DrawingSpec_point = mp_drawing.DrawingSpec((0, 255, 0), 1, 1)
        DrawingSpec_line = mp_drawing.DrawingSpec((0, 0, 255), 1, 1)

        # mp.solutions.hands，是人的手
        mp_hands = mp.solutions.hands

        # 参数：1、是否检测静态图片，2、手的数量，3、检测阈值，4、跟踪阈值
        hands_mode = mp_hands.Hands(max_num_hands=1)

        cap = cv2.VideoCapture(path)
        # print(type(path), path)
        self.frame_count = int(cap.get(7))  # 视频总帧数
        self.frame_rate = cap.get(5)
        self.frame_rate = self.process_frame_rate(self.frame_rate)
        self.ddl = self.frame_count - int(10 * self.frame_rate) + 1
        if self.ddl < 1:
            tk.messagebox.showwarning('提示', '视频总帧数不够')
            # return
        self.label9.config(text="帧率：" + str(self.frame_rate))
        self.keypoint_data = [[0.0 for j in range(43)] for i in range(self.frame_count)]  # 原始关键点数据
        self.keypoint_data_new = [[0 for j in range(43)] for i in range(self.frame_count)]  # 新关键点数据
        self.process = [False for i in range(self.frame_count)]
        self.exist = [True for i in range(self.frame_count)]
        i = 0

        # 创建video2img文件夹
        if not os.path.exists('./video2img'):
            os.mkdir('./video2img')
        else:
            rmtree('./video2img')
            os.mkdir('./video2img')

        # 创建video2img文件夹
        if not os.path.exists('./img2video'):
            os.mkdir('./img2video')
        else:
            rmtree('./img2video')
            os.mkdir('./img2video')

        while cap.isOpened():
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
                cv2.imwrite('./video2img/' + str(i + 1) + '.jpg', resized)
                # print("resizing index: " + str(i + 1))
            else:
                cv2.imwrite('./video2img/' + str(i + 1) + '.jpg', image)
                # print("original index: " + str(i + 1))

            cv2.imwrite('./img2video/' + str(i + 1) + '.jpg', image)

            image1 = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # image2 = image.copy()

            # 处理RGB图像
            results = hands_mode.process(image1)
            i = i + 1
            # print("i = "+str(i), results.multi_hand_landmarks, test)

            self.oringinal_hight, self.oringinal_width, c = image.shape  # get image shape
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
                    self.keypoint_data[i - 1][1] = round(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].x, 3)
                    self.keypoint_data[i - 1][2] = round(hand_landmarks.landmark[mp_hands.HandLandmark.WRIST].y, 3)
                    self.keypoint_data[i - 1][3] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_CMC].x, 3)
                    self.keypoint_data[i - 1][4] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_CMC].y, 3)
                    self.keypoint_data[i - 1][5] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP].x, 3)
                    self.keypoint_data[i - 1][6] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_MCP].y, 3)
                    self.keypoint_data[i - 1][7] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].x, 3)
                    self.keypoint_data[i - 1][8] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_IP].y, 3)
                    self.keypoint_data[i - 1][9] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x, 3)
                    self.keypoint_data[i - 1][10] = round(hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].y, 3)
                    self.keypoint_data[i - 1][11] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].x, 3)
                    self.keypoint_data[i - 1][12] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_MCP].y, 3)
                    self.keypoint_data[i - 1][13] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].x, 3)
                    self.keypoint_data[i - 1][14] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_PIP].y, 3)
                    self.keypoint_data[i - 1][15] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].x, 3)
                    self.keypoint_data[i - 1][16] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_DIP].y, 3)
                    self.keypoint_data[i - 1][17] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].x, 3)
                    self.keypoint_data[i - 1][18] = round(hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP].y, 3)
                    self.keypoint_data[i - 1][19] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].x, 3)
                    self.keypoint_data[i - 1][20] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_MCP].y, 3)
                    self.keypoint_data[i - 1][21] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].x, 3)
                    self.keypoint_data[i - 1][22] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_PIP].y, 3)
                    self.keypoint_data[i - 1][23] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].x, 3)
                    self.keypoint_data[i - 1][24] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_DIP].y, 3)
                    self.keypoint_data[i - 1][25] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].x, 3)
                    self.keypoint_data[i - 1][26] = round(hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP].y, 3)
                    self.keypoint_data[i - 1][27] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].x, 3)
                    self.keypoint_data[i - 1][28] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_MCP].y, 3)
                    self.keypoint_data[i - 1][29] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].x, 3)
                    self.keypoint_data[i - 1][30] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_PIP].y, 3)
                    self.keypoint_data[i - 1][31] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_DIP].x, 3)
                    self.keypoint_data[i - 1][32] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_DIP].y, 3)
                    self.keypoint_data[i - 1][33] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].x, 3)
                    self.keypoint_data[i - 1][34] = round(hand_landmarks.landmark[mp_hands.HandLandmark.RING_FINGER_TIP].y, 3)
                    self.keypoint_data[i - 1][35] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].x, 3)
                    self.keypoint_data[i - 1][36] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_MCP].y, 3)
                    self.keypoint_data[i - 1][37] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].x, 3)
                    self.keypoint_data[i - 1][38] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_PIP].y, 3)
                    self.keypoint_data[i - 1][39] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_DIP].x, 3)
                    self.keypoint_data[i - 1][40] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_DIP].y, 3)
                    self.keypoint_data[i - 1][41] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].x, 3)
                    self.keypoint_data[i - 1][42] = round(hand_landmarks.landmark[mp_hands.HandLandmark.PINKY_TIP].y, 3)

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

        # 计算detect的值
        if len(self.fail_frame) == self.frame_count:
            self.detect = 'none'
        elif len(self.fail_frame) > 0:
            self.detect = 'partial'
        print('detect: ', self.detect, ', fail frame: ', self.fail_frame)
        hands_mode.close()
        cv2.destroyAllWindows()
        cap.release()
        self.start = True
        self.load_image()

        path, name = os.path.split(self.videoPath.get())
        self.filename, suffix = os.path.splitext(name)
        self.label2.config(text="视频编号：" + self.filename)
        self.cb3.config(text="十秒视频起始帧：" + "请在第 " + str(self.ddl) + ' 帧及之前标注')

        # entry绑定回调函数
        for i in range(42):
            # self.entry_content[i].trace_variable("w", lambda var, index, mode: self.callback_test(var=0, index=i, mode=0))
            self.entry_content[i].trace_variable("w", self.callback_test)

if __name__ == '__main__':
    root = tk.Tk()
    tool = LabelTool(root)
    root.mainloop()



