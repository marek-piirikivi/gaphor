from gaphor.diagram.drop import drop
from gaphor.diagram.copypaste import copy, paste
from gaphor.UML.uml import Activity, CallBehaviorAction, Action
from gaphor.diagram.support import get_diagram_item
from gaphor.diagram.group import change_owner


@drop.register
def drop_activity(element: Activity, diagram, x, y):
    if element is diagram.element:
        item_class = get_diagram_item(Activity)
        if not item_class:
            return None

        item = diagram.create(item_class, subject=element)
        assert item
        item.matrix.translate(x, y)

        return item
    else:
        def drop_distance_to_item(item):
            local_x, local_y = item.matrix_i2c.inverse().transform_point(x, y)
            return item.point(local_x, local_y)

        closest_drop_action_item = min(
            diagram.select(
                lambda item: isinstance(item.subject, Action)
            ),
            key=drop_distance_to_item,
            default=None,
        )

        if not closest_drop_action_item or 0 < drop_distance_to_item(closest_drop_action_item):
            item_class = get_diagram_item(CallBehaviorAction)
            if not item_class:
                return None

            subject = diagram.model.create(CallBehaviorAction)
            subject.activity = diagram.element
            closest_drop_action_item = diagram.create(item_class, subject=subject)
            closest_drop_action_item.matrix.translate(x, y)
        elif not isinstance(closest_drop_action_item.subject, CallBehaviorAction):
            item_class = get_diagram_item(CallBehaviorAction)
            if not item_class:
                return None

            subject = diagram.model.create(CallBehaviorAction)
            subject.activity = diagram.element
            item = diagram.create(item_class, subject=subject)
            item.change_parent(closest_drop_action_item.parent)
            xx, yx, xy, yy, x0, y0 = closest_drop_action_item.matrix.tuple()
            item.matrix.set(xx, yx, xy, yy, x0, y0)
            item.change_parent(closest_drop_action_item.parent)

            closest_drop_action_item.unlink()
            closest_drop_action_item = item

        closest_drop_action_item.subject.behavior = element

        return closest_drop_action_item
