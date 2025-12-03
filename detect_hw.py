import subprocess
import platform
from typing import Dict, Any


# ============================================================
# 🧩 通用指令執行
# ============================================================
def run_cmd(cmd: str) -> str:
    """執行命令並回傳輸出（失敗回傳空字串）。"""
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            encoding="utf-8",
            errors="ignore",
            timeout=10,
        )
    except Exception:
        return ""


# ============================================================
# 🧠 Windows GPU/NPU 檢測
# ============================================================
import subprocess
import platform
import winreg
from typing import Dict, Any


# ============================================================
# 更快速的命令執行
# ============================================================
def run_cmd_fast(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            encoding="utf-8",
            errors="ignore"
        )
    except Exception:
        return ""


# ============================================================
# 🖥️ Windows GPU 偵測（wmic：0.01~0.03 秒）
# ============================================================
import platform
import wmi

import winreg

# ------------------------------------------------------------
# 執行指令（只給 NPU 用）
# ------------------------------------------------------------
def run_cmd(cmd: str) -> str:
    try:
        return subprocess.check_output(
            cmd,
            shell=True,
            encoding="utf-8",
            errors="ignore",
            timeout=5
        )
    except Exception:
        return ""

# ------------------------------------------------------------
# Windows GPU (iGPU / dGPU) - 快速 Registry 方法
# ------------------------------------------------------------
def _detect_windows_gpu(result: Dict[str, Any]) -> None:
    gpu_key_path = r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, gpu_key_path)
        for i in range(0, 256):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                name, _ = winreg.QueryValueEx(subkey, "DriverDesc")
                name_l = name.lower()
                result["detail"]["gpus"].append(name)

                # dGPU 偵測
                if any(x in name_l for x in ["nvidia", "geforce", "rtx", "rx "]):
                    result["dGPU"] = True

                # iGPU 偵測
                if any(x in name_l for x in ["intel", "uhd", "iris", "xe"]) or \
                   ("radeon graphics" in name_l and "rx" not in name_l):
                    result["iGPU"] = True
            except OSError:
                break
    except:
        pass

# ------------------------------------------------------------
# Windows NPU - PowerShell 方法（可靠）
# ------------------------------------------------------------
def _detect_windows_npu(result: Dict[str, Any]) -> None:
    cmd = (
        'powershell -NoProfile -NonInteractive -Command '
        '"Get-CimInstance Win32_PnPEntity | '
        'Where-Object { $_.PNPClass -eq \'ComputeAccelerator\' } | '
        'Select-Object -ExpandProperty Caption"'
    )
    out = run_cmd(cmd)
    if out.strip():
        npu_devices = [line.strip() for line in out.splitlines() if line.strip()]
        if npu_devices:
            result["NPU"] = True
            result["detail"]["npu"] = npu_devices[0]

# ------------------------------------------------------------
# 主偵測函式
# ------------------------------------------------------------
def detect_compute_devices() -> Dict[str, Any]:
    result = {"dGPU": False, "iGPU": False, "NPU": False, "detail": {"gpus": [], "npu": None}}
    os_name = platform.system()

    if os_name == "Windows":
        _detect_windows_gpu(result)   # 快速 GPU
        _detect_windows_npu(result)   # 可靠 NPU

    elif os_name == "Linux":
        out = subprocess.getoutput("lspci -nnk | grep -i vga -A3")
        for line in out.splitlines():
            gpu_l = line.lower()
            if "vga" in gpu_l or "3d" in gpu_l:
                gpu = line.split(":")[-1].strip()
                result["detail"]["gpus"].append(gpu)
                if "nvidia" in gpu_l or "amd" in gpu_l:
                    result["dGPU"] = True
                if "intel" in gpu_l:
                    result["iGPU"] = True
        if subprocess.getoutput("ls /dev/dri/ | grep 'accel'").strip():
            result["NPU"] = True
            result["detail"]["npu"] = "Generic Compute Accelerator (Linux)"

    elif os_name == "Darwin":
        result.update({"iGPU": True, "NPU": True})
        result["detail"]["gpus"].append("Apple M-series Integrated GPU")
        result["detail"]["npu"] = "Apple Neural Engine (ANE)"

    return result




import time
# ============================================================
# 🧾 主程式執行
# ============================================================
if __name__ == "__main__":
    start = time.time()
    devices = detect_compute_devices()
    # luid_utilization_data = get_gpu_engine_utilization_by_luid()
    elapsed = time.time() - start
    print(f"⏱️ 偵測完成，耗時 {elapsed:.2f} 秒")
    print("=" * 30)
    print("=== 運算設備檢測結果 ===")
    print("=" * 30)
    print("\n[摘要 Summary]:")
    print(f"🖥️ 獨立顯示卡 (dGPU): {'✅ 偵測到' if devices['dGPU'] else '❌ 未偵測到'}")
    print(f"🎮 整合顯示卡 (iGPU): {'✅ 偵測到' if devices['iGPU'] else '❌ 未偵測到'}")
    print(f"⚙️ 神經處理單元 (NPU): {'✅ 偵測到' if devices['NPU'] else '❌ 未偵測到'}")
