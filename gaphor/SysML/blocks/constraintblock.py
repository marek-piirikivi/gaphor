from gaphor.core.format import format
from gaphor.diagram.presentation import (
    Classified,
    ElementPresentation,
)
from gaphor.diagram.shapes import (
    Box,
    JustifyContent,
    Text,
    TextAlign,
    draw_border,
    draw_top_separator,
)
from gaphor.diagram.support import represents
from gaphor.diagram.text import FontStyle, FontWeight
from gaphor.SysML.sysml import ConstraintBlock
from gaphor.UML.recipes import stereotypes_str
from gaphor.UML.umlfmt import format_property


@represents(ConstraintBlock)
class ConstraintBlockItem(Classified, ElementPresentation[ConstraintBlock]):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id)

        self.watch("subject[NamedElement].name", self.update_shapes).watch(
            "subject[NamedElement].name"
        ).watch("subject[NamedElement].namespace.name", self.update_shapes).watch(
            "subject[Class].ownedAttribute", self.update_shapes
        ).watch("subject[Class].ownedAttribute.name", self.update_shapes).watch(
            "subject[ConstraintBlock].expression", self.update_shapes
        ).watch("subject[ConstraintBlock].expression.text", self.update_shapes).watch(
            "subject[ConstraintBlock].parameter", self.update_shapes
        ).watch("subject[ConstraintBlock].parameter.name", self.update_shapes).watch(
            "subject[ConstraintBlock].parameter.type", self.update_shapes
        ).watch("subject[ConstraintBlock].parameter.type.name", self.update_shapes)

    def update_shapes(self, event=None):
        self.shape = Box(
            Box(
                Text(text=lambda: stereotypes_str(self.subject, ["constraint"])),
                Text(
                    text=lambda: self.subject.name or "",
                    style={
                        "font-weight": FontWeight.BOLD,
                        "font-style": FontStyle.ITALIC
                        if self.subject and self.subject.isAbstract
                        else FontStyle.NORMAL,
                    },
                ),
                style={
                    "padding": (12, 4, 12, 4),
                    "justify-content": JustifyContent.START,
                },
            ),
            # Constraints
            Box(
                Text(
                    text=self.diagram.gettext("constraints"),
                    style={
                        "padding": (0, 0, 4, 0),
                        "font-size": "x-small",
                        "font-style": FontStyle.ITALIC,
                    },
                ),
                *(
                    [
                        Text(
                            text=f"{{{expression.text}}}",
                            style={"text-align": TextAlign.LEFT},
                        )
                        for expression in self.subject.expression
                    ]
                ),
                *(
                    [
                        Text(
                            text=format_property(attribute),
                            style={"text-align": TextAlign.LEFT},
                        )
                        for attribute in self.subject.ownedAttribute
                        if isinstance(attribute.type, ConstraintBlock)
                    ]
                ),
                style={
                    "padding": (4, 4, 4, 4),
                    "min-height": 8,
                    "justify-content": JustifyContent.START,
                },
                draw=draw_top_separator,
            ),
            # Parameters
            Box(
                Text(
                    text=self.diagram.gettext("parameters"),
                    style={
                        "padding": (0, 0, 4, 0),
                        "font-size": "x-small",
                        "font-style": FontStyle.ITALIC,
                    },
                ),
                *(
                    [
                        Text(
                            text=format(parameter),
                            style={"text-align": TextAlign.LEFT},
                        )
                        for parameter in self.subject.parameter
                    ]
                ),
                style={
                    "padding": (4, 4, 4, 4),
                    "min-height": 8,
                    "justify-content": JustifyContent.START,
                },
                draw=draw_top_separator,
            ),
            style={
                "justify-content": JustifyContent.START,
            },
            draw=draw_border,
        )
