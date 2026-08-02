from tongalang.ast_visualizer import format_ast
from tongalang.parser import parse_source


def test_format_ast_renders_program_tree():
    program = parse_source("""
    mulimo matalikilo() {
        zina x = 1
        amba(x)
    }
    """)

    tree = format_ast(program)

    assert "Program" in tree
    assert "FunctionDecl name=matalikilo" in tree
    assert "VarDecl name=x" in tree
    assert "OutputStmt" in tree
