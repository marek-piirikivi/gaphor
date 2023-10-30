from typing import Union

from gaphas.connector import Handle, Port

from gaphor import UML
from gaphor.diagram.connectors import Connector, RelationshipConnect
from gaphor.SysML import sysml
from gaphor.SysML.blocks.block import BlockItem
from gaphor.SysML.blocks.interfaceblock import InterfaceBlockItem
from gaphor.SysML.blocks.property import ConstraintParameterItem, PropertyItem
from gaphor.SysML.blocks.proxyport import ProxyPortItem
from gaphor.UML.deployments import ConnectorItem


@Connector.register(InterfaceBlockItem, ProxyPortItem)
@Connector.register(BlockItem, ProxyPortItem)
@Connector.register(PropertyItem, ProxyPortItem)
class BlockProperyProxyPortConnector:
    def __init__(
        self,
        block_or_property: Union[BlockItem, PropertyItem, InterfaceBlockItem],
        proxy_port: ProxyPortItem,
    ) -> None:
        self.element = block_or_property
        self.proxy_port = proxy_port

    def allow(self, handle: Handle, port: Port) -> bool:
        return (
            bool(self.element.diagram)
            and self.element.diagram is self.proxy_port.diagram
            and (
                isinstance(self.element.subject, UML.EncapsulatedClassifier)
                or isinstance(self.element.subject, UML.Property)
                and isinstance(self.element.subject.type, UML.EncapsulatedClassifier)
            )
        )

    def connect(self, handle: Handle, port: Port) -> bool:
        """Connect and reconnect at model level.

        Returns `True` if a connection is established.
        """
        proxy_port = self.proxy_port
        if not proxy_port.subject:
            proxy_port.subject = proxy_port.model.create(sysml.ProxyPort)

        if isinstance(self.element.subject, UML.EncapsulatedClassifier):
            proxy_port.subject.encapsulatedClassifier = self.element.subject
        elif isinstance(self.element.subject, UML.Property) and isinstance(
            self.element.subject.type, UML.EncapsulatedClassifier
        ):
            proxy_port.subject.encapsulatedClassifier = self.element.subject.type

        # This raises the item in the item hierarchy
        assert proxy_port.diagram
        assert self.element.diagram is proxy_port.diagram
        proxy_port.change_parent(self.element)

        return True

    def disconnect(self, handle: Handle) -> None:
        proxy_port = self.proxy_port
        if proxy_port.subject and proxy_port.diagram:
            proxy_port.change_parent(None)
            proxy_port.subject = None


def create_constraint_parameter_connection(c1, c2, line):
    assert not line.subject
    assert allowed_item_connection(c1, c2)

    model = line.model

    c1_end = model.create(UML.ConnectorEnd)
    c1_end.role = c1.subject
    if isinstance(c1, ConstraintParameterItem) and not isinstance(
        c1.parent.subject, sysml.ConstraintBlock
    ):
        c1_end.partWithPort = c1.parent.subject

    c2_end = model.create(UML.ConnectorEnd)
    c2_end.role = c2.subject
    if isinstance(c2, ConstraintParameterItem) and not isinstance(
        c2.parent.subject, sysml.ConstraintBlock
    ):
        c2_end.partWithPort = c2.parent.subject

    connector = model.create(UML.Connector)
    connector.end = c1_end
    connector.end = c2_end
    connector.structuredClassifier = c1.subject.owner or c2.subject.owner
    line.subject = connector


def allowed_item_connection(c1, c2):
    def part_parameter_item(item, other_item):
        return (
            isinstance(item, ConstraintParameterItem)
            and item.parent
            and isinstance(item.parent.subject, UML.Property)
            and isinstance(item.parent.subject.type, sysml.ConstraintBlock)
            and isinstance(item.subject, sysml.ConstraintParameter)
            and item.subject in item.parent.subject.type.parameter
        )

    def value_item(item, other_item):
        return (
            isinstance(item, PropertyItem)
            and item.subject
            and isinstance(item.subject.type, sysml.ValueType)
        )

    def block_parameter_item(item, other_item):
        return (
            isinstance(item, ConstraintParameterItem)
            and item.parent
            and isinstance(item.parent.subject, sysml.ConstraintBlock)
            and item.subject in item.parent.subject.parameter
        )

    def block_part_parameter_item(item, other_item):
        return (
            part_parameter_item(item, other_item)
            and block_parameter_item(other_item, item)
            and item.parent.subject in other_item.parent.subject.ownedAttribute
        )

    allowed_connections = (
        (part_parameter_item, part_parameter_item),
        (part_parameter_item, value_item),
        (value_item, value_item),
        (block_parameter_item, block_part_parameter_item),
    )

    return any(
        end_1_pred(c1, c2)
        and end_2_pred(c2, c1)
        or end_1_pred(c2, c1)
        and end_2_pred(c1, c2)
        for end_1_pred, end_2_pred in allowed_connections
    )


@Connector.register(ProxyPortItem, ConnectorItem)
@Connector.register(PropertyItem, ConnectorItem)
class PropertyConnectorConnector(RelationshipConnect):
    """Connect a Connector to a Port or Property."""

    line: ConnectorItem
    element: Union[PropertyItem, ProxyPortItem]

    def allow(self, handle, port):
        element = self.element
        other_item = self.get_connected(self.line.head) or self.get_connected(
            self.line.tail
        )

        return (
            other_item
            and allowed_item_connection(other_item, self.element)
            or super().allow(handle, port)
            and isinstance(element.subject, (UML.Port, UML.Property))
            and not isinstance(element.subject.type, sysml.ConstraintBlock)
        )

    def connect_subject(self, handle):
        line = self.line
        c1 = self.get_connected(line.head)
        c2 = self.get_connected(line.tail)
        if c1 and c2 and not line.subject:
            assert isinstance(c1.subject, UML.ConnectableElement)
            assert isinstance(c2.subject, UML.ConnectableElement)

            if isinstance(c1, ConstraintParameterItem) or isinstance(
                c2, ConstraintParameterItem
            ):
                create_constraint_parameter_connection(c1, c2, line)
            else:
                connector = UML.recipes.create_connector(c1.subject, c2.subject)
                line.subject = connector
                connector.structuredClassifier = c1.subject.owner or c2.subject.owner


@Connector.register(ConstraintParameterItem, ConnectorItem)
class ConstraintParameterConnectorConnector(RelationshipConnect):
    line: ConnectorItem
    element: ConstraintParameterItem

    def allow(self, handle, port):
        other_item = self.get_connected(self.line.head) or self.get_connected(
            self.line.tail
        )
        return (
            not other_item
            or other_item
            and allowed_item_connection(other_item, self.element)
        ) and super().allow(handle, port)

    def connect_subject(self, handle):
        line = self.line
        c1 = self.get_connected(line.head)
        c2 = self.get_connected(line.tail)
        if c1 and c2 and not line.subject:
            create_constraint_parameter_connection(c1, c2, line)
