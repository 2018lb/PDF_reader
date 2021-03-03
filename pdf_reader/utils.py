import fitz
from collections import namedtuple
import sqlite3

book_attr = 'path format title author creator producer'
book_info = namedtuple('info', book_attr)

class Book:
    def __init__(self, fname):
        # 文件名
        self.fname = fname
        # 是否被阅读
        self.flag = None
        self._info = None
        self._page = 0
        self.get_meta_data(self.fname)
    
    # 获取元信息
    def get_meta_data(self, fname):
        try:
            file = fitz.open(fname)
        except RuntimeError:
            raise 
        metadata = file.metadata
        self._total_page = file.pageCount
        file.close()
        pdf_format = metadata['format']
        pdf_title = metadata['title']
        pdf_author = metadata['author']
        pdf_creator = metadata['creator']
        pdf_producer = metadata['producer']
        self.info = book_info(self.fname, pdf_format, pdf_title, pdf_author, pdf_creator, pdf_producer)
    
    @property
    def total_page(self):
        return self._total_page - 1
    
    @property
    def book_info(self):
        return self._info
    
    @property
    def page(self):
        return self._page
        
    @page.setter
    def page(self, page):
        self._page = page
     
    # 用于判断是否为同一对象
    def __eq__(self, other):
        if hasattr(other, 'fname'):
            return self.fname == other.fname
        return False


# 设置缩放比例 
class Size:
    def __init__(self, x, y):
        self._x = x
        self._y = y
        
    @property
    def x(self):
        return self._x
        
    @x.setter
    def x(self, x):
        if x > 1 and x < 5:
            self._x = x
            
    @property
    def y(self):
        return self._y
        
    @y.setter
    def y(self, y):
        if y > 1 and y < 5:
            self._y = y
      

        
# 设置属性点
class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def update(self, x, y):
        self.x = x
        self.y = y


class DBManger:
    def __init__(self, name):
        self.name = name
        
    def __enter__(self):
        self.conn = sqlite3.connect(self.name)
        return self.conn
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        if exc_val:
            raise
