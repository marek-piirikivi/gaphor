from typing import Union

from gaphas.connector import Handle, Port

from gaphor import UML
from gaphor.diagram.connectors import Connector, RelationshipConnect
from gaphor.SysML import sysml
from gaphor.UML import uml
from gaphor.SysML.blocks.block import BlockItem
from gaphor.SysML.blocks.interfaceblock import InterfaceBlockItem
from gaphor.SysML.blocks.property import PropertyItem, ConstraintParameterItem
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
        assert block_or_property.diagram is proxy_port.diagram
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
        proxy_port.change_parent(self.element)

        return True

    def disconnect(self, handle: Handle) -> None:
        proxy_port = self.proxy_port
        if proxy_port.subject and proxy_port.diagram:
            subject = proxy_port.subject
            del proxy_port.subject
            proxy_port.change_parent(None)
            subject.unlink()


@Connector.register(ProxyPortItem, ConnectorItem)
@Connector.register(PropertyItem, ConnectorItem)
class PropertyConnectorConnector(RelationshipConnect):
    """Connect a Connector to a Port or Property."""

    line: ConnectorItem
    element: Union[PropertyItem, ProxyPortItem]

    def allow(self, handle, port):
        element = self.element

        # Element should be connected -> have a subject
        return super().allow(handle, port) and isinstance(
            element.subject, (UML.Port, UML.Property)
        )

    def connect_subject(self, handle):
        line = self.line

        c1 = self.get_connected(line.head)
        c2 = self.get_connected(line.tail)
        if c1 and c2 and not line.subject:
            assert isinstance(c1.subject, UML.ConnectableElement)
            assert isinstance(c2.subject, UML.ConnectableElement)
            connector = UML.recipes.create_connector(c1.subject, c2.subject)
            line.subject = connector
            connector.structuredClassifier = c1.subject.owner or c2.subject.owner


@Connector.register(ConstraintParameterItem, ConnectorItem)
class ConstraintParameterConnectorConnector(RelationshipConnect):
    def allow(self, handle, port):
        # TODO: check that only allow the connection ValueType typed property ←→ Constraintproperty ConstraintParameter

        return super().allow(handle, port)

    def connect_subject(self, handle):
        if self.line.subject:
            return

        c1 = self.get_connected(self.line.head)
        c2 = self.get_connected(self.line.tail)

        constraint_parameter_item = (
            c1 if isinstance(c1, ConstraintParameterItem) else c2
        )
        assert isinstance(constraint_parameter_item, ConstraintParameterItem)
        constraint_parameter = constraint_parameter_item.subject
        constraint_property = constraint_parameter_item.parent.subject

        connector_end = c2 if isinstance(c1, ConstraintParameterItem) else c1

        assert isinstance(connector_end, uml.ConnectorEnd)

        value_property = connector_end.subject
        assert isinstance(value_property, uml.Property)

        assert isinstance(constraint_property.type, sysml.ConstraintBlock)
        assert isinstance(value_property.type, sysml.ValueType)

        model = value_property.model

        end_value = model.create(uml.ConnectorEnd)
        end_value.role = value_property

        end_parameter = model.create(uml.ConnectorEnd)
        end_parameter.role = constraint_parameter
        end_parameter.partWithPort = constraint_property

        connector = model.create(uml.Connector)
        connector.end = end_value
        connector.end = end_parameter
        self.line.subject = connector
