$body = @{
    hostname = "gw.cortexlab.fr"
    username = "sayantan_maity"
    walltime = "00:30:00"
    reservation_name = "test-reservation"

    experiment = "basic_hardware_test"
    pr_id = 21456

    parameter = @{
    
        duration = 5
        sample_rate = 1000000
        gain = 20
        capture_samples = 5000000
        center_frequency = 1000000
        tone_frequency = 100000
    }
} | ConvertTo-Json -Depth 10

$response = Invoke-RestMethod `
    -Uri "http://localhost:5678/run-experiment" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body

$response | ConvertTo-Json -Depth 20