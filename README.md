# netbox-prometheus-sd
Prometheus service discovery for Netbox. Use tags within netbox to create prometheus service discovery files.

## Configuration
Use the netbox-prometheus-sd.yml file to configure the behavior of the netbox-prometheus-sd generator. You may use the netbox-prometheus-sd.service file to automatically start the generator as a service in systemd.

### netbox-prometheus-sd.yml
```
netbox_url: https://netbox.dev.level66.network/
netbox_token:
scan_interval: 300

groups:
  - netbox_tag: prometheus_exporter_node
    prometheus_file: /etc/prometheus/targets/prometheus_exporter_node.json
    prometheus_port: 9100
```

### prometheus.yml
```
  - job_name: 'node'
    honor_labels: true
    file_sd_configs:
      - files: ['/etc/prometheus/targets/prometheus_exporter_node.json']
```

### netbox-prometheus-sd.service
```
[Unit]
Description=Netbox Prometheus Service Discovery generator
After=network.target

[Service]
Type=simple
ExecStart=/opt/netbox-prometheus-sd/netbox-prometheus-sd.py /etc/prometheus/netbox-prometheus-sd.yml

[Install]
WantedBy=multi-user.target
```
