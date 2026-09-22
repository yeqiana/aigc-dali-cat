# Story OS V2.2.5 — Visual Test Fast Path

默认 `visual` 不再先启动隔离 worker。

```bat
python -X utf8 scripts/story_test.py visual "<episode>" --scene "..." --image-model gpt-image-2 --strict-model
```

它只做前检、建目录、写计划，并返回 `VISUAL_TEST_NATIVE_IMAGE_REQUIRED`。Codex 当前主会话必须直接调用原生图片工具一次，把真实图片保存到计划中的 `raw_target`，然后：

```bat
python -X utf8 scripts/story_test.py visual-finalize "<episode>"
```

Finalizer 会验证真实图片、Visual Profile SHA、规范化结果和 SHA256，最后写 `VISUAL_TEST_GENERATED_PENDING_REVIEW`。

旧隔离 worker 仅用于诊断：

```bat
python -X utf8 scripts/story_test.py visual "<episode>" --scene "..." --worker-route
```

Production Smoke Test 与正式 Production 不变。
