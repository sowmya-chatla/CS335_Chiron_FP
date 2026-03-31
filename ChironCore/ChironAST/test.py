import sys
import os
sys.path.append(os.path.abspath(".."))

from antlr4 import *
from turtparse.tlangLexer import tlangLexer
from turtparse.tlangParser import tlangParser
from builder import astGenPass   

def test_input(input_text):
    input_stream = InputStream(input_text)
    lexer = tlangLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = tlangParser(stream)

    tree = parser.start()

    print(tree.toStringTree(recog=parser))

    builder = astGenPass()
    result = builder.visit(tree)

    print("=== FINAL IR ===")
    for i, instr in enumerate(result):
        print(i, instr)

if __name__ == "__main__":
    with open("../ex_milestone2/test5.tl") as f:
        test_input(f.read())