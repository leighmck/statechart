# -*- coding: utf-8 -*-
#
# Copyright (c) 2016, Leigh McKenzie
# All rights reserved.
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from statechart.runtime import Metadata


class State:
    """
    A State is a simple state that has no regions or submachine states.

    :param name: An identifier for the model element.
    :param context: The parent context that contains this state.
    :param entry: An optional procedure that is executed whenever this state is
        entered regardless of the transition taken to reach the state. If
        defined, entry actions are always executed to completion prior to any
        internal activity or transitions performed within the state.
    :param do: An optional activity that is executed while being in the state.
        The execution starts when this state is entered, and stops either by
        itself, or when the state is exited, whichever comes first.
    :param exit: An optional procedure that is executed whenever this state is
        exited regardless of which transition was taken out of the state. If
        defined, exit actions are always executed to completion only after all
        internal activities and transition actions have completed execution.
    """

    def __init__(self, name, context, entry=None, do=None, exit=None):
        self.name = name

        """ Context can be null only for the statechart """
        if context is None and (not isinstance(self, Statechart)):
            raise RuntimeError("Context cannot be null")

        self.context = context
        parent = context

        """ Recursively move up to get the statechart object """
        if parent is not None:
            while 1:
                if isinstance(parent, Statechart):
                    break

                if parent is None:
                    break

                parent = parent.context

            if isinstance(parent, Statechart):
                self.statechart = parent
            else:
                raise RuntimeError("Statechart not found - check hierarchy")

        self.entry = entry
        self.do = do
        self.exit = exit
        self.transitions = []

    def add_transition(self, transition):
        """
        Add a transition from this state

        Transitions with guards are checked first.

        :param transition: transition to add, can be a normal or internal
            transition.
        """
        if transition is None:
            raise RuntimeError("Cannot add null transition")

        if transition.guard:
            self.transitions.insert(0, transition)
        else:
            self.transitions.append(transition)

    def activate(self, metadata, param):
        """
        Activate the state.

        :param metadata: Statechart metadata data.
        :param param: Transition parameter passed to state entry and do
            actions.
        :return: True if state activated, False if already active.
        """
        activated = False

        if not metadata.is_active(self):
            metadata.activate(self)

            if self.entry:
                self.entry.execute(param)

            if self.do:
                self.do.execute(param)

            activated = True

        return activated

    def deactivate(self, metadata, param):
        """
        Deactivate the state.

        :param metadata: Statechart metadata data.
        :param param: Transition parameter passed to state exit action.
        :return: True if state deactivated, False if already inactive.
        """
        if metadata.is_active(self):

            if self.exit:
                self.exit.execute(param)

            metadata.deactivate(self)

    def dispatch(self, metadata, event, param):
        """
        Dispatch transition.

        :param metadata: Statechart metadata data.
        :param event: Transition event trigger.
        :param param: Transition parameter passed to transition action.
        :return: True if transition executed, False if transition not allowed,
            due to mismatched event trigger or failed guard condition.
        """
        status = False

        for transition in self.transitions:
            if transition.execute(metadata, event, param):
                status = True
                break

        return status


class Context(State):
    """
    Domain of the state. Needed for setting up the hierarchy. This class
    needn't be instantiated directly.

    :param name: An identifier for the model element.
    :param context: The parent context that contains this state.
    :param entry: An optional procedure that is executed whenever this state is
        entered regardless of the transition taken to reach the state. If
        defined, entry actions are always executed to completion prior to any
        internal activity or transitions performed within the state.
    :param do: An optional activity that is executed while being in the state.
        The execution starts when this state is entered, and stops either by
        itself, or when the state is exited, whichever comes first.
    :param exit: An optional procedure that is executed whenever this state is
        exited regardless of which transition was taken out of the state. If
        defined, exit actions are always executed to completion only after all
        internal activities and transition actions have completed execution.
    """

    def __init__(self, name, context, entry=None, do=None, exit=None):
        State.__init__(self, name=name, context=context, entry=entry, do=do,
                       exit=exit)
        self.initial_state = None


