# Updates one key in the state file
# Args: <state_file> <key> <value>
param([string]$file, [string]$key, [string]$val)
if (-not (Test-Path $file)) { exit 1 }
$keyEsc = [regex]::Escape($key)
$content = Get-Content $file
$found = $false
$out = foreach ($ln in $content) {
    if ($ln -match "^$keyEsc=") {
        $found = $true
        "$key=$val"
    } else {
        $ln
    }
}
if (-not $found) { $out += "$key=$val" }
$out | Set-Content -Encoding ASCII $file
