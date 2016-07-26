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

from statechart import (Action, CompositeState, ConcurrentState, Event, FinalState,
                        InitialState, State, Statechart, Transition)


class ActionSpy(Action):
    def __init__(self):
        self.executed = False

    def execute(self, scope, event):
        self.executed = True


class StateSpy(State):
    def __init__(self, name, context):
        State.__init__(self, name=name, context=context)
        self.dispatch_called = False
        self.metadata = None
        self.event = None

    def dispatch(self, metadata, event):
        self.dispatch_called = True
        self.metadata = metadata
        self.event = event
        return True


class TestStatechart:
    def test_create_statechart(self):
        Statechart(name='statechart')

    def test_simple_statechart_finished(self):
        statechart = Statechart(name='statechart')
        init = InitialState(name='init', context=statechart)
        default = State(name='default', context=statechart)
        final = FinalState(name='final', context=statechart)

        finish = Event('finish')

        Transition(name='init', start=init, end=default)
        Transition(name='finish', start=default, end=final, event=finish)
        statechart.start()

        assert statechart.is_active('default')
        assert not statechart.is_finished()

        statechart.dispatch(finish)

        assert statechart.is_active('final')
        assert statechart.is_finished()

    def test_composite_statechart_finished(self):
        statechart = Statechart(name='statechart')
        init = InitialState(name='init', context=statechart)
        final = FinalState(name='final', context=statechart)

        composite = CompositeState(name='composite', context=statechart)
        composite_init = InitialState(name='composite_init', context=composite)
        composite_default = State(name='composite_default', context=composite)
        composite_final = FinalState(name='composite_final', context=composite)

        finish = Event('finish')

        Transition(name='init', start=init, end=composite)
        Transition(name='composite_init', start=composite_init, end=composite_default)
        Transition(name='finish_composite', start=composite_default, end=composite_final, event=finish)
        Transition(name='composite_finished', start=composite, end=final)

        statechart.start()

        assert statechart.is_active('composite')
        assert statechart.is_active('composite_default')
        assert not statechart.is_finished()

        statechart.dispatch(finish)

        assert statechart.is_active('final')
        assert statechart.is_finished()

    # def test_compound_statechart_finished(self):
    #     statechart = Statechart(name='statechart')
    #     init = InitialState(name='init', context=statechart)
    #     final = FinalState(name='final', context=statechart)
    #
    #     composite_1 = CompositeState(name='composite_1', context=statechart)
    #     composite_1_init = InitialState(name='composite_1_init', context=composite_1)
    #     composite_1_default = State(name='composite_1_default', context=composite_1)
    #     composite_1_final = FinalState(name='composite_1_final', context=composite_1)
    #
    #     composite_2 = CompositeState(name='composite_2', context=statechart)
    #     composite_2_init = InitialState(name='composite_2_init', context=composite_2)
    #     composite_2_default = State(name='composite_2_default', context=composite_2)
    #     composite_2_final = FinalState(name='composite_2_final', context=composite_2)
    #
    #     compound = ConcurrentState(name='compound', context=statechart)
    #     compound.add_region(composite_1)
    #     compound.add_region(composite_2)
    #
    #     finish_1 = Event('finish_1')
    #     finish_2 = Event('finish_2')
    #
    #     Transition(name='init', start=init, end=compound)
    #     Transition(name='composite_1_init', start=composite_1_init, end=composite_1_default)
    #     Transition(name='composite_2_init', start=composite_2_init, end=composite_2_default)
    #
    #     Transition(name='finish_composite_1', start=composite_1_default, end=composite_1_final, event=finish_1)
    #     Transition(name='finish_composite_2', start=composite_2_default, end=composite_2_final, event=finish_2)
    #
    #     Transition(name='compound_finished', start=compound, end=final, event=finish_1)
    #
    #     statechart.start()
    #
    #     assert statechart.is_active('compound')
    #     assert statechart.is_active('composite_1_default')
    #     assert statechart.is_active('composite_2_default')
    #     assert not statechart.is_finished()
    #
    #     statechart.dispatch(finish_1)
    #
    #     assert statechart.is_active('compound')
    #     assert statechart.is_active('composite_1_final')
    #     assert statechart.is_active('composite_2_default')
    #     assert not statechart.is_finished()
    #
    #     statechart.dispatch(finish_2)
    #
    #     assert not statechart.is_active('compound')
    #     assert statechart.is_active('final')
    #     assert statechart.is_finished()


