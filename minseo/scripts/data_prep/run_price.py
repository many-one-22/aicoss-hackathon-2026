# -*- coding: utf-8 -*-
"""시세 파이프라인 일괄 실행: 사전 → 가격 → 제철. lookup은 조회용이라 제외."""
import subprocess, sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
for step in ["price_ingredients.py", "build_price.py", "price_seasonality.py"]:
    print(f"\n### {step}")
    if subprocess.run([sys.executable, str(HERE / step)]).returncode != 0:
        sys.exit(f"[중단] {step} 실패")
print("\n[완료] 시세 파이프라인")
