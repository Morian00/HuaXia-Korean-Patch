param(
    [ValidateSet('Auto', 'Decrypt', 'Encrypt')]
    [string]$Mode = 'Auto',

    [switch]$InPlace,
    [switch]$Recurse
)

$ErrorActionPreference = 'Stop'

$Key = [BitConverter]::GetBytes([Int64]7358195901000939096)
$IV = [BitConverter]::GetBytes([Int64](-8635801623133398479))

function New-DesTransform {
    param(
        [ValidateSet('Decrypt', 'Encrypt')]
        [string]$Operation
    )

    $des = [Security.Cryptography.DES]::Create()
    $des.Mode = [Security.Cryptography.CipherMode]::CBC
    $des.Padding = [Security.Cryptography.PaddingMode]::PKCS7
    $des.Key = $Key
    $des.IV = $IV

    if ($Operation -eq 'Decrypt') {
        return @{
            Des = $des
            Transform = $des.CreateDecryptor()
        }
    }

    return @{
        Des = $des
        Transform = $des.CreateEncryptor()
    }
}

function Invoke-Des {
    param(
        [byte[]]$Bytes,
        [ValidateSet('Decrypt', 'Encrypt')]
        [string]$Operation
    )

    $ctx = New-DesTransform -Operation $Operation
    try {
        return $ctx.Transform.TransformFinalBlock($Bytes, 0, $Bytes.Length)
    } finally {
        $ctx.Transform.Dispose()
        $ctx.Des.Dispose()
    }
}

function Test-PlainXmlBytes {
    param([byte[]]$Bytes)

    if ($Bytes.Length -lt 5) {
        return $false
    }

    $offset = 0
    if ($Bytes.Length -ge 3 -and $Bytes[0] -eq 0xEF -and $Bytes[1] -eq 0xBB -and $Bytes[2] -eq 0xBF) {
        $offset = 3
    }

    while ($offset -lt $Bytes.Length -and ($Bytes[$offset] -eq 0x20 -or $Bytes[$offset] -eq 0x09 -or $Bytes[$offset] -eq 0x0D -or $Bytes[$offset] -eq 0x0A)) {
        $offset++
    }

    if ($offset + 5 -gt $Bytes.Length) {
        return $false
    }

    $headLength = [Math]::Min(32, $Bytes.Length - $offset)
    $head = [Text.Encoding]::UTF8.GetString($Bytes, $offset, $headLength)
    return $head.StartsWith('<?xml') -or $head.StartsWith('<objects')
}

function Resolve-Operation {
    param(
        [byte[]]$Bytes,
        [string]$RequestedMode
    )

    if ($RequestedMode -ne 'Auto') {
        return $RequestedMode
    }

    if (Test-PlainXmlBytes -Bytes $Bytes) {
        return 'Encrypt'
    }

    try {
        $decrypted = Invoke-Des -Bytes $Bytes -Operation Decrypt
        if (Test-PlainXmlBytes -Bytes $decrypted) {
            return 'Decrypt'
        }
    } catch {
    }

    return $null
}

$root = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($root)) {
    $root = (Get-Location).Path
}

if ($Recurse) {
    $files = Get-ChildItem -LiteralPath $root -Filter '*.xml' -File -Recurse
} else {
    $files = Get-ChildItem -LiteralPath $root -Filter '*.xml' -File
}

$files = @($files | Where-Object {
    $_.FullName -notmatch '\\__(decrypted|encrypted)(\\|$)'
})

if ($files.Count -eq 0) {
    Write-Host "No .xml files found in $root"
    exit 0
}

$ok = 0
$skipped = 0
$failed = 0
$operations = @{}

foreach ($file in $files) {
    try {
        $bytes = [IO.File]::ReadAllBytes($file.FullName)
        $operation = Resolve-Operation -Bytes $bytes -RequestedMode $Mode

        if ($null -eq $operation) {
            Write-Warning "Skipped: $($file.Name) - cannot detect XML encryption state."
            $skipped++
            continue
        }

        $outBytes = Invoke-Des -Bytes $bytes -Operation $operation

        if ($InPlace) {
            $targetPath = $file.FullName
        } else {
            $folderName = if ($operation -eq 'Decrypt') { '__decrypted' } else { '__encrypted' }
            $targetRoot = Join-Path $root $folderName

            if ($Recurse) {
                $relative = [IO.Path]::GetRelativePath($root, $file.DirectoryName)
                $targetDir = Join-Path $targetRoot $relative
            } else {
                $targetDir = $targetRoot
            }

            if (-not (Test-Path -LiteralPath $targetDir)) {
                New-Item -ItemType Directory -Path $targetDir | Out-Null
            }

            $targetPath = Join-Path $targetDir $file.Name
        }

        [IO.File]::WriteAllBytes($targetPath, $outBytes)
        $ok++

        if (-not $operations.ContainsKey($operation)) {
            $operations[$operation] = 0
        }
        $operations[$operation]++
    } catch {
        Write-Warning "Failed: $($file.Name) - $($_.Exception.Message)"
        $failed++
    }
}

Write-Host "Root: $root"
Write-Host "Mode: $Mode"
Write-Host "InPlace: $InPlace"
Write-Host "Processed: $ok"
Write-Host "Skipped: $skipped"
Write-Host "Failed: $failed"

foreach ($keyName in $operations.Keys | Sort-Object) {
    Write-Host "$keyName`: $($operations[$keyName])"
}
