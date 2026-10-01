"""Read-only Windows prerequisite checks; never download/install runtimes."""
import os
import platform
import sys

RUNTIME_ID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
WEBVIEW_URL = "https://developer.microsoft.com/en-us/microsoft-edge/webview2/"
DOTNET_URL = "https://dotnet.microsoft.com/en-us/download/dotnet-framework"


def registry_value(path, name):
    if os.name != "nt":
        return None
    import winreg
    for hive in (winreg.HKEY_CURRENT_USER,winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY,winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive,path,0,winreg.KEY_READ | view) as key:
                    value,_ = winreg.QueryValueEx(key,name)
                    if value not in (None,"","0","0.0.0.0"):
                        return value
            except OSError:
                continue
    return None


def check_windows():
    result = {"platform":platform.platform(),"architecture":platform.machine(),
              "python_bits":64 if sys.maxsize > 2**32 else 32,
              "webview2_version":None,"dotnet_framework_release":None,"problems":[],
              "setup_links":{"webview2":WEBVIEW_URL,"dotnet_framework":DOTNET_URL}}
    if os.name != "nt":
        result.update(ready=False,problems=["The packaged desktop application requires Windows x64"])
        return result
    if sys.getwindowsversion().major < 10:
        result["problems"].append("Windows 10/11 x64 is required")
    if result["python_bits"] != 64 or result["architecture"].lower() not in ("amd64","x86_64"):
        result["problems"].append("This build supports x64, not a native x86/ARM build")
    result["webview2_version"] = registry_value(f"SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\{RUNTIME_ID}","pv")
    result["dotnet_framework_release"] = registry_value(r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full","Release")
    if not result["webview2_version"]:
        result["problems"].append("Microsoft Edge WebView2 Evergreen Runtime was not found")
    release = result["dotnet_framework_release"]
    if not isinstance(release,int) or release < 394802:
        result["problems"].append(".NET Framework 4.6.2 or newer was not found")
    result["ready"] = not result["problems"]
    return result
