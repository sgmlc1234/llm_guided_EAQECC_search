"""Conservative per-request KRW reservations; failed/uncertain calls never retry."""

import json
import os
from pathlib import Path


class BudgetExceeded(RuntimeError):
    pass


def atomic_json(path, data):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


class Ledger:
    def __init__(self, path, cap_krw, input_rate, output_rate, multiplier=1.25):
        self.path = Path(path)
        self.cap = cap_krw
        self.input_rate = input_rate
        self.output_rate = output_rate
        self.multiplier = multiplier
        self.data = json.loads(self.path.read_text()) if self.path.exists() else {"calls": []}
        self.data.update(service_cap_krw=cap_krw, safety_multiplier=multiplier,
                         input_krw_per_token=input_rate, output_krw_per_token=output_rate)
        self.save()

    def save(self):
        self.data["committed_krw"] = sum(c["committed_krw"] for c in self.data["calls"])
        self.data["estimated_model_krw"] = sum(c.get("estimated_model_krw", 0) for c in self.data["calls"])
        atomic_json(self.path, self.data)

    def bound(self, prompt_bytes):
        # This exceeds the configured 8192-token output cap. Reserve twice
        # the model's full 65536-token limit to cover reasoning conservatively.
        return self.multiplier * ((prompt_bytes + 4096) * self.input_rate
                                  + 131072 * self.output_rate)

    def ensure(self, amount):
        if self.data["committed_krw"] + amount > self.cap:
            raise BudgetExceeded("next paired requests would exceed the conservative service cap")

    def reserve(self, call_id, amount):
        if any(c["id"] == call_id for c in self.data["calls"]):
            raise RuntimeError("duplicate generation ID; automatic replay is disabled")
        self.ensure(amount)
        entry = {"id": call_id, "status": "reserved", "reserved_krw": amount,
                 "committed_krw": amount}
        self.data["calls"].append(entry)
        self.save()
        return entry

    def settle(self, entry, usage):
        if not isinstance(usage.get("promptTokenCount"), int):
            raise RuntimeError("missing usage data; full reservation retained")
        prompt = usage["promptTokenCount"]
        output = usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)
        if not isinstance(output, int) or prompt < 0 or output < 0:
            raise RuntimeError("invalid usage data; full reservation retained")
        cost = prompt * self.input_rate + output * self.output_rate
        committed = cost * self.multiplier
        if committed > entry["reserved_krw"]:
            entry.update(status="bound_violation", usage=usage)
            self.save()
            raise RuntimeError("provider usage exceeded the reserved bound; stopped")
        entry.update(status="settled", usage=usage, estimated_model_krw=cost,
                     committed_krw=committed)
        self.save()

    def fail_http(self, entry, code):
        # Official Vertex pricing charges model tokens only for HTTP 200.
        entry.update(status="http_error", http_status=code, committed_krw=0.0)
        self.save()
