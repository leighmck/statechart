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
from collections import ChainMap


class StateRuntimeData:
    """
    Holds the runtime specific data for a state in the statechart.
    """

    def __init__(self):
        self.current_state = None
        self.state_set = list()
        self._logger = logging.getLogger(__name__)


class Metadata:
    """
    Describes runtime specific data of the statechart. The main data is the
    currently active state. For every active state a StateRuntimeData object is
    created which stores specific data for the state. This object is allocated
    only when the state is active, otherwise it is deleted.
    """

    def __init__(self):
        self.active_states = {}
        self.event = None
        self.history_states = {}
        self.transition = None
        self._logger = logging.getLogger(__name__)

    def activate(self, state):
        """
        Activates a state for this Metadata. If the state is not already
        active, it will be added and a new StateRuntimeData created.

        :param state: State to activate.
        """
        self._logger.info('activate %s', state.name)
        if not (state in self.active_states):
            self.active_states[state] = StateRuntimeData()

        data = self.active_states[state]
        data.current_state = None

        if state.context:
            if state.context not in self.active_states:
                raise RuntimeError('Parent state not activated')

            data = self.active_states[state.context]
            data.current_state = state

    def deactivate(self, state):
        """
        Deactivates the state and frees the allocated resources.

        :param state: State to deactivate.
        """
        self._logger.info('deactivate %s', state.name)

        if state in self.active_states:
            data = self.active_states[state]
            data.current_state = None
            data = None
            del self.active_states[state]

    def get_history_state(self, history_state):
        """
        Get the last active state when the history state context was
        deactivated.

        :param history_state: History state to lookup
        :return: The most recent state remembered by the specified history
            state.
        """
        self._logger.info('get history state %s', history_state.name)
        return self.history_states[history_state]

    def has_history_info(self, history_state):
        """
        Check if the active state runtime has history info to restore.

        :param history_state: History state to lookup
        :return: True if the history state has info of a state to be restored.
        """
        status = False

        if history_state in self.history_states:
            status = True

        self._logger.info('has history info %s? %s', history_state.name, str(status))
        return status

    def is_active(self, state):
        """
        Checks whether the given state is active or not.

        :param state: State to check.
        :return: True is the state is active.
        """
        status = False

        if state in self.active_states:
            status = True

        self._logger.info('is %s active? %s', state.name, str(status))
        return status

    def reset(self):
        """Resets the metadata object for reuse."""
        self._logger.info('reset active states & history')
        self.active_states.clear()
        self.history_states.clear()

    def store_history_info(self, history_state, actual_state):
        self._logger.info('store history state %s for actual state %s', history_state.name, actual_state.name)
        self.history_states[history_state] = actual_state


class Scope(ChainMap):
    """Variant of ChainMap that allows direct updates to inner scopes"""

    def __setitem__(self, key, value):
        for mapping in self.maps:
            if key in mapping:
                mapping[key] = value
                return
        self.maps[0][key] = value
