#!/usr/bin/env python
# coding: utf-8

# # Homework04. B+tree Deletion 구현하기

# ### 0. Tree 생성

from bplustree import BPlusTree
from bplustree.serializer import (IntSerializer, StrSerializer, UUIDSerializer, DatetimeUTCSerializer)
import os

if os.path.exists("database/homework04.db"):
      os.remove("database/homework04.db")
if os.path.exists("database/homework04.db-wal"):
      os.remove("database/homework04.db-wal")

tree = BPlusTree('database/homework04.db', key_size = 32, order=5, serializer=StrSerializer())


# ### 1. Insert: key, value 쌍을 tree index에 삽입
# * 삽입 과정에서 leaf node와 parent node의 split을 확인할 수 있다.

tree.insert('a', b'1')
tree.insert('b', b'2')
tree.insert('c', b'3')
tree.insert('d', b'4')
tree.display()

tree.insert('e', b'5')
tree.display()

tree.insert('f', b'6')
tree.insert('g', b'7')
tree.insert('h', b'8')
tree.insert('i', b'9')
tree.insert('j', b'10')
tree.insert('k', b'11')
tree.insert('l', b'12')
tree.insert('m', b'13')
tree.display()

tree.insert('n', b'14')
tree.insert('o', b'15')
tree.insert('p', b'16')
tree.insert('q', b'17')
tree.insert('r', b'18')
tree.insert('s', b'19')
tree.insert('t', b'20')
tree.insert('u', b'21')
tree.insert('v', b'22')
tree.insert('w', b'23')
tree.insert('x', b'24')
tree.insert('y', b'25')
tree.insert('z', b'26')
tree.insert('za', b'27')
tree.insert('zb', b'28')
tree.insert('zc', b'29')
tree.insert('zd', b'30')
tree.insert('ze', b'31')
tree.insert('zf', b'32')
tree.insert('zg', b'33')
tree.insert('zh', b'34')
tree.insert('zi', b'35')
tree.insert('zj', b'36')
tree.insert('zk', b'37')
tree.display()


# ### 2. Delete: key를 Tree에서 삭제
# * 삭제 과정에서 redistribute, merge 수행을 확인할 수 있다.

tree.delete('j')
tree.display()
tree.delete('n')
tree.display()
tree.delete('m')
tree.display()

tree.delete('zg')
tree.display()

tree.delete('zk')
tree.display()

tree.delete('zj')
tree.display()


tree.close()