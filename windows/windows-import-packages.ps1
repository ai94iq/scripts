$confirmation = "0"

while ($confirmation -ne "y" -and $confirmation -ne "n") {
    $confirmation = Read-Host "Import windows packages? (y/n) "
    if ($confirmation -eq "y") {
            winget import -i exported-4-9-21.json
        }
}
