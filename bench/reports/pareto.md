# Pareto table — all runs in bench/reports/

Latency/RSS only comparable within the same host. Smallest model that passes wins (PRD §10.1).

| run | model | prompt | gold | items | pass | field_f1 | unsupported | geo | p95 s | RSS MB | host |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 20260911-141916_Ministral-3-3B-Instruct-2512-Q4_K_M | Ministral-3-3B-Instruct-2512-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.61 | 12.2% | 60% | 179.35 | 4129.228 | lw-main |
| 20260911-152109_Qwen3-4B-Q4_K_M | Qwen3-4B-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.60 | 14.8% | 50% | 218.26 | 4922.58 | lw-main |
| 20260911-151112_Qwen_Qwen3-1.7B-Q4_K_M | Qwen_Qwen3-1.7B-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.56 | 23.3% | 30% | 81.69 | 2519.54 | lw-main |
| 20260911-144614_microsoft_Phi-4-mini-instruct-Q4_K_M | microsoft_Phi-4-mini-instruct-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.48 | 12.5% | 10% | 232.58 | 4387.748 | lw-main |
| 20260911-135755_granite-4.0-1b-Q4_K_M | granite-4.0-1b-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.42 | 23.5% | 30% | 91.11 | 2162.136 | lw-main |
| 20260911-133314_Qwen3-4B-Q4_K_M | Qwen3-4B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.40 | 19.8% | 20% | 174.07 | 4976.292 | lw-main |
| 20260911-125120_Ministral-3-3B-Instruct-2512-Q4_K_M | Ministral-3-3B-Instruct-2512-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.39 | 19.8% | 40% | 176.80 | 4134.94 | lw-main |
| 20260911-131216_microsoft_Phi-4-mini-instruct-Q4_K_M | microsoft_Phi-4-mini-instruct-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.35 | 28.4% | 20% | 121.92 | 4396.7 | lw-main |
| 20260911-154611_Qwen_Qwen3.5-0.8B-Q4_K_M | Qwen_Qwen3.5-0.8B-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.35 | 33.3% | 20% | 42.22 | 1030.872 | lw-main |
| 20260911-141110_LFM2.5-1.2B-Instruct-Q4_K_M | LFM2.5-1.2B-Instruct-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.27 | 52.2% | 10% | 42.50 | 1373.616 | lw-main |
| 20260911-140838_granite-4.0-350m-Q4_K_M | granite-4.0-350m-Q4_K_M.gguf | v0.2 | fixtures | 10 | ❌ | 0.26 | 46.7% | 0% | 18.83 | 604.02 | lw-main |
| 20260911-132629_Qwen_Qwen3-1.7B-Q4_K_M | Qwen_Qwen3-1.7B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.23 | 47.8% | 20% | 52.14 | 2524.224 | lw-main |
| 20260911-123345_granite-4.0-1b-Q4_K_M | granite-4.0-1b-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.22 | 43.1% | 10% | 105.88 | 2171.696 | lw-main |
| 20260911-135232_Qwen_Qwen3.5-0.8B-Q4_K_M | Qwen_Qwen3.5-0.8B-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.12 | 40.0% | 10% | 38.69 | 1122.516 | lw-main |
| 20260911-124434_LFM2.5-1.2B-Instruct-Q4_K_M | LFM2.5-1.2B-Instruct-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.11 | 63.3% | 0% | 35.68 | 1374.472 | lw-main |
| 20260911-124243_granite-4.0-350m-Q4_K_M | granite-4.0-350m-Q4_K_M.gguf | v0.1 | fixtures | 10 | ❌ | 0.09 | 66.7% | 10% | 12.67 | 558.376 | lw-main |
| 20260911-141731_LFM2.5-350M-QAD-Q4_0 | LFM2.5-350M-QAD-Q4_0.gguf | v0.2 | fixtures | 10 | ❌ | 0.05 | 54.4% | 0% | 11.09 | 509.128 | lw-main |
| 20260911-124944_LFM2.5-350M-QAD-Q4_0 | LFM2.5-350M-QAD-Q4_0.gguf | v0.1 | fixtures | 10 | ❌ | 0.05 | 77.8% | 0% | 11.21 | 537.816 | lw-main |
