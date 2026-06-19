# 🛰️ Satellite Telemetry Processing Pipeline

A production-style microservices architecture for processing satellite telemetry data, built as part of a DevOps systems engineering assignment.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Installation](#installation)
- [Operation](#operation)
- [Service Discovery](#service-discovery)
- [Network Security](#network-security)
- [Logging & Observability](#logging--observability)
- [Request Tracing](#request-tracing)
- [Troubleshooting](#troubleshooting)
- [API Reference](#api-reference)

---

## 🌍 Project Overview

This system simulates a **ground station telemetry processing pipeline** for satellite operations. When a satellite passes over the ground station, it downlinks telemetry frames containing sensor data (battery voltage, solar panel temperature, gyroscope readings, signal strength). The system validates, parses, and analyzes this data for anomalies, then reports back to the ground station.

**Real-world analogy:** This mirrors actual aerospace ground segment architectures where telemetry from satellites is processed through multiple stages before mission controllers receive actionable status updates.

### Services

| Service | Role | Port | Accessibility |
|---------|------|------|---------------|
| **Service A** | Ground Station API | 3001 | Public (via Nginx) |
| **Service B** | Telemetry Parser | 3002 | Internal Only |
| **Service C** | Anomaly Detector | 3003 | Internal Only |
| **Nginx** | Reverse Proxy | 80 | Public Entry Point |

---

## 🏗️ Architecture

```
Internet User
      ↓
   Nginx (Port 80) — Public Gateway
      ↓
Service A: Ground Station API (Port 3001)
      ↓
Service B: Telemetry Parser (Port 3002)
      ↓
Service C: Anomaly Detector (Port 3003)
      ↓
Service A: Ground Station API (Port 3001) — Callback
      ↓
   User receives: "Telemetry processed, status: nominal"
```

### Request Flow

1. **Client** sends telemetry frame to `POST /telemetry` via Nginx (port 80)
2. **Service A** (Ground Station API) receives frame, generates trace ID, forwards to Service B
3. **Service B** (Telemetry Parser) validates checksum, extracts sensor values, returns parsed data
4. **Service A** forwards parsed data to Service C
5. **Service C** (Anomaly Detector) checks thresholds, detects anomalies, **callbacks** to Service A
6. **Service A** returns final mission status to client

---

## 🚀 Installation

### Prerequisites

- Ubuntu 20.04+ VM
- sudo access
- Internet connection (for package installation)

### One-Command Deployment

```bash
# Clone the repository
git clone https://github.com/yordanoshagos/devops-satellite-telemetry.git
cd devops-satellite-telemetry

# Deploy everything
sudo bash install.sh
```

The `install.sh` script will:
1. Install system dependencies (Python, Nginx, ufw)
2. Create dedicated service users
3. Install Python virtual environments and dependencies
4. Configure `/etc/hosts` for service discovery
5. Install and enable systemd services
6. Configure Nginx reverse proxy
7. Set up firewall rules
8. Start all services in dependency order

### Manual Installation

If you prefer manual setup, follow these steps:

```bash
# 1. Install dependencies
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx curl ufw

# 2. Create service users
sudo useradd -r -s /usr/sbin/nologin groundstation
sudo useradd -r -s /usr/sbin/nologin telemetry
sudo useradd -r -s /usr/sbin/nologin anomaly

# 3. Deploy project to /opt
sudo cp -r . /opt/devops-satellite-telemetry
sudo chown -R root:root /opt/devops-satellite-telemetry

# 4. Install Python dependencies
for service in service-a service-b service-c; do
    cd /opt/devops-satellite-telemetry/$service
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    deactivate
done

# 5. Configure service discovery
sudo bash -c 'echo "127.0.0.1 telemetry-parser anomaly-detector ground-station-api" >> /etc/hosts'

# 6. Install systemd services
sudo cp /opt/devops-satellite-telemetry/systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# 7. Configure Nginx
sudo cp /opt/devops-satellite-telemetry/nginx/satellite-telemetry /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/satellite-telemetry /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 8. Configure firewall
sudo bash /opt/devops-satellite-telemetry/scripts/configure-firewall.sh

# 9. Start services
sudo systemctl start telemetry-parser
sudo systemctl start anomaly-detector
sudo systemctl start ground-station-api

# 10. Enable auto-start on boot
sudo systemctl enable telemetry-parser anomaly-detector ground-station-api
```

---

## ⚙️ Operation

### Start Services

```bash
# Start all services (in dependency order)
sudo systemctl start telemetry-parser
sudo systemctl start anomaly-detector
sudo systemctl start ground-station-api

# Or start all at once
sudo systemctl start telemetry-parser anomaly-detector ground-station-api
```

### Stop Services

```bash
# Stop all services
sudo systemctl stop ground-station-api
sudo systemctl stop anomaly-detector
sudo systemctl stop telemetry-parser
```

### Restart Services

```bash
# Restart a specific service
sudo systemctl restart ground-station-api

# Restart all
sudo systemctl restart telemetry-parser anomaly-detector ground-station-api
```

### Check Status

```bash
# Check all services
sudo systemctl status ground-station-api telemetry-parser anomaly-detector

# Check individual service
sudo systemctl status ground-station-api
```

### Verify Health

```bash
# Via Nginx (public)
curl http://localhost/health

# Direct access (localhost only)
curl http://localhost:3001/health  # Service A
curl http://localhost:3002/health  # Service B
curl http://localhost:3003/health  # Service C
```

### Run End-to-End Test

```bash
sudo bash /opt/devops-satellite-telemetry/scripts/test-end-to-end.sh
```

---

## 🔍 Service Discovery

### How Services Discover Each Other

Services communicate using **hostnames** rather than hardcoded IP addresses:

| From | To | URL |
|------|-----|-----|
| Service A | Service B | `http://telemetry-parser:3002/parse` |
| Service A | Service C | `http://anomaly-detector:3003/analyze` |
| Service C | Service A (callback) | `http://ground-station-api:3001/callback` |

### Name Resolution

Hostnames are resolved via `/etc/hosts`:
```
127.0.0.1 telemetry-parser
127.0.0.1 anomaly-detector
127.0.0.1 ground-station-api
```

**Why `/etc/hosts`?**
- Simple and reliable for a single-node deployment
- No external DNS dependency
- Easy to troubleshoot
- In production, this would be replaced by internal DNS (Consul, CoreDNS) or Docker networking

### Component Performing Resolution

The **Linux kernel's resolver** handles name resolution, checking `/etc/hosts` before querying DNS servers (as configured in `/etc/nsswitch.conf`).

### Troubleshooting Discovery Failures

```bash
# 1. Verify /etc/hosts entries
cat /etc/hosts | grep -E "telemetry-parser|anomaly-detector|ground-station-api"

# 2. Test name resolution
ping -c 1 telemetry-parser
ping -c 1 anomaly-detector

# 3. Test service connectivity
curl http://telemetry-parser:3002/health
curl http://anomaly-detector:3003/health

# 4. Check if services are listening
sudo ss -tlnp | grep -E "3001|3002|3003"

# 5. Check systemd status
sudo systemctl status telemetry-parser anomaly-detector
```

---

## 🛡️ Network Security

### Why Services Are Protected

- **Service B (Telemetry Parser)** and **Service C (Anomaly Detector)** contain internal business logic
- Direct public access could allow:
  - Injection of fake telemetry data
  - Bypassing validation in Service A
  - Denial of service on critical internal components

### Protection Mechanism

**Three layers of defense:**

1. **Nginx Routing**: Only Service A is exposed through Nginx on port 80
2. **Firewall (ufw/iptables)**: Ports 3002 and 3003 are blocked from external access
3. **Service Binding**: Internal services bind to `0.0.0.0` but firewall prevents external reach

### Verification

```bash
# From localhost (should work)
curl http://localhost:3002/health
curl http://localhost:3003/health

# From external machine (should fail/timeout)
curl --connect-timeout 2 http://<VM_PUBLIC_IP>:3002/health
curl --connect-timeout 2 http://<VM_PUBLIC_IP>:3003/health

# Check firewall rules
sudo ufw status verbose
sudo iptables -L -n --line-numbers
```

### Troubleshooting Connectivity Issues

```bash
# Check if service is running
sudo systemctl status telemetry-parser

# Check if port is listening
sudo ss -tlnp | grep 3002

# Test from localhost
curl http://localhost:3002/health

# Check firewall logs
sudo dmesg | grep -i "iptables"
sudo tail -f /var/log/ufw.log
```

---

## 📝 Logging & Observability

### Log Location

All services log to **journald** (systemd's logging system):

```bash
# View logs for all services
sudo journalctl -u ground-station-api -u telemetry-parser -u anomaly-detector -f

# View logs for specific service
sudo journalctl -u ground-station-api -f

# View logs since last boot
sudo journalctl -u ground-station-api --since today

# View logs in JSON format
sudo journalctl -u ground-station-api -o json
```

### Log Schema

Every log entry is structured JSON:

```json
{
  "timestamp": "2026-06-18T09:30:00.123Z",
  "service": "ground-station-api",
  "service_version": "v1.0.0",
  "level": "INFO",
  "event": "telemetry_received",
  "processing_request_id": "req-abc123",
  "satellite_id": "SAT-001",
  "mission_id": "MISSION-ALPHA-7",
  "endpoint": "/telemetry",
  "method": "POST",
  "client_ip": "192.168.1.100",
  "outcome": "success",
  "duration_ms": 45,
  "message": "Telemetry frame received from SAT-001"
}
```

### Log Fields

| Field | Description | Example |
|-------|-------------|---------|
| `timestamp` | ISO 8601 with milliseconds | `2026-06-18T09:30:00.123Z` |
| `service` | Service name | `ground-station-api` |
| `level` | Log severity | `INFO`, `WARN`, `ERROR` |
| `event` | What happened | `telemetry_received`, `anomaly_detected` |
| `processing_request_id` | **Trace ID** across all services | `req-abc123` |
| `satellite_id` | Business context | `SAT-001` |
| `outcome` | Result | `success`, `failure`, `nominal`, `warning` |
| `duration_ms` | Operation duration | `45` |

---

## 🔎 Request Tracing

### How Tracing Works

1. **Service A** generates a `processing_request_id` (e.g., `req-abc123`) when receiving telemetry
2. This ID is passed in the **HTTP header `X-Request-ID`** to all downstream services
3. Every service includes this ID in its structured logs
4. You can grep for this ID across all service logs to trace the complete journey

### Trace a Request

```bash
# Use the helper script
sudo bash /opt/devops-satellite-telemetry/scripts/trace-request.sh req-abc123

# Or manually with journalctl
sudo journalctl -u ground-station-api -u telemetry-parser -u anomaly-detector \
    --since "30 minutes ago" | grep "req-abc123"
```

### Example Trace Output

```
[Ground Station]   {"event": "telemetry_received", "processing_request_id": "req-abc123", ...}
[Ground Station]   {"event": "forward_to_parser", "processing_request_id": "req-abc123", ...}
[Telemetry Parser] {"event": "parse_request", "processing_request_id": "req-abc123", ...}
[Telemetry Parser] {"event": "telemetry_parsed", "processing_request_id": "req-abc123", ...}
[Ground Station]   {"event": "forward_to_detector", "processing_request_id": "req-abc123", ...}
[Anomaly Detector] {"event": "analyze_request", "processing_request_id": "req-abc123", ...}
[Anomaly Detector] {"event": "anomaly_detection", "processing_request_id": "req-abc123", ...}
[Anomaly Detector] {"event": "callback_sent", "processing_request_id": "req-abc123", ...}
[Ground Station]   {"event": "callback_received", "processing_request_id": "req-abc123", ...}
```

---

## 🔧 Troubleshooting

### Service Startup Failures

```bash
# Check service status
sudo systemctl status ground-station-api

# View startup logs
sudo journalctl -u ground-station-api --since "5 minutes ago"

# Check for Python errors
sudo journalctl -u ground-station-api | grep -i "error"

# Verify Python dependencies
ls /opt/devops-satellite-telemetry/service-a/venv/lib/python*/site-packages/ | grep flask
```

### Service Dependency Failures

```bash
# Check if dependencies are running
sudo systemctl status telemetry-parser anomaly-detector

# Check dependency health endpoints
curl http://localhost:3002/health
curl http://localhost:3003/health

# View dependency logs
sudo journalctl -u telemetry-parser --since "5 minutes ago"

# Restart dependencies and then Service A
sudo systemctl restart telemetry-parser anomaly-detector
sleep 3
sudo systemctl restart ground-station-api
```

### Reverse Proxy Failures

```bash
# Test Nginx configuration
sudo nginx -t

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx directly
curl http://localhost/nginx-health

# Check if Nginx is forwarding to Service A
sudo tail -f /var/log/nginx/access.log
```

### Service Discovery Failures

```bash
# Verify /etc/hosts
cat /etc/hosts

# Test DNS resolution
nslookup telemetry-parser
ping -c 1 telemetry-parser

# Check if services are listening on correct ports
sudo ss -tlnp | grep -E "3001|3002|3003"
```

### Name Resolution Failures

```bash
# Check nsswitch.conf
cat /etc/nsswitch.conf | grep hosts

# Test resolution order
getent hosts telemetry-parser

# Check /etc/hosts permissions
ls -la /etc/hosts
```

### Network Access Failures

```bash
# Check firewall status
sudo ufw status verbose
sudo iptables -L -n

# Test connectivity between services
curl http://telemetry-parser:3002/health
curl http://anomaly-detector:3003/health

# Check if ports are listening
sudo netstat -tlnp | grep python
```

### Missing Logs

```bash
# Check journald is running
sudo systemctl status systemd-journald

# Check disk space for logs
df -h /var/log

# View logs with different output formats
sudo journalctl -u ground-station-api --output=short
sudo journalctl -u ground-station-api --output=json

# Check log permissions
sudo journalctl --disk-usage
```

### Invalid Routing Behavior

```bash
# Check Nginx configuration
sudo cat /etc/nginx/sites-enabled/satellite-telemetry

# Test Nginx routes
curl -v http://localhost/health
curl -v http://localhost/telemetry-parser  # Should return 403

# Check if Service A is responding
curl http://localhost:3001/health
```

### Inter-Service Communication Failures

```bash
# Check if services can reach each other
sudo systemctl status ground-station-api
sudo journalctl -u ground-station-api | grep "Failed to reach"

# Test manual communication
curl -X POST http://telemetry-parser:3002/parse \
  -H "Content-Type: application/json" \
  -d '{"processing_request_id": "test-123", "satellite_id": "SAT-TEST", "telemetry_frame": {}}'

# Check network connectivity
ping -c 3 telemetry-parser
ping -c 3 anomaly-detector
```

---

## 📡 API Reference

### Service A: Ground Station API (Port 3001)

#### `GET /health`
Returns operational status and dependency health.

#### `POST /telemetry`
Accepts raw telemetry frame and initiates processing pipeline.

**Request Body:**
```json
{
  "satellite_id": "SAT-001",
  "mission_id": "MISSION-ALPHA-7",
  "timestamp": "2026-06-18T09:30:00Z",
  "telemetry_frame": {
    "battery_voltage": 14.2,
    "solar_panel_temp": 45.3,
    "gyro_x": 0.01,
    "gyro_y": -0.02,
    "gyro_z": 0.00,
    "signal_strength_dbm": -85,
    "downlink_frequency": 437.5
  }
}
```

#### `POST /callback`
Receives anomaly analysis results from Service C.

#### `GET /status/<processing_request_id>`
Returns the processing status of a specific request.

### Service B: Telemetry Parser (Port 3002)

#### `GET /health`
Returns parser operational status.

#### `POST /parse`
Validates and parses raw telemetry frames.

### Service C: Anomaly Detector (Port 3003)

#### `GET /health`
Returns detector operational status.

#### `POST /analyze`
Analyzes parsed telemetry against mission thresholds and callbacks to Service A.

---

## 🧪 Testing

### Generate Mock Telemetry

```bash
# Nominal (all values safe)
bash /opt/devops-satellite-telemetry/scripts/generate-telemetry.sh nominal

# Warning (some anomalies)
bash /opt/devops-satellite-telemetry/scripts/generate-telemetry.sh warning

# Critical (severe anomalies)
bash /opt/devops-satellite-telemetry/scripts/generate-telemetry.sh critical
```

### Manual curl Tests

```bash
# Health check via Nginx
curl http://localhost/health

# Send telemetry
curl -X POST http://localhost/telemetry \
  -H "Content-Type: application/json" \
  -d '{
    "satellite_id": "SAT-001",
    "mission_id": "MISSION-ALPHA-7",
    "timestamp": "2026-06-18T09:30:00Z",
    "telemetry_frame": {
      "battery_voltage": 14.2,
      "solar_panel_temp": 45.3,
      "gyro_x": 0.01,
      "gyro_y": -0.02,
      "gyro_z": 0.00,
      "signal_strength_dbm": -85,
      "downlink_frequency": 437.5
    }
  }'
```

---

## 👥 Authors

- **Your Team Name** - DevOps Systems Engineering Assignment

## 📄 License

This project is for educational purposes.
