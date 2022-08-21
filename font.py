import io
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

class _Type:
    '''数据类型的基类'''
    size = None # 数据大小（字节）
    discription = '' # 描述
    @classmethod
    def from_bytes(cls, bytes_):
        '''将字节转化为相应类型的数据，大端序'''
        return bytes_
    def to_bytes(self):
        '''将相应类型的数据转化为字节，大端序'''
        return self

class _Uint(_Type, int):
    '''无符号整数基类'''
    @classmethod
    def from_bytes(cls, bytes_):
        return int.from_bytes(bytes_, 'big', signed=False)
    def to_bytes(self):
        return int.to_bytes(self, self.size, 'big', signed=False)

class _Int(_Type, int):
    '''有符号整数基类'''
    @classmethod
    def from_bytes(cls, bytes_):
        return int.from_bytes(bytes_, 'big', signed=True)
    def to_bytese(self, bytes_):
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

class Fixed(_Type):
    '''TODO'''
    (4, '32位定点数，高16位整数，低16位小数')

class FWORD(int16):
    description = 'int16类型，以字体设计单位计量'

class UFWORD(uint16):
    description = 'uint16类型，以字体设计单位计量'

class F2DOT14(_Type):
    '''TODO'''
    (2, '16位定点数，高2位整数，低14位小数')

class LONGDATETIME(_Int):
    size = 8
    description = '时间日期，用从1904-01-01午夜12:00开始经过的秒数表示，是64位有符号整数'

class Tag(_Type, bytes):
    size = 4
    description = '4个uint8组成的数组，用于区分table等对象'

class Offset16(uint16):
    size = 2
    description = '短偏移量，实际是uint16'

class Offset32(uint32):
    size = 4
    description = '长偏移量，实际是uint32'


class _Table(dict):
    '''Table 接口，用于派生子类
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

class Font:
    '''读取字体文件，提供对字体数据的访问方法'''
    def __init__(self, filename):
        with open(filename, 'rb') as fontfile:
            self.parse(fontfile)

    def parse(self, fontfile:io.BufferedReader):
        self.offset_table = OffsetTable.unpack(fontfile)
if __name__ == '__main__':
    # pass
    # for k, v in Type.__members__.items():
    #     print(v, v.size, v.description)
    font = Font('DejaVuSans.ttf')
    for name, value in font.offset_table.items():
        print(name, value, OffsetTable.descriptions[name],
            sep='\t')