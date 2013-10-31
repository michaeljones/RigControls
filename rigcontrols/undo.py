

class Command(object):
    "Base class to provide NotImplemented warnings"

    def do(self):
        raise NotImplemented

    def undo(self):
        raise NotImplemented

    def redo(self):
        raise NotImplemented

class SetAttrCommand(Command):
    """Provides undoable setting of an attribute on a Python object. The code:

       myobject.counter = newCount

    Should modeled as:

       command = SetAttrCommand(myobject, "counter", newCount)

    This code does not account for the object_ not having an attribute called attrName already.
    """

    def __init__(self, object_, attrName, item):
        self.object_ = object_
        self.attrName = attrName
        self.item = item
        self.originalItem = None

    def do(self):
        "Store the original value and call redo"
        self.originalItem = getattr(self.object_, self.attrName)
        self.redo()

    def undo(self):
        "Set the original value to the attribute"
        setattr(self.object_, self.attrName, self.originalItem)

    def redo(self):
        "Set the new value to the attribute"
        setattr(self.object_, self.attrName, self.item)


class AppendCommand(Command):
    """Models the myobject.append(item) concept in an undoable way

    Assumes that the object follows the standard Python list interface of ``pop()`` being the
    opposite of ``append(item)``. It doesn't have to be a Python list though.
    """

    def __init__(self, object_, item):
        self.object_ = object_
        self.item = item

    def do(self):
        self.redo()

    def undo(self):
        self.object_.pop()

    def redo(self):
        self.object_.append(self.item)


class AddItemCommand(Command):
    """Models the myobject.addItem(item) concept in an undoable way

    Assumes that the object follows the Qt interface of ``removeItem()`` being the opposite of
    ``addItem(item)``.
    """

    def __init__(self, object_, item):
        self.object_ = object_
        self.item = item

    def do(self):
        self.redo()

    def undo(self):
        self.object_.removeItem(self.item)

    def redo(self):
        self.object_.addItem(self.item)

class CommandGroup(Command):
    """A groups of commands that are treated as a single command

    Can be used to break down operations into multiple steps but still have them as a single entry
    on the UndoStack.
    """

    def __init__(self, *commands):

        self.commands = commands

    def do(self):
        "Iterate over command list and call doIt on each one"

        for command in self.commands:
            command.do()

    def undo(self):
        """Iterate in reverse over the command list so that we undo each one in the reverse order to
        how we did them which is the expected behaviour for a sequence of operations
        """

        for command in reversed(self.commands):
            command.undo()

    def redo(self):
        "Iterate over command list and call redoIt on each one"

        for command in self.commands:
            command.redo()

class UndoStack(object):
    "Provides top level undo stack management for the application"

    def __init__(self):
        """Includes history stack for remembering commands which have been executed and could be
        undone and a future stack for commands which have been undone and could be redone."""

        self.history = []
        self.future = []

    def dispatch(self, command):
        "Executes the undo command and appends it"

        command.do()
        self.push(command)

    def push(self, command):
        """Introduces a new command so we clear out the current future stack as those previously
        undone commands are now out of date and should be unreachable and then we push the command
        to our history stack
        """

        self.future = []

        self.history.append(command)

    def undo(self):
        "Undoes the last dispatched/pushed command"

        command = self.history.pop()
        command.undo()
        self.future.append(command)

    def redo(self):
        "Redoes the last undone command"

        command = self.future.pop()
        command.redo()
        self.history.append(command)


