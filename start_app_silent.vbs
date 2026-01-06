Set shell=CreateObject("WScript.Shell")
root=CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
shell.CurrentDirectory=root
shell.Run "cmd /c streamlit run Home.py --server.headless true",0,False
WScript.Sleep 2500
shell.Run "http://localhost:8501/",1,False
