# Pareto table — all runs in bench/reports/

Latency/RSS only comparable within the same host. Smallest model that passes wins (PRD §10.1).

| run | model | prompt | gold | items | pass | field_f1 | unsupported | geo | p95 s | RSS MB | host |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260911-133314_Qwen3-4B-Q4_K_M | Qwen3-4B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.40 | 19.8% | 20% | 174.07 | 4976.292 | lw-main |
| 20260911-125120_Ministral-3-3B-Instruct-2512-Q4_K_M | Ministral-3-3B-Instruct-2512-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.39 | 19.8% | 40% | 176.80 | 4134.94 | lw-main |
| 20260911-131216_microsoft_Phi-4-mini-instruct-Q4_K_M | microsoft_Phi-4-mini-instruct-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.35 | 28.4% | 20% | 121.92 | 4396.7 | lw-main |
| 20260911-132629_Qwen_Qwen3-1.7B-Q4_K_M | Qwen_Qwen3-1.7B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.23 | 47.8% | 20% | 52.14 | 2524.224 | lw-main |
| 20260911-123345_granite-4.0-1b-Q4_K_M | granite-4.0-1b-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.22 | 43.1% | 10% | 105.88 | 2171.696 | lw-main |
| 20260911-135232_Qwen_Qwen3.5-0.8B-Q4_K_M | Qwen_Qwen3.5-0.8B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.12 | 40.0% | 10% | 38.69 | 1122.516 | lw-main |
| 20260911-124434_LFM2.5-1.2B-Instruct-Q4_K_M | LFM2.5-1.2B-Instruct-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.11 | 63.3% | 0% | 35.68 | 1374.472 | lw-main |
| 20260911-124243_granite-4.0-350m-Q4_K_M | granite-4.0-350m-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.09 | 66.7% | 10% | 12.67 | 558.376 | lw-main |
| 20260911-124944_LFM2.5-350M-QAD-Q4_0 | LFM2.5-350M-QAD-Q4_0.gguf | v0.1 | fixtures | 10 | ❌ | 0.05 | 77.8% | 0% | 11.21 | 537.816 | lw-main |
| 20260911-122205_Qwen_Qwen3.5-0.8B-Q4_K_M | Qwen_Qwen3.5-0.8B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.00 | 0.0% | 0% | 0.04 | 29.68 | lw-main |
