$confirmation = "0"

while ($confirmation -ne "y" -and $confirmation -ne "n") {
    $confirmation = Read-Host "Install windows stuff? (y/n) "
    if ($confirmation -eq "y") {
        foreach ($line in Get-Content $PSSCriptRoot\win-packages.txt) {
            if ($line.contains("#")) {
                continue
            }
            winget install --force --id $line -e        
        }
    }
}
