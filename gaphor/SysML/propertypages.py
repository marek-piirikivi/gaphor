from __future__ import annotations

from gi.repository import Gtk

from gaphor import UML
from gaphor.core import transactional
from gaphor.core.format import format, parse
from gaphor.diagram.propertypages import (
    EditableTreeModel,
    PropertyPageBase,
    PropertyPages,
    handler_blocking,
    new_resource_builder,
    on_text_cell_edited,
    unsubscribe_all_on_destroy,
)
from gaphor.SysML import sysml
from gaphor.SysML.blocks.block import BlockItem
from gaphor.SysML.blocks.interfaceblock import InterfaceBlockItem
from gaphor.SysML.blocks.property import PropertyItem
from gaphor.SysML.blocks.proxyport import ProxyPortItem
from gaphor.UML.classes.classespropertypages import OperationsPage, on_keypress_event
from gaphor.UML.propertypages import TypedElementPropertyPage, list_of_classifiers

new_builder = new_resource_builder("gaphor.SysML")


@PropertyPages.register(sysml.Requirement)
class RequirementPropertyPage(PropertyPageBase):
    order = 15

    def __init__(self, subject: sysml.Requirement):
        super().__init__()
        assert subject
        self.subject = subject
        self.watcher = subject.watcher()

    def construct(self):
        builder = new_builder(
            "requirement-editor",
            "requirement-text-buffer",
            signals={
                "requirement-id-changed": (self._on_id_changed,),
            },
        )
        subject = self.subject

        entry = builder.get_object("requirement-id")
        entry.set_text(subject.externalId or "")

        text_view = builder.get_object("requirement-text")

        buffer = builder.get_object("requirement-text-buffer")
        if subject.text:
            buffer.set_text(subject.text)

        @handler_blocking(buffer, "changed", self._on_text_changed)
        def text_handler(event):
            if not text_view.props.has_focus:
                buffer.set_text(event.new_value)

        self.watcher.watch("text", text_handler)

        return unsubscribe_all_on_destroy(
            builder.get_object("requirement-editor"), self.watcher
        )

    @transactional
    def _on_id_changed(self, entry):
        self.subject.externalId = entry.get_text()

    @transactional
    def _on_text_changed(self, buffer):
        self.subject.text = buffer.get_text(
            buffer.get_start_iter(), buffer.get_end_iter(), False
        )


PropertyPages.register(BlockItem)(OperationsPage)
PropertyPages.register(InterfaceBlockItem)(OperationsPage)

PropertyPages.register(PropertyItem)(TypedElementPropertyPage)
PropertyPages.register(ProxyPortItem)(TypedElementPropertyPage)


@PropertyPages.register(BlockItem)
class CompartmentPage(PropertyPageBase):
    """An editor for Block items."""

    order = 30

    def __init__(self, item):
        super().__init__()
        self.item = item

    def construct(self):
        if not self.item.subject:
            return

        builder = new_builder(
            "compartment-editor",
            signals={
                "show-constraints-changed": (self._on_show_constraints_change,),
                "show-parts-changed": (self._on_show_parts_change,),
                "show-references-changed": (self._on_show_references_change,),
                "show-values-changed": (self._on_show_values_change,),
            },
        )

        show_constraints = builder.get_object("show-constraints")
        show_constraints.set_active(self.item.show_constraints)

        show_parts = builder.get_object("show-parts")
        show_parts.set_active(self.item.show_parts)

        show_references = builder.get_object("show-references")
        show_references.set_active(self.item.show_references)

        show_values = builder.get_object("show-values")
        show_values.set_active(self.item.show_values)

        return builder.get_object("compartment-editor")

    @transactional
    def _on_show_constraints_change(self, button, gparam):
        self.item.show_constraints = button.get_active()

    @transactional
    def _on_show_parts_change(self, button, gparam):
        self.item.show_parts = button.get_active()

    @transactional
    def _on_show_references_change(self, button, gparam):
        self.item.show_references = button.get_active()

    @transactional
    def _on_show_values_change(self, button, gparam):
        self.item.show_values = button.get_active()


@PropertyPages.register(InterfaceBlockItem)
class InterfaceBlockPage(PropertyPageBase):
    """An editor for InterfaceBlock items."""

    order = 30

    def __init__(self, item):
        super().__init__()
        self.item = item

    def construct(self):
        if not self.item.subject:
            return

        builder = new_builder(
            "interfaceblock-editor",
            signals={
                "show-values-changed": (self._on_show_values_change,),
            },
        )

        show_values = builder.get_object("show-values")
        show_values.set_active(self.item.show_values)

        return builder.get_object("interfaceblock-editor")

    @transactional
    def _on_show_values_change(self, button, gparam):
        self.item.show_values = button.get_active()


