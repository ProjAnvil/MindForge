# Chinese dictionary context-cost study

Controlled fixed drafts; history varies independently of answer length.
Matched cases deliberately trigger review; they do not estimate the frequency of real-world matches.
Paired request order is balanced. Cache hits are recorded; tokens are not a monetary cost estimate.

Only retained paired trials are reported; warm-ups, protocol probes and invalid draft trials are excluded.
Input/output/cache counters aggregate the generation and continuation requests in each arm.

| Case | Injection mean ms | Stop mean ms | Annotations | Estimated injection tokens |
|---|---:|---:|---:|---:|
| matched | 27.60 | 28.39 | 3 | 1613 |
| clean | 27.68 | 27.79 | 0 | 1613 |

Local token backend: `estimate/cjk+1.3*words`.

Live requested model: `deepseek-v4-flash`; provider: `api.deepseek.com`.
Actual response models: deepseek-flash

| Context | History chars | Case | Baseline input/output | Dict input/output | Extra tokens | Baseline ms | Dict ms | Extra ms (range) |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| short | 2000 | matched | 1386 / 41 | 6360 / 84 | 5017 | 741.5 | 1899.8 | 1158.4 (1127.3..1174.8) |
| short | 2000 | clean | 1378 / 37 | 2834 / 37 | 1456 | 825.0 | 894.0 | 68.9 (-57.9..248.1) |
| medium | 16000 | matched | 9362 / 41 | 22312 / 84 | 12993 | 939.0 | 1871.3 | 932.3 (496.9..1508.9) |
| medium | 16000 | clean | 9354 / 37 | 10810 / 37 | 1456 | 813.4 | 714.3 | -99.1 (-180.1..-44.5) |
| long | 64000 | matched | 36711 / 41 | 77010 / 79 | 40337 | 1113.1 | 2438.9 | 1325.8 (1181.8..1570.3) |
| long | 64000 | clean | 36703 / 37 | 38159 / 37 | 1456 | 1349.5 | 1078.1 | -271.4 (-472.9..89.4) |

## Model outputs and preservation

### short / matched
Numeric facts preserved in every trial: True.
Last final response:

当前任务完成后就继续下一项；下一项已经安排好，等待执行。工作线程先休眠 20ms，再重试 7 次。任务ID是42，处理结果会写入日志。

### short / clean
Numeric facts preserved in every trial: True.
Last final response:

当前任务完成后继续下一项；已安排下一项，等待执行。工作线程休眠20ms后重试7次。任务ID是42，处理结果会写入日志。

### medium / matched
Numeric facts preserved in every trial: True.
Last final response:

当前任务完成后就继续下一项；下一项已经安排好，等待执行。工作线程先休眠 20ms，再重试 7 次。任务ID是42，处理结果会写入日志。

### medium / clean
Numeric facts preserved in every trial: True.
Last final response:

当前任务完成后继续下一项；已安排下一项，等待执行。工作线程休眠20ms后重试7次。任务ID是42，处理结果会写入日志。

### long / matched
Numeric facts preserved in every trial: True.
Last final response:

当前任务完成后就继续下一项；下一项已经安排好，等待执行。工作线程先 sleep 20ms，再重试7次。任务ID是42，处理结果会写入日志。

### long / clean
Numeric facts preserved in every trial: True.
Last final response:

当前任务完成后继续下一项；已安排下一项，等待执行。工作线程休眠20ms后重试7次。任务ID是42，处理结果会写入日志。

## Interpretation

Stop sees only the last response, not the entire history. Local checking therefore need not grow with conversation history.
A rewrite continuation sends the history again. Its input tokens, response tokens and network/generation latency are included above.
No automatic string replacement is performed. Remaining annotations can be legitimate retained wording.
These are synthetic, controlled samples from one provider; caching and network timing affect the observed deltas.
