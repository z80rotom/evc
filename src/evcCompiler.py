import logging
import struct
import sys
import os

from enum import IntEnum, auto
from dataclasses import dataclass, field

from antlr4 import *
from UnityPy.streams import EndianBinaryWriter

from evcListener import evcListener
from evcLexer import evcLexer
from evcParser import evcParser

from ev_argtype import EvArgType
from ev_cmd import EvCmdType
from ev_work import EvWork
# Not sure what I would use these for directly myself at the moment.
# from ev_flag import EvFlag
# from ev_sys_flag import EvSysFlag


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
class Scope:
    prefix: str = field(default_factory=lambda: None)
    commands: dict[str, Command] = field(default_factory=dict)
    functions: dict[str, Function] = field(default_factory=dict)
    variables: dict[str, Variable] = field(default_factory=dict)
    childScopes: list  = field(default_factory=list)

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
    commands: list[EvCmd]

@dataclass
class VariableDefinition:
    variable: Variable
    commands: list[EvCmd]

@dataclass
class AllocatorData:
    flags: list = field(default_factory=list)
    sys_flags: list = field(default_factory=list)
    works: list = field(default_factory=list)

def encode_float(var):
    var = float(var)
    data = int(struct.unpack('<i', struct.pack('<f', var))[0])
    return data