class ConstraintParameters(EditableTreeModel):
    """GTK tree model to edit class attributes."""

    def __init__(self, subject):
        super().__init__(subject, cols=(str, object))

    def find_type(self, name):
        type = next(
            (
                value_type
                for value_type in self._item.model.select(sysml.ValueType)
                if value_type.name == name
            ),
            None,
        )
        if not type:
            type = self._item.model.create(sysml.ValueType)
            # TODO: set parent as the closest package to the subject
            type.name = name

        return type

    def get_rows(self):
        for parameter in self._item.parameter:
            yield [format(parameter), parameter]

    def create_object(self):
        model = self._item.model
        parameter = model.create(sysml.ConstraintParameter)
        self._item.parameter.append(parameter)
        return parameter

    @transactional
    def set_object_value(self, row, col, value):
        parameter = row[-1]
        if col == 0:
            parse(parameter, value)
            row[0] = format(parameter)
        elif col == 1:
            row[0] = format(parameter)

    def swap_objects(self, o1, o2):
        return self._item.parameter.swap(o1, o2)

    def sync_model(self, new_order):
        self._item.parameter.order(
            lambda key: new_order.index(key) if key in new_order else -1
        )


class ConstraintExpressions(EditableTreeModel):
    """GTK tree model to edit class attributes."""

    def __init__(self, subject):
        super().__init__(subject, cols=(str, object))

    def get_rows(self):
        for expression in self._item.expression:
            yield [expression.text, expression]

    def create_object(self):
        model = self._item.model
        expression = model.create(sysml.ConstraintExpression)
        self._item.expression.append(expression)
        return expression

    @transactional
    def set_object_value(self, row, col, value):
        expression = row[-1]
        if col == 0:
            expression.text = value
            row[0] = expression.text
        elif col == 1:
            row[0] = expression.text

    def swap_objects(self, o1, o2):
        return self._item.parameter.swap(o1, o2)

    def sync_model(self, new_order):
        self._item.parameter.order(
            lambda key: new_order.index(key) if key in new_order else -1
        )


@PropertyPages.register(sysml.ConstraintBlock)
class ConstraintBlockExpressionsPage(PropertyPageBase):
    """An editor for ConstraintBlock."""

    order = 20

    def __init__(self, subject):
        super().__init__()
        self.subject = subject
        self.watcher = subject and subject.watcher()

    def construct(self):
        self.model = ConstraintExpressions(self.subject)

        builder = new_builder(
            "constraintblock-expressions-editor",
            signals={
                "edited": (on_text_cell_edited, self.model, 0),
            },
        )

        tree_view: Gtk.TreeView = builder.get_object("list")
        tree_view.set_model(self.model)
        controller = Gtk.EventControllerKey.new()
        tree_view.add_controller(controller)
        controller.connect("key-pressed", on_keypress_event, tree_view)

        return unsubscribe_all_on_destroy(
            builder.get_object("constraintblock-expressions-editor"), self.watcher
        )


@PropertyPages.register(sysml.ConstraintBlock)
class ConstraintBlockParametersPage(PropertyPageBase):
    """An editor for ConstraintBlock."""

    order = 30

    def __init__(self, subject):
        super().__init__()
        self.subject = subject
        self.watcher = subject and subject.watcher()

    def construct(self):
        self.model = ConstraintParameters(self.subject)

        builder = new_builder(
            "constraintblock-parameters-editor",
            signals={
                "edited": (on_text_cell_edited, self.model, 0),
            },
        )

        tree_view: Gtk.TreeView = builder.get_object("list")
        tree_view.set_model(self.model)
        controller = Gtk.EventControllerKey.new()
        tree_view.add_controller(controller)
        controller.connect("key-pressed", on_keypress_event, tree_view)

        return unsubscribe_all_on_destroy(
            builder.get_object("constraintblock-parameters-editor"), self.watcher
        )


