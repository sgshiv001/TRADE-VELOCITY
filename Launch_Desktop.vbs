Option Explicit
Dim shell, files, root, executable, command
Set shell = CreateObject("WScript.Shell")
Set files = CreateObject("Scripting.FileSystemObject")
root = files.GetParentFolderName(WScript.ScriptFullName)
executable = files.BuildPath(root, "TradeVelocity\TradeVelocity.exe")
If Not files.FileExists(executable) Then
    executable = files.BuildPath(root, "dist\TradeVelocity\TradeVelocity.exe")
End If
If files.FileExists(executable) Then
    command = Chr(34) & executable & Chr(34)
Else
    executable = files.BuildPath(root, ".venv\Scripts\pythonw.exe")
    If Not files.FileExists(executable) Then
        MsgBox "Set up the Python environment first, or build the desktop app. See README.md.", vbExclamation, "TradeVelocity"
        WScript.Quit 1
    End If
    command = Chr(34) & executable & Chr(34) & " " & Chr(34) & files.BuildPath(root, "app.py") & Chr(34) & " --desktop --skip-build"
End If
shell.CurrentDirectory = root
shell.Run command, 1, False