class TestState:
    def test_create_state(self):
        statechart = Statechart(name='statechart')
        State(name='anon', context=statechart)

    def test_create_state_without_parent(self):
        with pytest.raises(RuntimeError):
            State(name='anon', context=None)

    def test_add_transition(self):
        statechart = Statechart(name='statechart')
        initial_state = InitialState(name='initial', context=statechart)
        default_state = State(name='default', context=statechart)

        default_transition = Transition(name='default', start=initial_state, end=default_state)

        assert default_transition in initial_state._transitions


class TestFinalState:
    def test_add_transition(self):
        statechart = Statechart(name='statechart')
        final_state = FinalState(name='final', context=statechart)

        with pytest.raises(RuntimeError):
            Transition(name='final', start=final_state, end=statechart)

    def test_transition_from_finished_composite_state(self):
        statechart = Statechart(name='statechart')
        statechart_init = InitialState(name='statechart init', context=statechart)

        composite_state = CompositeState(name='composite', context=statechart)
        comp_init = InitialState(name='init comp', context=composite_state)
        a = State(name='a', context=composite_state)
        comp_final = FinalState(name='final comp', context=composite_state)

        Transition(name='statechart init', start=statechart_init, end=composite_state)
        Transition(name='comp init', start=comp_init, end=a)
        Transition(name='comp finished', start=a, end=comp_final, event=Event('e'))

        b = State(name='b', context=statechart)
        Transition(name='comp to b', start=composite_state, end=b)

        statechart.start()
        assert statechart.is_active('a')
        statechart.dispatch(Event('e'))
        assert statechart.is_active('b')

    def test_default_transition_from_finished_composite_state(self):
        statechart = Statechart(name='statechart')
        statechart_init = InitialState(name='statechart init', context=statechart)

        composite_state = CompositeState(name='composite', context=statechart)
        comp_init = InitialState(name='init comp', context=composite_state)
        a = State(name='a', context=composite_state)
        comp_final = FinalState(name='final comp', context=composite_state)

        Transition(name='statechart init', start=statechart_init, end=composite_state)
        Transition(name='comp init', start=comp_init, end=a)
        Transition(name='comp finished', start=a, end=comp_final, event=Event('e'))

        b = State(name='b', context=statechart)
        c = State(name='c', context=statechart)

        Transition(name='comp to c', start=composite_state, end=c, event=Event('f'))
        Transition(name='comp to b', start=composite_state, end=b)

        statechart.start()

        assert statechart.is_active('a')

        statechart.dispatch(Event('e'))

        assert statechart.is_active('b')


