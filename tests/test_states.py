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

import asyncio
import pytest

from statechart import (CompositeState, ConcurrentState, Event, FinalState,
                        InitialState, State, Statechart, Transition)


class StateSpy(State):
    def __init__(self, name, context):
        State.__init__(self, name=name, context=context)
        self.dispatch_called = False
        self.dispatch_internal_called = False
        self.metadata = None
        self.event = None

    def dispatch(self, metadata, event):
        self.dispatch_called = True
        self.metadata = metadata
        self.event = event
        return True

    def handle_internal(self, event):
        self.dispatch_internal_called = True


class TestStatechart:
    def test_create_statechart(self):
        Statechart(name='statechart')

    @pytest.mark.asyncio
    async def test_simple_statechart_finished(self):
        statechart = Statechart(name='statechart')
        init = InitialState(statechart)
        default = State(name='default', context=statechart)
        final = FinalState(statechart)

        finish = Event('finish')

        Transition(start=init, end=default)
        Transition(start=default, end=final, event=finish)
        await statechart.start()

        assert statechart.is_active('default')
        assert not statechart.finished

        await statechart.dispatch(finish)

        assert statechart.finished

    @pytest.mark.asyncio
    async def test_statechart_long_do(self):
        flag = False

        async def do_too_much(event):
            nonlocal flag
            flag = True
            # This sleep means the function will be still running when the finish
            # event is dispatched below, cancelling this task and preventing the
            # `flag = False` from being run.
            await asyncio.sleep(0.2)
            flag = False

        statechart = Statechart(name='statechart')
        init = InitialState(statechart)
        default = State(name='default', context=statechart)
        default.do = do_too_much
        final = FinalState(statechart)

        finish = Event('finish')

        Transition(start=init, end=default)
        Transition(start=default, end=final, event=finish)
        await statechart.start()

        assert statechart.is_active('default')
        assert not statechart.finished

        await statechart.dispatch(finish)
        assert flag

        assert statechart.finished

    @pytest.mark.asyncio
    async def test_statechart_do_dispatch(self):
        async def do_dispatch(event):
            await statechart.dispatch(finish)
            # Ensure this function is still running during deactivate and will
            # be cancelled. This tests that cancelling the dispatching do function
            # is safe.
            await asyncio.sleep(0.5)

        statechart = Statechart(name='statechart')
        init = InitialState(statechart)
        default = State(name='default', context=statechart)
        default.do = do_dispatch
        final = FinalState(statechart)

        finish = Event('finish')

        Transition(start=init, end=default)
        Transition(start=default, end=final, event=finish)
        await statechart.start()

        assert statechart.is_active('default')
        assert not statechart.finished

        # Give time for background do function to run
        await asyncio.sleep(0.1)

        assert statechart.finished

    @pytest.mark.asyncio
    async def test_composite_statechart_finished(self):
        statechart = Statechart(name='statechart')
        init = InitialState(statechart)
        final = FinalState(statechart)

        composite = CompositeState(name='composite', context=statechart)
        composite_init = InitialState(composite)
        composite_default = State(name='composite_default', context=composite)
        composite_final = FinalState(composite)

        finish = Event('finish')

        Transition(start=init, end=composite)
        Transition(start=composite_init, end=composite_default)
        Transition(start=composite_default, end=composite_final, event=finish)
        Transition(start=composite, end=final)

        await statechart.start()

        assert statechart.is_active('composite')
        assert statechart.is_active('composite_default')
        assert not statechart.finished

        await statechart.dispatch(finish)

        assert statechart.finished

    @pytest.mark.asyncio
    async def test_active_states(self):
        statechart = Statechart(name='a')
        statechart_init = InitialState(statechart)

        b = CompositeState(name='b', context=statechart)
        b_init = InitialState(b)

        c = CompositeState(name='c', context=b)
        c_init = InitialState(c)

        d = State(name='d', context=c)

        Transition(start=statechart_init, end=b)
        Transition(start=b_init, end=c)
        Transition(start=c_init, end=d)

        await statechart.start()
        assert statechart.active_states() == [statechart, b, c, d]


