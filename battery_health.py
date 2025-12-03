import subprocess
import sys
import ctypes
import os

def is_admin():
    """檢查是否以管理員身份執行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """如果不是管理員，重新以管理員身份執行自己"""
    if not is_admin():
        print("⚠️ Not running as admin, restarting with admin privileges...")
        # 重新啟動 Python 程式
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, ' '.join(f'"{arg}"' for arg in sys.argv), None, 1
        )
        sys.exit()

def set_battery_health(battery_no=1, function_mask=1, function_status=1):
    """呼叫 PowerShell 設定電池健康控制"""
    run_as_admin()  # 確保以管理員執行

    ps_script = f"""
    try {{
        $class = Get-WmiObject -Namespace "root\\wmi" -Class BatteryControl -ErrorAction Stop

        if ($class) {{
            $in = $class.psbase.GetMethodParameters("SetBatteryHealthControl")
            $in.uBatteryNo = [byte]{battery_no}
            $in.uFunctionMask = [byte]{function_mask}
            $in.uFunctionStatus = [byte]{function_status}
            $in.uReservedIn = @([byte]0,[byte]0,[byte]0,[byte]0,[byte]0)

            $class.InvokeMethod("SetBatteryHealthControl", $in, $null)
            Write-Host "✅ Battery health control applied successfully."
        }} else {{
            Write-Host "❌ BatteryControl class not found."
        }}
    }} catch {{
        Write-Host "❌ Error: $_"
    }}
    """

    # 呼叫 PowerShell
    result = subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True
    )

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print("PowerShell stderr:", result.stderr.strip())


# 範例呼叫
if __name__ == "__main__":
    set_battery_health(battery_no=1, function_status=1)
