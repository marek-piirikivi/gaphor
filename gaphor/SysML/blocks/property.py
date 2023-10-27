"""Property item."""

from typing import Sequence, Union

from gaphor import UML
from gaphor.core.modeling.properties import attribute
from gaphor.core.styling import FontWeight, JustifyContent
from gaphor.diagram.presentation import (
    ElementPresentation,
    Named,
    AttachedPresentation,
)
from gaphor.diagram.shapes import (
    Box,
    Text,
    draw_border,
    IconBox,
    TextAlign,
    VerticalAlign,
)
from gaphor.diagram.support import represents
from gaphor.UML.classes.stereotype import stereotype_compartments
from gaphor.UML.umlfmt import format_property
from gaphor.SysML import sysml


@represents(UML.Property)
class PropertyItem(Named, ElementPresentation[UML.Property]):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id)

        self.watch("show_stereotypes", self.update_shapes)
        self.watch("subject[Property].name")
        self.watch("subject[Property].type.name")
        self.watch("subject[Property].lowerValue")
        self.watch("subject[Property].upperValue")
        self.watch("subject.appliedStereotype", self.update_shapes)
        self.watch("subject.appliedStereotype.classifier.name")
        self.watch("subject.appliedStereotype.slot", self.update_shapes)
        self.watch("subject.appliedStereotype.slot.definingFeature.name")
        self.watch("subject.appliedStereotype.slot.value", self.update_shapes)
        self.watch("subject[Property].aggregation", self.update_shapes)

    show_stereotypes: attribute[int] = attribute("show_stereotypes", int)

    def justify(self) -> JustifyContent:
        if self.diagram and self.children:
            return JustifyContent.START
        else:
            return JustifyContent.CENTER

    def dash(self) -> Sequence[Union[int, float]]:
        if self.subject and self.subject.aggregation != "composite":
            return (7.0, 5.0)
        else:
            return ()

    def update_shapes(self, event=None):
        if self.subject and isinstance(self.subject.type, sysml.ConstraintBlock):
            self.shape = Box(
                Text(text=lambda: format_property(self.subject, type=True)),
                Text(
                    text=lambda: f"{{{self.subject.type.expression}}}",
                    style={"font-size": "x-small"},
                ),
                style={
                    "justify-content": JustifyContent.CENTER,
                    "border-radius": 10,
                },
                draw=draw_border,
            )

            self.update_parameters()
        else:
            self.shape = Box(
                Box(
                    Text(
                        text=lambda: UML.recipes.stereotypes_str(self.subject),
                    ),
                    Text(
                        text=lambda: format_property(
                            self.subject, type=True, multiplicity=True
                        )
                        or "",
                        style={"font-weight": FontWeight.BOLD},
                    ),
                    style={"padding": (12, 4, 12, 4)},
                ),
                *(
                    self.show_stereotypes
                    and stereotype_compartments(self.subject)
                    or []
                ),
                style={
                    "justify-content": self.justify(),
                    "dash-style": self.dash(),
                },
                draw=draw_border,
            )

    def update_parameters(self):
        pass
        # Find all parameters from the expressions
        # TODO: draw property parameters
        # if self.subject.type.parameter:
        #     return

        # expression = self.subject.type.expression or ""

        # def unique(items):
        #     unique_list = []
        #     for x in items:
        #         if operator.countOf(unique_list, x) == 0:
        #             unique_list.append(x)
        #     return unique_list

        # parameter_names = unique(findall(r"([a-zA-Z_][_a-zA-Z0-9]*)", expression))

        # for name in parameter_names:
        #     if name not in [par.name for par in self.subject.type.parameter]:
        #         param = self.subject.model.create(sysml.ConstraintParameter)
        #         param.name = name
        #         self.subject.type.parameter.append(param)

        # for param in self.subject.type.parameter:
        #     item = self.diagram.create(
        #         ConstraintParameterItem, parent=self, subject=param
        #     )
        #     item.matrix.translate(0, 0)
        #     connect(item, item.handles()[0], self)


def text_position(position):
    return {
        "text-align": TextAlign.RIGHT if position == "left" else TextAlign.LEFT,
        "vertical-align": VerticalAlign.TOP
        if position == "bottom"
        else VerticalAlign.BOTTOM,
    }


@represents(sysml.ConstraintParameter)
class ConstraintParameterItem(AttachedPresentation[sysml.ConstraintParameter]):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id, width=16, height=16)

    def update_shapes(self, event=None):
        position = self.connected_side()
        self.update_width(
            self.width,
            factor=0 if position == "right" else 1 if position == "left" else 0.5,
        )
        self.update_height(
            self.width,
            factor=0 if position == "bottom" else 1 if position == "top" else 0.5,
        )

        self.shape = IconBox(
            Box(draw=draw_border),
            Text(text=lambda: self.subject.name),
            style=text_position(self.connected_side()),
        )
