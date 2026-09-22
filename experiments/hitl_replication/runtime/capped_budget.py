"""V3 reservations use twice the explicitly configured output-token cap."""

from pilot_budget import Ledger


class CappedLedger(Ledger):
    def bound(self, prompt_bytes):
        # Requests are limited to 8192 output+thinking tokens. Retain a 2x
        # output reserve plus the common 25% multiplier and KRW 6000 buffer.
        return self.multiplier * ((prompt_bytes + 4096) * self.input_rate + 16384 * self.output_rate)

    def settle(self, entry, usage):
        try:
            super().settle(entry, usage)
        except RuntimeError:
            if entry.get("status") == "bound_violation":
                # Never under-report a provider limit violation. The caller stops;
                # the separate authorization buffer covers this exceptional call.
                cost = usage["promptTokenCount"] * self.input_rate + (
                    usage.get("candidatesTokenCount", 0) + usage.get("thoughtsTokenCount", 0)) * self.output_rate
                entry.update(estimated_model_krw=cost, committed_krw=cost * self.multiplier)
                self.save()
            raise
