import pytest

from gaphor import UML
from gaphor.diagram.connectors import Connector
from gaphor.diagram.tests.fixtures import allow, connect, disconnect
from gaphor.SysML import sysml
from gaphor.SysML.blocks.block import BlockItem
from gaphor.SysML.blocks.connectors import BlockProperyProxyPortConnector
from gaphor.SysML.blocks.constraintblock import ConstraintBlockItem
from gaphor.SysML.blocks.property import ConstraintParameterItem, PropertyItem
from gaphor.SysML.blocks.proxyport import ProxyPortItem
from gaphor.UML.deployments import ConnectorItem


@pytest.fixture
def block_item(diagram, element_factory):
    return diagram.create(BlockItem, subject=element_factory.create(sysml.Block))


@pytest.fixture
def property_item(diagram, element_factory):
    type = element_factory.create(sysml.Block)
    prop = diagram.create(PropertyItem, subject=element_factory.create(sysml.Property))
    prop.subject.type = type
    return prop


@pytest.fixture
def proxy_port_item(diagram):
    return diagram.create(ProxyPortItem)


def connected_proxy_port_item(diagram, element_factory):
    proxy_port_item = diagram.create(ProxyPortItem)
    block_item = diagram.create(BlockItem, subject=element_factory.create(sysml.Block))

    connector = Connector(block_item, proxy_port_item)
    connector.connect(proxy_port_item.handles()[0], block_item.ports()[0])

    return proxy_port_item


@pytest.fixture
def head_proxy_port_item(diagram, element_factory):
    return connected_proxy_port_item(diagram, element_factory)


@pytest.fixture
def tail_proxy_port_item(diagram, element_factory):
    return connected_proxy_port_item(diagram, element_factory)


@pytest.fixture
def other_proxy_port_item(diagram, element_factory):
    return connected_proxy_port_item(diagram, element_factory)


@pytest.fixture
def connector_item(diagram):
    return diagram.create(ConnectorItem)


def test_connection_is_allowed(block_item, proxy_port_item):
    connector = Connector(block_item, proxy_port_item)

    assert isinstance(connector, BlockProperyProxyPortConnector)
    assert connector.allow(proxy_port_item.handles()[0], block_item.ports()[0])


def test_connect_proxy_port_to_block(block_item, proxy_port_item):
    connector = Connector(block_item, proxy_port_item)

    connected = connector.connect(proxy_port_item.handles()[0], block_item.ports()[0])

    assert connected
    assert proxy_port_item.subject
    assert proxy_port_item.subject.encapsulatedClassifier is block_item.subject
    assert proxy_port_item.subject in block_item.subject.ownedPort


def test_disconnect_proxy_port_to_block(block_item, proxy_port_item):
    connector = Connector(block_item, proxy_port_item)
    connector.connect(proxy_port_item.handles()[0], block_item.ports()[0])

    connector.disconnect(proxy_port_item.handles()[0])

    assert proxy_port_item.subject is None
    assert proxy_port_item.diagram


def test_connect_proxy_port_to_property(property_item, proxy_port_item):
    connector = Connector(property_item, proxy_port_item)

    connected = connector.connect(
        proxy_port_item.handles()[0], property_item.ports()[0]
    )

    assert connected
    assert proxy_port_item.subject
    assert proxy_port_item.subject.encapsulatedClassifier is property_item.subject.type
    assert proxy_port_item.subject in property_item.subject.type.ownedPort


def test_allow_connector_to_proxy_port(
    connector_item: ConnectorItem, head_proxy_port_item: ProxyPortItem
):
    assert allow(connector_item, connector_item.handles()[0], head_proxy_port_item)


def test_connect_connector_on_one_end_to_proxy_port(
    connector_item: ConnectorItem, head_proxy_port_item: ProxyPortItem
):
    connect(connector_item, connector_item.handles()[0], head_proxy_port_item)

    assert connector_item.subject is None


