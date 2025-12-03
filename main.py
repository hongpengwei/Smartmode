import time
from detect_hw import detect_compute_devices
from compute_info import get_gpu_utilization_fast, luid_to_int
from get_dgpu_usage import get_dgpu_utilization_nvidia_smi, get_dgpu_vram
from benchmark_final import auto_find_threshold

def get_igpu_npu_usage():
    """使用快速版本獲取 iGPU 和 NPU 的使用率與記憶體 (MB)

    回傳: (igpu_util, npu_util, igpu_mem_MB, npu_mem_MB)
    """
    igpu_util = npu_util = 0.0
    igpu_mem = npu_mem = 0.0

    try:
        luid_utilization_data = get_gpu_utilization_fast()
        if not luid_utilization_data:
            print("⚠️ 無法取得 GPU/NPU 使用率資料。")
            return igpu_util, npu_util, igpu_mem, npu_mem

        # 按 LUID 排序
        luid_utilization_data.sort(key=lambda d: luid_to_int(d["luid"]))

        # 最小 LUID → iGPU
        igpu_util = luid_utilization_data[0]["utilization"]
        igpu_mem = luid_utilization_data[0].get("memory_usage_MB", 0.0)

        # 最大 LUID → NPU（如果有多個設備）
        if len(luid_utilization_data) > 1:
            npu_util = luid_utilization_data[-1]["utilization"]
            npu_mem = luid_utilization_data[-1].get("memory_usage_MB", 0.0)

    except Exception as e:
        print(f"⚠️ 無法取得使用率資訊: {e}")

    return igpu_util, npu_util, igpu_mem, npu_mem
def pick_best_dgpu_model(dgpu_mem, model_list, model_vram):
    """
    根據 dGPU 可用 VRAM 選擇最佳模型

    參數：
        dgpu_mem (float): dGPU 可用 VRAM (GB)
        model_list (dict): 可用模型列表，例如 {"dGPU": ["model1", "model2"]}
        model_vram (dict): 每個模型所需 VRAM，例如 {"model1": 6, "model2": 12}

    回傳：
        str 或 None：選到的最佳模型名稱，若無可用模型回傳 None
    """

    candidates = model_list.get("dGPU", [])

    # 過濾 VRAM 足夠的模型
    available = [
        model for model in candidates
        if model_vram.get(model, 0) <= dgpu_mem
    ]

    if not available:
        return None  # VRAM 不夠，不能用 dGPU

    # 選 VRAM 需求最大的模型
    return sorted(
        available,
        key=lambda m: model_vram[m],
        reverse=True
    )[0]

def select_best_device_and_model(devices, igpu_util, npu_util, dgpu_util, dgpu_mem, usage_threshold, model_list, model_vram):
    """
    選擇最佳運算裝置並回傳對應的模型

    函式用途：
        根據系統中 dGPU、iGPU、NPU 的存在狀態與使用率，以及 dGPU 可用 VRAM，
        自動選擇最適合執行 AI 模型的運算裝置，並回傳對應的模型名稱。

    參數：
        devices (dict): 偵測到的硬體設備
            例如 {"dGPU": True, "iGPU": True, "NPU": True}
        igpu_util (float): iGPU 當前使用率 (0~100)
        npu_util (float): NPU 當前使用率 (0~100)
        dgpu_util (float): dGPU 當前使用率 (0~100)
        dgpu_mem (float): dGPU 可用 VRAM (GB)
        usage_threshold (float): iGPU / NPU 最大可接受使用率門檻 (0~1，例如 0.5 表示 50%)

    回傳：
        tuple (str, str): (選擇的裝置名稱, 對應模型名稱)
            裝置名稱可能為 "dGPU", "iGPU", "NPU"
            模型名稱根據裝置和可用 VRAM 選擇

    流程說明：
        1. 顯示目前偵測到的硬體與使用率。
        2. 優先使用 dGPU：
            - 若 dGPU 使用率 ≤ 50%，呼叫 pick_best_dgpu_model() 選出 VRAM 足夠且需求最大的模型。
            - 若 VRAM 不足或使用率過高，跳過 dGPU。
        3. 判斷 iGPU：
            - 若 iGPU 存在且使用率 ≤ usage_threshold，使用 iGPU 對應模型。
        4. 判斷 NPU：
            - 若 NPU 存在且使用率 ≤ usage_threshold，使用 NPU 對應模型。
        5. fallback：
            - 若所有裝置都超載或無可用模型，預設使用 iGPU 及其模型。
    """
    
    print("=== 偵測到的硬體 ===")
    # 1. dGPU 優先判斷
    if devices.get("dGPU", False):
        print(f"➡️ dGPU 使用率: {dgpu_util:.2f}% VRAM: {dgpu_mem:.2f}GB")

        if dgpu_util <= 50.0:
            model = pick_best_dgpu_model(dgpu_mem, model_list, model_vram)

            if model:
                print(f"✅ dGPU VRAM 足夠，選擇模型: {model}")
                return "dGPU", model
            else:
                print("⚠️ dGPU VRAM 不足，跳過 dGPU")
        else:
            print("⚠️ dGPU 使用率過高，跳過 dGPU")
    # 2. iGPU
    if devices.get("iGPU", False) and igpu_util <= usage_threshold * 100:
        model = MODEL_LIST["iGPU"][0]
        print(f"➡️ iGPU 使用率 OK，使用 {model}")
        return "iGPU", model
    # 3. NPU
    if devices.get("NPU", False) and npu_util <= usage_threshold * 100:
        model = MODEL_LIST["NPU"][0]
        print(f"➡️ NPU 使用率 OK，使用 {model}")
        return "NPU", model
    # 4. fallback
    print("⚠️ 全部裝置都繁忙，fallback 至 iGPU")
    return "iGPU", MODEL_LIST["iGPU"][0]




