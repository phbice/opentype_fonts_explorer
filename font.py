import io
import math
# import struct
import enum
import datetime

# class Type(enum.Enum):
#     '''数据类型枚举
#     每个类型实例包括三个属性：
#         value:       自动生成的类型标识码
#         size:        类型大小（字节）
#         description: 类型描述
#     '''
#     def __new__(cls, size, description):
#         value = len(cls.__members__) + 1
#         obj = object.__new__(cls)
#         obj._value_ = value
#         obj.size = size
#         obj.description = description
#         return obj
    
#     def __str__(self):
#         return self.name
#     def __repr__(self):
#         return f'<{self.__class__.__name__},{self.name}>'
#     @staticmethod
#     def unpack_uint(bytes_):
#         return int.from_bytes(bytes_, 'big', signed=False)
#     @staticmethod
#     def unpack_int(bytes_):
#         return int.from_bytes(bytes_, 'big', signed=True)

#     uint8  = (1, '8位无符号整数', unpack_uint,
#         lambda x: x.to_bytes(1, 'big', signed=False))
#     int8   = (1, '8位整数',       unpack_int,
#         lambda x: x.to_bytes(1, 'big', signed=True))
#     uint16 = (2, '16位无符号整数', unpack_uint,
#         lambda x: x.to_bytes(2, 'big', signed=False))
#     int16  = (2, '16位整数',      unpack_int,
#         lambda x: x.to_bytes(2, 'big', signed=False))
#     uint24 = (3, '24位整数')
#     uint32 = (4, '32位无符号整数')
#     int32  = (4, '32位整数')
#     Fixed  = (4, '32位定点数，高16位整数，低16位小数')
#     FWORD  = (2, 'int16类型，以字体设计单位计量')
#     UWFORD = (2, 'uint16类型，以字体设计单位计量')
#     F2DOT14      = (2, '16位定点数，高2位整数，低14位小数')
#     LONGDATETIME = (8, '时间日期，用从1904-01-01午夜12:00开始经过的秒数表示，是64位有符号整数')
#     Tag          = (4, '4个uint8组成的数组，用于区分table等对象')
#     Offset16     = (2, '短偏移量，实际是uint16')
#     Offset32     = (4, '长偏移量，实际是uint32')

class _Atom:
    '''数据类型的基类'''
    size = None # 数据大小（字节）
    discription = '' # 描述
    @classmethod
    def from_bytes(cls, bytes_):
        '''将字节转化为相应类型的数据，大端序'''
        return cls(bytes_)
    def to_bytes(self):
        '''将相应类型的数据转化为字节，大端序'''
        return bytes(self)

class _Uint(_Atom, int):
    '''无符号整数基类'''
    @classmethod
    def from_bytes(cls, bytes_):
        return cls(int.from_bytes(bytes_, 'big', signed=False))
    def to_bytes(self):
        return int.to_bytes(self, self.size, 'big', signed=False)

class _Int(_Atom, int):
    '''有符号整数基类'''
    @classmethod
    def from_bytes(cls, bytes_):
        return cls(int.from_bytes(bytes_, 'big', signed=True))
    def to_bytes(self):
        return int.to_bytes(self, self.size, 'big', signed=True)

class uint8(_Uint):
    size = 1
    description = '8位无符号整数'

class int8(_Int):
    size = 1
    description = '8位整数'

class uint16(_Uint):
    size = 2
    description = '16位无符号整数'

class int16(_Int):
    size = 2
    description = '16位整数'

class uint24(_Uint):
    size = 3
    description = '24位整数'

class uint32(_Uint):
    size = 4
    description = '32位无符号整数'

class int32(_Int):
    size = 4
    description = '32位整数'

