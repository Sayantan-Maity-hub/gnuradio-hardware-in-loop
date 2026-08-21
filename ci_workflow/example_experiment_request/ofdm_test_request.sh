$body = @{
    hostname = "gw.cortexlab.fr"
    username = "sayantan_maity"
    walltime = "00:30:00"
    reservation_name = "test-reservation"
    experiment = "ofdm_hardware_test"
    pr_id = 21456

    parameter = @{
        message = "Hello CortexLab"
        sample_rate = 195312
        center_frequency = 915000000
        tx_gain = 10
        rx_gain = 20
        tx_amplitude = 0.05
        rx_output_file = "rx_payload.bin"
    }
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri "http://localhost:5678/run-experiment" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body