# Pearl Exporter

A Prometheus exporter for Epiphan Pearl devices, written in Python.

This exporter queries the Epiphan Pearl API for various status information (firmware, system, storage, recorders, channels, SDI, HDMI, audio) and exposes them as Prometheus metrics.

## Usage

### Docker

#### Build

To build the Docker image, run:

```bash
docker build -t pearl-exporter .
```

#### Run

To run the Docker container:

```bash
docker run -p 9115:9115 pearl-exporter
```

### Manual

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Run the exporter:
    ```bash
    python3 pearl_exporter.py
    ```

## Metrics

The exporter exposes metrics on the `/probe` endpoint. You need to provide the `target`, `user`, and `password` as query parameters.

Example:

```bash
curl "http://localhost:9115/probe?target=http://pearl.local&user=admin&password=password"
```

### Exposed Metrics

-   `pearl_probe_success`: Displays whether or not the probe was a success.
-   `pearl_probe_duration_seconds`: Returns how long the probe took to complete in seconds.
-   `pearl_system_info`: Returns system info for the probed device (labels: `firmware_version`, `uptime`).
-   `pearl_storage`: Returns the current status for the storage devices attached (labels: `type`).
-   `pearl_cpu_info`: Returns information regarding the system's CPU load (labels: `type`).
-   `pearl_cpu_temp`: Current temperature for the CPU.
-   `pearl_recorder_info`: Returns information regarding the configured recorders (labels: `id`).
-   `pearl_channels_info`: Returns information regarding the configured channels (labels: `id`, `status`, `type`).
-   `pearl_sdi_status`: Returns information regarding the SDI channel (labels: `resolution`).
-   `pearl_hdmi_status`: Returns information regarding the HDMI channel (labels: `resolution`).
-   `pearl_rca_audio_status`: Returns the current audio levels for the RCA/line-in audio input (labels: `channel`, `type`).
-   `pearl_xlr_audio_status`: Returns the current audio levels for the XLR audio input (labels: `channel`, `type`).