def test_connect_connector_on_both_ends_to_proxy_port(
    connector_item: ConnectorItem,
    head_proxy_port_item: ProxyPortItem,
    tail_proxy_port_item: ProxyPortItem,
):
    connect(connector_item, connector_item.handles()[0], head_proxy_port_item)
    connect(connector_item, connector_item.handles()[1], tail_proxy_port_item)

    assert connector_item.subject
    assert head_proxy_port_item.subject in connector_item.subject.end[:].role
    assert tail_proxy_port_item.subject in connector_item.subject.end[:].role


def test_disconnect_connector_from_proxy_port(
    connector_item: ConnectorItem,
    head_proxy_port_item: ProxyPortItem,
    tail_proxy_port_item: ProxyPortItem,
    element_factory,
):
    connect(connector_item, connector_item.handles()[0], head_proxy_port_item)
    connect(connector_item, connector_item.handles()[1], tail_proxy_port_item)

    disconnect(connector_item, connector_item.handles()[0])

    assert not connector_item.subject
    assert element_factory.lselect(UML.Connector) == []
    assert element_factory.lselect(UML.ConnectorEnd) == []
    assert head_proxy_port_item.subject in element_factory.select(UML.Port)
    assert tail_proxy_port_item.subject in element_factory.select(UML.Port)


@pytest.fixture
def value_item(element_factory, diagram):
    value_type = element_factory.create(sysml.ValueType)
    value_property = element_factory.create(UML.Property)
    value_property.type = value_type
    return diagram.create(PropertyItem, subject=value_property)


@pytest.fixture
def part_constraint_parameter_item(element_factory, diagram):
    constraint = element_factory.create(sysml.ConstraintBlock)
    parameter = element_factory.create(sysml.ConstraintParameter)
    constraint.parameter = parameter

    constraint_property = element_factory.create(UML.Property)
    constraint_property.type = constraint

    property_item = diagram.create(PropertyItem, subject=constraint_property)
    return diagram.create(
        ConstraintParameterItem, subject=parameter, parent=property_item
    )


@pytest.fixture
def block_constraint_parameter_item(element_factory, diagram):
    constraint = element_factory.create(sysml.ConstraintBlock)
    parameter = element_factory.create(sysml.ConstraintParameter)
    constraint.parameter = parameter

    block_item = diagram.create(ConstraintBlockItem, subject=constraint)
    return diagram.create(ConstraintParameterItem, subject=parameter, parent=block_item)


@pytest.fixture
def other_part_constraint_parameter_item(part_constraint_parameter_item):
    return part_constraint_parameter_item


def test_constraint_parameter_binding_from_block_parameter_to_part_parameter(
    block_constraint_parameter_item,
    part_constraint_parameter_item,
    connector_item,
    element_factory,
):
    block_constraint_parameter_item.parent.subject.ownedAttribute = (
        part_constraint_parameter_item.parent.subject
    )

    connect(
        connector_item, connector_item.handles()[0], block_constraint_parameter_item
    )
    connect(connector_item, connector_item.handles()[1], part_constraint_parameter_item)

    assert connector_item.subject.end[0].role == block_constraint_parameter_item.subject
    assert not connector_item.subject.end[0].partWithPort
    assert connector_item.subject.end[1].role == part_constraint_parameter_item.subject
    assert (
        connector_item.subject.end[1].partWithPort
        == part_constraint_parameter_item.parent.subject
    )

    disconnect(connector_item, connector_item.handles()[0])

    assert not connector_item.subject
    assert element_factory.lselect(UML.Connector) == []
    assert element_factory.lselect(UML.ConnectorEnd) == []
    assert part_constraint_parameter_item.subject
    assert block_constraint_parameter_item.subject


