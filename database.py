import os
import sqlite3
from collections import namedtuple
from utils import Book, DBManger


book_db = 'PDF.db'
book_info = namedtuple('info',  'path page flag')




def read_db():
    # 将路径更改为该文件所处路径
    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    if not os.path.exists(book_db):
        with DBManger(book_db) as conn:
            conn.execute("CREATE TABLE book_info(path, page, flag)")
            conn.commit()

    with DBManger(book_db) as conn:
        for row in conn.execute('SELECT * FROM book_info'):
            info = book_info(*row)
            try:
                book = Book(info.path)
            except RuntimeError:
                continue
            book.page = info.page
            book.flag = info.flag
            yield book

  
  
    

def remove_db():
    with DBManger(book_db) as conn:
        conn.execute('DELETE FROM book_info')
        conn.commit()


def save2db(booklist):
    with DBManger(book_db) as conn:
        conn.executemany("INSERT INTO book_info Values (?,?,?)",
                    ((book.fname, book.page, book.flag) for book in booklist))
        conn.commit()

    
    
if __name__ == '__main__':
    pass
