# Anti-Sleep heartbeat for EPKolar Bug Hunt
# Started by bughunt-eternal-baumgmt.bat
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;
public class P {
    [DllImport("kernel32.dll")]
    public static extern uint SetThreadExecutionState(uint esFlags);
}
"@
$ES_CONTINUOUS = 0x80000000
$ES_SYSTEM_REQUIRED = 0x00000001
$ES_DISPLAY_REQUIRED = 0x00000040
$shell = New-Object -ComObject WScript.Shell
while ($true) {
    [P]::SetThreadExecutionState($ES_CONTINUOUS -bor $ES_SYSTEM_REQUIRED -bor $ES_DISPLAY_REQUIRED)
    $shell.SendKeys("{SCROLLLOCK 2}")
    Start-Sleep -Seconds 60
}