class TestState:
    def test_create_state(self):
        statechart = Statechart(name='statechart')
        State(name='anon', context=statechart)

    def test_create_state_without_parent(self):
        with pytest.raises(RuntimeError):
            State(name='anon', context=None)

    def test_add_transition(self):
        statechart = Statechart(name='statechart')
        initial_state = InitialState(statechart)
        default_state = State(name='default', context=statechart)

        default_transition = Transition(start=initial_state, end=default_state)

        assert default_transition in initial_state.transitions

    @pytest.mark.asyncio
    async def test_light_switch(self):
        """
                      --Flick-->
        init ---> Off            On
                      <--Flick--   Entry: Light = ON
                                   Exit: Light = OFF
                                   Internal:
                                     Flick: Count++
        """

        class On(State):
            def __init__(self, name, context, data):
                State.__init__(self, name=name, context=context)
                self.data = data

            async def entry(self, event):
                self.data['light'] = 'on'

            async def exit(self, event):
                self.data['light'] = 'off'

            def handle_internal(self, event):
                if event.name == 'flick':
                    self.data['on_count'] += 1

        sm = Statechart(name='sm')
        data = dict(light='off', on_count=0)
        sm.initial_state = InitialState(context=sm)
        off = State(name='off', context=sm)
        on = On(name='on', context=sm, data=data)

        Transition(start=sm.initial_state, end=off)
        Transition(start=off, end=on, event=Event('flick'))
        Transition(start=on, end=off, event=Event('flick'))

        await sm.start()

        assert data['light'] == 'off'

        await sm.dispatch(Event('flick'))
        assert data['light'] == 'on'

        assert data['on_count'] == 0

        await sm.dispatch(Event('flick'))
        assert data['light'] == 'off'

        assert data['on_count'] == 1


class TestFinalState:
    def test_add_transition(self):
        statechart = Statechart(name='statechart')
        final_state = FinalState(statechart)

        with pytest.raises(RuntimeError):
            Transition(start=final_state, end=statechart)

    @pytest.mark.asyncio
    async def test_transition_from_finished_composite_state(self):
        statechart = Statechart(name='statechart')
        statechart_init = InitialState(statechart)

        composite_state = CompositeState(name='composite', context=statechart)
        comp_init = InitialState(composite_state)
        a = State(name='a', context=composite_state)
        comp_final = FinalState(composite_state)

        Transition(start=statechart_init, end=composite_state)
        Transition(start=comp_init, end=a)
        Transition(start=a, end=comp_final, event=Event('e'))

        b = State(name='b', context=statechart)
        Transition(start=composite_state, end=b)

        await statechart.start()
        assert statechart.is_active('a')
        await statechart.dispatch(Event('e'))
        assert statechart.is_active('b')

    @pytest.mark.asyncio
    async def test_default_transition_from_finished_composite_state(self):
        statechart = Statechart(name='statechart')
        statechart_init = InitialState(statechart)

        composite_state = CompositeState(name='composite', context=statechart)
        comp_init = InitialState(composite_state)
        a = State(name='a', context=composite_state)
        comp_final = FinalState(composite_state)

        Transition(start=statechart_init, end=composite_state)
        Transition(start=comp_init, end=a)
        Transition(start=a, end=comp_final, event=Event('e'))

        b = State(name='b', context=statechart)
        c = State(name='c', context=statechart)
        d = State(name='d', context=statechart)

        Transition(start=composite_state, end=c, event=Event('f'))
        Transition(start=composite_state, end=b, event=Event('e'))
        Transition(start=composite_state, end=d)

        await statechart.start()

        assert statechart.is_active('a')

        await statechart.dispatch(Event('e'))

        assert statechart.is_active('d')

    @pytest.mark.asyncio
    async def test_default_transition_isnt_executed_from_unfinished_composite_state(self):
        statechart = Statechart(name='statechart')
        statechart_init = InitialState(statechart)

        composite_state = CompositeState(name='composite', context=statechart)
        comp_init = InitialState(composite_state)
        a = State(name='a', context=composite_state)

        Transition(start=statechart_init, end=composite_state)
        Transition(start=comp_init, end=a)

        b = State(name='b', context=statechart)

        Transition(start=composite_state, end=b)

        await statechart.start()

        assert statechart.is_active('a')

        await statechart.dispatch(Event('e'))

        assert statechart.is_active('a')


