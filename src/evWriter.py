from core import *

class EvWriter:
    def write(self, labels, strTbl, ofpath):
        with open(ofpath, 'w') as ofobj:
            lines = []
            for labelIdx, label in labels.items():
                fmtCommands = []
                for command in label.commands:
                    fmtArgs = []
                    for arg in command.args:
                        if arg.argType == EvArgType.Value:
                            argVal = decode_int(arg.data)
                            if int(argVal) == argVal:
                                fmtArgs.append(str(int(argVal)))
                            else:
                                fmtArgs.append("{:03f}".format(argVal))
                        elif arg.argType == EvArgType.Work:
                            # Work
                            try:
                                evWork = EvWork(arg.data)
                                fmtArgs.append("@{}".format(evWork.name))
                            except ValueError: # Unknown work
                                fmtArgs.append("@{}".format(arg.data))
                        elif arg.argType == EvArgType.Flag:
                            # Flag
                            try:
                                evFlag = EvFlag(arg.data)
                                fmtArgs.append("#{}".format(evFlag.name))
                            except ValueError: # Unknown flag
                                fmtArgs.append("#{}".format(arg.data))  
                        elif arg.argType == EvArgType.SysFlag:
                            # SysFlag
                            try:
                                evSysFlag = EvSysFlag(arg.data)
                                fmtArgs.append("${}".format(evSysFlag.name))                    
                            except ValueError: # Unknown sys flag
                                fmtArgs.append("${}".format(arg.data))  
                        elif arg.argType == EvArgType.String:
                            strIdx = arg.data
                            strVal = strTbl[strIdx]
                            fmtArgs.append("'{}'".format(strVal))
                    commandName = ""
                    if type(command.cmdType) == EvCmdType:
                        commandName = command.cmdType.name
                    elif type(command.cmdType) == int:
                        commandName = EvCmdType(command.cmdType).name
                    fmtCommands.append("{}({})".format(
                        commandName,
                        ", ".join([str(arg) for arg in fmtArgs])
                    ))
                lines.append("{}:\n{}".format(
                    strTbl[labelIdx],
                    "\n".join(["\t{}".format(cmd) for cmd in fmtCommands])
                ))
            data = "\n".join(lines)
            ofobj.write(data)