if __name__ == "__main__":
    print("=== 智能裝置選擇系統啟動 ===")
    
    # ⬅️ 初始化：只偵測一次硬體
    devices = detect_compute_devices()
    # if devices['iGPU'] is True and devices['NPU'] is True:
        # usage = auto_find_threshold("Qwen3-8B-int4-cw-ov", "Qwen3-8B-int4-ov")
    MODEL_LIST = {
    "dGPU": ["gpt-oss:20b", "qwen3:14b", "qwen3:8b"],
    "iGPU": ["OpenVINO/Qwen3-8B-int4-ov"],
    "NPU":  ["OpenVINO/Qwen3-8B-int4-cw-ov"]
    }
    MODEL_VRAM = {
    "gpt-oss:20b": 15,
    "qwen3:14b": 12,
    "qwen3:8b": 6,
    "OpenVINO/Qwen3-8B-int4-ov": 0,
    "OpenVINO/Qwen3-8B-int4-cw-ov": 0
    }
    while True:
        # 獲取各裝置的使用率
        # 預設為 0.0（若沒有 dGPU 或無法取得則維持 0）
        dgpu_util = 0.0
        dgpu_util_vram = 0.0
        usage = 0.0
        if devices.get("dGPU", False):
            try:
                dgpu_util = get_dgpu_utilization_nvidia_smi()
                dgpu_util_vram = get_dgpu_vram()
                print(f"NVIDIA dGPU VRAM 使用量: {dgpu_util_vram:.2f} GB ")
            except Exception as e:
                print(f"⚠️ 無法取得 dGPU 使用率: {e}")
                dgpu_util = 0.0
        print("=== 取得各裝置使用率 ===")
        # igpu_util, npu_util, igpu_mem, npu_mem = get_igpu_npu_usage()
        igpu_util = 51
        npu_util = 25
        igpu_mem = 0.0
        dgpu_util = 51
        # print(f"🎮 iGPU 使用率: {igpu_util:.2f}%, 記憶體使用: {igpu_mem:.2f} MB")
        best, model = select_best_device_and_model(devices, igpu_util, npu_util, dgpu_util, dgpu_util_vram ,0.5, MODEL_LIST, MODEL_VRAM)
        print(f"建議使用裝置: {best}, 模型: {model}")
        time.sleep(10)


# import time
# from detect_hw import detect_compute_devices
# from compute_info import get_gpu_utilization_fast, luid_to_int
# from get_dgpu_usage import get_dgpu_utilization_nvidia_smi, get_dgpu_vram
# from benchmark_final import auto_find_threshold

# def get_igpu_npu_usage():
#     """快速獲取 iGPU 和 NPU 的使用率與記憶體 (MB)"""
#     igpu_util = npu_util = 0.0
#     igpu_mem = npu_mem = 0.0
#     try:
#         luid_utilization_data = get_gpu_utilization_fast()
#         if not luid_utilization_data:
#             print("⚠️ 無法取得 GPU/NPU 使用率資料。")
#             return igpu_util, npu_util, igpu_mem, npu_mem

