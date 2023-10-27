import math


class Expression:
    def fill_parameter_names(self, parameter_names):
        """Fills parameter names"""

    def evaluate(self, parameters):
        """Evaluates expression"""


class Parameter(Expression):
    def __init__(self, name: str):
        assert isinstance(name, str)
        self.name = name

    def fill_parameter_names(self, parameter_names):
        parameter_names.append(self.name)

    def evaluate(self, parameters):
        return parameters.get(self.name) or 0


class Function(Expression):
    def __init__(self, name: str, parameters):
        assert isinstance(name, str)
        self.name = name
        self.parameters = parameters

    def fill_parameter_names(self, parameter_names):
        for par in self.parameters:
            par.fill_parameter_names(parameter_names)

    def evaluate(self, parameters):
        if fnc := parameters.get(self.name):
            return fnc(*[par.evaluate(parameters) for par in self.parameters])
        return False


class Constant(Expression):
    def __init__(self, value):
        assert not math.isnan(value)
        self.value = value

    def fill_parameter_names(self, parameter_names):
        pass

    def evaluate(self, parameters):
        return self.value


class Arithmetic(Expression):
    def __init__(self, operator, lhs, rhs):
        assert operator in ("+", "-", "*", "/")
        assert isinstance(lhs, Expression)
        assert isinstance(rhs, Expression)

        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def fill_parameter_names(self, parameter_names):
        self.lhs.fill_parameter_names(parameter_names)
        self.rhs.fill_parameter_names(parameter_names)

    def evaluate(self, parameters):
        match self.operator:
            case "+":
                return self.lhs.evaluate(parameters) + self.rhs.evaluate(parameters)
            case "-":
                return self.lhs.evaluate(parameters) - self.rhs.evaluate(parameters)
            case "*":
                return self.lhs.evaluate(parameters) * self.rhs.evaluate(parameters)
            case "/":
                return self.lhs.evaluate(parameters) / self.rhs.evaluate(parameters)


class Comparisson(Expression):
    def __init__(self, operator, lhs, rhs):
        assert operator in ("<", "<=", "=", ">=", ">")
        assert isinstance(lhs, Expression)
        assert isinstance(rhs, Expression)

        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def fill_parameter_names(self, parameter_names):
        self.lhs.fill_parameter_names(parameter_names)
        self.rhs.fill_parameter_names(parameter_names)

    def evaluate(self, parameters) -> bool:
        match self.operator:
            case "<":
                return bool(
                    self.lhs.evaluate(parameters) < self.rhs.evaluate(parameters)
                )
            case "<=":
                return bool(
                    self.lhs.evaluate(parameters) <= self.rhs.evaluate(parameters)
                )
            case "=":
                return bool(
                    self.lhs.evaluate(parameters) == self.rhs.evaluate(parameters)
                )
            case ">=":
                return bool(
                    self.lhs.evaluate(parameters) >= self.rhs.evaluate(parameters)
                )
            case ">":
                return bool(
                    self.lhs.evaluate(parameters) > self.rhs.evaluate(parameters)
                )
        return False
