import pytest
from gi.repository import GLib

from gaphor.application import Session
from gaphor.core.modeling import Comment, Diagram
from gaphor.diagram.event import DiagramOpened
from gaphor.ui.abc import UIComponent
from gaphor.ui.event import ElementOpened


@pytest.fixture
def session():
    session = Session(
        services=[
            "event_manager",
            "component_registry",
            "element_factory",
            "modeling_language",
            "properties",
            "main_window",
            "model_browser",
            "diagrams",
            "toolbox",
            "element_editor",
            "export_menu",
            "tools_menu",
        ]
    )
    main_w = session.get_service("main_window")
    main_w.open()
    yield session
    session.shutdown()


def get_current_diagram(session):
    return (
        session.get_service("component_registry")
        .get(UIComponent, "diagrams")
        .get_current_diagram()
    )


def test_creation(session):
    assert get_current_diagram(session) is None


def test_show_diagram(session):
    element_factory = session.get_service("element_factory")
    diagram = element_factory.create(Diagram)

    event_manager = session.get_service("event_manager")
    event_manager.handle(DiagramOpened(diagram))
    assert get_current_diagram(session) == diagram


def test_close_diagram(session):
    element_factory = session.get_service("element_factory")
    diagram = element_factory.create(Diagram)

    event_manager = session.get_service("event_manager")
    event_manager.handle(DiagramOpened(diagram))

    diagrams = session.get_service("diagrams")
    diagrams.close_current_tab()

    assert not get_current_diagram(session)


def test_open_element_on_diagram(session):
    element_factory = session.get_service("element_factory")
    diagram = element_factory.create(Diagram)
    comment = element_factory.create(Comment)

    event_manager = session.get_service("event_manager")
    event_manager.handle(DiagramOpened(diagram))

    event_manager.handle(ElementOpened(comment))

    assert comment.presentation
    assert comment.presentation[0] in get_current_diagram(session).ownedPresentation


def test_update_diagram_name(session):
    element_factory = session.get_service("element_factory")
    diagram = element_factory.create(Diagram)

    event_manager = session.get_service("event_manager")
    event_manager.handle(DiagramOpened(diagram))

    diagram.name = "Foo"


def test_flush_model(session):
    element_factory = session.get_service("element_factory")
    diagram = element_factory.create(Diagram)

    event_manager = session.get_service("event_manager")
    event_manager.handle(DiagramOpened(diagram))

    element_factory.flush()


@pytest.mark.skip(reason="May cause funky window manager behavior")
def test_window_mode_maximized(session):
    main_window = session.get_service("main_window")
    properties = session.get_service("properties")

    main_window.window.unfullscreen()
    main_window.window.maximize()
    iteration(lambda: properties.get("ui.window-mode") == "maximized")

    assert properties.get("ui.window-mode") == "maximized"

    main_window.window.unmaximize()


@pytest.mark.skip(reason="May cause funky window manager behavior")
def test_window_mode_fullscreened(session):
    main_window = session.get_service("main_window")
    properties = session.get_service("properties")

    main_window.window.fullscreen()
    iteration(lambda: properties.get("ui.window-mode") == "fullscreened")

    assert properties.get("ui.window-mode") == "fullscreened"

    main_window.window.unfullscreen()


def test_window_mode_normal(session):
    main_window = session.get_service("main_window")
    properties = session.get_service("properties")

    main_window.window.unfullscreen()
    main_window.window.unmaximize()
    iteration(lambda: properties.get("ui.window-mode") == "")

    assert properties.get("ui.window-mode") == ""


def iteration(condition, timeout=5):
    sentinel = False

    def check_condition():
        nonlocal sentinel
        if condition():
            sentinel = True
        return GLib.SOURCE_REMOVE if sentinel else GLib.SOURCE_CONTINUE

    def do_timeout():
        nonlocal sentinel
        sentinel = True
        print("Check timed out")
        return GLib.SOURCE_REMOVE

    GLib.idle_add(check_condition, priority=GLib.PRIORITY_LOW)
    timeout_id = GLib.timeout_add(interval=timeout * 1_000, function=do_timeout)

    ctx = GLib.main_context_default()
    while ctx.pending():
        if sentinel:
            break
        ctx.iteration(False)

    GLib.source_remove(timeout_id)
