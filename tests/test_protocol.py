import asyncio
import json
import unittest
from unittest.mock import patch

from service.server import handle


class Socket:
    def __init__(self, messages):
        self.messages = iter(messages)
        self.sent = []

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return next(self.messages)
        except StopIteration:
            raise StopAsyncIteration

    async def send(self, message):
        self.sent.append(json.loads(message))


class Engine:
    device = "cpu"

    def infer(self, data, tags, confidence, max_boxes):
        return {"tags": tags, "confidence": confidence, "max_boxes": max_boxes}


class ProtocolTest(unittest.TestCase):
    def test_config_frame_and_invalid_config_are_isolated(self):
        ws = Socket([json.dumps({"type": "config", "tags": ["holding"]}),
                     json.dumps({"type": "config", "tags": ["beside"], "max_boxes": 1}),
                     b"frame"])
        asyncio.run(handle(ws, Engine()))
        self.assertEqual([x["type"] for x in ws.sent], ["ready", "configured", "error", "result"])
        self.assertEqual(ws.sent[-1]["tags"], ["holding"])
        self.assertEqual(ws.sent[-1]["max_boxes"], 12)


if __name__ == "__main__":
    unittest.main()
