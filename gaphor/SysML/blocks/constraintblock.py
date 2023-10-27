from gaphor.diagram.presentation import (
    Classified,
    ElementPresentation,
    from_package_str,
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


@represents(ConstraintBlock)
class ConstraintBlockItem(Classified, ElementPresentation[ConstraintBlock]):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id)

        self.watch(
            "subject[NamedElement].name"
        ).watch(
            "subject[NamedElement].name"
        ).watch(
            "subject[NamedElement].namespace.name"
        ).watch(
            "subject[Classifier].isAbstract", self.update_shapes
        ).watch(
            "subject[ConstraintBlock].expression", self.update_shapes
        ).watch(
            "subject[ConstraintBlock].parameter", self.update_shapes
        )

    def update_shapes(self, event=None):
        print([par.name for par in self.subject.parameter])

        def lazy_format(name):
            return lambda: name

        self.shape = Box(
            Box(
                Text(
                    text=lambda: stereotypes_str(
                        self.subject, ["constraint"]
                    )
                ),
                Text(
                    text=lambda: self.subject.name or "",
                    width=lambda: self.width - 4,
                    style={
                        "font-weight": FontWeight.BOLD,
                        "font-style": FontStyle.ITALIC
                        if self.subject and self.subject.isAbstract
                        else FontStyle.NORMAL,
                    },
                ),
                Text(
                    text=lambda: from_package_str(self),
                    style={"font-size": "x-small"},
                ),
                style={
                    "padding": (12, 4, 12, 4),
                    "justify-content": JustifyContent.START,
                },
            ),
            Box(
                Text(
                    text="constraints",
                    style={
                        "padding": (0, 0, 4, 0),
                        "font-size": "x-small",
                        "font-style": FontStyle.ITALIC,
                    },
                ),
                Text(
                    text=lambda: f"{{{self.subject.expression}}}" if self.subject.expression else "",
                    width=lambda: self.width - 4,
                    style={"text-align": TextAlign.CENTER}
                ),
                style={
                    "padding": (4, 4, 4, 4),
                    "min-height": 8,
                    "justify-content": JustifyContent.START,
                },
                draw=draw_top_separator,
            ),
            Box(
                Text(
                    text="parameters",
                    style={
                        "padding": (0, 0, 4, 0),
                        "font-size": "x-small",
                        "font-style": FontStyle.ITALIC,
                    },
                ),
                *(
                    Text(text=lazy_format(parameter.name), style={"text-align": TextAlign.LEFT})
                    for parameter in self.subject.parameter
                ),
                style={
                    "padding": (4, 4, 4, 4),
                    "min-height": 8,
                    "justify-content": JustifyContent.START,
                },
                draw=draw_top_separator,
            ),
            draw=draw_border,
        )
