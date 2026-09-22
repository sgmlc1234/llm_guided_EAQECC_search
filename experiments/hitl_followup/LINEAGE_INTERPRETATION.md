# What the preserved lineage comparison can test

The three frozen programs already use the small dual-space representation. The follow-up does not test whether generation discovers that representation without the shared researcher hint.

- g00: rank-four dual-space basis, low-support replacement/XOR moves (one to three qubits), objective based on entanglement mismatch and offending-vector count.
- g01: retains that search and adds a penalty for distance below the target. This is the narrowest adjacent change in the stored lineage.
- g02: changes objective weights, move-support range and mixture (including basis-row mixing), temperature/restart rules, and adds best-state return after stagnation. These changes occur together.

A pure XOR of one basis row with another preserves the span; its immediate role is a basis change. Combined with later coordinate mutations it can change the subsequent search trajectory. Do not describe every such move as a new code.

The frozen classical L-side control uses the same representation but retains the older simulated-annealing objective and move/restart policy. Comparing it with the generated programs addresses the missing non-LLM baseline. It does not isolate individual evolved edits.

Report g00/g01/g02 at every approved length and all fresh execution seeds. The lineage was selected after its original observed performance, so any improvement is a diagnosis of this preserved lineage, not independent generation replication. The four original generation blocks remain the unit for claims about generation policy; the 32 execution seeds do not replace them.
