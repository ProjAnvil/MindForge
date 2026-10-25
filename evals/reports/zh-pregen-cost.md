# Pre-generation Chinese context lookup: token comparison

A: concise writing rules, direct answer. B: the same rules, real context lookup, then answer.
No Stop hook, full-draft preflight or post-generation polishing is included.
One readonly MCP tool is exposed. Native tool choice ensures the required lookup occurs;
this experiment does not measure whether an unconstrained agent obeys a tool-use prompt.

Requested model: `deepseek-v4-flash`; provider: `api.deepseek.com`; 3 paired rounds per context.

| Context | History chars | A input/output | B input/output | Extra tokens | B/A | A ms | B ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| short | 2000 | 1265 / 36 | 3100 / 63 | 1861 | 2.43x | 921.8 | 1908.8 |
| medium | 16000 | 9241 / 31 | 19052 / 66 | 9846 | 2.06x | 1117.7 | 2284.4 |
| long | 64000 | 36590 / 28 | 73750 / 63 | 37195 | 2.02x | 1137.4 | 2718.0 |

Input includes cached tokens. API token counts are not monetary costs.
Table values are paired-trial means, rounded for display; ratios use the mean totals.
B includes both model requests, schema overhead, tool-call arguments and actual lookup results.
The local lookup measurement includes MCP process startup; the measured token counts are unaffected.
Only synthetic background is submitted. Samples are small and latency depends on cache/network conditions.

## Sample answers

### short
A: 任务42目前尚未完成，后续会先处理它，再执行已经安排好的下一项。下一项虽已排定，但还没有开始执行。

B: 任务42尚未完成，等它完成后就会接着处理下一项。下一项已经安排好，但目前还没有开始执行。

Actual lookup result: 纯尾即就绪（任务衔接语境：等这个任务完成之后，就继续下一项；直接说明先后关系，不引入额外状态或机制）

Task ID preserved in every paired trial: True.

### medium
A: 任务42目前尚未完成，请先等待它处理完毕。下一项任务已经排好，但还没有开始执行，会在42之后再继续。

B: 任务42目前尚未完成，需要先等它完成。之后会接着执行已经安排好的下一项，但下一项现在还没有开始。

Actual lookup result: 纯尾即就绪（任务衔接语境：等这个任务完成之后，就继续下一项；直接说明先后关系，不引入额外状态或机制）

Task ID preserved in every paired trial: True.

### long
A: 任务42尚未完成，目前处于就绪状态。后续将先继续处理任务42，再执行已安排但尚未开始的下一项。

B: 任务42目前尚未完成，等它完成后，再继续下一项。下一项已经安排好，但还没有开始执行。

Actual lookup result: 纯尾即就绪（任务衔接语境：等这个任务完成之后，就继续下一项；直接说明先后关系，不引入额外状态或机制）

Task ID preserved in every paired trial: True.

