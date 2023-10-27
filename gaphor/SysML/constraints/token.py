import re


class Token:
    pattern = ""

    def __init__(self, text: str):
        self.text = text


class Skip(Token):
    pattern = r"\s+"


class LeftParenthesis(Token):
    pattern = r"\("

    def __init__(self, text: str):
        super().__init__(text)
        assert text in ("(")


class RightParenthesis(Token):
    pattern = r"\)"

    def __init__(self, text: str):
        super().__init__(text)
        assert text in (")")


class AdditionSubtraction(Token):
    pattern = r"\+|\-"

    def __init__(self, text: str):
        super().__init__(text)
        assert text in ("+", "-")


class MultiplicationDivision(Token):
    pattern = r"\*|\/"

    def __init__(self, text: str):
        super().__init__(text)
        assert text in ("*", "/")


class Comparisson(Token):
    pattern = r"\<\=|\<|\>\=|\>|\="

    def __init__(self, text: str):
        super().__init__(text)
        assert text in ("<", "<=", "=", ">=", ">")


class Name(Token):
    pattern = "[A-Za-z_][A-Za-z0-9_]*"


class Number(Token):
    pattern = r"[0-9]+(\.[0-9]+)?"


class Comma(Token):
    pattern = r","


tokens = (
    Name,
    Number,
    LeftParenthesis,
    RightParenthesis,
    AdditionSubtraction,
    MultiplicationDivision,
    Comparisson,
    Comma,
    Skip,
)

full_pattern = "|".join(f"(?P<{token.__name__}>{token.pattern})" for token in tokens)


class Tokenizer:
    def __init__(self, text):
        self.iter = re.finditer(full_pattern, text)
        self.current_token = None
        self.advance()

    def __next__(self):
        m = next(self.iter, None)
        if m:
            return next(
                token(m.group(token.__name__))
                for token in tokens
                if m.group(token.__name__)
            )
        return None

    def current(self):
        return self.current_token

    def advance(self):
        current = self.current()

        self.current_token = next(self)
        while self.current_token and isinstance(self.current_token, Skip):
            self.current_token = next(self)

        return current
