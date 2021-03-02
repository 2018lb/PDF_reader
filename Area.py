from PyQt5.QtWidgets import QScrollArea, QShortcut, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMenu
from PyQt5.QtCore import QObject , pyqtSignal
import dlib
import cv2
import numpy as np
import tensorflow as tf
import cv2 as cv
import math


class MyArea(QScrollArea):
    cap = 0
    # 判断摄像头是否打开
    camera_on = False
    book = 0;

    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget = parent
        self.initUi()
        self.setAlignment(Qt.AlignCenter)
        # self inherit QWidget
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.custom_right_menu)

    def initUi(self):
        self.init_action()

    def init_action(self):
        zoom_minus = QShortcut(QKeySequence("Ctrl+-"), self)
        zoom_minus.activated.connect(self.minus)
        zoom_plus = QShortcut(QKeySequence("Ctrl+="), self)
        zoom_plus.activated.connect(self.plus)

        switch_left_ = QShortcut(QKeySequence("←"), self)
        switch_left_.activated.connect(self.left)

        switch_left = QShortcut(QKeySequence(Qt.Key_Left), self)
        switch_left.activated.connect(self.left)

        switch_right_ = QShortcut(QKeySequence("→"), self)
        switch_right_.activated.connect(self.plus)

        switch_right = QShortcut(QKeySequence(Qt.Key_Right), self)
        switch_right.activated.connect(self.right)

    def sebook(s1):
        book = s1;

    # 鼠标左键翻页
    def mousePressEvent(self, event):
        pos = event.pos().x()
        width = self.size().width()
        if event.button() == Qt.LeftButton:
            if pos > width * 2 / 3:
                self.right()
            elif pos < width / 3:
                self.left()
        # 眼睛翻页
        # self.vedio()

    # 右键菜单
    def custom_right_menu(self, pos):
        menu = QMenu()
        opt1 = menu.addAction("放大图片（Ctrl+-）")
        opt2 = menu.addAction("缩小图片（Ctrl+=）")
        opt3 = menu.addAction("上一页（←）")
        opt4 = menu.addAction("下一页（→）")
        opt5 = menu.addAction("开启眼动翻页")
        opt6 = menu.addAction("关闭眼动翻页（关闭窗口）")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == opt1:
            self.plus()
            return
        elif action == opt2:
            self.minus()
            return
        elif action == opt3:
            self.left()
            return
        elif action == opt4:
            self.right()
            return
        elif action == opt5:
            self.vedio()
        elif action == opt6:
            self.shutdown_vedio()
        else:
            return

    # 放大
    def plus(self):
        self.widget.zoom_book(plus=True)

    # 缩小
    def minus(self):
        self.widget.zoom_book(plus=False)

    # 下一页
    def right(self):
        self.widget.switch_page(right=True)

    # 前一页
    def left(self):
        self.widget.switch_page(right=False)

    def Gpu(self):
        gpus = tf.config.experimental.list_physical_devices('GPU')
        if gpus:
            try:
                # 设置GPU 显存占用为按需分配
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                logical_gpus = tf.config.experimental.list_logical_devices('GPU')
                print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
            except RuntimeError as e:
                # 异常处理
                print(e)

    # 开启眼动翻页
    def vedio(self):
        # 若眼动翻页以打开则跳过
        if self.camera_on:
            return
        self.camera_on = True

        self.Gpu()
        detector = dlib.get_frontal_face_detector()
        predictor_path = r'shape_predictor_68_face_landmarks.dat'

        predictor = dlib.shape_predictor(predictor_path)

        network = tf.keras.models.load_model('final2.h5')

        # 创建 cv2 摄像头对象e
        # cap = cv2.VideoCapture(0)
        self.cap = cv2.VideoCapture(0)

        # 设置视频参数，propId 设置的视频参数，value 设置的参数值
        self.cap.set(3, 1920)
        self.cap.set(4, 1080)

        kk = 0

        times = 0
        last_sum_result = 5
        last_result = 0
        clock = 1
        final_result = 0

        while self.cap.isOpened():
            flag, img_rd = self.cap.read()
            #img_rd = img_rd[60:400, 60:580]

            # 每帧数据延时 1ms，延时为 0 读取的是静态帧
            k = cv2.waitKey(1)

            # 取灰度
            img_gray = cv2.cvtColor(img_rd, cv2.COLOR_RGB2GRAY)

            # 人脸数
            faces = detector(img_gray, 0)

            # 待会要写的字体
            font = cv2.FONT_HERSHEY_SIMPLEX

            max_area = 0
            max_face = 0
            # 检测到人脸
            if len(faces) > 0:
                # 记录每次开始写入人脸像素的宽度位置
                for k, face in enumerate(faces):
                    height = face.bottom() - face.top()
                    width = face.right() - face.left()
                    area = height * width
                    if (area > max_area):
                        max_area = area
                        max_face = face

                face = max_face
                # 绘制脸部矩形框
                cv2.rectangle(img_rd, tuple([face.left(), face.top()]), tuple([face.right(), face.bottom()]),
                              (0, 255, 255), 2)

                height = face.bottom() - face.top()
                width = face.right() - face.left()

                if (face.bottom() < 340) and (face.right() < 520) and \
                        ((face.top() + height) < 340) and ((face.left() + width) < 520):

                    if (clock == 1):
                        clock_res = 'Unlocked'
                    else:
                        clock_res = 'Locked'

                    # 识别人脸特征
                    shape = predictor(img_rd, face)

                    mid_left_x = math.ceil((shape.part(37).x + shape.part(40).x) / 2)
                    mid_left_y = math.ceil((shape.part(37).y + shape.part(40).y) / 2)
                    mid_right_x = math.ceil((shape.part(43).x + shape.part(46).x) / 2)
                    mid_right_y = math.ceil((shape.part(43).y + shape.part(46).y) / 2)

                    if (mid_left_x > 20) and (mid_left_y > 12) and \
                            (mid_right_x < 500) and (mid_right_y > 12):

                        right_eye = np.zeros((24, 40, 3), np.uint8)
                        left_eye = np.zeros((24, 40, 3), np.uint8)
                        for i in range(24):
                            for j in range(40):
                                right_eye[i][j] = img_rd[mid_right_y - 12 + i][mid_right_x - 20 + j]
                        for i in range(24):
                            for j in range(40):
                                left_eye[i][j] = img_rd[mid_left_y - 12 + i][mid_left_x - 20 + j]


                        #绘制眼睛矩形框
                        cv2.rectangle(img_rd, (mid_right_x - 20, mid_right_y - 12),
                                      (mid_right_x + 20, mid_right_y + 12),
                                      (0, 255, 255), 2)
                        cv2.rectangle(img_rd, (mid_left_x - 20, mid_left_y - 12),
                                      (mid_left_x + 20, mid_left_y + 12),
                                      (0, 255, 255), 2)

                        right_eye = cv.resize(right_eye, (40, 24))
                        right_eye = cv.cvtColor(right_eye, cv.COLOR_BGR2GRAY)
                        right_eye = right_eye.reshape(1, 40, 24, 1)
                        right_eye = tf.cast(right_eye, dtype=tf.float64)
                        right_result = network.predict(right_eye).reshape(4, )
                        right_result = tf.argmax(right_result)
                        left_eye = cv.resize(left_eye, (40, 24))
                        left_eye = cv.cvtColor(left_eye, cv.COLOR_BGR2GRAY)
                        left_eye = left_eye.reshape(1, 40, 24, 1)
                        left_eye = tf.cast(left_eye, dtype=tf.float64)
                        left_result = network.predict(left_eye).reshape(4, )
                        left_result = tf.argmax(left_result)

                        if ((left_result == 2) or (right_result == 2)):
                            result = 2
                        elif ((left_result == 3) and (right_result == 3)):
                            result = 3
                        elif ((left_result == 0) or (right_result == 0)):
                            result = 0
                        else:
                            result = 1

                        if (result == last_result):
                            times += 1
                        else:
                            times = 0

                        if ((times == 3) and (result != last_sum_result) and ((result == 2)or(result ==3)) and (clock == 1)):
                            print(result, end='  ')
                            if(result==2):
                                self.left()
                            elif(result==3):
                                self.right()
                            last_sum_result = result
                            times = 0
                        elif ((times == 3) and (result != last_sum_result) and (result == 1)):
                            print(result, end='  ')
                            last_sum_result = result
                            times = 0
                        elif ((times == 5) and (result == 0)and (result != last_sum_result)):
                            print(result, end='  ')
                            times = 0
                            last_sum_result = result
                            clock = -clock

                        last_result = result

                        if(result==0):
                            result_show='close'
                        elif(result==1):
                            result_show = 'open'
                        elif(result==2):
                            result_show = 'left'
                        else:
                            result_show = 'right'

                        #显示检测到的眼睛状态
                        cv2.putText(img_rd, 'L:' + np.str(result_show), (mid_left_x - 70, mid_left_y - 53),
                            cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 1)
                        cv2.putText(img_rd, 'R:' + np.str(result_show), (mid_right_x - 20, mid_right_y - 53),
                            cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 0, 255), 1)
                        cv2.putText(img_rd, 'L:' + np.str(clock_res), (0, 30), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 1)

            if cv2.getWindowProperty("camera", cv2.WND_PROP_AUTOSIZE) < 1 and kk == 1:
                break

            kk = 1
            cv2.namedWindow("camera", 1)
            cv2.imshow("camera", img_rd)


        # 释放摄像头
        self.cap.release()

        # 删除建立的窗口
        cv2.destroyAllWindows()

        self.camera_on = False

    # 关闭眼动翻页
    def shutdown_vedio(self):

        self.cap.release()
