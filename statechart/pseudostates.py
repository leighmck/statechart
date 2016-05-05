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

from statechart import CompositeState, State


class PseudoState(State):
    """
    A pseudostate is an abstraction that encompasses different types of
    transient states. They are used, typically, to connect multiple transitions
    into more complex state transitions paths.

    :param name: An identifier for the model element.
    :param context: The parent context that contains this state.
    """

    def __init__(self, name, context):
        State.__init__(self, name=name, context=context, entry=None, do=None,
                       exit=None)

    def activate(self, metadata, param):
        """
        Activate the state.

        :param metadata: Statechart metadata data
        :param param: Transition parameter passed to state entry and do actions
        """
        metadata.activate(self)

        if self.entry:
            self.entry.execute(metadata=metadata, param=param)

        return True

    def dispatch(self, metadata, event, param):
        """
        Dispatch transition.

        :param metadata: Statechart metadata data
        :param event: Transition event trigger
        :param param: Transition parameter passed to transition action
        :return: True if transition executed, False if transition not allowed
            due to mismatched event trigger or failed guard condition.
        """
        return State.dispatch(self, metadata=metadata, event=event, param=param)


class InitialState(PseudoState):
    """
    A special kind of state signifying the source for a single transition to
    the default state of the composite state.

    :param name: An identifier for the model element.
    :param context: The parent context that contains this state.
    """

    def __init__(self, name, context):
        PseudoState.__init__(self, name=name, context=context)

        if self.context.initial_state:
            raise RuntimeError("Initial state already present")
        else:
            self.context.initial_state = self

    def activate(self, metadata, param):
        """
        Activate the state and dispatch transition to the default state of the
        composite state.

        :param metadata: Statechart metadata data
        :param param: Transition parameter passed to state entry and do actions
        """
        self.dispatch(metadata=metadata, event=None, param=param)


class ShallowHistoryState(PseudoState):
    def __init__(self, name, context):
        """
        A special kind of state signifying the source for a single transition
        to the most recent active state of its containing composite state (but
        not the substates of that substate).
        There can only be one history state per context.

        :param name: An identifier for the model element.
        :param context: The parent context that contains this state.
        """

        PseudoState.__init__(self, name=name, context=context)
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

        :param metadata: Statechart metadata data
        :param param: Transition parameter passed to state entry and do actions
        """
        if len(self.transitions) > 1:
            raise RuntimeError("History state cannot have more than 1 transition")

        if metadata.has_history_info(self):
            state = metadata.get_history_state(self)
            state.activate(metadata=metadata, param=param)
        else:
            self.dispatch(metadata=metadata, event=None, param=param)
