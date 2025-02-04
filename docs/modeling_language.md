# Modeling Languages

Since version 2.0, Gaphor supports the concept of Modeling languages. This
allows for development of separate modeling languages separate from the Gaphor
core application.

The main language was, and will be UML. Gaphor now also supports a subset of
SysML, RAAML and the C4 model.

A modeling language in Gaphor is defined by a class implementing the
`gaphor.abc.ModelingLanguage` abstract base class. The modeling language should
be registered as a `gaphor.modelinglanguage` entry point.

The `ModelingLanguage` interface is fairly minimal. It allows other services to
look up elements and diagram items, as well as a toolbox, and diagram types.
However, the responsibilities of a modeling language do not stop there. Parts of
functionality will be implemented by registering handlers to a set of generic
functions.

But let's not get ahead of ourselves. What is the functionality a modeling
language implementation can offer?

* A data model (elements) and diagram items
* Diagram types
* A toolbox definition
* [Connectors](#connectors), allow diagram items to connect
* [Format/parse](#format-and-parse) model elements to and from a textual representation
* [Copy/paste](#copy-and-paste) behavior when element copying is not trivial,
  for example with more than one element is involved
* [Grouping](#grouping), allow elements to be nested in one another
* [Dropping](#dropping), allow elements to be dragged from the tree view onto a diagram
* [Automatic cleanup rules](#automated-model-cleanup) to keep the model consistent

The first three by functionalities are exposed by the `ModelingLanguage` class.
The other functionalities can be extended by adding handlers to the respective
generic functions.

Modeling languages can also provide new UI components. Those components are not loaded
directly when you import a modeling language package. Instead, they should be imported via
the `gaphor.modules` entrypoint.

* [Editor pages](#editor-property-pages), shown in the collapsible pane on the right side
* [Instant (diagram) editor popups](#instant-diagram-editor-popups)
* Special diagram interactions


```{eval-rst}
.. autoclass:: gaphor.abc.ModelingLanguage
   :members:
```

## Connectors

Connectors are used to connect one element to another.

Connectors should adhere to the `ConnectorProtocol`.
Normally you would inherit from `BaseConnector`.

```{eval-rst}
.. autoclass:: gaphor.diagram.connectors.BaseConnector
   :members:
```

## Format and parse

Model elements can be formatted to a simple text representation. For example, This is used in the Model Browser.
It isn't a full serialization of the model element.

In some cases it's useful to parse a text back into an object. This is done when you edit attributes and operations
on a class.

Not every ``format()`` needs to have an equivalent ``parse()`` function.

```{eval-rst}
.. function:: gaphor.core.format.format(element: Element) -> str

   Returns a human readable representation of the model element. In most cases this is just the name,
   however, properties (attributes) and operations are formatted more extensively:

   .. code::

      + attr: str
      + format(element: Element): string

.. function:: gaphor.core.format.parse(element: Element, text: str) -> None

   Parse ``text`` and populate ``element``. The element is populated with elements from the text. This may mean that
   new model elements are created as part of the parse process.
```

## Copy and paste

Copy and paste works out of the box for simple items: one diagram item with one model element (the `subject`).
It leverages the `load()` and `save()` methods of the elements to ensure all relevant data is copied.

Sometimes items need more than one model element to work. For example an Association: it has two association ends.

In those specific cases you need to implement your own copy and paste functions. To create such a thing you'll need to create
two functions: one for copying and one for pasting.

```{function} gaphor.diagram.copypaste.copy(obj: ~gaphor.core.modeling.Element) -> ~typing.Iterator[tuple[Id, Opaque]]

Create a copy of an element (or list of elements).
The returned type should be distinct, so the `paste()`
function can properly dispatch.
A copy function normally copies only the element and mandatory related elements. E.g. an Association needs two association ends.
```

```{function} gaphor.diagram.copypaste.paste(copy_data: Opaque, diagram: ~gaphor.core.modeling.Diagram, lookup: ~typing.Callable[[str], ~gaphor.core.modeling.Element | None]) -> ~typing.Iterator[~gaphor.core.modeling.Element]

Paste previously copied data. Based on the data type created in the
``copy()`` function, try to duplicate the copied elements.
Returns the newly created item or element.
```

Gaphor provides some convenience functions:

```{function} gaphor.diagram.copypaste.copy_full(items: ~typing.Collection[~gaphor.core.modeling.Element], lookup: ~typing.Callable[[Id], ~gaphor.core.modeling.Element | None] | None = None) -> CopyData:

Copy ``items``. The ``lookup`` function is used to look up owned elements (shown as child nodes in the Model Browser).
```

```{function} gaphor.diagram.copypaste.paste_link(copy_data: CopyData, diagram: ~gaphor.core.modeling.Diagram) -> set[~gaphor.core.modeling.Presentation]:

Paste a copy of the Presentation element to the diagram, but try to link the underlying model element.
A shallow copy.
```

```{function} gaphor.diagram.copypaste.paste_full(copy_data: CopyData, diagram: ~gaphor.core.modeling.Diagram) -> set[~gaphor.core.modeling.Presentation]:

Paste a copy of both Presentation and model element. A deep copy.
```

## Grouping

Grouping is done by dragging one item on top of another, in a diagram or in the tree view.

```{function} gaphor.diagram.group.group(parent: ~gaphor.core.modeling.Element, element: ~gaphor.core.modeling.Element) -> bool

Group an element in a parent element. The grouping can be based on ownership,
but other types of grouping are also possible.
```

```{function} gaphor.diagram.group.ungroup(parent: ~gaphor.core.modeling.Element, element: ~gaphor.core.modeling.Element) -> bool

Remove the grouping from an element.
The function needs to check if the provided `parent` node is the right one.
```

```{function} gaphor.diagram.group.can_group(parent_type: type[~gaphor.core.modeling.Element], element_or_type: type[~gaphor.core.modeling.Element] | ~gaphor.core.modeling.Element) -> bool

This function tries to determine if grouping is possible,
without actually performing a group operation.
This is not 100% accurate.
```

## Dropping

Dropping is performed by dragging an element from the tree view and drop it on a diagram.
This is an easy way to extend a diagram with already existing model elements.

```{function} gaphor.diagram.drop.drop(element: ~gaphor.core.modeling.Element, diagram: ~gaphor.core.modeling.Diagram, x: float, y: float) -> ~gaphor.core.modeling.Presentation | None

The drop function creates a new presentation for an element on the diagram.
For relationships, a drop only works if both connected elements are present in the
same diagram.

The big difference with dragging an element from the toolbox, is that dragging from the toolbox
will actually place a new ``Presentation`` element on the diagram. ``drop`` works the other way
around: it starts with a model element and creates an accompanying ``Presentation``.
```

## Automated model cleanup

Gaphor wants to keep the model in sync with the diagrams.

A little dispatch function is used to determine if a model element can be removed.

```{function} gaphor.diagram.deletable.deletable(element: ~gaphor.core.modeling.Element) -> bool

Determine if a model element can safely be removed.
```

## Editor property pages

The editor page is constructed from snippets. For example: almost each element has a name,
so there is a UI snippet that allows you to edit a name.

Each property page (snippet) should inherit from `PropertyPageBase`.

```{eval-rst}
.. autoclass:: gaphor.diagram.propertypages.PropertyPageBase
   :members:
```

## Instant (diagram) editor popups

When you double-click on an item in a diagram, a popup can show up, so you can easily change the name.

By default, this works for any named element. You can register your own inline editor function if you need to.

```{function} gaphor.diagram.instanteditors.instant_editor(item: ~gaphas.item.Item, view, event_manager: ~gaphor.core.eventmanager.EventManager, pos: tuple[int, int] | None = None) -> bool

Show a small editor popup in the diagram. Makes for
easy editing without resorting to the Element editor.

In case of a mouse press event, the mouse position
(relative to the element) are also provided.
```
