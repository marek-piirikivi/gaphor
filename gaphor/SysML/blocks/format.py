import re

from gaphor.core.format import format, parse
from gaphor.SysML.sysml import ConstraintParameter, ValueType


@format.register(ConstraintParameter)
def format_constraint_parameter(parameter: ConstraintParameter, **kwargs) -> str:
    type_name = (
        f": {parameter.type.name}" if parameter.type and parameter.type.name else ""
    )
    name = f"{parameter.name}" if parameter.name else ""
    return f"{name}{type_name}"


@parse.register
def parse_constraint_parameter(parameter: ConstraintParameter, text: str) -> None:
    def find_type(name: str):
        return next(
            (
                value_type
                for value_type in parameter.model.select(ValueType)
                if value_type.name == name
            ),
            None,
        )

    m = re.match(
        r"^\s*([a-zA-Z_]+[a-zA-Z_0-9]*)?\s*(:\s*([a-zA-Z_]+[a-zA-Z_0-9]*))?\s*$", text
    )

    if not m:
        return

    if name := m.group(1):
        parameter.name = name

    if type_name := m.group(3):
        parameter.type = find_type(type_name)
