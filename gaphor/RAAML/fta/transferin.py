"""Transfer In item definition."""

from gaphas.geometry import Rectangle

from gaphor.core.modeling import DrawContext
from gaphor.diagram.presentation import (
    Classified,
    ElementPresentation,
    text_from_package,
    text_name,
)
from gaphor.diagram.shapes import Box, IconBox, stroke
from gaphor.diagram.support import represents
from gaphor.RAAML import raaml
from gaphor.RAAML.fta.constants import DEFAULT_FTA_MAJOR
from gaphor.UML.shapes import text_stereotypes


@represents(raaml.TransferIn)
class TransferInItem(Classified, ElementPresentation):
    def __init__(self, diagram, id=None):
        super().__init__(diagram, id, width=DEFAULT_FTA_MAJOR, height=DEFAULT_FTA_MAJOR)

        self.watch("subject[NamedElement].name").watch(
            "subject[NamedElement].namespace.name"
        )

    def update_shapes(self, event=None):
        self.shape = IconBox(
            Box(
                draw=draw_transfer_in,
            ),
            text_stereotypes(self, lambda: [self.diagram.gettext("Transfer In")]),
            text_name(self),
            text_from_package(self),
        )


def draw_transfer_in(box, context: DrawContext, bounding_box: Rectangle):
    cr = context.cairo
    cr.move_to(0, bounding_box.height)
    cr.line_to(bounding_box.width, bounding_box.height)
    cr.line_to(bounding_box.width / 2.0, 0)
    cr.line_to(0, bounding_box.height)
    stroke(context, fill=True)