#         luid_utilization_data.sort(key=lambda d: luid_to_int(d["luid"]))

#         # 最小 LUID → iGPU
#         igpu_util = luid_utilization_data[0]["utilization"]
#         igpu_mem = luid_utilization_data[0].get("memory_usage_MB", 0.0)

#         # 最大 LUID → NPU
#         if len(luid_utilization_data) > 1:
#             npu_util = luid_utilization_data[-1]["utilization"]
#             npu_mem = luid_utilization_data[-1].get("memory_usage_MB", 0.0)

#     except Exception as e:
#         print(f"⚠️ 無法取得使用率資訊: {e}")

#     return igpu_util, npu_util, igpu_mem, npu_mem


# def select_best_device_and_model(devices, igpu_util=0.0, npu_util=0.0, dgpu_util=0.0, dgpu_mem=0.0, usage=0.0):
#     """選擇最佳運算裝置與對應模型"""
#     device_model_mapping = {
#         "dGPU": "gpt-oss:20b",
#         "iGPU": "OpenVINO/Qwen3-8B-int4-ov",
#         "NPU": "OpenVINO/Qwen3-8B-int4-cw-ov"
#     }

#     selected_device = "iGPU"

#     # Step 1 - dGPU
#     if devices.get("dGPU", False):
#         if dgpu_util <= 50.0 or dgpu_mem <= 6.0:
#             selected_device = "dGPU"
#             if 6.0 <= dgpu_mem <= 11.5:
#                 device_model_mapping[selected_device] = "qwen3:8b"
#             elif 11.5 < dgpu_mem <= 13.5:
#                 device_model_mapping[selected_device] = "qwen3:14b"
#             else:
#                 device_model_mapping[selected_device] = "gpt-oss:20b"
#             return selected_device, device_model_mapping[selected_device]

#     # Step 2 & 3 - iGPU / NPU
#     if devices.get("iGPU", False) and igpu_util <= usage * 100:
#         selected_device = "iGPU"
#         return selected_device, device_model_mapping[selected_device]

#     if devices.get("NPU", False) and npu_util <= usage * 100:
#         selected_device = "NPU"
#         return selected_device, device_model_mapping[selected_device]

#     # 無低負載裝置 → 預設 iGPU
#     return selected_device, device_model_mapping[selected_device]


# def select_optimal_device_loop(loop_interval=1):
#     """
#     整合流程：偵測硬體 → 取得使用率 → 選擇最佳裝置 → 循環輸出建議
    
#     參數：
#         loop_interval (int): 每次迴圈間隔秒數
#     """
#     print("=== 智能裝置選擇系統啟動 ===")
    
#     # 偵測硬體
#     devices = detect_compute_devices()
    
#     # 自動閾值設定（iGPU/NPU 用）
#     usage = 0.0
#     if devices.get('iGPU', False) and devices.get('NPU', False):
#         usage = auto_find_threshold("Qwen3-8B-int4-cw-ov", "Qwen3-8B-int4-ov")

#     while True:
#         # 預設 dGPU 使用率/顯存
#         dgpu_util = dgpu_util_vram = 0.0

#         if devices.get("dGPU", False):
#             try:
#                 dgpu_util = get_dgpu_utilization_nvidia_smi()
#                 dgpu_util_vram = get_dgpu_vram()
#             except Exception as e:
#                 print(f"⚠️ 無法取得 dGPU 使用率: {e}")

#         # 取得 iGPU / NPU 使用率
#         igpu_util, npu_util, igpu_mem, npu_mem = get_igpu_npu_usage()

#         # 選擇最佳裝置與模型
#         best_device, model = select_best_device_and_model(
#             devices, igpu_util, npu_util, dgpu_util, dgpu_util_vram, usage
#         )

#         # 輸出資訊
#         print("=== 取得各裝置使用率 ===")
#         print(f"💾 dGPU 使用率: {dgpu_util:.2f}%, VRAM: {dgpu_util_vram:.2f} GB")
#         print(f"🎮 iGPU 使用率: {igpu_util:.2f}%, 記憶體使用: {igpu_mem:.2f} MB")
#         print(f"⚙️ NPU 使用率: {npu_util:.2f}%, 記憶體使用: {npu_mem:.2f} MB")
#         print(f"✅ 建議使用裝置: {best_device}, 模型: {model}\n")

#         time.sleep(loop_interval)


# # 範例：啟動流程
# if __name__ == "__main__":
#     select_optimal_device_loop(loop_interval=1)
