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

from statechart.runtime import Metadata, Scope


class State:
    """A State is a simple state that has no regions or submachine states.

    Args:
        name (str): State name used to identify this instance for logging.
           A unique name is recommended although not enforced.
        context (Context): The parent context that contains this state.

    Attributes:
        name (str): State name used to identify this instance.
        context (Context): State's parent context.

    Examples:
        * First create the parent context
        statechart = Statechart(name='statechart')

        * Then create the states
        a = State(name='a', context=statechart)
        b = State(name='b', context=statechart)

        * Finally create the transitions between states with any associated
        event triggers, actions or guard conditions.
        Transition(name='a to b', start=a, end=b)

    Note:
        Do not dispatch a synchronous event within the action (enter, do or
        exit) functions. If you need to dispatch an event, do so using the
        async_dispatch function of the statechart.

    Raises:
        RuntimeError: If the parent context is invalid.
            Only a state chart can have no parent context.
    """

    def __init__(self, name, context):
        self._logger = logging.getLogger(self.__class__.__name__)

        self.name = name

        """ Context can be null only for the statechart """
        if context is None and (not isinstance(self, Statechart)):
            raise RuntimeError('Context cannot be null')

        self.context = context
        parent = context

        """ Recursively move up to get the statechart object """
        if parent is not None:

            # Create a new child scope subcontext to existing scopes.
            self._scope = context.scope.new_child()

            while 1:
                if isinstance(parent, Statechart):
                    break

                if parent is None:
                    break

                parent = parent.context

            if isinstance(parent, Statechart):
                self.statechart = parent
            else:
                raise RuntimeError('Statechart not found - check hierarchy')

        self._transitions = []

    @property
    def scope(self):
        return self._scope

    def entry(self, event):
        """
        An optional action that is executed whenever this state is
        entered, regardless of the transition taken to reach the state. If
        defined, entry actions are always executed to completion prior to any
        internal activity or transitions performed within the state.

        Args:
            event (Event): Event which led to the transition into this state.
        """
        pass

    def do(self, event):
        """
        An optional action that is executed whilst this state is active.
        The execution starts after this state is entered, and stops either by
        itself, or when the state is exited, whichever comes first.

        Starts an async task. When the task is finished, it may fire an event
        to trigger a state transition. If the task is still in progress when
        this state is deactivated it will be cancelled.

        Args:
            event (Event): Event which led to the transition into this state.
        """
        pass

    def exit(self, event):
        """
        An optional action that is executed upon deactivation of this state
        regardless of which transition was taken out of the state. If defined,
        exit actions are always executed to completion only after all
        internal activities and transition actions have completed execution.
        Initiates cancellation of the state do action if it is still running.

        Args:
            event (Event): Event which led to the transition into this state.
        """
        pass

    def add_transition(self, transition):
        """Add a transition from this state.

        Transitions with guards are checked first.

        Args:
            transition (Transition): Transition to add, can be a normal or
                internal transition.

        Raises:
            RuntimeError: If transition is invalid.
        """
        if transition is None:
            raise RuntimeError('Cannot add null transition')

        if transition.guard:
            self._transitions.insert(0, transition)
        else:
            self._transitions.append(transition)

    def activate(self, metadata, event):
        """
        Activate the state.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Event which led to the transition into this state.

        Returns:
            True if the state was activated.
        """
        self._logger.info('Activate "%s"', self.name)

        if not metadata.is_active(self):
            metadata.activate(self)

            if self.entry:
                self.entry(event)

            if self.do:
                self.do(event)

            return True

        return False

    def deactivate(self, metadata, event):
        """
        Deactivate the state.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Event which led to the transition out of this state.

        Returns:
            True if state deactivated, False if already inactive.
        """
        self._logger.info('Deactivate "%s"', self.name)

        if metadata.is_active(self):

            if self.exit:
                self.exit(event)

            metadata.deactivate(self)

    def dispatch(self, metadata, event):
        """
        Dispatch transition.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Transition event trigger.

        Returns:
            True if transition executed, False if transition not allowed,
            due to mismatched event trigger or failed guard condition.
        """
        status = False

        for transition in self._transitions:
            if transition.execute(metadata, event):
                status = True
                break

        return status


