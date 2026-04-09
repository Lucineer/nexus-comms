'''Nexus Comms — MQTT bridge, mesh networking, relay routing.'''
import time, random, math, hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Set
from enum import IntEnum

class MsgType(IntEnum):
    DATA = 0; HEARTBEAT = 1; DISCOVERY = 2; ROUTE = 3; ACK = 4

@dataclass
class Message:
    msg_id: str; src: str; dst: str; msg_type: MsgType; payload: str = ""
    ttl: int = 10; hops: int = 0; timestamp: float = 0

class MeshNetwork:
    def __init__(self, node_id: str):
        self.node_id = node_id; self.neighbors: Dict[str, float] = {}
        self.routing_table: Dict[str, str] = {}; self.msg_log: List[Message] = []
        self.msg_counter = 0
    def add_neighbor(self, neighbor_id: str, link_quality: float = 1.0) -> None:
        self.neighbors[neighbor_id] = link_quality
    def flood(self, msg: Message) -> List[str]:
        forwarded_to = []
        for nid, quality in self.neighbors.items():
            if nid != msg.src and msg.hops < msg.ttl:
                msg.hops += 1; forwarded_to.append(nid)
        self.msg_log.append(msg); return forwarded_to
    def route(self, msg: Message) -> Optional[str]:
        if msg.dst in self.neighbors: return msg.dst
        next_hop = self.routing_table.get(msg.dst)
        if next_hop and next_hop in self.neighbors: return next_hop
        return None

class RelayRouter:
    def __init__(self, network: MeshNetwork):
        self.network = network; self.forwarded: Set[str] = set()
    def handle_message(self, msg: Message) -> Tuple[bool, Optional[str]]:
        if msg.msg_id in self.forwarded: return (False, None)
        self.forwarded.add(msg.msg_id)
        if msg.dst == self.network.node_id: return (True, None)
        next_hop = self.network.route(msg)
        return (False, next_hop)

class TopicBridge:
    def __init__(self):
        self.subscriptions: Dict[str, List[str]] = {}; self.messages: List[Dict] = []
    def subscribe(self, topic: str, subscriber_id: str) -> None:
        if topic not in self.subscriptions: self.subscriptions[topic] = []
        if subscriber_id not in self.subscriptions[topic]:
            self.subscriptions[topic].append(subscriber_id)
    def publish(self, topic: str, payload: str, sender: str) -> List[str]:
        self.messages.append({"topic": topic, "payload": payload,
                             "sender": sender, "time": time.time()})
        return self.subscriptions.get(topic, [])
    def topics(self) -> List[str]:
        return list(self.subscriptions.keys())

def demo():
    print("=== Comms ===")
    mesh = MeshNetwork("node_0")
    for i in range(1, 5): mesh.add_neighbor(f"node_{i}", random.uniform(0.5, 1.0))
    mesh.routing_table["node_10"] = "node_2"
    msg = Message("m1", "node_1", "node_10", MsgType.DATA, "survey_data")
    next_hop = mesh.route(msg)
    print(f"  Route node_1→node_10: via {next_hop}")
    flooded = mesh.flood(msg)
    print(f"  Flood: forwarded to {flooded}")
    relay = RelayRouter(mesh)
    handled, next_hop = relay.handle_message(Message("m2", "node_3", "node_0", MsgType.DATA, "ping"))
    print(f"  Relay: delivered={handled}, forward={next_hop}")
    bridge = TopicBridge()
    bridge.subscribe("depth", "auv_1"); bridge.subscribe("depth", "auv_2")
    bridge.subscribe("position", "surface")
    subs = bridge.publish("depth", "5.2m", "auv_1")
    print(f"  Topic 'depth': {subs}")

if __name__ == "__main__": demo()