class evcCompiler(evcListener):
    def __init__(self, ifpath):
        self.src_ifpath = ifpath
        self.logger = logging.getLogger(__name__)
        self.scope = Scope()
        self.globalScope = self.scope
        self.prevScope = []
        self.labels = {}
        self.strTbl = []
        self.writer = EndianBinaryWriter()
    
    def parseNumberContext(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return float(ctx.NUMBER().getText())

    def parseNumberContextInt(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return int(ctx.NUMBER().getText())

    def parseType(self, argType:evcParser.TypeContext):
        argTypes = {
            "flag" : ECommandArgType.Flag,
            "sysflag" : ECommandArgType.SysFlag,
            "int" : ECommandArgType.Integer,
            "float" : ECommandArgType.Float,
            "bool" : ECommandArgType.Boolean,
            "str" : ECommandArgType.String
        }
        eArgType = argTypes[argType.getText()]
        return eArgType


    def parseFunctionSpecifier(self, ctx:evcParser.FunctionSpecifierContext):
        if ctx.COMMON() is not None:
            return EFunctionSpecifier.Common
        elif ctx.ENTRY is not None:
            return EFunctionSpecifier.Entry

    def parseFuncArgStorage(self, ctx:evcParser.FuncArgStorageContext):
        if ctx is not None:
            if ctx.RETURN() is not None:
                storage = RETURN_STORAGE
            else:
                storage = self.parseNumberContextInt(ctx.number())
        else:
            storage = None
        return storage
    
    def mapFuncArg(self, ctx:evcParser.FuncArgContext):
        identifier = ctx.Identifier().getText()
        storage = parseFuncArgStorage(ctx.funcArgStorage())
        eArgType = self.parseType(ctx.type_())
        argTypeIdentifier = ctx.type_().getText()

        # TODO: Validate storage based on type

        return CommandDefArgument(
            eArgType,
            argTypeIdentifier,
            identifier,
            storage,
            ctx.start.line,
            ctx.start.column
        )

    def parseFuncArgList(self, ctx:evcParser.FuncArgListContext):
        return map(self.mapFuncArg, ctx.funcArg())

    def parseRetFuncArg(self, ctx:evcParser.TypeContext):
        eArgType = self.parseType(ctx)
        argTypeIdentifier = ctx.getText()
        retArg = CommandDefArgument(
            eArgType,
            argTypeIdentifier,
            None,
            None,
            ctx.start.line,
            ctx.start.line
        )
        return retArg

    def enterCommand(self, ctx:evcParser.CommandContext):
        if ctx.Identifier() is None:
            self.logger.error("Invalid name for command at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
            return
        identifier = ctx.Identifier().getText()
        args = []
        retArg = None

        storage = self.parseNumberContextInt(ctx.number())

        if ctx.funcArgList() is not None:
            args = self.parseFuncArgList(ctx.funcArgList())

        if ctx.type_() is not None:
            retArg = self.parseRetFuncArg(ctx.type_())

        self.scope.commands[identifier] = Command(
            identifier,
            storage,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        )

    def addStringToTable(self, string):
        if string not in self.strTbl:
            self.strTbl.append(string)
            return len(self.strTbl) - 1
        return self.strTbl.index(string)

    def generateLabel(self, name):
        idx = self.addStringToTable(name)
        label = Label(idx, [])
        self.labels[idx] = label
        return label

    def newScope(self):
        newScope = Scope()
        self.scope.childScopes.append(newScope)
        self.prevScope.append(self.scope)
        self.scope = newScope

    def popScope(self):
        if len(self.prevScope) <= 0:
            self.logger.warn("Attempting to popscope without prevScope")
            return
        if self.scope is self.globalScope:
            self.logger.warn("Attempting to popScope when at globalScope")
            return
        self.scope = self.prevScope.pop()

    def parseBlock(self, ctx:evcParser.BlockContext, allocator):
        self.newScope()
        for blockEntry in ctx.blockEntry():
            if blockEntry.variableDefinition() is not None:
                variableDefinition = self.parseVariableDefinition(blockEntry.variableDefinition(), allocator, True)
                self.scope.variables[variableDefinition.variable.identifier] = variableDefinition.variable
        self.popScope()

    def parseConstVariableRightHandAssignment(self, ctx:evcParser.VariableRightHandAssignmentContext, eArgType):
        constValue = None
        if ctx.number() is not None:
            if eArgType == ECommandArgType.Integer:
                constValue = encode_float(int(ctx.number().getText()))
                try:
                    self.writer.write_int(constValue)
                except Exception as exc:
                    print("Invalid float: {}".format(argVal))
            elif argType == ECommandArgType.NumberEnum:
                self.logger.error("Enums are not fully supported at the moment")
                sys.exit()
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.number().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.boolValue() is not None:
            if eArgType == ECommandArgType.Boolean:
                constValue = int(ctx.boolValue().TRUE() is not None)
            elif eArgType == ECommandArgType.Flag:
                self.logger.error("No such thing as a constant Flag")
                sys.exit()
            elif eArgType == ECommandArgType.SysFlag:
                self.logger.error("No such thing as a constant SysFlag")
                sys.exit()
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.boolValue().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.string_() is not None:
            self.logger.error("Variable must be mutable to assign from string at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        elif ctx.functionCall() is not None:
            self.logger.error("Variable must be mutable to assign from function call at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        else:
            self.logger.error("Unknown variable declaration at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return constValue
    
    def parseMutVariableRightHandAssignment(self, ctx:evcParser.VariableRightHandAssignmentContext, eArgType, storage):
        commands = []
        if ctx.number() is not None:
            if eArgType == ECommandArgType.Integer:
                constValue = encode_float(int(ctx.number().getText()))
                try:
                    self.writer.write_int(constValue)
                except Exception as exc:
                    print("Invalid float: {}".format(argVal))
                commands.append(
                    EvCmd(EvCmdType._LDVAL, [
                        EvArg(EvArgType.Work, storage),
                        EvArg(EvArgType.Value, constValue)
                    ])
                )
            elif argType == ECommandArgType.NumberEnum:
                self.logger.error("Enums are not fully supported at the moment")
                sys.exit()
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.number().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.boolValue() is not None:
            if eArgType == ECommandArgType.Boolean:
                self.logger.error("No such thing as a mutable bool")
                sys.exit()
            elif eArgType == ECommandArgType.Flag:
                if ctx.boolValue().TRUE() is not None:
                    commands.append(
                        EvCmd(EvCmdType._FLAG_SET, [
                            EvArg(EvArgType.Flag, storage)    
                        ])
                    )
                else:
                    commands.append(
                        EvCmd(EvCmdType._FLAG_RESET, [
                            EvArg(EvArgType.Flag, storage)    
                        ])
                    )
            elif eArgType == ECommandArgType.SysFlag:
                if ctx.boolValue().TRUE() is not None:
                    commands.append(
                        EvCmd(EvCmdType._SET_SYS_FLAG, [
                            EvArg(EvArgType.SysFlag, storage)    
                        ])
                    )
                else:
                    commands.append(
                        EvCmd(EvCmdType._RESET_SYS_FLAG, [
                            EvArg(EvArgType.SysFlag, storage)    
                        ])
                    )
            else:
                self.logger.error("Invalid value {} for type {} at: {}:{}:{}".format(ctx.boolValue().getText(), argTypeIdentifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        elif ctx.string_() is not None:
            self.logger.error("String variables aren't currently supported: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        elif ctx.functionCall() is not None:
            self.logger.error("TODO: Cannot retrieve value from function call")
            sys.exit()
        else:
            self.logger.error("Unknown variable declaration at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return commands

    def parseVariableDefinition(self, ctx:evcParser.VariableDefinitionContext, allocator, canAssignMut):
        eArgType = self.parseType(ctx.type_())
        argTypeIdentifier = ctx.type_().getText()
        identifier = ctx.Identifier().getText()
        storage = self.parseNumberContextInt(ctx.number())
        isConst = ctx.CONST() is not None
        constValue = None

        # TODO: Check if variable is already defined in scope

        commands = []
        aCtx = ctx.variableRightHandAssignment()
        if isConst:
            if aCtx is not None:
                constValue = self.parseConstVariableRightHandAssignment(aCtx, eArgType)
            else:
                self.logger.error("Must specify value for const variable: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
        else:
            if storage is None:
                storage = allocator(ctx, eArgType)
            if aCtx is not None:
                if not canAssignMut:
                    self.logger.error("Not able to assign mut at this scope at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
                commands = self.parseMutVariableRightHandAssignment(aCtx, eArgType, storage)
        # print(commands)
        return VariableDefinition(Variable(
            eArgType,
            argTypeIdentifier,
            identifier,
            storage,
            isConst,
            constValue,
            ctx.start.line,
            ctx.start.column,
        ), commands)

    def allocateStorageFunction(self, ctx, eArgType: ECommandArgType, allocatorData: AllocatorData):
        WORK_ALLOCATION_ORDER = []
        WORK_ALLOCATION_ORDER.extend(range(32)) # LOCALWORK0...LOCALWORK31
        # Don't want to work with SCWK_TEMP0 yet, because I want to use them for arguments
        # for common functions because that's what ILCA does.
        # WORK_ALLOCATION_ORDER.extend(range(238, 242)) # SCWK_TEMP0...SCWK_TEMP3
        if eArgType == ECommandArgType.Integer:
            if len(allocatorData.works) >= len(WORK_ALLOCATION_ORDER):
                self.logger.error("Out of LOCALWORK values to allocate. Specify storage if you really need > 32 ints: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
                return
            idx = len(allocatorData.works)
            storage = WORK_ALLOCATION_ORDER[idx]
            allocatorData.works.append(storage)
            return storage
        else:
            self.logger.error("Cannot automatically allocate storage for non-int: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()

    def enterFunction(self, ctx:evcParser.FunctionContext):
        if ctx.Identifier() is None:
            self.logger.error("Invalid name for function at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
            return
        identifier = ctx.Identifier().getText()
        args = []
        retArg = None
        specifier = None

        if ctx.functionSpecifier() is not None:
            specifier = self.parseFunctionSpecifier(ctx.functionSpecifier())

        if ctx.funcArgList() is not None:
            args = self.parseFuncArgList(ctx.funcArgList())

        if ctx.type_() is not None:
            retArg = self.parseRetFuncArg(ctx.type_())

        if specifier is not None:
            labelName = identifier
        else:
            # TODO: Need to properly mangle identifier based on scope.
            labelName = "_{}".format(identifier)

        label = self.generateLabel(labelName)
        
        self.scope.functions[identifier] = Function(
            specifier,
            label.nameIdx,
            identifier,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        )

        # Only integers should be scoped to function.
        allocatorData = AllocatorData()
        # Time to start handling blocks Yipee
        self.parseBlock(ctx.block(), 
            lambda ctx, eArgType: self.allocateStorageFunction(ctx, eArgType, allocatorData))

    def readImport(self, ifpath):
        print("Processing file: ", ifpath)
        input_stream = FileStream(ifpath, encoding='utf-8')
        lexer = evcLexer(input_stream)
        stream = CommonTokenStream(lexer)
        parser = evcParser(stream)
        tree = parser.prog()

        assembler = evcCompiler(ifpath)
        walker = ParseTreeWalker()
        walker.walk(assembler, tree)
        return assembler

    def handleImport(self, ctx, identifier):
        resolveOrder = [
            os.path.join(os.path.dirname(self.src_ifpath), "{}.evc".format(identifier)),
            "scripts/lib/{}/lib.evc".format(identifier)
        ]

        resolvedIfpath = None
        for ifpath in resolveOrder:
            if os.path.exists(ifpath):
                resolvedIfpath = ifpath
                break
        if resolvedIfpath is None:
            self.logger.error("Unable to resolve import '{}' at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return self.readImport(resolvedIfpath)

    def enterFromImport(self, ctx:evcParser.FromImportContext):
        assembler = self.handleImport(ctx, ctx.Identifier().getText())
        if ctx.fromImportRhs() is None:
            self.logger.error("Malformed from ... import {{ ... }} at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()

        if ctx.fromImportRhs().WILDCARD() is not None:
            self.scope.functions.update(assembler.globalScope.functions)
            self.scope.commands.update(assembler.globalScope.commands)
            self.scope.variables.update(assembler.globalScope.variables)
            self.scope.childScopes.extend(assembler.globalScope.childScopes)
        else:
            # How to bring in namespaced variables specifically?
            for identifierTkn in ctx.fromImportRhs().Identifier():
                identifier = identifierTkn.getText()
                foundIdentifier = False
                if identifier in assembler.globalScope.functions:
                    self.scope.functions[identifier] = assembler.globalScope.functions[identifier]
                    foundIdentifier = True
                if identifier in assembler.globalScope.commands:
                    self.scope.commands[identifier] = assembler.globalScope.commands[identifier]
                    foundIdentifier = True
                if identifier in assembler.globalScope.variables:
                    self.scope.variables[identifier] = assembler.globalScope.variables[identifier]
                    foundIdentifier = True
                if not foundIdentifier:
                    self.logger.error("Unable to retrieve identifier {} at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
            
    
    def enterImport_(self, ctx:evcParser.Import_Context):
        assembler = self.handleImport(ctx, ctx.Identifier().getText())
        assembler.globalScope.prefix = ctx.Identifier().getText()
        # print(len(assembler.globalScope.variables))
        self.scope.childScopes.append(assembler.globalScope)

    def enterProgEntry(self, ctx:evcParser.ProgEntryContext):
        if ctx.variableDefinition() is not None:
            # print("Processing variable definition")
            allocator = lambda ctx, eArgType: self.logger.error("Unable to allocate work at this scope at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            variableDefinition = self.parseVariableDefinition(ctx.variableDefinition(), allocator, True)
            self.scope.variables[variableDefinition.variable.identifier] = variableDefinition.variable
