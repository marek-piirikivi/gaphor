from gaphor.abc import ActionProvider, Service
from gaphor.core import action
from gaphor.i18n import gettext

from gaphor.UML import uml
from gaphor.SysML import sysml

from gi.repository import Adw
import re


def full_property_name(property):
    name = property.name or ""
    type = property.type.name
    return f"{name}:{type}"


class ConstraintConnector:
    def __init__(self, value_property, constraint_parameter, constraint_property):
        self.value_property = value_property
        self.constraint_parameter = constraint_parameter
        self.constraint_property = constraint_property

    def __repr__(self):

        return f"{full_property_name(self.value_property)} ←→ \"{full_property_name(self.constraint_property)}\".{self.constraint_parameter.name}"


class TokenIterator:
    def __init__(self, tokens):
        self.tokens = tokens
        self.cursor = 0

    def next(self):
        self.cursor += 1
        return self.tokens[self.cursor - 1]

    def peek(self):
        if self.cursor < len(self.tokens):
            return self.tokens[self.cursor]
        return False

    def all_consumed(self):
        return self.cursor == len(self.tokens)


class Parameter:
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def __repr__(self):
        return f"<parameter> {self.name} → {self.value}"

    def tree(self, depth=0):
        return f"{' '*4*depth}{self.name} → {self.value}"

    def evaluate(self):
        return self.value


class Number:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"<number> {self.value}"

    def tree(self, depth=0):
        return f"{' '*4*depth}{self.value}"

    def evaluate(self):
        return self.value


class Comparisson:
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def tree(self, depth=1):
        return f"comparisson:\n{' '*depth*4}op: {self.op}\n{' '*depth*4}lhs:\n{self.lhs.tree(depth + 1)}\n{' '*depth*4}rhs:\n{self.rhs.tree(depth + 1)}"

    def evaluate(self):
        match self.op:
            case '=':
                return self.lhs.evaluate() == self.rhs.evaluate()
            case '>':
                return self.lhs.evaluate() > self.rhs.evaluate()
            case '<':
                return self.lhs.evaluate() < self.rhs.evaluate()
            case '>=':
                return self.lhs.evaluate() >= self.rhs.evaluate()
            case '<=':
                return self.lhs.evaluate() <= self.rhs.evaluate()


class Operation:
    def __init__(self, op, lhs, rhs):
        self.op = op
        self.lhs = lhs
        self.rhs = rhs

    def tree(self, depth=1):
        return f"{' '*depth*4}op: {self.op}\n{' '*depth*4}lhs:\n{self.lhs.tree(depth + 1)}\n{' '*depth*4}rhs:\n{self.rhs.tree(depth + 1)}"

    def evaluate(self):
        if self.op == "+":
            return self.lhs.evaluate() + self.rhs.evaluate()
        if self.op == "-":
            return self.lhs.evaluate() - self.rhs.evaluate()
        if self.op == "*":
            return self.lhs.evaluate() * self.rhs.evaluate()
        if self.op == "/":
            return self.lhs.evaluate() / self.rhs.evaluate()


class Parser:
    '''
    C  → E _C E
    _C → "=" | "<" | ">" | "<=" | ">="
    E  → T _E
    _E → "+" T _E | "-" T _E | ε
    T  → F _T
    _T → "*" F _T | "/" F _T | ε
    F  → "(" E ")" | parameter | number
    '''
    def __init__(self, tokens):
        assert isinstance(tokens, TokenIterator)
        self.tokens = tokens
        self.stack = []

    def get_ast(self):
        if self.C() and self.tokens.all_consumed():
            ast = self.stack.pop()

            # TODO: check that stack is completely empty
            # TODO: check that no tokens are left
            return ast
        # TODO: return error about parsing

    '''E _C E'''
    def C(self):
        if self.E():
            if self._C():
                if self.E():
                    rhs = self.stack.pop()
                    op = self.stack.pop()
                    lhs = self.stack.pop()
                    expr = Comparisson(op, lhs, rhs)
                    self.stack.append(expr)
                    return True

    '''"=" | "<" | ">" | "<=" | ">="'''
    def _C(self):
        if isinstance(self.tokens.peek(), str) and self.tokens.peek() in ("=", "<", ">", "<=", ">="):
            self.stack.append(self.tokens.next())
            return True

    '''T _E'''
    def E(self):
        if self.T():
            self._E()
            return True

    '''"+" T _E | "-" T _E | ε'''
    def _E(self):
        if isinstance(self.tokens.peek(), str) and self.tokens.peek() in ("+", "-"):
            self.stack.append(self.tokens.next())
            if self.T():
                rhs = self.stack.pop()
                op = self.stack.pop()
                lhs = self.stack.pop()
                expr = Operation(op, lhs, rhs)
                self.stack.append(expr)
                self._E()
                return True


    '''F _T'''
    def T(self):
        if self.F():
            self._T()
            return True

    '''"*" F _T | "/" F _T | ε'''
    def _T(self):
        if isinstance(self.tokens.peek(), str) and self.tokens.peek() in ("*", "/"):
            self.stack.append(self.tokens.next())
            if self.F():
                rhs = self.stack.pop()
                op = self.stack.pop()
                lhs = self.stack.pop()
                expr = Operation(op, lhs, rhs)
                self.stack.append(expr)
                self._T()
                return True

    '''"(" E ")" | parameter | number'''
    def F(self):
        if isinstance(self.tokens.peek(), str) and self.tokens.peek() == '(':
            self.tokens.next()
            if self.E():
                if isinstance(self.tokens.peek(), str) and self.tokens.peek() == ')':
                    self.tokens.next()
                    return True
        elif isinstance(self.tokens.peek(), (Parameter, Number)):
            self.stack.append(self.tokens.next())
            return True