def test_constraint_parameter_binding_from_part_parameter_to_block_parameter(
    part_constraint_parameter_item,
    block_constraint_parameter_item,
    connector_item,
    element_factory,
):
    block_constraint_parameter_item.parent.subject.ownedAttribute = (
        part_constraint_parameter_item.parent.subject
    )

    connect(connector_item, connector_item.handles()[0], part_constraint_parameter_item)
    connect(
        connector_item, connector_item.handles()[1], block_constraint_parameter_item
    )

    assert connector_item.subject.end[0].role == part_constraint_parameter_item.subject
    assert (
        connector_item.subject.end[0].partWithPort
        == part_constraint_parameter_item.parent.subject
    )
    assert connector_item.subject.end[1].role == block_constraint_parameter_item.subject
    assert not connector_item.subject.end[1].partWithPort

    disconnect(connector_item, connector_item.handles()[0])

    assert not connector_item.subject
    assert element_factory.lselect(UML.Connector) == []
    assert element_factory.lselect(UML.ConnectorEnd) == []
    assert part_constraint_parameter_item.subject
    assert block_constraint_parameter_item.subject


def test_constraint_parameter_binding_from_value_to_parameter(
    value_item, part_constraint_parameter_item, connector_item, element_factory
):
    connect(connector_item, connector_item.handles()[0], value_item)
    connect(connector_item, connector_item.handles()[1], part_constraint_parameter_item)

    assert connector_item.subject.end[0].role == value_item.subject
    assert not connector_item.subject.end[0].partWithPort
    assert connector_item.subject.end[1].role == part_constraint_parameter_item.subject
    assert (
        connector_item.subject.end[1].partWithPort
        == part_constraint_parameter_item.parent.subject
    )

    disconnect(connector_item, connector_item.handles()[0])

    assert not connector_item.subject
    assert element_factory.lselect(UML.Connector) == []
    assert element_factory.lselect(UML.ConnectorEnd) == []
    assert value_item.subject
    assert part_constraint_parameter_item.subject


def test_constraint_parameter_binding_from_parameter_to_value(
    value_item, part_constraint_parameter_item, connector_item, element_factory
):
    connect(connector_item, connector_item.handles()[0], part_constraint_parameter_item)
    connect(connector_item, connector_item.handles()[1], value_item)

    assert connector_item.subject.end[0].role == part_constraint_parameter_item.subject
    assert (
        connector_item.subject.end[0].partWithPort
        == part_constraint_parameter_item.parent.subject
    )
    assert connector_item.subject.end[1].role == value_item.subject
    assert not connector_item.subject.end[1].partWithPort

    disconnect(connector_item, connector_item.handles()[0])

    assert not connector_item.subject
    assert element_factory.lselect(UML.Connector) == []
    assert element_factory.lselect(UML.ConnectorEnd) == []
    assert value_item.subject
    assert part_constraint_parameter_item.subject


def test_constraint_parameter_binding_from_parameter_to_parameter(
    part_constraint_parameter_item,
    other_part_constraint_parameter_item,
    connector_item,
    element_factory,
):
    connect(connector_item, connector_item.handles()[0], part_constraint_parameter_item)
    connect(
        connector_item,
        connector_item.handles()[1],
        other_part_constraint_parameter_item,
    )

    assert connector_item.subject.end[0].role == part_constraint_parameter_item.subject
    assert (
        connector_item.subject.end[0].partWithPort
        == part_constraint_parameter_item.parent.subject
    )
    assert (
        connector_item.subject.end[1].role
        == other_part_constraint_parameter_item.subject
    )
    assert (
        connector_item.subject.end[1].partWithPort
        == other_part_constraint_parameter_item.parent.subject
    )

    disconnect(connector_item, connector_item.handles()[0])

    assert not connector_item.subject
    assert element_factory.lselect(UML.Connector) == []
    assert element_factory.lselect(UML.ConnectorEnd) == []
    assert part_constraint_parameter_item.subject
    assert other_part_constraint_parameter_item.subject