class Fixed(_Atom, float):
    size = 4
    description = '32位定点数，高16位整数，低16位小数'
    @classmethod
    def from_bytes(cls, bytes_):
        return (int16.from_bytes(bytes_[:2]) +
            uint16.from_bytes(bytes_[2:]) / 0x10000)
    def to_bytes(self):
        int_part = int16(math.floor(self))
        dec_part = uint16(round((self - int_part) * 0x10000))
        return int_part.to_bytes() + dec_part.to_bytes()

class FWORD(int16):
    description = 'int16类型，以字体设计单位计量'

class UFWORD(uint16):
    description = 'uint16类型，以字体设计单位计量'

class F2DOT14(_Atom):
    '''TODO'''
    (2, '16位定点数，高2位整数，低14位小数')

class LONGDATETIME(_Int):
    size = 8
    description = '时间日期，用从1904-01-01午夜12:00开始经过的秒数表示，是64位有符号整数'
    ref_time = datetime.datetime(1904, 1, 2, 0, 0, 0, 0)
    def __str__(self):
        return (self.ref_time + datetime.timedelta(seconds=self)
            ).isoformat(' ','seconds')

class Tag(_Atom, bytes):
    size = 4
    description = '4个uint8组成的数组，用于区分table等对象'

class Offset16(uint16):
    size = 2
    description = '短偏移量，实际是uint16'

class Offset32(uint32):
    size = 4
    description = '长偏移量，实际是uint32'


class _Table(dict):
    '''Table 基类，用于派生子类
    子类需指定类属性 structure
    structure 是由tuple: (type, name, description) 组成的元组
    '''
    structure = ((uint32, 'demo', 'no description'),)
    @classmethod
    def __init_subclass__(cls):
        cls.descriptions = {name:desc
            for _, name, desc in cls.structure}

    def length(self):
        '''给出 Table 的大小，单位是字节'''
        raise NotImplementedError

    @classmethod
    def unpack(cls, buffer:io.BufferedReader):
        return cls({name: type.from_bytes(buffer.read(type.size))
            for  type, name, description in cls.structure})

class OffsetTable(_Table):
    structure = (
        (uint32, 'sfntVersion', '0x00010000 for TrueTyep'
        ' outlines, 0x4F54544F if containing CFF data'),
        (uint16, 'numTables', 'Number of tables'),
        (uint16, 'searchRange', '2**floor(log2(numTables))*16'),
        (uint16, 'entrySelector', 'floor(log2(numTables))'),
        (uint16, 'rangeShift', 'numTables*16 - searchRange')
    )

class TableRecord(_Table):
    structure = (
        (Tag, 'tableTag', 'Table identifier'),
        (uint32, 'checkSum', 'CheckSum for this table'),
        (Offset32, 'offset', 'Offset from begining of TrueType font file'),
        (uint32, 'length', 'Length of this table')
    )

class Font:
    '''读取字体文件，提供对字体数据的访问方法'''
    def __init__(self, filename):
        with open(filename, 'rb') as fontfile:
            self.parse(fontfile)

    def parse(self, fontfile:io.BufferedReader):
        self.offset_table = OffsetTable.unpack(fontfile)
        self.table_records = [TableRecord.unpack(fontfile)
            for _ in range(self.offset_table['numTables'])]

if __name__ == '__main__':
    # pass
    # for k, v in Type.__members__.items():
    #     print(v, v.size, v.description)
    # print(Fixed.from_bytes(b'\xff\xf6\xff\xfc'))
    # print(Fixed(-9.000061).to_bytes())
    # print(LONGDATETIME(3734255578))
    font = Font('DejaVuSans.ttf')
    print('-'*15 + 'offset table' + '-'*15)
    for name, value in font.offset_table.items():
        print(f'{name: <14}{str(value): <14}'
            f'{OffsetTable.descriptions[name]: <14}')
    for table_record in font.table_records:
        print('-'*15 + 'table record' + '-'*15)
        for name, value in table_record.items():
            print(f'{name: <14}{str(value): <14}'
                f'{TableRecord.descriptions[name]: <14}')