class FinalState(State):
    """
    A special kind of state signifying that the enclosing composite state or
    the entire state machine is completed.

    A final state cannot have transitions or dispatch other transitions.

    :param name: An identifier for the model element.
    :param context: The parent context that contains this state.
    """

    def __init__(self, name, context):
        State.__init__(self, name=name, context=context)

    def add_transition(self, transition):
        raise RuntimeError(
            "Cannot add a transition from the final state")

    def dispatch(self, metadata, event, param):
        raise RuntimeError("Cannot dispatch an event to the final state")


class CompositeState(Context):
    """
    A composite state is a state that contains other state vertices (states,
    pseudostates, etc.).

    :param name: An identifier for the model element.
    :param context: The parent context that contains this state.
    :param entry: An optional procedure that is executed whenever this state is
        entered regardless of the transition taken to reach the state. If
        defined, entry actions are always executed to completion prior to any
        internal activity or transitions performed within the state.
    :param do: An optional activity that is executed while being in the state.
        The execution starts when this state is entered, and stops either by
        itself, or when the state is exited, whichever comes first.
    :param exit: An optional procedure that is executed whenever this state is
        exited regardless of which transition was taken out of the state. If
        defined, exit actions are always executed to completion only after all
        internal activities and transition actions have completed execution.
    """

    def __init__(self, name, context, entry=None, do=None, exit=None):
        Context.__init__(self, name=name, context=context, entry=entry, do=do,
                         exit=exit)
        self.history = None

    def activate(self, metadata, param):
        """
        Activate the state.

        If the transition being activated leads to this state, activate
        the initial state.

        :param metadata: Statechart metadata data.
        :param param: Transition parameter passed to state entry and do
            actions.
        """
        Context.activate(self, metadata, param)

        # if metadata.transition and metadata.transition.end is self:
        self.initial_state.activate(metadata=metadata, param=param)

    def deactivate(self, metadata, param):
        """
        Deactivate the state.

        If this state contains a history state, store the currently active
        state in history so it can be restored once the history state is
        activated.

        :param metadata: Statechart metadata data.
        :param param: Transition parameter passed to state exit action.
        """
        state_runtime_data = metadata.active_states[self]

        if self.history:
            metadata.store_history_info(self.history, state_runtime_data.current_state)

        if metadata.is_active(state=state_runtime_data.current_state):
            state_runtime_data.current_state.deactivate(metadata=metadata, param=param)

        Context.deactivate(self, metadata, param)

    def dispatch(self, metadata, event, param):
        """
        Dispatch transition.

        :param metadata: Statechart metadata data.
        :param event: Transition event trigger.
        :param param: Transition parameter passed to transition action.
        :return: True if transition executed, False if transition not allowed,
            due to mismatched event trigger or failed guard condition.
        """
        if not metadata.active_states[self]:
            raise RuntimeError('Inactive composite state attempting to'
                               'dispatch transition')

        # See if the current child state can handle the event
        data = metadata.active_states[self]
        if data.current_state is None and self.initial_state:
            metadata.activate(self.initial_state)
            data.current_state.activate(metadata, param)

        if data.current_state and data.current_state.dispatch(metadata, event,
                                                              param):
            return True

        # Since none of the child states can handle the event, let this state
        # try handling the event.
        for transition in self.transitions:
            if transition.execute(metadata, event, param):
                return True

        return False


class Statechart(Context):
    """
    The main entry point for using the statechart framework. Contains all
    necessary methods for delegating incoming events to the substates.

    :param name: An identifier for the model element.
    :param param: The parent context that contains this state.
    """

    def __init__(self, name, param):
        Context.__init__(self, name=name, context=None, entry=None, do=None,
                         exit=None)
        self.param = param
        self.metadata = Metadata()

    def start(self):
        """
        Initialises the Statechart in the metadata. Sets the start state.

        Ensure the statechart has at least an initial state.
        """
        self.metadata.reset()
        self.metadata.activate(self)
        self.metadata.activate(self.initial_state)
        self.dispatch(None)

    def dispatch(self, event):
        """
        Calls the dispatch method on the current state.

        :param event: Transition event trigger.
        :return: True if transition executed.
        """
        current_state = self.metadata.active_states[self].current_state
        return current_state.dispatch(self.metadata, event, self.param)

    def add_transition(self, transition):
        raise RuntimeError("Cannot add transition to a statechart")
