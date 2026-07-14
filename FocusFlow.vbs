' Silent Windows launcher — no console window. Use this as the shortcut target.
Option Explicit

Dim fso, shell, appDir, pythonw, cmd

Set fso = CreateObject("Scripting.FileSystemObject")
Set shell = CreateObject("WScript.Shell")
appDir = fso.GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory = appDir

pythonw = appDir & "\.venv\Scripts\pythonw.exe"
If Not fso.FileExists(pythonw) Then
    pythonw = FindOnPath("pythonw.exe")
End If

If pythonw <> "" Then
    shell.Run """" & pythonw & """ """ & appDir & "\FocusFlow.pyw""", 0, False
Else
    ' Hidden cmd fallback (still no visible console when launched via wscript)
    cmd = "cmd /c """ & appDir & "\FocusFlow.cmd"""
    shell.Run cmd, 0, False
End If

Function FindOnPath(exeName)
    Dim paths, p, candidate
    FindOnPath = ""
    paths = Split(shell.ExpandEnvironmentStrings("%PATH%"), ";")
    For Each p In paths
        candidate = fso.BuildPath(p, exeName)
        If fso.FileExists(candidate) Then
            FindOnPath = candidate
            Exit Function
        End If
    Next
End Function
