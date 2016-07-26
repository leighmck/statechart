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

from statechart import (Action, CompositeState, Event, State, InitialState, InternalTransition,
                        Statechart, Transition)


class ActionSpy(Action):
    def __init__(self):
        self.executed = False

    def execute(self, scope, event):
        self.executed = True


@pytest.fixture
def empty_statechart():
    statechart = Statechart(name='statechart')
    return statechart


class TestTransition:
    class StateSpy(CompositeState):
        def __init__(self, name, context):
            super().__init__(name=name, context=context)

            # Count state entries and exit
            self.entries = 0
            self.exits = 0

            init = InitialState(name='init', context=self)
            self.default = State(name='default', context=self)
            self.local = State(name='local', context=self)

            Transition(name='init', start=init, end=self.default)

        def entry(self, event):
            self.entries += 1

        def exit(self, event):
            self.exits += 1

    def test_create_transition(self, empty_statechart):
        initial_state = InitialState(name='initial', context=empty_statechart)
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(name='name', start=initial_state, end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions
        assert transition in initial_state._transitions

        # When executed, the transition should be setup to deactivate the
        # initial state and to activate the next state
        assert initial_state in transition.deactivate
        assert next_state in transition.activate

    def test_create_cyclic_transition(self, empty_statechart):
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(name='name', start=next_state, end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions.
        assert transition in next_state._transitions

        # When executed, the transition should be setup to deactivate the
        # next state and to re-activate it.
        assert next_state in transition.deactivate
        assert next_state in transition.activate

    def test_external_transition(self, empty_statechart):
        init = InitialState(name='init', context=empty_statechart)
        state_spy = self.StateSpy(name='spy', context=empty_statechart)

        Transition(name='init', start=init, end=state_spy)
        Transition(name='extern', start=state_spy, end=state_spy, event=Event('extern'))

        empty_statechart.start()

        assert empty_statechart.is_active('spy')
        assert state_spy.entries is 1
        assert state_spy.exits is 0

        empty_statechart.dispatch(Event('extern'))

        # After dispatching the external event from the state spy, the
        # state should be deactivated and activated again.
        assert empty_statechart.is_active('spy')
        assert state_spy.entries is 2
        assert state_spy.exits is 1

    def test_local_transition(self, empty_statechart):
        init = InitialState(name='init', context=empty_statechart)
        state_spy = self.StateSpy(name='spy', context=empty_statechart)

        Transition(name='init', start=init, end=state_spy)
        Transition(name='local', start=state_spy, end=state_spy.local, event=Event('local'))

        empty_statechart.start()

        assert empty_statechart.is_active('spy')
        assert empty_statechart.is_active('default')
        assert state_spy.entries is 1
        assert state_spy.exits is 0

        empty_statechart.dispatch(Event('local'))

        assert empty_statechart.is_active('spy')
        assert not empty_statechart.is_active('default')
        assert empty_statechart.is_active('local')
        assert state_spy.entries is 1
        assert state_spy.exits is 0

    def test_deep_local_transitions(self, empty_statechart):
        sc = empty_statechart
        init = InitialState(name='init', context=sc)

        top = CompositeState(name='top', context=sc)
        top_init = InitialState(name='top_init', context=top)
        middle_a = CompositeState(name='middle_a', context=top)
        middle_b = CompositeState(name='middle_b', context=top)

        middle_a_init = InitialState(name='middle_a_init', context=middle_a)
        bottom_a1 = State(name='bottom_a1', context=middle_a)
        bottom_a2 = State(name='bottom_a2', context=middle_a)

        middle_b_init = InitialState(name='middle_b_init', context=middle_b)
        bottom_b1 = State(name='bottom_b1', context=middle_b)
        bottom_b2 = State(name='bottom_b2', context=middle_b)

        # Setup default transitions
        Transition(name='sc_init', start=init, end=top)
        Transition(name='top_init', start=top_init, end=middle_a)
        Transition(name='middle_a_init', start=middle_a_init, end=bottom_a1)
        Transition(name='middle_b_init', start=middle_b_init, end=bottom_b1)

        # Setup events to trigger transitions
        a_to_b = Event('a_to_b')
        a1_to_a2 = Event('a1_to_a2')
        b1_to_b2 = Event('b1_to_b2')
        top_to_middle_a = Event('top_to_middle_a')
        top_to_middle_b = Event('top_to_middle_b')
        middle_a_to_a1 = Event('middle_a_to_a1')
        middle_a_to_a2 = Event('middle_a_to_a2')
        middle_b_to_b1 = Event('middle_b_to_b1')
        middle_b_to_b2 = Event('middle_b_to_b2')

        # Setup external transitions
        Transition(name='middle_a_to_b', start=middle_a, end=middle_b, event=a_to_b)
        Transition(name='bottom_a1_to_a2', start=bottom_a1, end=bottom_a2, event=a1_to_a2)
        Transition(name='bottom_b1_to_b2', start=bottom_a1, end=bottom_a2, event=b1_to_b2)

        # Setup local transitions
        Transition(name='top_to_middle_a', start=top, end=middle_a, event=top_to_middle_a)
        Transition(name='top_to_middle_b', start=top, end=middle_b, event=top_to_middle_b)

        Transition(name='middle_a_to_a1', start=middle_a, end=bottom_a1, event=middle_a_to_a1)
        Transition(name='middle_a_to_a2', start=middle_a, end=bottom_a2, event=middle_a_to_a2)

        Transition(name='middle_b_to_b1', start=middle_b, end=bottom_b1, event=middle_b_to_b1)
        Transition(name='middle_b_to_b2', start=middle_b, end=bottom_b2, event=middle_b_to_b2)

        sc.start()

        assert sc.is_active('top')
        assert sc.is_active('middle_a')
        assert sc.is_active('bottom_a1')

        sc.dispatch(middle_a_to_a2)

        assert sc.is_active('top')
        assert sc.is_active('middle_a')
        assert sc.is_active('bottom_a2')

        sc.dispatch(top_to_middle_b)

        assert sc.is_active('top')
        assert sc.is_active('middle_b')
        assert sc.is_active('bottom_b1')

        sc.dispatch(top_to_middle_a)

        assert sc.is_active('top')
        assert sc.is_active('middle_a')
        assert sc.is_active('bottom_a1')

        sc.dispatch(a_to_b)

        assert sc.is_active('top')
        assert sc.is_active('middle_b')
        assert sc.is_active('bottom_b1')

        sc.dispatch(middle_b_to_b2)

        assert sc.is_active('top')
        assert sc.is_active('middle_b')
        assert sc.is_active('bottom_b2')


class TestInternalTransition:
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

    def test_execute(self, empty_statechart):
        initial_state = InitialState(name='initial', context=empty_statechart)
        default_state = self.StateSpy(name='next', context=empty_statechart)
        Transition(name='name', start=initial_state, end=default_state)

        internal_event = Event(name='internal-event')
        internal_action = ActionSpy()
        InternalTransition(name='internal',
                           state=default_state,
                           event=internal_event,
                           guard=None,
                           action=internal_action)
        empty_statechart.start()

        assert empty_statechart.is_active('next')
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