class Context(State):
    """
    Domain of the state. Needed for setting up the hierarchy. This class
    needn't be instantiated directly.

    Args:
        name (str): An identifier for the model element.
        context (Context): The parent context that contains this state.
    """

    def __init__(self, name, context):
        super().__init__(name=name, context=context)
        self.initial_state = None


class FinalState(State):
    """
    A special kind of state signifying that the enclosing composite state or
    the entire state machine is completed.

    A final state cannot have transitions or dispatch other transitions.

    Args:
        name (str): An identifier for the model element.
        context (Context): The parent context that contains this state.

    Raises:
        RuntimeError: If the model is ill-formed by attempting to add a transition directly from
            the final state.
    """

    def __init__(self, name, context):
        super().__init__(name=name, context=context)

    def add_transition(self, transition):
        raise RuntimeError('Cannot add a transition from the final state')

    def dispatch(self, metadata, event):
        raise RuntimeError('Cannot dispatch an event to the final state')


class ConcurrentState(Context):
    """
    A concurrent state is a state that contains composite state regions,
    activated concurrently.

    Args:
        name (str): An identifier for the model element.
        context (Context): The parent context that contains this state.
    """

    def __init__(self, name, context):
        super().__init__(name, context)
        self._regions = []

    def add_region(self, region):
        """
        Add a new region to the concurrent state.

        Arsg:
            region (CompositeState): Region to add.
        """
        if isinstance(region, CompositeState):
            self._regions.append(region)
        else:
            raise RuntimeError('A concurrent state can only add composite state regions')

    def activate(self, metadata, param):
        """
        Activate the state.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Event which led to the transition into this state.

        Returns:
            True if state activated, False if already active.
        """
        if super().activate(metadata, param):
            rdata = metadata.active_states[self]

            for region in self._regions:
                if not (region in rdata.state_set):
                    # Check if region is activated implicitly via incoming transition.
                    region.activate(metadata, param)
                    region.initial_state.activate(metadata, param)

            return True

        return False

    def deactivate(self, metadata, param):
        """
        Deactivate child states within regions, then overall state.

        Args:
            metadata (Metadata): Statechart metadata data.
            event: Event which led to the transition out of this state.

        Returns:
            True if state deactivated, False if already inactive.
        """
        self._logger.info('Deactivate "%s"', self.name)

        for region in self._regions:
            if metadata.is_active(region):
                region.deactivate(metadata, param)

        super().deactivate(metadata, param)

    def dispatch(self, metadata, event):
        """
        Dispatch transition.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Transition event trigger.

        Returns:
            True if transition executed, False if transition not allowed,
            due to mismatched event trigger or failed guard condition.
        """
        if not metadata.active_states[self]:
            raise RuntimeError('Inactive composite state attempting to dispatch transition')

        dispatched = False

        """ Check if any of the child regions can handle the event """
        for region in self._regions:
            if region.dispatch(metadata, event):
                dispatched = True

        if dispatched:
            return True

        """ Check if this state can handle the event by itself """
        for transition in self._transitions:
            if transition.execute(metadata, event):
                dispatched = True
                break

        return dispatched

    def is_finished(self, metadata):
        """"
        Check if all regions within the concurrent state are finished.

        Args:
            metadata (Metadata): Statechart metadata data.

        Returns:
            True if the concurrent state is finished.
        """
        return all(region.is_finished(metadata) for region in self._regions)


