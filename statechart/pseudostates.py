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

from statechart import CompositeState, State, Statechart


class PseudoState(State):
    """
    A pseudostate is an abstraction that encompasses different types of
    transient states. They are used, typically, to connect multiple transitions
    into more complex state transitions paths.

    Args:
        name (str): An identifier for the model element.
        context (Context): The parent context that contains this state.
    """

    def __init__(self, name, context):
        super().__init__(name=name, context=context)

    def activate(self, metadata, event):
        """
        Activate the state.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Event which led to the transition into this state.

        Returns:
            True if the state was activated.
        """
        metadata.activate(self)

        if self.entry:
            self.entry(metadata=metadata, event=event)

        return True


class InitialState(PseudoState):
    """
    A special kind of state signifying the source for a single transition to
    the default state of the composite state.

    Args:
        context (Context): The parent context that contains this state.
    """

    def __init__(self, context):
        super().__init__(name='Initial', context=context)

        if isinstance(self.context, CompositeState) or isinstance(self.context, Statechart):
            if self.context.initial_state:
                raise RuntimeError('Initial state already present')
            else:
                self.context.initial_state = self
        else:
            raise RuntimeError('Parent not a composite state or statechart')

    def activate(self, metadata, event):
        """
        Activate the state and dispatch transition to the default state of the
        composite state.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Event which led to the transition into this state.

        Returns:
            True if the state was activated.
        """
        self.dispatch(metadata=metadata, event=None)

        return True

    def dispatch(self, metadata, event):
        """
        Dispatch transition.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Transition event trigger.

        Returns:
            True if the transition was executed, False if transition was not
            triggered for this event or if the guard condition failed.

        Raises:
            RuntimeError: If the state could not dispatch transition
        """
        if super().dispatch(metadata=metadata, event=event):
            return True
        else:
            raise RuntimeError('Initial state must be able to dispatch transition')

    def add_transition(self, transition):
        """Add a transition from this state.

        An initial state must have a single transition. The transition must not need an
        event trigger or have a guard condition.

        Args:
            transition (Transition): Transition to add, must be an external transition.

        Raises:
            RuntimeError: If transition is invalid, or if transition already exists.
        """
        if len(self._transitions) is not 0:
            raise RuntimeError('There can only be a single transition from an initial state')
        elif transition.event is not None:
            raise RuntimeError('Transition from initial state must not require an event trigger')
        elif transition.guard is not None:
            raise RuntimeError('Transition from initial state cannot have a guard condition')
        else:
            super().add_transition(transition)


class ShallowHistoryState(PseudoState):
    def __init__(self, context):
        """
        Shallow history is a pseudo state representing the most recent
        substate of a submachine.

        A submachine can have at most one shallow history state. A transition
        with a history pseudo state as target is equivalent to a transition
        with the most recent substate as target. And very importantly, only
        one transition may originate from the history.

        Args:
            context (Context): The parent context that contains this state.
        """
        super().__init__(name='Shallow history', context=context)

        self.state = None

        if isinstance(self.context, CompositeState):
            if self.context.history:
                raise RuntimeError('"History state already present')
            else:
                self.context.history = self
        else:
            raise RuntimeError('Parent not a composite state')

    def activate(self, metadata, event):
        """
        Activate the state and dispatch transition to the default state of the
        composite state.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Event which led to the transition into this state.

        Returns:
            True if the state was activated.
        """
        if len(self._transitions) > 1:
            raise RuntimeError('History state cannot have more than 1 transition')

        if metadata.has_history_info(self):
            state = metadata.get_history_state(self)

            # Setup transition to the history's target state
            metadata.transition.start = self
            metadata.transition.end = state

            state.activate(metadata=metadata, event=event)
        else:
            self.dispatch(metadata=metadata, event=None)

        return True


class ChoiceState(PseudoState):
    """
    The Choice pseudo-state is used to compose complex transitional path which,
    which, when reached, result in the dynamic evaluation of the guards of the
    triggers of its outgoing transitions.

    It enables splitting of transitions into multiple outgoing paths.

    Args:
        context (Context): The parent context that contains this state.

    Note:
        It must have at least one incoming and one outgoing Transition.

        If none of the guards evaluates to true, then the model is considered ill-formed.
        To avoid this, it is recommended to define one outgoing transition with a
        predefined "else" guard for every choice vertex.
    """

    def __init__(self, context):
        super().__init__(name='Choice', context=context)

    def activate(self, metadata, event):
        """
        Activate the state and dispatch transition to the default state of the
        composite state.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): Event which led to the transition into this state.

        Returns:
            True if the state was activated.
        """
        for transition in self._transitions:
            if transition.execute(metadata=metadata, event=None):
                return True

        raise RuntimeError('No choice made due to guard conditions, '
                           'suggest to add transition with "Else" guard')

    def add_transition(self, transition):
        """Add a transition from this state.

        Transitions are checked in the order they are defined.

        Args:
            transition (Transition): Transition to add.

        Raises:
            RuntimeError: If transition is invalid.
        """
        if transition is None:
            raise RuntimeError('Cannot add null transition')

        self._transitions.append(transition)