@PropertyPages.register(sysml.Property)
class PropertyAggregationPropertyPage(PropertyPageBase):
    """An editor for Properties (a.k.a.

    attributes).
    """

    order = 30

    AGGREGATION = ("none", "shared", "composite")

    def __init__(self, subject: sysml.Property):
        super().__init__()
        self.subject = subject

    def construct(self):
        if not self.subject or isinstance(self.subject, UML.Port):
            return

        builder = new_builder(
            "property-aggregation-editor",
            signals={
                "aggregation-changed": (self._on_aggregation_change,),
            },
        )

        aggregation = builder.get_object("aggregation")
        aggregation.set_selected(self.AGGREGATION.index(self.subject.aggregation))

        return builder.get_object("property-aggregation-editor")

    @transactional
    def _on_aggregation_change(self, combo, _pspec):
        self.subject.aggregation = self.AGGREGATION[combo.get_selected()]


@PropertyPages.register(UML.Association)
@PropertyPages.register(sysml.Connector)
class ItemFlowPropertyPage(PropertyPageBase):
    """Item Flow on Connectors."""

    order = 35

    def __init__(self, subject: UML.Association | sysml.Connector):
        super().__init__()
        self.subject = subject

    @property
    def information_flow(self):
        subject = self.subject
        if isinstance(subject, sysml.Connector):
            iflows = subject.informationFlow
        elif isinstance(subject, UML.Relationship):
            iflows = subject.abstraction
        return iflows[0] if iflows else None

    def construct(self):
        if not self.subject:
            return

        builder = new_builder(
            "item-flow-editor",
            signals={
                "item-flow-active": (self._on_item_flow_active,),
                "item-flow-name-changed": (self._on_item_flow_name_changed,),
                "invert-direction-changed": (self._invert_direction_changed,),
            },
        )

        use_flow = builder.get_object("use-item-flow")
        self.entry = builder.get_object("item-flow-name")

        dropdown = builder.get_object("item-flow-type")
        model = list_of_classifiers(self.subject.model, UML.Classifier)
        dropdown.set_model(model)

        use_flow.set_active(isinstance(self.information_flow, sysml.ItemFlow))
        use_flow.set_sensitive(
            not (
                self.information_flow
                and type(self.information_flow) is UML.InformationFlow
            )
        )
        self.entry.set_sensitive(use_flow.get_active())
        if (iflow := self.information_flow) and iflow.itemProperty:
            assert isinstance(iflow, sysml.ItemFlow)
            self.entry.set_text(iflow.itemProperty.name or "")
            if iflow.itemProperty.type:
                dropdown.set_selected(
                    next(
                        n
                        for n, lv in enumerate(model)
                        if lv.value == iflow.itemProperty.type.id
                    )
                )

        dropdown.connect("notify::selected", self._on_item_flow_type_changed)

        return builder.get_object("item-flow-editor")

    @transactional
    def _on_item_flow_active(self, switch, gparam):
        active = switch.get_active()
        subject = self.subject
        iflow = self.information_flow
        if active and not iflow:
            if isinstance(subject, sysml.Connector):
                subject.informationFlow = create_item_flow(subject)
            elif isinstance(subject, UML.Relationship):
                subject.abstraction = create_item_flow(subject)
        elif not active and iflow:
            iflow.unlink()
        self.entry.set_sensitive(switch.get_active())
        self.entry.set_text("")

    @transactional
    def _on_item_flow_name_changed(self, entry):
        if not (iflow := self.information_flow):
            return

        assert isinstance(iflow, sysml.ItemFlow)
        iflow.itemProperty.name = entry.get_text()

    @transactional
    def _on_item_flow_type_changed(self, dropdown, _pspec):
        if not (iflow := self.information_flow):
            return

        assert isinstance(iflow, sysml.ItemFlow)
        if id := dropdown.get_selected_item().value:
            element = self.subject.model.lookup(id)
            assert isinstance(element, UML.Type)
            iflow.itemProperty.type = element
        else:
            del iflow.itemProperty.type

    @transactional
    def _invert_direction_changed(self, button):
        if not (iflow := self.information_flow):
            return

        iflow.informationSource, iflow.informationTarget = (
            iflow.informationTarget,
            iflow.informationSource,
        )


def create_item_flow(subject: UML.Association | sysml.Connector) -> sysml.ItemFlow:
    iflow = subject.model.create(sysml.ItemFlow)
    if isinstance(subject, sysml.Connector):
        iflow.informationSource = subject.end[0].role
        iflow.informationTarget = subject.end[1].role
    elif isinstance(subject, UML.Relationship):
        iflow.informationSource = subject.memberEnd[0]
        iflow.informationTarget = subject.memberEnd[1]
    iflow.itemProperty = subject.model.create(sysml.Property)
    return iflow
