Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
WshShell.CurrentDirectory = appDir

exe = appDir & "\FocusFlow.exe"
If fso.FileExists(exe) Then
    WshShell.Run """" & exe & """", 1, False
    WScript.Quit 0
End If

pythonw = appDir & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = FindOnPath("pythonw.exe")
End If

If pythonw <> "" Then
    WshShell.Run """" & pythonw & """ """ & appDir & "\FocusFlow.pyw""", 1, False
Else
    WshShell.Run "cmd /c """ & appDir & "\FocusFlow.cmd""", 0, False
End If

Function FindOnPath(exeName)
    FindOnPath = ""
    paths = Split(WshShell.ExpandEnvironmentStrings("%PATH%"), ";")
    For Each p In paths
        candidate = fso.BuildPath(p, exeName)
        If fso.FileExists(candidate) Then
            FindOnPath = candidate
            Exit Function
        End If
    Next
End Function
