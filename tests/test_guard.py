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

from statechart import CallGuard, ElseGuard, EqualGuard, Guard, KwEvent, NotGuard


class GreaterThanZero(Guard):
    def check(self, event):
        if 'value' in event.kwargs and event.kwargs['value'] > 0:
            return True
        else:
            return False


class TestGuard:
    def test_abstract_instantiation_throws(self):
        with pytest.raises(TypeError):
            Guard()

    @pytest.mark.parametrize('event, expected',
                             [(KwEvent(name='a', value=0), False),
                              (KwEvent(name='a', value=1), True)])
    def test_guard_check(self, event, expected):
        guard = GreaterThanZero()
        assert guard.check(event=event) == expected

    @pytest.mark.parametrize('a, b, expected',
                             [(1, 1, True),
                              (1, 2, False),
                              ('1', '1', True),
                              ('1', '2', False)])
    def test_equal_guard(self, a, b, expected):
        guard = EqualGuard(a=a, b=b)
        assert guard.check(event=None) == expected


def true_cb(event):
    return True


def false_cb(event):
    return False


class TestCallGuard:
    def my_invalid_callback(self):
        pass

    @pytest.mark.parametrize('guard_cb, expected', [(true_cb, True), (false_cb, False)])
    def test_check_callback_guard(self, guard_cb, expected):
        callback_guard = CallGuard(guard_cb)
        value = callback_guard.check(event=None)
        assert value is expected


class TestNotGuard:
    def test_not_guard(self):
        else_guard = ElseGuard()
        not_guard = NotGuard(else_guard)

        assert else_guard.check(event=None) is True
        assert not_guard.check(event=None) is False
