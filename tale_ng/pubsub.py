"""
Simple synchronous Pubsub signaling.

Uses weakrefs to not needlessly lock subscribers/topics in memory.

'Tale-NG' mud driver, mudlib and interactive fiction framework
Copyright by Irmen de Jong (irmen@razorvine.net)

"""

import threading
import weakref
from typing import Dict, List, Any, Callable, Set

ListenerType = Callable[[str, Any], None]


class Topic:
    """
    A pubsub topic to send/receive events.
    Usually you can just interact with the Bus though.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self.subscribers: Set[weakref.ReferenceType[ListenerType]] = set()

    def subscribe(self, subscriber: ListenerType) -> None:
        self.subscribers.add(weakref.ref(subscriber))

    def unsubscribe(self, subscriber: ListenerType) -> None:
        self.subscribers.discard(weakref.ref(subscriber))

    def send(self, event: Any) -> None:
        for sub_ref in self.subscribers:
            sub = sub_ref()
            if sub:
                sub(self.name, event)


class Bus:
    """
    Pubsub message bus.
    """

    def __init__(self) -> None:
        self._topics: Dict[str, Topic] = {}
        self._lock = threading.Lock()

    @property
    def topics(self) -> List[str]:
        return list(self._topics)

    def remove_topic(self, name: str) -> None:
        del self._topics[name]

    def subscribe(self, topic: str, listener: ListenerType) -> None:
        t = self.topic(topic, False)
        t.subscribe(listener)

    def unsubscribe(self, topic: str, listener: ListenerType) -> None:
        with self._lock:
            t = self.topic(topic, True)
            t.unsubscribe(listener)

    def unsubscribe_all(self, subscriber: ListenerType) -> None:
        """unsubscribe the given subscriber object from all topics that it may have been subscribed to."""
        for topic in list(self._topics.values()):
            topic.unsubscribe(subscriber)

    def send(self, topic: str, message: Any) -> None:
        t = self.topic(topic, True)
        t.send(message)

    def broadcast(self, message: Any) -> None:
        for topic in list(self._topics.values()):
            topic.send(message)

    def topic(self, name: str, must_exist: bool = False) -> Topic:
        with self._lock:
            if name in self._topics:
                return self._topics[name]
            if must_exist:
                raise LookupError("no such topic")
            topic = self._topics[name] = Topic(name)
            return topic


if __name__ == '__main__':
    def listener1(topic, event):
        print("1 got an event:", topic, event)


    def listener2(topic, event):
        print("2 got an event:", topic, event)


    bus = Bus()
    bus.subscribe("test.topic1", listener1)
    bus.subscribe("test.topic1", listener2)
    bus.subscribe("test.topic2", listener1)
    print(bus.topics)
    bus.send("test.topic1", [1, 2, 3])
    bus.send("test.topic2", [1, 2, 3])
    bus.unsubscribe_all(listener2)
    bus.broadcast("broadcasted")
