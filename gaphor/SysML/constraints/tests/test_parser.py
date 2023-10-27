from gaphor.SysML.constraints.parser import (
    parse_expression,
    AbstractSyntaxTree,
    AbstractSyntaxTreeError,
)


def test_parser_no_parameters():
    ast = parse_expression("1 + 2 = 3")

    assert isinstance(ast, AbstractSyntaxTree)
    assert not ast.get_parameter_names(), "No parameters in this expression"
    assert ast.evaluate(), "One plus two equals three"


def test_parser_with_parameters():
    ast = parse_expression("a + b = 3")

    assert isinstance(ast, AbstractSyntaxTree)
    assert ast.get_parameter_names() == ["a", "b"]
    assert ast.evaluate({"a": 1, "b": 2}), "One plus two equals three"
    assert not ast.evaluate({"a": 1, "b": 7}), "One plus seven does not equal three"


def test_parser_with_function_call():
    ast = parse_expression("a + 2 = min(1 + 2, 7 - 2 * (1 - 1))")
    assert isinstance(ast, AbstractSyntaxTree)
    assert ast.evaluate({"a": 1, "min": min})
    assert not ast.evaluate({"a": 1, "min": lambda p0, p1: 100})


def test_parser_with_parameterless_function_call():
    ast = parse_expression("1 + 2 = f()")
    assert isinstance(ast, AbstractSyntaxTree)
    assert not ast.evaluate({"f": lambda: 4})
    assert ast.evaluate({"f": lambda: 3})


def test_parser_with_nested_function_calls():
    ast = parse_expression("5 = f(g(1, f(2, 3)), 9)")
    assert isinstance(ast, AbstractSyntaxTree)
    assert ast.evaluate({"f": lambda a, b: a + b, "g": lambda a, b: a - b})


def test_parser_error():
    ast = parse_expression("1 + 2 / b <= a / 9 +")

    assert isinstance(ast, AbstractSyntaxTreeError)
    assert ast.errors
    assert ast.errors[0] == 'Expecting "(", <name> or <number>, got "<none>"'
