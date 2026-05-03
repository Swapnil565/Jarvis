$SERVER1 = "http://127.0.0.1:5001"
$SERVER2 = "http://127.0.0.1:5002"
$SERVER3 = "http://127.0.0.1:5003"

Write-Host "========================================"
Write-Host "1. Checking initial state on all servers"
Write-Host "========================================"
try { Invoke-RestMethod -Uri "$SERVER1/check/T101" } catch { Write-Host "Server 1 down" }
try { Invoke-RestMethod -Uri "$SERVER2/check/T101" } catch { Write-Host "Server 2 down" }
try { Invoke-RestMethod -Uri "$SERVER3/check/T101" } catch { Write-Host "Server 3 down" }

Write-Host "`n========================================"
Write-Host "2. Booking 2 seats on Train T101"
Write-Host "========================================"
$body = @{
    train_id = "T101"
    seats = 2
    passenger = "Rahul Kumar"
} | ConvertTo-Json
try {
    $response = Invoke-RestMethod -Uri "$SERVER1/book" -Method Post -Body $body -ContentType "application/json"
    Write-Host "Booking Response:"
    $response | Format-List
} catch {
    Write-Host "Booking failed: $_"
}

Start-Sleep -Seconds 2

Write-Host "`n========================================"
Write-Host "3. Checking after booking (all servers)"
Write-Host "========================================"
try { Invoke-RestMethod -Uri "$SERVER1/check/T101" } catch { Write-Host "Server 1 down" }
try { Invoke-RestMethod -Uri "$SERVER2/check/T101" } catch { Write-Host "Server 2 down" }
try { Invoke-RestMethod -Uri "$SERVER3/check/T101" } catch { Write-Host "Server 3 down" }

Write-Host "`n========================================"
Write-Host "4. View all bookings"
Write-Host "========================================"
try { 
    $bookings = Invoke-RestMethod -Uri "$SERVER1/bookings"
    $bookings.bookings | Format-Table
} catch { Write-Host "Failed to get bookings" }
