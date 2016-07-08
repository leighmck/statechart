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

import pytest
from statechart import (Action, Event, State, InitialState, InternalTransition,
                        Statechart, Transition)


class ActionSpy(Action):
    def __init__(self):
        self.executed = False

    def execute(self, event):
        self.executed = True


class StateSpy(State):
    def __init__(self, name, context):
        super().__init__(name=name, context=context)
        self.entry_executed = False
        self.do_executed = False
        self.exit_executed = False

    def entry(self, event):
        self.entry_executed = True

    def do(self, event):
        self.do_executed = True

    def exit(self, event):
        self.exit_executed = True


@pytest.fixture
def empty_statechart():
    statechart = Statechart(name='statechart')
    return statechart


class TestTransition:
    def test_create_transition(self, empty_statechart):
        initial_state = InitialState(name='initial', context=empty_statechart)
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(name='name', start=initial_state,
                                end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions
        assert transition in initial_state._transitions

        # When executed, the transition should be setup to deactivate the
        # initial state and to activate the next state
        assert initial_state in transition.deactivate
        assert next_state in transition.activate

    def test_create_cyclic_transition(self, empty_statechart):
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(name='name', start=next_state,
                                end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions.
        assert transition in next_state._transitions

        # When executed, the transition should be setup to deactivate the
        # next state and to re-activate it.
        assert next_state in transition.deactivate
        assert next_state in transition.activate


class TestInternalTransition:
    def test_execute(self, empty_statechart):
        initial_state = InitialState(name='initial', context=empty_statechart)
        default_state = StateSpy(name='next', context=empty_statechart)
        Transition(name='name', start=initial_state,
                   end=default_state)

        internal_event = Event(name='internal-event')
        internal_action = ActionSpy()
        InternalTransition(name='internal',
                           state=default_state,
                           event=internal_event,
                           guard=None,
                           action=internal_action)
        empty_statechart.start()

        assert empty_statechart.metadata.is_active(default_state)
        assert default_state.entry_executed is True
        assert default_state.do_executed is True
        assert default_state.exit_executed is False

        # Ensure we don't leave and re-enter the default state after triggering
        # the internal transition.
        default_state.entry_executed = False
        default_state.do_executed = False

        empty_statechart.dispatch(internal_event)

        assert default_state.entry_executed is False
        assert default_state.do_executed is False
        assert default_state.exit_executed is False

        assert internal_action.executed is True
