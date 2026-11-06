"""Local, single-client inference server for the TouchDesigner prototype."""
import argparse
import asyncio
import io
import json
import struct
import time

from PIL import Image
from websockets.asyncio.server import serve


class Engine:
    def __init__(self, device):
        from ultralytics import YOLO
        from relsgg import RelateAnything

        self.detector = YOLO("yolo26n.pt")
        self.model = RelateAnything.from_pretrained("maelic/relsgg-vits16plus", device=device)
        self.device = device
        self.tags = None

    def infer(self, data, tags, confidence, max_boxes):
        if data[:4] == b"TDR1":
            if len(data) < 12:
                raise ValueError("incomplete raw frame header")
            width, height = struct.unpack(">II", data[4:12])
            if not (1 <= width <= 2048 and 1 <= height <= 2048) or len(data) != 12 + width * height * 3:
                raise ValueError("invalid raw RGB frame dimensions or length")
            image = Image.frombytes("RGB", (width, height), data[12:])
        else:
            image = Image.open(io.BytesIO(data)).convert("RGB")
        if self.tags != tags:
            self.model.set_vocabulary(tags)
            self.tags = list(tags)
        detection = self.detector(image, conf=confidence, max_det=max_boxes,
                                  device=self.device, verbose=False)[0]
        boxes = detection.boxes.xyxy.cpu().numpy()
        labels = [detection.names[int(c)] for c in detection.boxes.cls]
        objects = [{"index": i, "label": labels[i], "box": box.tolist(),
                    "score": float(detection.boxes.conf[i])}
                   for i, box in enumerate(boxes)]
        relations = []
        if len(boxes) >= 2:
            for triplet in self.model.predict(image, boxes, box_labels=labels, topk=100,
                                              max_boxes=max_boxes):
                relations.append({"subject": triplet.subject_idx, "object": triplet.object_idx,
                                  "tag": triplet.predicate, "score": float(triplet.score)})
        return {"width": image.width, "height": image.height,
                "objects": objects, "relations": relations}


async def handle(ws, engine):
    tags = ["holding", "beside", "looking at"]
    confidence, max_boxes = 0.35, 12
    await ws.send(json.dumps({"type": "ready", "protocol": 1, "device": engine.device}))
    async for message in ws:
        try:
            if isinstance(message, str):
                obj = json.loads(message)
                if obj.get("type") != "config":
                    raise ValueError("expected a config message")
                new_tags = obj.get("tags", tags)
                if not isinstance(new_tags, list) or not 1 <= len(new_tags) <= 32 or any(
                    not isinstance(t, str) or not t.strip() or len(t) > 100 for t in new_tags
                ):
                    raise ValueError("tags must be a list of 1–32 nonempty strings")
                new_confidence = float(obj.get("confidence", confidence))
                new_max_boxes = int(obj.get("max_boxes", max_boxes))
                if not 0 <= new_confidence <= 1 or not 2 <= new_max_boxes <= 60:
                    raise ValueError("confidence or max_boxes out of range")
                tags = [t.strip() for t in new_tags]
                confidence, max_boxes = new_confidence, new_max_boxes
                await ws.send(json.dumps({"type": "configured", "tags": tags}))
            else:
                started = time.monotonic()
                result = await asyncio.to_thread(engine.infer, message, tags, confidence, max_boxes)
                result.update(type="result", inference_ms=round((time.monotonic() - started) * 1000, 1))
                await ws.send(json.dumps(result))
        except Exception as exc:
            await ws.send(json.dumps({"type": "error", "message": str(exc)}))


async def run(engine, port):
    # A single connection avoids concurrent model mutation and unbounded queues.
    lock = asyncio.Lock()
    async def client(ws):
        if lock.locked():
            await ws.close(1013, "server already has a client")
            return
        async with lock:
            await handle(ws, engine)
    async with serve(client, "127.0.0.1", port, max_size=8 * 1024 * 1024, max_queue=1):
        print(f"Ready at ws://127.0.0.1:{port}", flush=True)
        await asyncio.Future()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", choices=["cpu", "mps", "cuda"], default="cpu")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print("Loading models; first run downloads weights...", flush=True)
    asyncio.run(run(Engine(args.device), args.port))


if __name__ == "__main__":
    main()
