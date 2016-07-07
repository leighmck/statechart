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

import logging

from statechart import CompositeState, State


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
        State.__init__(self, name=name, context=context)
        self._logger = logging.getLogger(__name__)

    def activate(self, metadata, param):
        """
        Activate the state.

        Args:
            metadata (Metadata): Statechart metadata data.
            param: Transition parameter passed to state entry and do actions.

        Returns:
            True if the state was activated.
        """
        self._logger.info('activate %s', self.name)
        metadata.activate(self)

        if self.entry:
            self.entry(param=param)

        return True

    def dispatch(self, metadata, event, param):
        """
        Dispatch transition.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Transition event trigger.
            param: Transition parameter passed to transition action.

        Returns:
            True if the transition was executed, False if transition was not
            triggered for this event or if the guard condition failed.
        """
        self._logger.info('dispatch %s', self.name)
        return State.dispatch(self, metadata=metadata, event=event,
                              param=param)


class InitialState(PseudoState):
    """
    A special kind of state signifying the source for a single transition to
    the default state of the composite state.

    Args:
        name (str): An identifier for the model element.
        context (Context): The parent context that contains this state.
    """

    def __init__(self, name, context):
        PseudoState.__init__(self, name=name, context=context)
        self._logger = logging.getLogger(__name__)

        if self.context.initial_state:
            raise RuntimeError("Initial state already present")
        else:
            self.context.initial_state = self

    def activate(self, metadata, param):
        """
        Activate the state and dispatch transition to the default state of the
        composite state.

        Args:
            metadata (Metadata): Statechart metadata data.
            param: Transition parameter passed to state entry and do actions.

        Returns:
            True if the state was activated.
        """
        self._logger.info('activate %s', self.name)
        self.dispatch(metadata=metadata, event=None, param=param)
        return True


class ShallowHistoryState(PseudoState):
    def __init__(self, name, context):
        """
        Shallow history is a pseudo state representing the most recent
        substate of a submachine.

        A submachine can have at most one
        shallow history. A transition with a history pseudo state as
        target is equivalent to a transition with the most recent substate
        as target. And very importantly, only one transition may originate
        from the history.

        Args:
            name (str): An identifier for the model element.
            context (Context): The parent context that contains this state.
        """
        PseudoState.__init__(self, name=name, context=context)
        self._logger = logging.getLogger(__name__)

        self.state = None

        if isinstance(self.context, CompositeState):
            if self.context.history:
                raise RuntimeError("History state already present")
            else:
                self.context.history = self
        else:
            raise RuntimeError("Parent not a composite state")

    def activate(self, metadata, param):
        """
        Activate the state and dispatch transition to the default state of the
        composite state.

        Args:
            metadata (Metadata): Statechart metadata data.
            param: Transition parameter passed to state entry and do actions.

        Returns:
            True if the state was activated.
        """
        self._logger.info('activate %s', self.name)

        if len(self._transitions) > 1:
            raise RuntimeError("History state cannot have more than 1 "
                               "transition")

        if metadata.has_history_info(self):
            state = metadata.get_history_state(self)
            # Setup transition to the history's target state
            metadata.transition.start = self
            metadata.transition.end = state

            state.activate(metadata=metadata, param=param)
        else:
            self.dispatch(metadata=metadata, event=None, param=param)

        return True