# TODO(lam) Add test with final states - state shouldn't dispatch default
# event until all regions have finished.
# TOOD(lam) Add test for transition directly into a concurrent, composite sub
# state.
class TestConcurrentState:
    def test_keyboard_example(self):
        """
        Test classic concurrent state keyboard example with concurrent states
        for caps, num and scroll lock.

        init - -
               |
               v
        -- keyboard --------------------------------------
        |                                                |
        |  init ---> --caps lock off --                  |
        |        --- |                | <--              |
        |        |   -----------------|   |              |
        |  caps lock pressed       caps lock pressed     |
        |        |   -- caps lock on --   |              |
        |        --> |                | ---              |
        |            ------------------                  |
        |                                                |
        --------------------------------------------------
        |                                                |
        |  init ---> --num lock off ---                  |
        |        --- |                | <--              |
        |        |   -----------------|   |              |
        |  num lock pressed      num lock pressed        |
        |        |   -- num lock on ---   |              |
        |        --> |                | ---              |
        |            ------------------                  |
        |                                                |
        --------------------------------------------------
        |                                                |
        |  init ---> -- scroll lock off --               |
        |        --- |                    | <--          |
        |        |   ---------------------|   |          |
        |  scroll lock pressed      scroll lock pressed  |
        |        |   -- scroll lock on ---|   |          |
        |        --> |                    | ---          |
        |            ----------------------              |
        |                                                |
        --------------------------------------------------
        """
        statechart = Statechart(name='statechart')

        start_state = InitialState(name='start_state', context=statechart)
        keyboard = ConcurrentState(name='keyboard', context=statechart)
        Transition(name='start', start=start_state, end=keyboard)

        caps_lock = CompositeState(name='caps_lock', context=keyboard)
        caps_lock_initial = InitialState(name='caps_lock_initial', context=caps_lock)
        caps_lock_on = State(name='caps_lock_on', context=caps_lock)
        caps_lock_off = State(name='caps_lock_off', context=caps_lock)
        caps_lock_pressed = Event(name='caps_lock_pressed')
        Transition(name='caps_lock_default_off', start=caps_lock_initial, end=caps_lock_off)
        Transition(name='caps_lock_on', start=caps_lock_on, end=caps_lock_off,
                   event=caps_lock_pressed)
        Transition(name='caps_lock_off', start=caps_lock_off, end=caps_lock_on,
                   event=caps_lock_pressed)

        num_lock = CompositeState(name='num_lock', context=keyboard)
        num_lock_initial = InitialState(name='num_lock_initial', context=num_lock)
        num_lock_on = State(name='num_lock_on', context=num_lock)
        num_lock_off = State(name='num_lock_off', context=num_lock)
        num_lock_pressed = Event(name='num_lock_pressed')
        Transition(name='num_lock_default_off', start=num_lock_initial, end=num_lock_off)
        Transition(name='num_lock_on', start=num_lock_on, end=num_lock_off, event=num_lock_pressed)
        Transition(name='num_lock_off', start=num_lock_off, end=num_lock_on,
                   event=num_lock_pressed)

        scroll_lock = CompositeState(name='scroll_lock', context=keyboard)
        scroll_lock_initial = InitialState(name='scroll_lock_initial', context=scroll_lock)
        scroll_lock_on = State(name='scroll_lock_on', context=scroll_lock)
        scroll_lock_off = State(name='scroll_lock_off', context=scroll_lock)
        scroll_lock_pressed = Event(name='scroll_lock_pressed')
        Transition(name='scroll_lock_default_off', start=scroll_lock_initial, end=scroll_lock_off)
        Transition(name='scroll_lock_on', start=scroll_lock_on, end=scroll_lock_off,
                   event=scroll_lock_pressed)
        Transition(name='scroll_lock_off', start=scroll_lock_off, end=scroll_lock_on,
                   event=scroll_lock_pressed)

        statechart.start()

        assert statechart.is_active('keyboard')
        assert statechart.is_active('caps_lock_off')
        assert statechart.is_active('num_lock_off')
        assert statechart.is_active('scroll_lock_off')

        statechart.dispatch(event=caps_lock_pressed)
        assert statechart.is_active('caps_lock_on')

        statechart.dispatch(event=num_lock_pressed)
        assert statechart.is_active('num_lock_on')

        statechart.dispatch(event=scroll_lock_pressed)
        assert statechart.is_active('scroll_lock_on')

        statechart.dispatch(event=caps_lock_pressed)
        assert statechart.is_active('caps_lock_off')

        statechart.dispatch(event=num_lock_pressed)
        assert statechart.is_active('num_lock_off')

        statechart.dispatch(event=scroll_lock_pressed)
        assert statechart.is_active('scroll_lock_off')


class TestCompositeState:
    class Submachine(CompositeState):
        def __init__(self, name, context):
            CompositeState.__init__(self, name=name, context=context)

            init = InitialState(name='init submachine', context=self)
            self.state_a = State(name='sub state a', context=self)
            self.state_b = State(name='sub state b', context=self)

            self.sub_a_to_b = Event('sub_ab')
            Transition(name='init', start=init, end=self.state_a)
            Transition(name='sub_ab', start=self.state_a, end=self.state_b, event=self.sub_a_to_b)

    def test_submachines(self):
        statechart = Statechart(name='statechart')

        init = InitialState(name='init a', context=statechart)
        top_a = self.Submachine('top a', statechart)
        top_b = self.Submachine('top b', statechart)

        top_a_to_b = Event('top ab')
        Transition(name='init', start=init, end=top_a)
        Transition(name='top_a_to_b', start=top_a, end=top_b, event=top_a_to_b)

        statechart.start()

        assert statechart.is_active('top a')
        assert statechart.is_active('sub state a')

        statechart.dispatch(top_a.sub_a_to_b)

        assert statechart.is_active('top a')
        assert statechart.is_active('sub state b')

        statechart.dispatch(top_a_to_b)

        assert statechart.is_active('top b')
        assert statechart.is_active('sub state a')

        statechart.dispatch(top_a.sub_a_to_b)

        assert statechart.is_active('top b')
        assert statechart.is_active('sub state b')
