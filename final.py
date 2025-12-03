# controller.py
import subprocess
import json
import numpy as np
import time
import signal
import sys

NPU_MODEL  = "Qwen3-4B-int4-ov"
IGPU_MODEL = "Qwen3-4B-int4-ov"

LOADS = np.linspace(0.3, 1.0, 10)


def run_benchmark():
    p = subprocess.run(
        ["python", "benchmark_final.py", NPU_MODEL, IGPU_MODEL],
        capture_output=True, text=True
    )
    data = json.loads(p.stdout)
    return data["npu_tps"], data["igpu_tps"]


def run_load(load):
    return subprocess.Popen(
        ["python", "burn_load.py", "--load", str(load)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


if __name__ == "__main__":
    print("===== Auto Threshold Search =====")

    for load in LOADS:
        print(f"\n⚙️ 測試 iGPU load = {load*100:.0f}%")

        # 啟動 burn_load.py
        proc = run_load(load)

        # 等 3 秒穩定負載
        time.sleep(3)

        # benchmark
        npu_tps, igpu_tps = run_benchmark()

        print(f"iGPU={igpu_tps:.2f} tok/s | NPU={npu_tps:.2f} tok/s")

        # 關閉 burn_load.py
        proc.kill()
        proc.wait()

        # 判斷 threshold
        if igpu_tps < npu_tps:
            print(f"\n📌 Threshold = {load*100:.0f}% 以上 → 換用 NPU")
            sys.exit(0)

    print("\n⚠️ iGPU 沒有比 NPU 慢")
