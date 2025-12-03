import wmi
import re
import sys
import subprocess
from typing import List, Dict, Any
from collections import defaultdict


# ============================================================
# 🧩 輔助函式
# ============================================================

def extract_luid(name: str) -> str:
    """從名稱中提取 LUID。"""
    for pattern in [r"luid_([0-9A-Za-z_x]+)(?=_phys_0)", r"luid_([0-9A-Za-z_x]+)"]:
        match = re.search(pattern, name)
        if match:
            return match.group(1)
    return "unknown"


def luid_to_int(luid_str: str) -> int:
    """將 LUID 轉換為整數 (方便排序)。"""
    try:
        return int(luid_str.split('_')[-1], 16)
    except Exception:
        return 0


def run_powershell(cmd: str) -> str:
    """執行 PowerShell 指令並回傳輸出。"""
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        print(f"⚠️ PowerShell 指令執行失敗: {e}", file=sys.stderr)
        return ""


# ============================================================
# 🧠 主核心：整合 Utilization 與 Shared Memory
# ============================================================

def _get_luid_data() -> List[Dict[str, Any]]:
    """取得 GPU LUID 對應的利用率與共享記憶體使用量。"""
    try:
        w = wmi.WMI(namespace=r'root\CIMV2')
        gpu_engines = w.query(
            "SELECT Name, UtilizationPercentage "
            "FROM Win32_PerfFormattedData_GPUPerformanceCounters_GPUEngine"
        )
    except wmi.x_access_denied:
        print("❌ 錯誤: 拒絕存取 WMI，請以管理員權限執行。", file=sys.stderr)
        return []
    except Exception as e:
        print(f"❌ 錯誤: 無法連線或查詢 WMI: {e}", file=sys.stderr)
        return []

    if not gpu_engines:
        return []

    # 1️⃣ 匯總各 LUID 的利用率
    utilization_sum = defaultdict(float)
    for gpu in gpu_engines:
        luid = extract_luid(getattr(gpu, "Name", "")).lower()  # ✅ 統一轉小寫
        try:
            utilization_sum[luid] += float(gpu.UtilizationPercentage)
        except (TypeError, ValueError):
            continue

    # 2️⃣ 取得 Shared Memory (MB)
    memory_sum = defaultdict(float)
    ps_out = run_powershell(
        'Get-Counter "\\GPU Adapter Memory(*)\\Shared Usage" | '
        'Select-Object -ExpandProperty CounterSamples | '
        'Select InstanceName, CookedValue | '
        'ForEach-Object { "$($_.InstanceName):$($_.CookedValue)" }'
    )

    if ps_out:
        for line in ps_out.splitlines():
            if ":" not in line:
                continue
            name, value = line.split(":", 1)
            luid = extract_luid(name).lower()  # ✅ 統一轉小寫
            try:
                memory_sum[luid] += float(value) / (1024 * 1024)
            except ValueError:
                continue

    # 3️⃣ 合併結果
    all_luids = set(utilization_sum.keys()) | set(memory_sum.keys())
    if not all_luids:
        return []

    results = []
    sorted_luids = sorted(all_luids, key=luid_to_int)
    num_devices = len(sorted_luids)

    for idx, luid in enumerate(sorted_luids):
        if idx == 0:
            label = "iGPU - 內建顯卡"
        elif num_devices > 1 and idx == num_devices - 1:
            label = "NPU - 神經處理單元"
        else:
            label = "dGPU - 獨立顯卡/其他元件"

        results.append({
            "luid": luid,
            "utilization": utilization_sum.get(luid, 0.0),
            "memory_usage_MB": memory_sum.get(luid, 0.0),
            "type": label
        })

    return results


def get_gpu_utilization_fast() -> List[Dict[str, Any]]:
    """
    使用 PowerShell Get-Counter 直接取得 GPU 使用率 (更快)
    回傳格式: [{"luid": "...", "utilization": 85.5, "type": "iGPU"}, ...]
    """
    ps_cmd = (
        'Get-Counter "\\GPU Engine(*)\\Utilization Percentage" -ErrorAction SilentlyContinue | '
        'Select-Object -ExpandProperty CounterSamples | '
        'ForEach-Object { '
        '  if ($_.InstanceName -match "luid_0x[0-9a-fA-F]+_0x[0-9a-fA-F]+") { '
        '    $_.InstanceName + "|" + [int]$_.CookedValue '
        '  } '
        '}'
    )
    
    ps_out = run_powershell(ps_cmd)
    
    if not ps_out:
        return []
    
    # 1️⃣ 按 LUID 分組並求最大值
    luid_utilization = defaultdict(float)
    for line in ps_out.splitlines():
        if not line or "|" not in line:
            continue
        instance_name, utilization_str = line.rsplit("|", 1)
        luid = extract_luid(instance_name).lower()
        try:
            util_val = float(utilization_str)
            luid_utilization[luid] = max(luid_utilization[luid], util_val)
        except ValueError:
            continue
    
    if not luid_utilization:
        return []
    
    # 2️⃣ 排序並標記設備類型
    results = []
    sorted_luids = sorted(luid_utilization.keys(), key=luid_to_int)
    num_devices = len(sorted_luids)
    
    for idx, luid in enumerate(sorted_luids):
        if idx == 0:
            label = "iGPU - 內建顯卡"
        elif num_devices > 1 and idx == num_devices - 1:
            label = "NPU - 神經處理單元"
        else:
            label = "dGPU - 獨立顯卡/其他元件"
        
        results.append({
            "luid": luid,
            "utilization": luid_utilization[luid],
            "type": label
        })
    
    return results


def get_gpu_engine_utilization_by_luid() -> List[Dict[str, Any]]:
    """回傳 LUID、使用率與記憶體使用量資訊 (完整版 - 較慢但更詳細)。"""
    return _get_luid_data()


# ============================================================
# 🧾 主程式
# ============================================================

if __name__ == "__main__":
    import time
    while True: 
    # 快速版本
        start = time.time()
        data_fast = get_gpu_utilization_fast()
        elapsed_fast = time.time() - start
        
        print("--- iGPU & NPU 使用率 ---")
        if not data_fast:
            print("❌ 沒有可用的 GPU 或資料。")
        else:
            # 只顯示 iGPU 和 NPU (不顯示 dGPU)
            for entry in data_fast:
                if "iGPU" in entry['type'] or "NPU" in entry['type']:
                    device_name = "iGPU" if "iGPU" in entry['type'] else "NPU"
                    print(f"🔹 {device_name:6s} | 利用率: {entry['utilization']:6.2f}%")
        
        print(f"\n⏱️ 查詢耗時: {elapsed_fast:.3f} 秒")
