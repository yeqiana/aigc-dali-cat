# -*- coding: utf-8 -*-
import ast, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
src = open(r"episodes/_system/codex_subscription_image.py", encoding="utf-8").read()
t = ast.parse(src)
lines = src.splitlines()
def show(node, n=60):
    print("###", node.name, "lines", node.lineno, "-", node.end_lineno)
    for i in range(node.lineno - 1, min(node.end_lineno, node.lineno - 1 + n)):
        print(lines[i])
for node in ast.walk(t):
    if isinstance(node, ast.FunctionDef) and node.name in ("cmd_generate_for_frame", "cmd_generate", "main"):
        show(node)