# TODO(lam) Add test with final states - state shouldn't dispatch default
# event until all regions have finished.
# TOOD(lam) Add test for transition directly into a concurrent, composite sub
# state.
class TestConcurrentState:
    @pytest.mark.asyncio
    async def test_keyboard_example(self):
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

        start_state = InitialState(statechart)
        keyboard = ConcurrentState(name='keyboard', context=statechart)
        Transition(start=start_state, end=keyboard)

        caps_lock = CompositeState(name='caps_lock', context=keyboard)
        caps_lock_initial = InitialState(caps_lock)
        caps_lock_on = State(name='caps_lock_on', context=caps_lock)
        caps_lock_off = State(name='caps_lock_off', context=caps_lock)
        caps_lock_pressed = Event(name='caps_lock_pressed')
        Transition(start=caps_lock_initial, end=caps_lock_off)
        Transition(start=caps_lock_on, end=caps_lock_off, event=caps_lock_pressed)
        Transition(start=caps_lock_off, end=caps_lock_on, event=caps_lock_pressed)

        num_lock = CompositeState(name='num_lock', context=keyboard)
        num_lock_initial = InitialState(num_lock)
        num_lock_on = State(name='num_lock_on', context=num_lock)
        num_lock_off = State(name='num_lock_off', context=num_lock)
        num_lock_pressed = Event(name='num_lock_pressed')
        Transition(start=num_lock_initial, end=num_lock_off)
        Transition(start=num_lock_on, end=num_lock_off, event=num_lock_pressed)
        Transition(start=num_lock_off, end=num_lock_on, event=num_lock_pressed)

        scroll_lock = CompositeState(name='scroll_lock', context=keyboard)
        scroll_lock_initial = InitialState(scroll_lock)
        scroll_lock_on = State(name='scroll_lock_on', context=scroll_lock)
        scroll_lock_off = State(name='scroll_lock_off', context=scroll_lock)
        scroll_lock_pressed = Event(name='scroll_lock_pressed')
        Transition(start=scroll_lock_initial, end=scroll_lock_off)
        Transition(start=scroll_lock_on, end=scroll_lock_off, event=scroll_lock_pressed)
        Transition(start=scroll_lock_off, end=scroll_lock_on, event=scroll_lock_pressed)

        await statechart.start()

        assert statechart.is_active('keyboard')
        assert statechart.is_active('caps_lock_off')
        assert statechart.is_active('num_lock_off')
        assert statechart.is_active('scroll_lock_off')

        await statechart.dispatch(event=caps_lock_pressed)
        assert statechart.is_active('caps_lock_on')

        await statechart.dispatch(event=num_lock_pressed)
        assert statechart.is_active('num_lock_on')

        await statechart.dispatch(event=scroll_lock_pressed)
        assert statechart.is_active('scroll_lock_on')

        await statechart.dispatch(event=caps_lock_pressed)
        assert statechart.is_active('caps_lock_off')

        await statechart.dispatch(event=num_lock_pressed)
        assert statechart.is_active('num_lock_off')

        await statechart.dispatch(event=scroll_lock_pressed)
        assert statechart.is_active('scroll_lock_off')


class TestCompositeState:
    class Submachine(CompositeState):
        def __init__(self, name, context):
            CompositeState.__init__(self, name=name, context=context)

            init = InitialState(self)
            self.state_a = State(name='sub state a', context=self)
            self.state_b = State(name='sub state b', context=self)

            self.sub_a_to_b = Event('sub_ab')
            Transition(start=init, end=self.state_a)
            Transition(start=self.state_a, end=self.state_b, event=self.sub_a_to_b)

    @pytest.mark.asyncio
    async def test_submachines(self):
        statechart = Statechart(name='statechart')

        init = InitialState(statechart)
        top_a = self.Submachine('top a', statechart)
        top_b = self.Submachine('top b', statechart)

        top_a_to_b = Event('top ab')
        Transition(start=init, end=top_a)
        Transition(start=top_a, end=top_b, event=top_a_to_b)

        await statechart.start()

        assert statechart.is_active('top a')
        assert statechart.is_active('sub state a')

        await statechart.dispatch(top_a.sub_a_to_b)

        assert statechart.is_active('top a')
        assert statechart.is_active('sub state b')

        await statechart.dispatch(top_a_to_b)

        assert statechart.is_active('top b')
        assert statechart.is_active('sub state a')

        await statechart.dispatch(top_a.sub_a_to_b)

        assert statechart.is_active('top b')
        assert statechart.is_active('sub state b')
