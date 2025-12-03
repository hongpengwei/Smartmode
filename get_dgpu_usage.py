import subprocess
from typing import Optional

def get_dgpu_utilization_nvidia_smi() -> float:
    """
    使用 `nvidia-smi` 取得 NVIDIA dGPU 的 GPU 核心使用率 (%)
    
    Returns:
        float: GPU 使用率百分比 (0.0 ~ 100.0)，若失敗則返回 0.0。
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,nounits,noheader"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,  # 命令失敗會引發 CalledProcessError
            timeout=5     # 增加超時保護
        )

        output = result.stdout.strip()
        if not output:
            # 無輸出代表系統無 GPU 或無法存取
            return 0.0

        # 支援多 GPU 時僅取第一張卡
        first_line = output.splitlines()[0].strip()
        return float(first_line) if first_line else 0.0

    except FileNotFoundError:
        print("❌ 錯誤: 找不到 'nvidia-smi' 命令，請確認 NVIDIA 驅動已安裝。")
    except subprocess.CalledProcessError as e:
        print(f"❌ 錯誤: 執行 nvidia-smi 失敗。訊息: {e.stderr.strip() or '未知錯誤'}")
    except ValueError:
        print("⚠️ 無法解析 nvidia-smi 的輸出內容。")
    except subprocess.TimeoutExpired:
        print("⚠️ nvidia-smi 查詢逾時。")
    except Exception as e:
        print(f"⚠️ 發生未預期的錯誤: {e}")

    return 0.0
def run_cmd(cmd):
    """執行命令列指令並回傳輸出，失敗則回傳空字串"""
    try:
        return subprocess.check_output(
                    cmd,
                    shell=True,
                    encoding="utf-8",
                    errors="ignore",
                    timeout=5,
                    )
    except Exception as err:
        return str(err)
def get_dgpu_vram():
    """
    取得 NVIDIA dGPU VRAM 使用量與剩餘容量 (MB)
    回傳: (used_vram_mb, free_vram_mb, total_vram_mb)
    """
    try:
        cmd = [
            'nvidia-smi',
            '--query-gpu=memory.used,memory.free,memory.total',
            '--format=csv,noheader,nounits'
        ]
        out = run_cmd(cmd)
        lines = out.splitlines()
        if lines:
            used, free, total = map(float, lines[0].strip().split(','))
            return free/1024.0
    except Exception as e:
        return 0.0

# 範例調用 (Example Call)
if __name__ == "__main__":
    dgpu_util = get_dgpu_utilization_nvidia_smi()
    dgpu_memory = get_dgpu_vram()
    used_vram, free_vram, total_vram = dgpu_memory
    print(f"💾 NVIDIA dGPU VRAM 使用量: {used_vram:.2f} MB / {total_vram:.2f} MB (剩餘: {free_vram:.2f} MB)")
    print(f"🚀 NVIDIA dGPU 核心使用率 (GPU-Util): {dgpu_util:.2f}%")
