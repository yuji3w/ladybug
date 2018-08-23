REM this script will click on a series of SPJ files and go through the microsoft ICE dialog with ORDERED planar stitching and autocomplete, and save as 100% quality jpeg
REM place the SPJ files in a folder, and place this script in the parent of that folder with one icon between that folder and the script 
REM credits to Yujie

Set WshShell = CreateObject("WScript.Shell")

WScript.Sleep 1000
WshShell.SendKeys "{UP}"
WScript.Sleep 100
WshShell.SendKeys "{UP}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 100
WshShell.SendKeys "{DOWN}"
WScript.Sleep 100
WshShell.SendKeys "{UP}"
WScript.Sleep 100

REM the above does the initial finding the folder and clicking on the first SPJ file

Dim x
x = 0


Do While x < 434
REM the number of SPJ files you have
WshShell.SendKeys "{ENTER}"
WScript.Sleep 6000


WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 1000

WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 65000


REM the time it takes to do stitching plus safety


WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 2000
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 35000

REM the time it takes to do autocomplete plus safety

WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 2000
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{1}"
WScript.Sleep 100
WshShell.SendKeys "{0}"
WScript.Sleep 100
WshShell.SendKeys "{0}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{TAB}"
WScript.Sleep 100
WshShell.SendKeys "{ENTER}"
WScript.Sleep 5000
WshShell.SendKeys "{ENTER}"
WScript.Sleep 1000
WshShell.SendKeys "%{F4}"
WScript.Sleep 100
WshShell.SendKeys "d"
WScript.Sleep 1000
WshShell.SendKeys "{DOWN}"
WScript.Sleep 100

x = x + 1
Loop