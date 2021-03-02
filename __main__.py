import sys
from PyQt5.QtWidgets import QMainWindow, QDesktopWidget, QTabWidget, QWidget, QVBoxLayout,  \
    QApplication, QFileDialog, QTableWidget, QLabel, QMenu, QMessageBox, \
    QAbstractItemView
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from Ui_PyReader import Ui_MainWindow
from PyQt5.QtCore import QObject , pyqtSignal

try:
    import fitz
except ImportError:
    print('请安装 fitz')


from Area import MyArea
from utils import Size, Point, Book
from BookList import TabWidget
from database import read_db, save2db, remove_db
from info import Info
import os

class Reader(QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        # 继承主窗口类
        super(Reader, self).__init__(parent)
        # 设置应用图标
        self.setWindowIcon(QIcon('source/book.png'))
        # 获取屏幕对象
        self.screen = QDesktopWidget().screenGeometry()
        self.setupUi(self)

        # 去掉 toolbar 右键菜单
        self.setContextMenuPolicy(Qt.NoContextMenu)

        # 界面初始大小
        self.resize(self.screen.width(), self.screen.height() - 75)
        # self.showFullScreen()
        # 获取 QTableWidget 实例
        self.table = QTableWidget()
        # 将 self.table 设置为中心 widget
        # self.setCentralWidget(self.table)
        # 初始化选项卡
        self.tabwidget = TabWidget()
        # 添加书库选项卡
        self.tabwidget.addTab(self.table, '书库')
        self.setCentralWidget(self.tabwidget)
        # 设置选项卡可以关闭
        self.tabwidget.setTabsClosable(True)
        # 隐藏边框
        self.tabwidget.setDocumentMode(True)
        # 点击选项卡叉号时，执行 removeTabab 操作
        self.tabwidget.tabCloseRequested[int].connect(self.remove_tab)
        #self.showFullScreen()
        #self.toolBar.hide()
        #self.tabwidget.hide()
        self.initUi()

    def initUi(self):
        # 属性点 1
        self.coord = Point(0, 0)
        # 初始化
        self.crow = Point(-1, -1)
        # 需要改进，只允许打开一本书
        # 列表
        self.size = Size(2.6, 2.6)
        # 设置标准宽度
        self.width = self.screen.width() // 8
        # 初始化表格类型
        self._set_table_style()
        # 将 toolbar + 号与 self.open 函数绑定
        self.addbar.triggered.connect(self.open)
        # 信息
        # 连接
        self._init_bookset()

    # 连接数据库
    # 更改图书地址删除存储
    def _init_bookset(self):
        self.booklist = [book for book in read_db()]
        self.read_list = [None]
        self.read_list.extend(book for book in self.booklist if book.flag)
        for book in self.read_list[1:]:
            self.read_book(book)

        # 设置封面
        for book in self.booklist:
            self.set_icon(book.fname)

    # 获取无重复图书的地址
    def filter_book(self, book):
        if not book.fname:
            return False
        if book not in self.booklist:
            self.booklist.append(book)
            return True
        return False

    def get_files(self):
        # 打开单个文件
        fnames, _ = QFileDialog.getOpenFileNames(self, 'Open files', './', '(*.pdf)')
        return fnames

    def open(self):
        # 打开文件
        fnames = self.get_files()
        for fname in fnames:
            book = Book(fname)
            if self.filter_book(book):
                self.set_icon(fname)

    def _set_table_style(self):
        # 开启水平与垂直滚轴
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # 设置 5 行 8 列 的表格
        self.table.setColumnCount(8)
        self.table.setRowCount(5)
        # 设置单元格的宽度
        for i in range(8):
            self.table.setColumnWidth(i, self.width)
        # 设置单元格的高度
        # 设置纵横比为 4 : 3
        for i in range(5):
            self.table.setRowHeight(i, self.width * 4 // 3)
        # 隐藏标题栏
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setVisible(False)
        # 禁止编辑
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 不显示网格线
        self.table.setShowGrid(False)
        # 将单元格绑定右键菜单
        # 点击单元格，调用 self.generateMenu 函数
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.generate_menu)

    def set_icon(self, fname):
        # 打开 PDF
        doc = fitz.open(fname)
        # 加载封面
        page = doc.loadPage(0)
        # 生成封面图像
        cover = render_pdf_page(page)
        doc.close()
        label = QLabel(self)
        # label.resize(self.width, self.width * 4 // 3)
        # 设置图片自动填充 label
        label.setScaledContents(True)
        # 设置封面图片
        p = QPixmap(cover)
        p.scaled(self.width, self.width * 4 // 3, Qt.KeepAspectRatio)
        label.setPixmap(p)
        label.setFixedWidth(self.width)
        label.setFixedHeight(self.width * 4 // 3)
        # 设置单元格元素为 label
        self.table.setCellWidget(self.coord.x, self.coord.y, label)
        # 删除 label 对象，防止后期无法即时刷新界面
        # 因为 label 的生存周期未结束
        del label
        # 设置当前行数与列数
        self.crow.update(self.coord.x, self.coord.y)
        # 每 8 个元素换行
        if not self.coord.y % 7 and self.coord.y:
            self.coord.x += 1
            self.coord.y = 0
        else:
            self.coord.y += 1

    def generate_menu(self, pos):
        row_num = col_num = -1
        # 获取选中的单元格的行数以及列数
        for i in self.table.selectionModel().selection().indexes():
            row_num = i.row()
            col_num = i.column()
        # 若选取的单元格中有元素，则支持右键菜单
        if (row_num < self.crow.x) or (row_num == self.crow.x and col_num <= self.crow.y):
            menu = QMenu()
            item1 = menu.addAction('开始阅读')
            item2 = menu.addAction('删除图书')
            item3 = menu.addAction('文档信息')
            # 获取选项
            action = menu.exec_(self.table.mapToGlobal(pos))
            if action == item1:
                index = row_num * 8 + col_num
                # 之后改成 book
                book = self.booklist[index]
                # 不重复打开书
                # 可以不限制
                if book not in self.read_list and len(self.read_list) < 5:
                    book.flag = True
                    self.read_list.append(book)
                    self.read_book(book)
            elif action == item2:
                self.delete_book(row_num, col_num)
                
            elif action == item3:
                index = row_num * 8 + col_num
                # 之后改成 book
                book = self.booklist[index]
                info = book.info
                fmt = f'路径：{info.path}\n\n' \
                      f'格式：{info.format}\n\n' \
                      f'标题：{info.title}\n\n' \
                      f'作者：{info.author}\n\n' \
                      f'Creator：{info.creator}\n\n' \
                      f'Producer：{info.producer}\n\n'
                    
                QMessageBox.about(self, '文档信息', fmt)

    # 删除图书
    def delete_book(self, row, col):
        # 获取图书在列表中的位置
        index = row * 8 + col
        self.coord.update(row, col)
        if index >= 0:
            self.booklist.pop(index)

        i, j = row, col
        while 1:
            # 移除 i 行 j 列单元格的元素
            self.table.removeCellWidget(i, j)
            # 一直删到最后一个有元素的单元格
            if i == self.crow.x and j == self.crow.y:
                break
            if not j % 7 and j:
                i += 1
                j = 0
            else:
                j += 1

        # 如果 booklist 为空，设置当前单元格为 -1
        if not self.booklist:
            self.crow.update(-1, -1)
        # 删除图书后，重新按顺序显示封面图片
        for book in self.booklist[index:]:
            self.set_icon(book.fname)

    def read_book(self, book):
        # self.close()
        # 内存有可能泄露
        fname = book.fname
        doc = fitz.open(fname)
        title = fname.split('/' or '\\')[-1].replace('.pdf', '')

        vbox = self.book_area(doc.loadPage(book.page))
        doc.close()
        self.book_add_tab(title, vbox)

    def book_add_tab(self, title, vbox):
        tab = QWidget()
        tab.setLayout(vbox)
        # tab 为页面，title 为标签名称
        self.tabwidget.addTab(tab, title)
        self.tabwidget.setCurrentIndex(self.tabwidget.count() - 1)

    def page_pixmap(self, page):
        # 在标签上显示图片
        label = QLabel(self)
        p = render_pdf_page(page, x = self.size.x, y = self.size.y)
        # 按屏幕大小缩放标签
        p.scaled(self.screen.width(), self.screen.height())
        # 在标签上设置图片
        label.setPixmap(QPixmap(p))
        return label

    def book_area(self, page):
        label = self.page_pixmap(page)
        area = MyArea(self)
#        area.init(self)
        area.setWidget(label)
        # area.sebook(self.get_read_book())

        vbox = QVBoxLayout()
        vbox.addWidget(area)
        return vbox

    def set_current_page(self, right):
        book = self.get_read_book()
        # 之后统一在 book 中
        if right and book.page < book.total_page:
            book.page += 1

        elif not right and book.page:
            book.page -= 1

    def switch_page(self, right=True):
        self.set_current_page(right)
        self.set_page()

    def get_read_book(self):
        index = self.tabwidget.currentIndex()
        book = self.read_list[index]
        return book

    def set_page(self):
        book = self.get_read_book()
        # 加载页面
        doc = fitz.open(book.fname)
        page = doc.loadPage(book.page)
        # 获取当前 Widget
        tab = self.tabwidget.currentWidget()
        # 获取当前的 Layout
        layout = tab.layout()
        # 获取 Layout 上的控件
        widget = layout.itemAt(0).widget()
        # 获取已经绘制好的 label 对象
        label = self.page_pixmap(page)
        # 将 widget 的内容更改为现在的 label 对象
        doc.close()
        widget.setWidget(label)


    def zoom_book(self, plus=True):
        if plus:
            self.size.x += 0.4
            self.size.y += 0.4
            self.set_page()
        elif not plus:
            self.size.x -= 0.4
            self.size.y -= 0.4
            self.set_page()

    def remove_tab(self, index):
        if index:
            # 当前页数
            # self.read_list[index].page = 0
            self.tabwidget.removeTab(index)
            # self.doc.close()
            # 正在阅读的书
            
            book = self.read_list.pop(index)
            book.flag = False
     
    def closeEvent(self, event):
        remove_db()
        save2db(self.booklist)
        event.accept()

# 显示 PDF 封面
def render_pdf_page(page_data, x = 1,  y = 1):
    # 图像缩放比例

    zoom_matrix = fitz.Matrix(x, y)

    # 获取封面对应的 Pixmap 对象
    # alpha 设置背景为白色
    pagePixmap = page_data.getPixmap(
        matrix=zoom_matrix,
        alpha=False)
    # 获取 image 格式
    imageFormat = QtGui.QImage.Format_RGB888
    # 生成 QImage 对象
    pageQImage = QtGui.QImage(
        pagePixmap.samples,
        pagePixmap.width,
        pagePixmap.height,
        pagePixmap.stride,
        imageFormat)

    # 生成 pixmap 对象
    pixmap = QtGui.QPixmap()
    pixmap.convertFromImage(pageQImage)
    return pixmap  
            



if __name__ == '__main__':


    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    app = QApplication(sys.argv)
    reader = Reader()
    info = Info()
    reader.infobar.triggered.connect(info.show)
    reader.show()
    sys.exit(app.exec_())
