
import glob
import os

# Antlr4
from antlr4 import *
from evcCompiler import evcCompiler
from evcLexer import evcLexer
from evcParser import evcParser
from evWriter import EvWriter

# Allocate a couple of flags to use as bool registers.
def process_file(ifpath):
    input_stream = FileStream(ifpath, encoding='utf-8')
    lexer = evcLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = evcParser(stream)
    tree = parser.prog()

    assembler = evcCompiler(ifpath)
    walker = ParseTreeWalker()
    walker.walk(assembler, tree)
    # print(assembler.labels)
    # print(assembler.strTbl)

    dirPath, ext = os.path.splitext(ifpath)
    leaf = os.path.basename(dirPath)
    ofpath = os.path.join("output", "{}.ev".format(leaf))
    evWriter = EvWriter()
    evWriter.write(assembler.labels, assembler.strTbl, ofpath)


def main():
    # print("Start")
    # Will be pulled in via imports.
    # for ifpath in glob.glob("scripts/lib/std/*.ev"):
    #     print("Processing file: ", ifpath)
    #     process_file(ifpath)
    for ifpath in glob.glob("scripts/src/*.evc"):
        print("Processing file: ", ifpath)
        process_file(ifpath)

if __name__ == "__main__":
    main()