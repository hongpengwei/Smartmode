import time
import requests
import numpy as np
import subprocess
import sys
PORT = 8000  # 你用單一 OVMS port

models = [
    ("Qwen3-4B-int4-ov", "Qwen3-4B-int4-cw-ov"),  # (NPU_model, iGPU_model)
    ("Qwen3-8B-int4-ov", "Qwen3-8B-int4-cw-ov")
]

prompt = "Hello, how are you today?"
tokens_to_generate = 1000

# --------------------------------------------------
# 呼叫 usage_load.py 來啟動指定的 iGPU 使用率
# --------------------------------------------------
def start_load_process(load_value):
    print(f"\n⚙️ 啟動 iGPU load = {load_value:.2f}")

    # 開新 subprocess 讓它自己跑，不阻塞主程式
    p = subprocess.Popen(
    [sys.executable, "usage_load.py", "--load", str(load_value)],
    )


    # 給 3 秒鐘讓負載穩定
    time.sleep(3)
    return p


# --------------------------------------------------
# 停止 usage_load.py
# --------------------------------------------------
def stop_load_process(proc):
    print("🛑 停止負載程式")
    proc.terminate()
    time.sleep(1)


def benchmark_ovms(model_name, prompt, max_tokens):
    url = f"http://localhost:{PORT}/v3/chat/completions"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        "max_new_tokens": max_tokens,
        "temperature": 0
    }

    start = time.time()
    response = requests.post(url, json=payload)
    end = time.time()

    if response.status_code != 200:
        print(f"❌ Error: {response.text}")
        return None, 0

    data = response.json()
    actual_tokens = data.get("usage", {}).get("completion_tokens", None)

    if actual_tokens is None:
        print("⚠️ OVMS 沒回傳 usage")
        return None, 0

    total_time = end - start
    tps = actual_tokens / total_time
    return total_time, tps


def run_benchmark(model_npu, model_igpu, prompt, tokens):
    print("\n============================================")
    print(f"🧪 Benchmark: {model_npu} vs {model_igpu}")
    print("============================================\n")

    # NPU
    print("⚡ Testing NPU...")
    t_npu, tps_npu = benchmark_ovms(model_npu, prompt, tokens)

    # iGPU
    print("⚡ Testing iGPU...")
    t_igpu, tps_igpu = benchmark_ovms(model_igpu, prompt, tokens)

    print("\n=== Result ===")
    print(f"NPU  ({model_npu}):  {tps_npu:.2f} tok/s")
    print(f"iGPU ({model_igpu}): {tps_igpu:.2f} tok/s")
    print("-------------------------------")

    if tps_igpu > tps_npu:
        print("🏆 iGPU is faster")
    else:
        print("🏆 NPU is faster")

    return tps_npu, tps_igpu


def auto_find_threshold(model_npu, model_igpu):
    print("\n============================================")
    print(f"🔍 Auto threshold test for {model_igpu}")
    print("============================================")

    test_loads = np.linspace(0.3, 1.0, 8)

    for load in test_loads:
        # print(f"\n⚙️ 請手動執行：python burn_load.py --load {load:.1f}")
        # input("👉 按 Enter 繼續跑 benchmark...")
        procs = start_load_process(load)
        tps_npu, tps_igpu = run_benchmark(model_npu, model_igpu, prompt, tokens_to_generate)
        stop_load_process(procs)
        if tps_igpu < tps_npu:
            print(f"\n📌 建議切換點：CPU/iGPU load > {load*100:.0f}% → 換 NPU")
            return load
            break


if __name__ == "__main__":
    for model_igpu, model_npu in models:
        start_time = time.time()
        usage = auto_find_threshold(model_npu, model_igpu)
        print(f"⚙️ 建議 iGPU 使用率切換點: {usage*100:.0f}%")
        end_time = time.time()
        elapsed = end_time - start_time
        print(f"⏱️ {model_npu} , {model_igpu}測試完成，耗時 {elapsed:.2f} 秒\n")