class CompositeState(Context):
    """
    A composite state is a state that contains other state vertices (states,
    pseudostates, etc.).

    Args:
        name (str): An identifier for the model element.
        context (Context): The parent context that contains this state.
    """

    def __init__(self, name, context):
        super().__init__(name=name, context=context)
        self.history = None

        if isinstance(context, ConcurrentState):
            context.add_region(self)

    def activate(self, metadata, event):
        """
        Activate the state.

        If the transition being activated leads to this state, activate
        the initial state.

        Args:
            metadata (Metadata): Statechart metadata data.
            event: Event which led to the transition into this state.
        """
        super().activate(metadata, event)

        if metadata.transition and metadata.transition.end is self:
            self.initial_state.activate(metadata=metadata, event=event)

    def deactivate(self, metadata, event):
        """
        Deactivate the state.

        If this state contains a history state, store the currently active
        state in history so it can be restored once the history state is
        activated.

        Args:
            metadata (Metadata): Statechart metadata data.
            event: Event which led to the transition out of this state.
        """
        state_runtime_data = metadata.active_states[self]

        # If the composite state contains a history pseudostate, preserve the current active child
        # state in history, unless that state is a final state.
        if self.history and not (isinstance(state_runtime_data.current_state, FinalState)):
            metadata.store_history_info(self.history, state_runtime_data.current_state)

        if metadata.is_active(state=state_runtime_data.current_state):
            state_runtime_data.current_state.deactivate(metadata=metadata, event=event)

        super().deactivate(metadata, event)

    def dispatch(self, metadata, event):
        """
        Dispatch transition.

        Args:
            metadata (Metadata): Statechart metadata data.
            event (Event): Transition event trigger.

        Returns:
            True if transition executed, False if transition not allowed,
            due to mismatched event trigger or failed guard condition.
        """
        if not metadata.active_states[self]:
            raise RuntimeError('Inactive composite state attempting to dispatch transition')

        # See if the current child state can handle the event
        data = metadata.active_states[self]
        if data.current_state is None and self.initial_state:
            metadata.activate(self.initial_state)
            data.current_state.activate(metadata, event)

        dispatched = False

        if data.current_state and data.current_state.dispatch(metadata, event):
            dispatched = True

        # If the substate dispatched the event and reached a final state or if this state
        # is no longer active, trigger a new dispatch for the end transition, otherwise return.
        if dispatched and metadata.is_active(self) and not isinstance(metadata.active_states[self].current_state,
                                                                      FinalState):
            return True

        # Since none of the child states can handle the event, let this state
        # try handling the event.
        for transition in self._transitions:
            # If transition is local, deactivate current state if transition is allowed.
            if self not in transition.deactivate and transition.is_allowed(event):
                transition.deactivate.insert(0, metadata.active_states[self].current_state)

            if transition.execute(metadata, event):
                return True

        return False

    def is_finished(self, metadata):
        """"
        Check if the composite state has reached it's final state.

        Args:
            metadata (Metadata): Statechart metadata data.

        Returns:
            True if the composite state is finished.
        """
        return isinstance(metadata.active_states[self].current_state, FinalState)


class Statechart(Context):
    """
    The main entry point for using the statechart framework. Contains all
    necessary methods for delegating incoming events to the substates.

    Args:
        name (str): An identifier for the model element.
    """

    def __init__(self, name):
        super().__init__(name=name, context=None)
        self._scope = Scope()
        self._metadata = Metadata()

    def start(self):
        """
        Initialises the Statechart in the metadata. Sets the start state.

        Ensure the statechart has at least an initial state.

        Raises:
            RuntimeError if the statechart had already been started.
        """
        self._logger.info('Start "%s"', self.name)
        self._metadata.reset()
        self._metadata.activate(self)
        self._metadata.activate(self.initial_state)
        self.dispatch(None)

    def stop(self):
        """
        Stops the statemachine by deactivating statechart and thus all it's child states.
        """
        self._logger.info('Stop "%s"', self.name)
        self.deactivate(self._metadata, event=None)

    def dispatch(self, event):
        """
        Calls the dispatch method on the current state.

        Args:
            event (Event): Transition event trigger.

        Returns:
            True if transition executed.
        """
        current_state = self._metadata.active_states[self].current_state
        return current_state.dispatch(self._metadata, event)

    def add_transition(self, transition):
        raise RuntimeError('Cannot add transition to a statechart')

    def is_active(self, state_name):
        """
        Check if the state name is active

        Args:
            state_name (str): State name to check.

        Returns:
            True if the state name is currently active.
        """
        for state in self._metadata.active_states:
            if state.name == state_name:
                return True

        return False

    def is_finished(self):
        """"
        Check if the statechart has finished

        Returns:
            True if the statechart has finished.
        """
        if isinstance(self._metadata.active_states[self].current_state, FinalState):
            return True
        else:
            return False
