# Task1 更换并发结构

请你帮我更换并发结构为如下的结构：

```python
with ThreadPoolExecutor(max_workers=max_worker) as executor:
        futures = [
            executor.submit(eval_llm, item, judge_config, model_name)
            for item in need_process_infer_data
        ]

        for future in tqdm(
            as_completed(futures), total=len(need_process_infer_data), desc="processing"
        ):
            result = future.result()
            if result:  # 确保 result 不是 None
                with open(output_jsonl_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    f.flush()  # 强制刷新缓冲区
```