class ConstraintProperty:
    def __init__(self, property, bindings):
        self.property = property
        self.bindings = bindings

    def tokens(self, expression: str) -> TokenIterator:
        def tokenize(txt):
            if re.match("^[a-zA-Z][a-zA-Z0-9_]*$", txt):
                return Parameter(txt, self.value(txt))
            elif re.match("^([0-9]+\.[0-9]+|[0-9]+)$", txt):
                return Number(float(txt))
            else:
                return txt

        str_tokens = re.findall("([a-zA-Z][a-zA-Z0-9_]*|\(|\)|\+|\-|\*|\/|<=|>=|>|<|=|[0-9]+\.[0-9]+|[0-9]+)", expression)

        return TokenIterator([tokenize(t) for t in str_tokens])

    def validate(self):
        tokens = self.tokens(self.property.type.expression)
        parser = Parser(tokens)
        ast = parser.get_ast()

        return (ast.evaluate(), ast)

    def value(self, name):
        return float(next(binding.value_property.defaultValue for binding in self.bindings if binding.constraint_parameter.name == name))

    def __repr__(self):
        def format(binding):
            return f"{full_property_name(binding.value_property)} = {binding.value_property.defaultValue} ←→ {binding.constraint_parameter.name}"

        return f"{full_property_name(self.property)}\n{{{self.property.type.expression}}}\n[{', '.join(format(binding) for binding in self.bindings)}]"


class ConstraintService(Service, ActionProvider):

    def __init__(self, element_factory, main_window, tools_menu=None):
        self.element_factory = element_factory
        self.main_window = main_window
        if tools_menu:
            tools_menu.add_actions(self)

    def shutdown(self):
        pass

    @action(name="validate-constraints", label=gettext("Validate constraints"))
    def validate_constraints(self):
        def constraint_connector(el):
            if not isinstance(el, uml.Connector):
                return False

            def is_property_end(end):
                return isinstance(end.role, uml.Property)

            def is_constraint_parameter_end(end):
                return isinstance(end.role, sysml.ConstraintParameter)

            if is_property_end(el.end[0]) and is_constraint_parameter_end(el.end[1]):
                return True

            if is_property_end(el.end[1]) and is_constraint_parameter_end(el.end[0]):
                return True

            return False

        def create_constraint_connector(connector):
            value_property = connector.end[0].role if isinstance(connector.end[0].role, uml.Property) else connector.end[1].role
            constraint_parameter, constraint_property = (connector.end[1].role, connector.end[1].partWithPort) if isinstance(connector.end[1].role, sysml.ConstraintParameter) else (connector.end[0].role, connector.end[0].partWithPort)

            return ConstraintConnector(value_property, constraint_parameter, constraint_property)

        constraint_connectors = [create_constraint_connector(conn) for conn in self.element_factory.select(constraint_connector)]

        def constraint_property(el):
            return isinstance(el, uml.Property) and isinstance(el.type, sysml.ConstraintBlock)

        def create_constraint_property(property):
            return ConstraintProperty(property, list(item for item in constraint_connectors if item.constraint_property and item.constraint_property.id == property.id))

        constraint_properties = [create_constraint_property(prop) for prop in self.element_factory.select(constraint_property)]

        results = [(prop, *prop.validate()) for prop in constraint_properties]
        problems = [(prop, is_valid, ast) for (prop, is_valid, ast) in results if not is_valid]

        window = self.main_window.window if self.main_window else None

        if len(problems):
            dialog = Adw.MessageDialog.new(window, "Constraints validated")
            options = "\n".join([f"{prop} {ast.tree()}" for (prop, _, ast) in problems])
            dialog.set_body(f'Some constraints are violated\n{options}')
            dialog.add_response("ok", gettext("OK"))
            dialog.set_visible(True)
        else:
            dialog = Adw.MessageDialog.new(window, "Constraints validated")
            dialog.set_body("All constraints are satisfied")
            dialog.add_response("ok", gettext("OK"))
            dialog.set_visible(True)

