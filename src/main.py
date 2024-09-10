
import glob

# Antlr4
from antlr4 import *
from evcCompiler import evcCompiler
from evcLexer import evcLexer
from evcParser import evcParser

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

def main():
    for ifpath in glob.glob("scripts/lib/std/*.ev"):
        print("Processing file: ", ifpath)
        process_file(ifpath)
    for ifpath in glob.glob("scripts/src/*.ev"):
        print("Processing file: ", ifpath)
        process_file(ifpath)

if __name__ == "__main__":
    main()