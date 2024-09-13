import logging
import sys
import os


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

from core import *
from scope_mgr import ScopeManager

class evcCompiler(evcListener):
    def __init__(self, ifpath):
        self.logger = logging.getLogger(__name__)
        self.src_ifpath = ifpath
        self.labels = {}
        self.strTbl = []
        self.writer = EndianBinaryWriter()
        self.scope_mgr = ScopeManager()
    
    def parseNumberContext(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return float(ctx.NUMBER().getText())

    def parseNumberContextInt(self, ctx:evcParser.NumberContext):
        if ctx is None:
            return None
        return int(ctx.NUMBER().getText())
    
    def parseStringContext(self, ctx:evcParser.String_Context):
        strValue = ctx.STRING().getText()
        print(strValue)
        return self.addStringToTable(strValue)

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

        self.scope_mgr.addCommand(identifier, Command(
            identifier,
            storage,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        ))

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

    def parseBlock(self, ctx:evcParser.BlockContext, allocator):
        self.scope_mgr.push()
        for blockEntry in ctx.blockEntry():
            if blockEntry.variableDefinition() is not None:
                variableDefinition = self.parseVariableDefinition(blockEntry.variableDefinition(), allocator, True)
                self.scope_mgr.addVariable(variableDefinition.variable.identifier, variableDefinition.variable)
        self.scope_mgr.pop()

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
            functionCall = self.parseFunctionCall(ctx.functionCall())
            # TODO: Translate into commands
            print(functionCall)
            if type(functionCall.function) == Function:
                self.logger.error("Function calls returning a value aren't currently supported: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            else:
                commands.extend(self.compileCommandCall(ctx, functionCall, storage, eArgType))
            sys.exit()
        else:
            self.logger.error("Unknown variable declaration at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        return commands
    
    def compileCommandCall(self, ctx, cmdCall: FunctionCall, eArgTypeRet: ECommandArgType, retStorage: int):
        commands = []
        if eArgTypeRet != cmdCall.function.retArg.eArgType:
            # Note: Looks like passed in eArgTypeRet is probably not accurate here.
            self.logger.error("Invalid return type of command ({} != {}) for variable at: {}:{}:{}".format(eArgTypeRet, cmdCall.function.retArg.eArgType, self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        
        args = []
        foundReturn = False
        for arg in cmdCall.args:
            if arg.isConst:
                if arg.constValueType in (ECommandArgType.Integer, ECommandArgType.Float):
                    args.append(EvArg(EvArgType.Value, arg.constValue))
                elif arg.constValueType == ECommandArgType.String:
                    args.append(EvArg(EvArgType.String, arg.constValue))
                elif arg.constValueType == ECommandArgType.Boolean:
                    self.logger.error("Not possible to pass const bool to command at: {}:{}:{}. Must use flag/sysflag for storage.".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
                else:
                    self.logger.error("I missed something it seems at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
            else:
                if arg.variable.eArgType in (ECommandArgType.Integer, ECommandArgType.Float):
                    args.append(EvArg(EvArgType.Work, arg.variable.storage))
                elif arg.variable.eArgType == ECommandArgType.Flag:
                    args.append(EvArg(EvArgType.Flag, arg.variable.storage))
                elif arg.variable.eArgType == ECommandArgType.SysFlag:
                    args.append(EvArg(EvArgType.SysFlag, arg.variable.storage))
                else:
                    self.logger.error("I missed something it seems at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                    sys.exit()
        if not foundReturn:
            args = [EvArg(EvArgType.Work, retStorage)] + args

        commands.append(
            EvCmd(cmdCall.Command.storage, [
                args 
            ])
        )

        return commands

    def mapFuncCallArg(self, ctx:evcParser.FuncCallArgContext):
        if ctx.Identifier() is not None:
            identifier = ctx.Identifier().getText()
            variable = self.scope_mgr.resolveVariable(identifier)
            if variable is None:
                self.logger.error("Unable to resolve variable name at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            # Translate const variable into the actual value
            if variable.isConst:
                return FunctionCallArg(None, True, variable.constValue, variable.eArgType)
            return FunctionCallArg(variable, False, None, None)
        if ctx.string_() is not None:
            strValue = self.parseStringContext(ctx.string_())
            if strValue is None:
                self.logger.error("Unable to parse string at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            return FunctionCallArg(None, True, strValue, ECommandArgType.String)
        
        if ctx.number() is not None:
            number = self.parseNumberContext(ctx.number())
            if number is None:
                self.logger.error("Unable to parse number at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            return FunctionCallArg(None, True, number, ECommandArgType.Float)

    def parseFuncCallArgList(self, ctx:evcParser.FuncCallArgListContext):
        return map(self.mapFuncCallArg, ctx.funcCallArg())

    def parseFunctionCall(self, ctx:evcParser.FunctionCallContext):
        identifier = None
        if ctx.Identifier() is not None:
            identifier = ctx.Identifier()
        if ctx.ScopedIdentifier() is not None:
            identifier = ctx.ScopedIdentifier()
        if identifier is None:
            self.logger.error("Unable to parse function/command name at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            sys.exit()
        identifier = identifier.getText()
        args = self.parseFuncCallArgList(ctx.funcCallArgList())

        command = self.scope_mgr.resolveCommand(identifier)
        if command is not None:
            return FunctionCall(command, args)
        else:
            function = self.scope_mgr.resolveFunction(identifier)
            if function is None:
                self.logger.error("Unable to resolve function/command name at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
            return FunctionCall(function, args)


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
        
        self.scope_mgr.addFunction(identifier, Function(
            specifier,
            label.nameIdx,
            identifier,
            retArg,
            args,
            ctx.start.line,
            ctx.start.column
        ))

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
            self.scope_mgr.wildCardImport(assembler.scope_mgr)
        else:
            identifiers = [identifierTkn.getText() in ctx.fromImportRhs().Identifier()]
            foundIdentifiers = self.scope_mgr.fromImport(assembler.scope_mgr, identifiers)
            if not foundIdentifiers:
                self.logger.error("Unable to retrieve identifier {} at: {}:{}:{}".format(identifier, self.src_ifpath, ctx.start.line, ctx.start.column))
                sys.exit()
    
    def enterImport_(self, ctx:evcParser.Import_Context):
        assembler = self.handleImport(ctx, ctx.Identifier().getText())
        assembler.scope_mgr.getGlobalScope().prefix = ctx.Identifier().getText()
        self.scope_mgr.addChildGlobal(assembler.scope_mgr.getGlobalScope())

    def enterProgEntry(self, ctx:evcParser.ProgEntryContext):
        if ctx.variableDefinition() is not None:
            # print("Processing variable definition")
            allocator = lambda ctx, eArgType: self.logger.error("Unable to allocate work at this scope at: {}:{}:{}".format(self.src_ifpath, ctx.start.line, ctx.start.column))
            variableDefinition = self.parseVariableDefinition(ctx.variableDefinition(), allocator, True)
            self.scope_mgr.addVariable(variableDefinition.variable.identifier, variableDefinition.variable)