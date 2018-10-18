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

from functools import partial

import pytest

from statechart import (CompositeState, Event, State, InitialState, Statechart, Transition)


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

            init = InitialState(self)
            self.default = State(name='default', context=self)
            self.local = State(name='local', context=self)

            Transition(start=init, end=self.default)

        def entry(self, event):
            self.entries += 1

        def exit(self, event):
            self.exits += 1

    def test_create_transition(self, empty_statechart):
        initial_state = InitialState(empty_statechart)
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(start=initial_state, end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions
        assert transition in initial_state.transitions

        # When executed, the transition should be setup to deactivate the
        # initial state and to activate the next state
        assert initial_state in transition.deactivate
        assert next_state in transition.activate

    def test_create_cyclic_transition(self, empty_statechart):
        next_state = State(name='next', context=empty_statechart)
        transition = Transition(start=next_state, end=next_state)

        # The transition should be added to the initial state's list of
        # outgoing transitions.
        assert transition in next_state.transitions

        # When executed, the transition should be setup to deactivate the
        # next state and to re-activate it.
        assert next_state in transition.deactivate
        assert next_state in transition.activate

    def test_external_transition(self, empty_statechart):
        init = InitialState(empty_statechart)
        state_spy = self.StateSpy(name='spy', context=empty_statechart)

        Transition(start=init, end=state_spy)
        Transition(start=state_spy, end=state_spy, event='extern')

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
        init = InitialState(empty_statechart)
        state_spy = self.StateSpy(name='spy', context=empty_statechart)

        Transition(start=init, end=state_spy)
        Transition(start=state_spy, end=state_spy.local, event=Event('local'))

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
        init = InitialState(sc)

        top = CompositeState(name='top', context=sc)
        top_init = InitialState(top)
        middle_a = CompositeState(name='middle_a', context=top)
        middle_b = CompositeState(name='middle_b', context=top)

        middle_a_init = InitialState(middle_a)
        bottom_a1 = State(name='bottom_a1', context=middle_a)
        bottom_a2 = State(name='bottom_a2', context=middle_a)

        middle_b_init = InitialState(middle_b)
        bottom_b1 = State(name='bottom_b1', context=middle_b)
        bottom_b2 = State(name='bottom_b2', context=middle_b)

        # Setup default transitions
        Transition(start=init, end=top)
        Transition(start=top_init, end=middle_a)
        Transition(start=middle_a_init, end=bottom_a1)
        Transition(start=middle_b_init, end=bottom_b1)

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
        Transition(start=middle_a, end=middle_b, event=a_to_b)
        Transition(start=bottom_a1, end=bottom_a2, event=a1_to_a2)
        Transition(start=bottom_a1, end=bottom_a2, event=b1_to_b2)

        # Setup local transitions
        Transition(start=top, end=middle_a, event=top_to_middle_a)
        Transition(start=top, end=middle_b, event=top_to_middle_b)

        Transition(start=middle_a, end=bottom_a1, event=middle_a_to_a1)
        Transition(start=middle_a, end=bottom_a2, event=middle_a_to_a2)

        Transition(start=middle_b, end=bottom_b1, event=middle_b_to_b1)
        Transition(start=middle_b, end=bottom_b2, event=middle_b_to_b2)

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

    def test_transition_hierarchy(self, empty_statechart):
        sc = empty_statechart
        init = InitialState(sc)

        top = CompositeState(name='top', context=sc)
        top_init = InitialState(top)
        middle_a = CompositeState(name='middle_a', context=top)
        middle_b = CompositeState(name='middle_b', context=top)

        middle_a_init = InitialState(middle_a)
        bottom_a1 = State(name='bottom_a1', context=middle_a)
        bottom_a2 = State(name='bottom_a2', context=middle_a)

        middle_b_init = InitialState(middle_b)
        bottom_b1 = State(name='bottom_b1', context=middle_b)

        # Setup default transitions
        Transition(start=init, end=top)
        Transition(start=top_init, end=middle_a)
        Transition(start=middle_a_init, end=bottom_a1)
        Transition(start=middle_b_init, end=bottom_b1)

        # Setup event triggers
        across = Event('across')
        up = Event('up')

        # Setup external transitions
        Transition(start=bottom_a1, end=bottom_a2, event=across)
        Transition(start=bottom_a2, end=middle_b, event=up)
        Transition(start=middle_b, end=middle_a, event=across)

        sc.start()

        assert sc.is_active('top')
        assert sc.is_active('middle_a')
        assert sc.is_active('bottom_a1')

        sc.dispatch(across)

        assert sc.is_active('top')
        assert sc.is_active('middle_a')
        assert sc.is_active('bottom_a2')

        sc.dispatch(up)

        assert sc.is_active('top')
        assert sc.is_active('middle_b')
        assert sc.is_active('bottom_b1')

        sc.dispatch(across)

        assert sc.is_active('top')
        assert sc.is_active('middle_a')
        assert sc.is_active('bottom_a1')

    def test_transition_event_consumed(self, empty_statechart):
        sc = empty_statechart
        init = InitialState(sc)

        # a = State(name='a', context=sc)
        b = State(name='b', context=sc)

        cs = CompositeState(name='cs', context=sc)
        cs_init = InitialState(cs)
        cs_a = State(name='cs a', context=cs)
        cs_b = State(name='cs b', context=cs)

        Transition(start=init, end=cs)
        Transition(start=cs, end=cs_init)

        Transition(start=cs_init, end=cs_a)
        Transition(start=cs_a, end=cs_b, event='home')
        Transition(start=cs, end=b, event='home')

        sc.start()

        assert sc.is_active('cs a')

        sc.dispatch(Event('home'))

        assert sc.is_active('cs b')

    def test_transition_action_function(self, empty_statechart):
        self.state = False

        def set_state(state):
            self.state = bool(state)

        set_true = partial(set_state, True)

        sc = empty_statechart
        initial = InitialState(sc)
        default = State(name='default', context=sc)
        next = State(name='next', context=sc)

        Transition(start=initial, end=default)
        Transition(start=default, end=next, event='next', action=set_true)

        sc.start()
        sc.dispatch(Event('next'))

        assert self.state

    def test_transition_action_function_with_event(self, empty_statechart):
        self.state = False

        def set_state(event):
            self.state = event.data['state']

        sc = empty_statechart
        initial = InitialState(sc)
        default = State(name='default', context=sc)
        next = State(name='next', context=sc)

        Transition(start=initial, end=default)
        Transition(start=default, end=next, event='next', action=set_state)

        sc.start()
        sc.dispatch(Event(name='next', data={'state': True}))

        assert self.state

    def test_transition_action_function_with_metadata(self, empty_statechart):
        sc = empty_statechart
        sc.metadata.state = True

        self.state = False

        def set_state(event):
            self.state = sc.metadata.state

        initial = InitialState(sc)
        default = State(name='default', context=sc)
        next = State(name='next', context=sc)

        Transition(start=initial, end=default)
        Transition(start=default, end=next, event='next', action=set_state)

        sc.start()
        sc.dispatch(Event('next'))

        assert self.state
