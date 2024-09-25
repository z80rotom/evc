import struct

from enum import IntEnum, auto
from dataclasses import dataclass, field

from ev_argtype import EvArgType
from ev_cmd import EvCmdType
from ev_work import EvWork
from ev_sys_flag import EvSysFlag

MAX_WORK = 500
MAX_FLAG = 4000
MAX_SYS_FLAG = 1000
RETURN_STORAGE = -1

class ECommandArgType(IntEnum):
    Flag = auto()
    SysFlag = auto()
    Integer = auto()
    Float = auto()
    Boolean = auto()
    String = auto()
    NumberEnum = auto()

class EFunctionSpecifier(IntEnum):
    Common = auto()
    Entry = auto()

@dataclass
class CommandDefArgument:
    eArgType: ECommandArgType
    argTypeIdentifier: str
    identifier: str
    storage: int
    line: int
    column: int

@dataclass
class Command:
    identifier: str
    storage: int
    retArg: CommandDefArgument
    args: list[CommandDefArgument]
    line: int
    column: int

@dataclass
class Function:
    specifier: EFunctionSpecifier
    label: int
    identifier: str
    retArg: CommandDefArgument
    args: list[CommandDefArgument]
    line: int
    column: int

@dataclass
class Animation:
    label: int
    identifier: str
    line: int
    column: int

@dataclass
class Variable:
    eArgType: ECommandArgType
    argTypeIdentifier: str
    identifier: str
    storage: int
    isConst: bool
    constValue: int
    line: int
    column: int

@dataclass
class EvArg:
    argType: EvArgType
    data: int

@dataclass
class EvCmd:
    cmdType: EvCmdType
    args: list[EvArg]

@dataclass
class Label:
    nameIdx: int # StrTbl 
    childLabels: list = field(default_factory=list)
    commands: list[EvCmd] = field(default_factory=list)

@dataclass
class VariableDefinition:
    variable: Variable
    commands: list[EvCmd]

@dataclass
class AllocatorData:
    flags: list = field(default_factory=list)
    sys_flags: list = field(default_factory=list)
    works: list = field(default_factory=list)

@dataclass
class FunctionCallArg:
    variable: Variable
    isConst: bool
    constValue: int
    constValueType: ECommandArgType

@dataclass
class FunctionCall:
    function: object
    args: list[FunctionCallArg]

@dataclass
class ComparatorLeft:
    storage: int
    eArgType: ECommandArgType
    commands: list[EvCmd]


def encode_float(var):
    var = float(var)
    data = int(struct.unpack('<i', struct.pack('<f', var))[0])
    return data

def decode_int(var):
    # Thanks Aldo796
    var = int(var)
    data = float(struct.unpack('!f', struct.pack('!I', var & 0xFFFFFFFF))[0])
    return data