# V4 Runtime Safety

The Streamlit process never imports XGBoost. Historical XGBoost probes remain in the fixed-entry persistent JSON worker; V4 does not send fabricated live features to it. Registry and Health remain metadata-first.

## Latency governance

Measured cold Hybrid + V1 latency was `5337.484 ms`. Warm p95: TF-IDF `337.263 ms`, semantic `558.201 ms`, Hybrid `517.417 ms`, Hybrid + V1 `491.903 ms`, requested ranker policy with V1 fallback `543.111 ms`, blended fallback `503.891 ms`.

All warm paths remained below one second. The 250 ms Hybrid + V1 target was not met. The 500 ms worker target was not met. No production SLA is claimed. The selected Hybrid retrieval-only path is suitable for a bounded local demo. Cold model/index initialization remains material.

## Memory governance

Peak RSS was `1099.453 MB`. Ending RSS was `1091.203 MB`. Cold initialization increase was `+978.344 MB`. Semantic model/index load counts were `1/1`. Child process count was `1` with a stable worker PID. There was no repeated model download, no repeated index build, no zombie process and no uncontrolled cycle-over-cycle growth. Memory is stable after warm-up and remains in the multi-gigabyte class after cold initialization.
