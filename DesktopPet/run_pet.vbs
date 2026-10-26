' ================================================================
' run_pet.vbs - Silent / Windowless Launcher for Desktop Pet
' ================================================================
' Launches Desktop Pet in background with ZERO terminal/PowerShell window.
' Detached via Windows Shell (Explorer) so closing any terminal never kills the pet.
' ================================================================
Option Explicit

Dim fso, wshShell, shellApp, projectDir, mainPy, pythonwExe, argPython

Set fso = CreateObject("Scripting.FileSystemObject")
Set wshShell = CreateObject("WScript.Shell")
Set shellApp = CreateObject("Shell.Application")

projectDir = fso.GetParentFolderName(WScript.ScriptFullName)
mainPy = fso.BuildPath(projectDir, "main.py")

' 1. Check if pythonw was passed as a command-line argument
If WScript.Arguments.Count > 0 Then
    argPython = WScript.Arguments(0)
    If fso.FileExists(argPython) Then
        pythonwExe = argPython
    End If
End If

' 2. Check cached python path if available (.python_path file)
If pythonwExe = "" Then
    Dim cacheFile
    cacheFile = fso.BuildPath(projectDir, ".python_path")
    If fso.FileExists(cacheFile) Then
        On Error Resume Next
        Dim ts, cachedLine
        Set ts = fso.OpenTextFile(cacheFile, 1)
        If Not ts.AtEndOfStream Then
            cachedLine = Trim(ts.ReadLine)
            If fso.FileExists(cachedLine) Then
                pythonwExe = cachedLine
            End If
        End If
        ts.Close
        On Error GoTo 0
    End If
End If

' 3. Search known Python / Virtualenv locations
If pythonwExe = "" Then
    Dim userProfile, localAppData, appData, candidates, candidatePath
    userProfile = wshShell.ExpandEnvironmentStrings("%USERPROFILE%")
    localAppData = wshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
    appData = wshShell.ExpandEnvironmentStrings("%APPDATA%")

    candidates = Array( _
        fso.BuildPath(projectDir, ".venv\Scripts\pythonw.exe"), _
        fso.BuildPath(projectDir, "venv\Scripts\pythonw.exe"), _
        localAppData & "\hermes\hermes-agent\venv\Scripts\pythonw.exe", _
        localAppData & "\Programs\Python\Python312\pythonw.exe", _
        localAppData & "\Programs\Python\Python311\pythonw.exe", _
        localAppData & "\Programs\Python\Python310\pythonw.exe", _
        userProfile & "\miniconda3\pythonw.exe", _
        userProfile & "\anaconda3\pythonw.exe", _
        "C:\Program Files\Python312\pythonw.exe", _
        "C:\Program Files\Python311\pythonw.exe", _
        "C:\Program Files\Python310\pythonw.exe" _
    )

    For Each candidatePath In candidates
        If fso.FileExists(candidatePath) Then
            pythonwExe = candidatePath
            Exit For
        End If
    Next
End If

' 4. Fallback to pythonw in system PATH
If pythonwExe = "" Then
    pythonwExe = "pythonw.exe"
End If

' 5. Cache the resolved pythonw path for fast instant launch next time
If pythonwExe <> "pythonw.exe" Then
    On Error Resume Next
    Dim tsOut
    Set tsOut = fso.CreateTextFile(fso.BuildPath(projectDir, ".python_path"), True)
    tsOut.WriteLine pythonwExe
    tsOut.Close
    On Error GoTo 0
End If

shellApp.ShellExecute pythonwExe, "main.py", projectDir, "open", 1





