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

from statechart import Event
from statechart import Statechart


class Transition:
    """
    A transition is a directed relationship between a source state and a target
    state. It may be part of a compound transition, which takes the state
    machine from one state configuration to another, representing the complete
    response of the state machine to a particular event instance.

    Args:
        start (State): The originating state (or pseudostate) of the
            transition.
        end (State): The target state (or pseudostate) that is reached when the
        transition is executed.
        event (Event|str): The event or event name that fires the transition.
        guard (Guard): A boolean predicate that  must be true for the
            transition to be fired. It is evaluated at the time the event is
            dispatched.
        action (Action): An optional procedure to be performed when the
            transition fires.
    """

    def __init__(self, start, end, event=None, guard=None, action=None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self.start = start
        self.end = end
        self.event = event
        self.guard = guard
        self.action = action

        if isinstance(event, str):
            self.event = Event(event)

        """ Used to store the states that will get activated """
        self.activate = list()

        """ Used to store the states that will get de-activated """
        self.deactivate = list()

        self._calculate_state_set(start=start, end=end)

        start.add_transition(self)

    def execute(self, metadata, event):
        """
        Attempt to execute the transition.
        Evaluate if the transition is allowed by checking the guard condition.
        If the transition is allowed, deactivate source states, perform
        transition action and activate all target states.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): The event that fires the transition.

        Returns:
            True if the transition was executed.
        """
        if not self.is_allowed(metadata=metadata, event=event):
            return False

        metadata.event = event
        metadata.transition = self

        if event:
            self._logger.info('Transition from  "%s" to "%s" due to event trigger "%s"',
                              self.start.name, self.end.name, event.name)
        else:
            self._logger.info('Default transition from  "%s" to "%s"',
                              self.start.name, self.end.name)

        for state in self.deactivate:
            state.deactivate(metadata=metadata, event=event)

        if self.action:
            self.action.execute(metadata=metadata, event=event)

        for state in self.activate:
            state.activate(metadata=metadata, event=event)

        metadata.transition = None
        metadata.event = None

        return True

    def is_allowed(self, metadata, event):
        """"
        Check if the transition is allowed.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): The event that fires the transition.

        Returns:
            True if the transition is allowed.
        """
        if self.event != event:
            return False

        if self.guard and not self.guard.check(metadata=metadata, event=event):
            return False

        return True

    def _calculate_state_set(self, start, end):
        """
        Calculate all the states which must be deactivated and then activated
        when triggering the transition.

        Args:
            start (State): The originating state (or pseudostate) of the transition.
            end (State): The target state (or pseudostate) that is reached when the transition is
                executed.
        """
        start_states = list()
        end_states = list()

        """ Recursively get all the context start states """
        s = start
        while s is not None:
            start_states.insert(0, s)
            context = s.context
            if context and not isinstance(context, Statechart):
                s = context
            else:
                s = None

        """ Recursively get all the context end states """
        e = end
        while e is not None:
            end_states.insert(0, e)
            context = e.context
            if context and not isinstance(context, Statechart):
                e = context
            else:
                e = None

        """ Get the Least Common Ancestor (LCA) of the start and end states """
        min_state_count = min(len(start_states), len(end_states))
        lca = min_state_count - 1

        if start is not end:
            lca = 0
            while lca < min_state_count:
                if start_states[lca] is not end_states[lca]:
                    break
                lca += 1

        """ Starting from the LCA get the states that will be deactivated """
        i = lca
        while i < len(start_states):
            self.deactivate.insert(0, start_states[i])
            i += 1

        """ Starting from the LCA get the states that will be activated """
        i = lca
        while i < len(end_states):
            self.activate.append(end_states[i])
            i += 1


class InternalTransition(Transition):
    """
    A transition that executes without exiting or re-entering the state in which it is defined.
    This is true even if the state machine is in a nested state within this state.

    Args:
        state (State): The state which owns this transition. The transition executes without
            exiting or re-entering this state.
        event (Event|str): The event or event name that fires the transition.
        guard (Guard): A boolean predicate that  must be true for the transition to be fired.
            It is evaluated at the time the event is dispatched.
        action (Action): An optional procedure to be performed when the transition fires.
    """

    def __init__(self, state, event=None, guard=None, action=None):
        super().__init__(start=state, end=state, event=event, guard=guard, action=action)
        self.deactivate.clear()
        self.activate.clear()

    def execute(self, metadata, event):
        """
        Attempt to execute the transition.
        Evaluate if the transition is allowed by checking the guard condition.
        If the transition is allowed perform transition action.

        Args:
            metadata (Metadata): Common statechart metadata.
            event (Event): The event that fires the transition.

        Returns:
            True if the transition was executed.
        """
        if not self.is_allowed(metadata=metadata, event=event):
            return False

        if self.action:
            self.action.execute(metadata=metadata, event=event)

        return True
