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

from statechart import (ConcurrentState, CompositeState, Event, FinalState, InitialState,
                        State, Statechart, Transition)
from statechart.display import Display


@pytest.fixture
def simple_statechart():
    sc = Statechart('simple')
    sc.init = InitialState(sc)
    sc.state = State(name='state', context=sc)
    sc.final = FinalState(sc)

    Transition(start=sc.init, end=sc.state)
    Transition(start=sc.state, end=sc.final, event=Event('finish'))

    return sc


@pytest.fixture
def composite_statechart():
    sc = Statechart('simple')
    sc.init = InitialState(sc)

    sc.composite = CompositeState(name='composite', context=sc)
    sc.composite.init = InitialState(sc.composite)
    sc.composite.state = State(name='state', context=sc.composite)
    sc.composite.final = FinalState(sc.composite)

    sc.final = FinalState(sc)

    Transition(start=sc.init, end=sc.composite)
    Transition(start=sc.composite.init, end=sc.composite.state)
    Transition(start=sc.composite.state, end=sc.composite.final, event=Event('finish'))

    Transition(start=sc.composite, end=sc.final, event=Event('finish'))

    return sc


@pytest.fixture
def concurrent_statechart():
    def composite(name, context):
        composite = CompositeState(name=name, context=context)
        composite.init = InitialState(composite)
        composite.state = State(name='state', context=composite)
        composite.final = FinalState(composite)

        Transition(start=composite.init, end=composite.state)
        Transition(start=composite.state, end=composite.final, event=Event('finish'))

        return composite

    sc = Statechart('simple')
    sc.init = InitialState(sc)

    sc.concurrent = ConcurrentState(name='compound', context=sc)

    sc.concurrent.composite_a = composite(name='a', context=sc.concurrent)
    sc.concurrent.composite_b = composite(name='b', context=sc.concurrent)
    sc.concurrent.composite_c = composite(name='c', context=sc.concurrent)

    sc.final = FinalState(sc)

    Transition(start=sc.init, end=sc.concurrent)
    Transition(start=sc.concurrent, end=sc.final, event=Event('finish'))

    return sc


class TestDescribe:
    def test_describe_simple_statechart(self, simple_statechart):
        sc = simple_statechart
        display = Display()

        (states, transitions) = display.describe(sc.initial_state, states=[], transitions=[])

        assert set(states) == {sc.init, sc.state, sc.final}
        assert set(transitions) == set(sc.init._transitions + sc.state._transitions)

    def test_describe_composite_statechart(self, composite_statechart):
        sc = composite_statechart
        display = Display()

        (states, transitions) = display.describe(sc.initial_state, states=[], transitions=[])

        assert set(states) == {
            sc.init,
            sc.composite,
            sc.composite.init,
            sc.composite.state,
            sc.composite.final,
            sc.final
        }

        assert set(transitions) == set(
            sc.init._transitions +
            sc.composite._transitions +
            sc.composite.init._transitions +
            sc.composite.state._transitions
        )

    def test_describe_concurrent_statechart(self, concurrent_statechart):
        sc = concurrent_statechart
        display = Display()

        (states, transitions) = display.describe(sc.initial_state, states=[], transitions=[])

        assert set(states) == {
            sc.init,
            sc.concurrent,
            sc.concurrent.composite_a,
            sc.concurrent.composite_a.init,
            sc.concurrent.composite_a.state,
            sc.concurrent.composite_a.final,
            sc.concurrent.composite_b,
            sc.concurrent.composite_b.init,
            sc.concurrent.composite_b.state,
            sc.concurrent.composite_b.final,
            sc.concurrent.composite_c,
            sc.concurrent.composite_c.init,
            sc.concurrent.composite_c.state,
            sc.concurrent.composite_c.final,
            sc.final
        }

        assert set(transitions) == set(
            sc.init._transitions +
            sc.concurrent._transitions +
            sc.concurrent.composite_a._transitions +
            sc.concurrent.composite_a.init._transitions +
            sc.concurrent.composite_a.state._transitions +
            sc.concurrent.composite_b._transitions +
            sc.concurrent.composite_b.init._transitions +
            sc.concurrent.composite_b.state._transitions +
            sc.concurrent.composite_c._transitions +
            sc.concurrent.composite_c.init._transitions +
            sc.concurrent.composite_c.state._transitions
        )

    def test_plantuml_simple_statechart(self, simple_statechart):
        sc = simple_statechart
        display = Display()

        plantuml = display.plantuml(sc)

        # Manually verify the expected PlantUML code was generated.
        assert plantuml

    def test_plantuml_composite_statechart(self, composite_statechart):
        sc = composite_statechart
        display = Display()

        plantuml = display.plantuml(sc)

        # Manually verify the expected PlantUML code was generated.
        assert plantuml

    def test_plantuml_concurrent_statechart(self, concurrent_statechart):
        sc = concurrent_statechart
        display = Display()

        plantuml = display.plantuml(sc)

        # Manually verify the expected PlantUML code was generated.
        assert plantuml
