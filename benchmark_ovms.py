import subprocess
import time
import psutil
import requests
import os

PORT_NPU = "8001"
PORT_IGPU = "8000"
# WAIT_MODEL_READY = 50   # 等模型 load 完時間

models = [
    ("OpenVINO/Qwen3-4B-int4-ov", "OpenVINO/Qwen3-4B-int4-ov"),
]

prompt = "Hello, how are you today?"
tokens_to_generate = 10000  # 生成 token 數

def benchmark_ovms(url, model_name, prompt, max_tokens):
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_new_tokens": max_tokens,
        "temperature": 0
    }

    start = time.time()
    response = requests.post(url, json=payload)
    end = time.time()

    if response.status_code != 200:
        print(f"❌ Model request error from {url}: {response.text}")
        return None, 0

    data = response.json()

    # 取得實際生成 token 數
    actual_tokens = data.get("usage", {}).get("completion_tokens", None)

    if actual_tokens is None:
        print("⚠️ WARNING: OVMS 沒回傳 usage.completion_tokens")
        return None, 0

    total_time = end - start
    tps = actual_tokens / total_time

    return total_time, tps


# def kill_ovms():
#     # 刪掉 OVMS process
#     os.system("taskkill /IM ovms.exe /F >nul 2>&1")

# def start_model(model_name, device, port):
#     kill_ovms()
#     time.sleep(3)

#     print(f"\n🚀 Starting model {model_name} on {device} (port {port})")
#     subprocess.Popen([BAT_PATH, model_name, device, port], shell=True)
#     print(f"⏳ Waiting {WAIT_MODEL_READY}s for model to load...\n")
#     time.sleep(WAIT_MODEL_READY)

def run_all_tests():
    results = []

    for model_npu, model_igpu in models:
        print("\n====================================================")
        print(f"🔥 Testing model family: {model_npu.split('/')[-1].split('-int4')[0]}")
        print("====================================================\n")

        # 🧠 Test NPU
        # start_model(model_npu, "NPU", PORT_NPU)
        time_npu, tps_npu = benchmark_ovms(f"http://localhost:{PORT_NPU}/v3/chat/completions",
                                           model_npu, prompt, tokens_to_generate)

        # 🧠 Test iGPU
        # start_model(model_igpu, "GPU", PORT_IGPU)
        time_igpu, tps_igpu = benchmark_ovms(f"http://localhost:{PORT_IGPU}/v3/chat/completions",
                                             model_igpu, prompt, tokens_to_generate)

        results.append((model_npu, model_igpu, tps_npu, tps_igpu))

        # 印結果
        print("✅ Results:")
        print(f"NPU [{model_npu}]: {tps_npu:.2f} tokens/s")
        print(f"iGPU[{model_igpu}]: {tps_igpu:.2f} tokens/s")
        print("----------------------------------------------------")
        print("✅ Faster:", "NPU" if tps_npu > tps_igpu else "iGPU")

    print("\n================= FINAL SUMMARY =================")
    for m_npu, m_igpu, tps_npu, tps_igpu in results:
        name = m_npu.split('/')[-1].split('-int4')[0]
        print(f"{name:28s} | NPU {tps_npu:8.2f} tok/s | iGPU {tps_igpu:8.2f} tok/s | 🔥 { 'NPU' if tps_npu > tps_igpu else 'iGPU'} wins")

    # kill_ovms()

if __name__ == "__main__":
    run_all_tests()

