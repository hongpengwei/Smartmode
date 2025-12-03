import subprocess
import ctypes
from fastmcp import FastMCP

mcp = FastMCP("battery_health_tool")

def is_admin() -> bool:
    """檢查是否以管理員身份執行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def set_battery_health_ps(battery_no=1, function_mask=1, function_status=1) -> subprocess.CompletedProcess:
    """
    Internal helper function that executes a PowerShell script to apply
    Battery Health Control settings.

    Args:
        battery_no (int): Battery index (usually 1)
        function_mask (int): WMI function mask (always 1 for BatteryHealthControl)
        function_status (int): 1 = enable health mode, 0 = disable

    Returns:
        CompletedProcess: The result object returned by subprocess.run()
    """
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
            Write-Output "✅ Battery health control applied successfully."
        }} else {{
            Write-Output "❌ BatteryControl class not found."
        }}
    }} catch {{
        Write-Output "❌ Error: $_"
    }}
    """

    return subprocess.run(
        ["powershell", "-Command", ps_script],
        capture_output=True, text=True
    )

@mcp.tool()
def enable_battery_health() -> dict:
    """
    Enables the system’s Battery Health Control mode.

    This tool calls a Windows WMI interface through PowerShell to activate
    Battery Health Control (function_status = 1). This may require administrator
    privileges to succeed.

    Returns:
        dict: {
            "status": "success" or "error",
            "report": str (present when successful),
            "error_message": str (present when failed),
            "__state_delta__": {"battery_health_enabled": True} (if successful)
        }
    """
    if not is_admin():
        return {
            "status": "error",
            "error_message": "MCP server is not running as administrator. Please restart with admin privileges."
        }
    try:
        result = set_battery_health_ps(function_status=1)
        output = result.stdout.strip() + result.stderr.strip()
        if "✅" in output:
            return {
                "status": "success",
                "report": "Battery Health Control enabled",
                "__state_delta__": {"battery_health_enabled": True}
            }
        else:
            return {
                "status": "error",
                "error_message": output
            }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

@mcp.tool()
def disable_battery_health() -> dict:
    """
    Disables the system’s Battery Health Control mode(Normal mode).

    This tool calls a Windows WMI interface through PowerShell to disable
    Battery Health Control (function_status = 0). This may require administrator
    privileges to succeed.

    Returns:
        dict: {
            "status": "success" or "error",
            "report": str (present when successful),
            "error_message": str (present when failed),
            "__state_delta__": {"battery_health_enabled": False} (if successful)
        }
    """
    if not is_admin():
        return {
            "status": "error",
            "error_message": "MCP server is not running as administrator. Please restart with admin privileges."
        }
    try:
        result = set_battery_health_ps(function_status=0)
        output = result.stdout.strip() + result.stderr.strip()
        if "✅" in output:
            return {
                "status": "success",
                "report": "Battery Health Control disabled",
                "__state_delta__": {"battery_health_enabled": False}
            }
        else:
            return {
                "status": "error",
                "error_message": output
            }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}

if __name__ == "__main__":
    mcp.run(transport="sse", host="0.0.0.0", port=8090)
