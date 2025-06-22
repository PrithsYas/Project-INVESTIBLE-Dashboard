Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\PROJECT'"   '✅ update to your exact folder
WshShell.Run "run.bat", 0, False
WScript.Sleep 1000
Set objShell = CreateObject("WScript.Shell")
objShell.Run "http://127.0.0.1:5001"
