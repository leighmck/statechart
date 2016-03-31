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
from statechart import (Action, CompositeState, Event, FinalState,
                        InitialState, State, Statechart, Transition)


class ActionSpy(Action):
    def __init__(self):
        self.executed = False

    def execute(self, param):
        self.executed = True


class StateSpy(State):
    def __init__(self, name, context, entry=None, do=None, exit=None):
        State.__init__(self, name=name, context=context, entry=entry, do=do,
                       exit=exit)
        self.dispatch_called = False
        self.metadata = None
        self.event = None

    def dispatch(self, metadata, event, param):
        self.dispatch_called = True
        self.metadata = metadata
        self.event = event
        return True


class TestStatechart:
    def test_create_statechart(self):
        Statechart(name='statechart', param=0)

    def test_start(self):
        statechart = Statechart(name='statechart', param=0)
        initial_state = InitialState(name='initial', context=statechart)
        statechart.start()
        assert statechart.initial_state is initial_state

    def test_dispatch(self):
        statechart = Statechart(name='statechart', param=0)
        initial_state = InitialState(name='initial', context=statechart)
        default_state = StateSpy(name='default', context=statechart)
        next_state = State(name='next', context=statechart)
        test_event = Event(name='test_event', param=123)
        Transition('default_transition', start=initial_state,
                   end=default_state)
        Transition(name='test_transition', start=default_state, end=next_state,
                   event=test_event)
        statechart.start()
        assert statechart.dispatch(event=test_event)
        assert default_state.dispatch_called
        assert default_state.event == test_event

    def test_add_transition(self):
        statechart = Statechart(name='statechart', param=0)
        initial_state = InitialState(name='initial', context=statechart)

        with pytest.raises(RuntimeError):
            Transition('initial_transition', start=statechart,
                       end=initial_state)


class TestState:
    def test_create_state(self):
        statechart = Statechart(name='statechart', param=0)
        State(name='anon', context=statechart)

    def test_create_state_without_parent(self):
        with pytest.raises(RuntimeError):
            State(name='anon', context=None)

    def test_add_transition(self):
        statechart = Statechart(name='statechart', param=0)
        initial_state = InitialState(name='initial', context=statechart)
        default_state = State(name='default', context=statechart)

        default_transition = Transition(name='default', start=initial_state,
                                        end=default_state)

        assert default_transition in initial_state.transitions

    def test_activate(self):
        statechart = Statechart(name='statechart', param=0)
        InitialState(name='initial', context=statechart)
        default_state = State(name='default', context=statechart)
        statechart.start()

        default_state.activate(statechart.metadata, 0)

        assert statechart.metadata.is_active(default_state)

    def test_deactivate(self):
        statechart = Statechart(name='statechart', param=0)
        InitialState(name='initial', context=statechart)
        default_state = State(name='default', context=statechart)
        statechart.start()

        default_state.activate(statechart.metadata, 0)
        assert statechart.metadata.is_active(default_state)

        default_state.deactivate(statechart.metadata, 0)
        assert not statechart.metadata.is_active(default_state)

    def test_dispatch(self):
        statechart = Statechart(name='statechart', param=0)
        initial_state = InitialState(name='initial', context=statechart)
        default_state = State(name='default', context=statechart)
        statechart.start()

        default_trigger = Event('default_trigger', 0)
        Transition(name='default', start=initial_state, end=default_state,
                   event=default_trigger)

        assert initial_state.dispatch(metadata=statechart.metadata,
                                      event=default_trigger, param=0)

        assert statechart.metadata.is_active(default_state)


class TestFinalState:
    def test_add_transition(self):
        statechart = Statechart(name='statechart', param=0)
        final_state = FinalState(name='final', context=statechart)

        with pytest.raises(RuntimeError):
            Transition(name='final', start=final_state, end=statechart)

    def test_dispatch(self):
        statechart = Statechart(name='statechart', param=0)
        final_state = FinalState(name='final', context=statechart)
        final_trigger = Event(name='final_trigger', param=0)
        with pytest.raises(RuntimeError):
            final_state.dispatch(metadata=statechart.metadata,
                                 event=final_trigger, param=0)


class TestCompositeState:
    def test_activate(self):
        statechart = Statechart(name='statechart', param=0)
        InitialState(name='initial', context=statechart)
        composite = CompositeState(name='composite', context=statechart)
        statechart.start()

        composite.activate(statechart.metadata, 0)
        assert statechart.metadata.is_active(composite)

    def test_deactivate(self):
        statechart = Statechart(name='statechart', param=0)
        InitialState(name='initial', context=statechart)
        composite = CompositeState(name='composite', context=statechart)
        statechart.start()

        composite.activate(statechart.metadata, 0)
        assert statechart.metadata.is_active(composite)

        composite.deactivate(statechart.metadata, 0)
        assert not statechart.metadata.is_active(composite)

    def test_dispatch(self):
        statechart = Statechart(name='statechart', param=0)
        InitialState(name='initial', context=statechart)
        composite = CompositeState(name='composite', context=statechart)
        composite_initial = InitialState(name='initial', context=composite)
        default_direct_substate = State(name='default direct substate',
                                        context=composite)
        Transition(name='default', start=composite_initial,
                   end=default_direct_substate)
        next_direct_substate = State(name='next direct substate',
                                     context=composite)
        composite_to_next_event = Event(name='tcomposite_to_next_event',
                                        param=123)
        Transition(name='default', start=composite, end=next_direct_substate,
                   event=composite_to_next_event)

        statechart.start()
        composite.activate(statechart.metadata, 0)

        assert composite.dispatch(metadata=statechart.metadata,
                                  event=composite_to_next_event, param=0)

        assert statechart.metadata.is_active(composite)
