from gaphor.SysML.constraints import token, expression
from typing import List


class AbstractSyntaxTree:
    def __init__(self, root: expression.Expression):
        self.root = root

    def get_parameter_names(self):
        names: List[str] = []
        self.root.fill_parameter_names(names)
        unique_names = list(set(names))
        unique_names.sort()
        return unique_names

    def evaluate(self, parameters):
        return self.root.evaluate(parameters)


class AbstractSyntaxTreeError:
    def __init__(self, errors):
        self.errors = errors


class Success:
    pass


class Error:
    def __init__(self, errors):
        self.errors = errors

    def append(self, error):
        self.errors.append(error)


def parse_expression(text: str):
    """
    Parses according to the following grammar:
        C  → E _C E
        _C → "=" | "<" | ">" | "<=" | ">="
        E  → T _E
        _E → "+" T _E | "-" T _E | ε
        T  → F _T
        _T → "*" F _T | "/" F _T | ε
        F  → "(" E ")" | name ("(" P? ")")? | number
        P  → E _P?
        _P → "," E _P?
    """

    tokens = token.Tokenizer(text)
    stack: List[expression.Expression | str] = []

    def token_string(token: token.Token) -> str:
        if token:
            return token.text
        return "<none>"

    def C():
        # E _C E
        status = E()
        print(f"→E _C E: {status}")
        if isinstance(status, Success):
            status = _C()
            print(f"E →_C E: {status}")
            if isinstance(status, Success):
                status = E()
                print(f"E _C →E: {status}")
                if isinstance(status, Success):
                    assert 3 <= len(stack)
                    rhs = stack.pop()
                    op = stack.pop()
                    print("OP", op)
                    lhs = stack.pop()
                    expr = expression.Comparisson(op, lhs, rhs)
                    stack.append(expr)
                    return Success()
                else:
                    status.append("Constraint is expected to end with an expression")
                    return status
            else:
                status.append(
                    f'Expected comparisson operator, got "{token_string(tokens.current())}"'
                )
                return status
        else:
            status.append("Constraint is expected to start with an expression")
            return status

    def _C():
        # "=" | "<" | ">" | "<=" | ">="
        if isinstance(tokens.current(), token.Comparisson):
            stack.append(tokens.advance().text)
            return Success()
        return Error([])

    def E():
        # T _E
        status = T()
        if isinstance(status, Success):
            status = _E()
            if isinstance(status, Success):
                return Success()
            else:
                status.append('Expecting expression "_E"')
                return status
        else:
            status.append('Expecting expression "T"')
            return status

    def _E():
        # ("+"|"-") T _E | (end)
        if isinstance(tokens.current(), token.AdditionSubtraction):
            stack.append(tokens.advance().text)
            status = T()
            if isinstance(status, Success):
                assert 3 <= len(stack)
                rhs = stack.pop()
                op = stack.pop()
                lhs = stack.pop()
                expr = expression.Arithmetic(op, lhs, rhs)
                stack.append(expr)
                status = _E()
                if isinstance(status, Success):
                    return Success()
                else:
                    status.append('Expecting expression "_E"')
                    return status
            else:
                status.append('Expecting expression "T"')
                return status
        else:
            return Success()

    def T():
        # F _T?
        status = F()
        if isinstance(status, Success):
            _T()
            return Success()
        else:
            status.append('Expecting expression "F"')
            return status

    def _T():
        # ("*"|"/") F _T | (end)
        if isinstance(tokens.current(), token.MultiplicationDivision):
            stack.append(tokens.advance().text)
            status = F()
            if isinstance(status, Success):
                assert 3 <= len(stack)
                rhs = stack.pop()
                op = stack.pop()
                lhs = stack.pop()
                expr = expression.Arithmetic(op, lhs, rhs)
                stack.append(expr)
                status = _T()
                if isinstance(status, Success):
                    return Success()
                else:
                    status.append('Expecting expression "_T"')
                    return status
            else:
                status.append('Expecting expression "F"')
                return status
        else:
            return Success()

    def F():
        # "(" E ")" | name ("(" P? ")")? | number
        if isinstance(tokens.current(), token.LeftParenthesis):
            tokens.advance()
            status = E()
            if isinstance(status, Success):
                if isinstance(tokens.current(), token.RightParenthesis):
                    tokens.advance()
                    return Success()
                else:
                    return Error(
                        [f'Expecting ")", got "{token_string(tokens.current())}"']
                    )
            else:
                status.append('Expecting expression "E"')
                return status
        elif isinstance(tokens.current(), token.Name):
            name = tokens.advance().text
            if isinstance(tokens.current(), token.LeftParenthesis):
                tokens.advance()
                if isinstance(tokens.current(), token.RightParenthesis):
                    tokens.advance()
                    stack.append(expression.Function(name, []))
                    return Success()

                start_stack_size = len(stack)
                status = P()
                if isinstance(status, Success):
                    parameters = stack[start_stack_size:]
                    del stack[start_stack_size:]
                    if isinstance(tokens.current(), token.RightParenthesis):
                        tokens.advance()
                        stack.append(expression.Function(name, parameters))
                        return Success()
                    else:
                        return Error(
                            f'Expecting ")", got "{token_string(tokens.current())}"'
                        )
                else:
                    status.append('Expecting function parameters from expression "P"')
                    return status
            else:
                stack.append(expression.Parameter(name))
                return Success()
        elif isinstance(tokens.current(), token.Number):
            stack.append(expression.Constant(float(tokens.advance().text)))
            return Success()
        else:
            return Error(
                [
                    f'Expecting "(", <name> or <number>, got "{token_string(tokens.current())}"'
                ]
            )

    def P():
        # E _P?
        status = E()
        if isinstance(status, Success):
            return _P()
        else:
            status.append('Expecting expression "E"')
            return status

    def _P():
        # "," E _P?
        if isinstance(tokens.current(), token.Comma):
            tokens.advance()
            status = E()
            if isinstance(status, Success):
                return _P()
            else:
                status.append(
                    'Expecting expression "E" in function parameters after ","'
                )
                return status
        else:
            return Success()

    status = C()
    if isinstance(status, Success):
        if not tokens.current() and len(stack) == 1:
            root = stack.pop()
            assert isinstance(root, expression.Expression)
            return AbstractSyntaxTree(root)
        else:
            return AbstractSyntaxTreeError("Expression not fully parsed")

    return AbstractSyntaxTreeError(status.errors)
