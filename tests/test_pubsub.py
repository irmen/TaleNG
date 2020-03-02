"""
Unittests for Pubsub

'Tale-NG' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)
"""


import gc
import pytest
from tale_ng.pubsub import Bus


@pytest.fixture()
def bus():
    return Bus()


def test_global_namespace(bus: Bus):
    s1 = bus.topic("s1")
    s2 = bus.topic("s2")
    s3 = bus.topic("s1")
    assert s1 is s3
    assert s1 is not s2


def test_pubsub_sync(bus: Bus):
    s = bus.topic("testsync")
    subber1_msgs = []
    subber2_msgs = []
    def subber1(topic, event):
        subber1_msgs.append((topic, event))
    def subber2(topic, event):
        subber2_msgs.append((topic, event))
    s.subscribe(subber1)
    s.subscribe(subber1)
    s.subscribe(subber2)
    s.subscribe(subber2)
    s.send([1, 2, 3])
    assert subber1_msgs == [("testsync", [1, 2, 3])]
    assert subber2_msgs == [("testsync", [1, 2, 3])]
    # check explicit unsubscribe
    subber1_msgs = []
    subber2_msgs = []
    s.unsubscribe(subber1)
    s.unsubscribe(subber1)
    s.unsubscribe(subber2)
    s.send("after unsubscribing")
    assert subber1_msgs == []
    assert subber2_msgs == []


def test_weakrefs(bus: Bus):
    s = bus.topic("test222")
    def subber(topic, event):
        raise RuntimeError("shouldn't reach this")
    s.subscribe(subber)
    del subber
    gc.collect()
    s.send("after gc")


def test_unsubscribe_all(bus: Bus):
    s1 = bus.topic("testA")
    s2 = bus.topic("testB")
    s3 = bus.topic("testC")
    subber_msgs = set()
    def subber(topic, event):
        subber_msgs.add((topic, event))
    s1.subscribe(subber)
    s2.subscribe(subber)
    s3.subscribe(subber)
    s1.send("one")
    s2.send("two")
    s3.send("three")
    assert subber_msgs == {('testA', 'one'), ('testB', 'two'), ('testC', 'three')}
    subber_msgs.clear()
    bus.unsubscribe_all(subber)
    bus.unsubscribe_all(subber)
    s1.send("one")
    s2.send("two")
    s3.send("three")
    assert len(subber_msgs)==0


def test_remove_topic(bus: Bus):
    s1 = bus.topic("testA")
    def subber(topic, event):
        raise RuntimeError("should not get event")
    s1.subscribe(subber)
    s1.remove_from(bus)
    s1.remove_from(bus)
    assert s1.name == "<defunct>"
    s1.send("123")
