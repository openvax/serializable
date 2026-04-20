from serializable import Serializable, from_serializable_repr, to_serializable_repr

from .common import eq_


class A(Serializable):
    def __init__(self, a_val):
        self.a = a_val

    def to_dict(self):
        return {"a_val": self.a}


class B(Serializable):
    def __init__(self, set_a_vals=set([A(1), A(2)])):
        self.set_a_vals = set_a_vals

    def to_dict(self):
        return {"set_a_vals": self.set_a_vals}


def test_list_of_lists():
    x = [[1, 2], ["hello", "wookies"], [A(1), A(2)]]
    eq_(x, from_serializable_repr(to_serializable_repr(x)))


def test_dict_of_lists():
    x = {"a": [1, 2, 3], "b": ["hello", "goodbye"], "1": [A(1), A(2)]}
    eq_(x, from_serializable_repr(to_serializable_repr(x)))


def test_dict_with_tuple_keys():
    x = {(1, 2): "hello"}
    eq_(x, from_serializable_repr(to_serializable_repr(x)))


def test_object_with_dict_values():
    x = A(dict(snooze=5))
    eq_(x, from_serializable_repr(to_serializable_repr(x)))


def test_object_with_set_values():
    x = B()
    eq_(x, from_serializable_repr(to_serializable_repr(x)))
