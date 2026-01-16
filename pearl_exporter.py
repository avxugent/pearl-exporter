import time
import logging
import asyncio
from sanic import Sanic, response
from prometheus_client import CollectorRegistry, Gauge, generate_latest, CONTENT_TYPE_LATEST

import prober

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

NAMESPACE = "pearl"

app = Sanic("PearlExporter")

@app.route("/")
async def index(request):
    return response.html("""<html>
    <head><title>Pearl Exporter</title></head>
    <body>
    <h1>Pearl Exporter</h1>
    <p><a href="probe?target=pearl.local">Probe pearl.local for epiphan pearl metrics</a></p>
    <p><a href="metrics">Metrics</a></p>
    </body></html>""")

@app.route("/metrics")
async def metrics(request):
    return response.text(generate_latest(CollectorRegistry()).decode('utf-8'), content_type=CONTENT_TYPE_LATEST)

@app.route("/probe")
async def probe(request):
    target = request.args.get("target")
    user = request.args.get("user")
    password = request.args.get("password")

    if not target:
        return response.text("Target parameter is missing", status=400)

    logger.info(f"Beginning epiphan pearl probe with username {user} and password {password}")

    # Run the blocking probe logic in a separate thread
    registry = await asyncio.to_thread(run_probe, target, user, password)
    
    return response.raw(generate_latest(registry), content_type=CONTENT_TYPE_LATEST)

def run_probe(target, user, password):
    registry = CollectorRegistry()
    
    # Define Metrics
    probe_success = Gauge('probe_success', 'Displays whether or not the probe was a success', namespace=NAMESPACE, registry=registry)
    probe_duration = Gauge('probe_duration_seconds', 'Returns how long the probe took to complete in seconds', namespace=NAMESPACE, registry=registry)
    
    probe_info = Gauge('system_info', 'Returns system info for the probed device', ['firmware_version', 'uptime'], namespace=NAMESPACE, registry=registry)
    probe_storage = Gauge('storage', 'Returns the current status for the storage devices attached', ['type'], namespace=NAMESPACE, registry=registry)
    probe_cpu = Gauge('cpu_info', 'Returns information regarding the systems cpu load and temperature', ['type'], namespace=NAMESPACE, registry=registry)
    probe_cpu_temp = Gauge('cpu_temp', 'Current temperature for the CPU', namespace=NAMESPACE, registry=registry)
    probe_recorder = Gauge('recorder_info', 'Returns information regarding the configured recorders', ['id'], namespace=NAMESPACE, registry=registry)
    probe_channels = Gauge('channels_info', 'Returns information regarding the configured channels and their publishers', ['id', 'status', 'type'], namespace=NAMESPACE, registry=registry)
    probe_sdi_status = Gauge('sdi_status', 'Returns information regarding the SDI channel, sets the value to the current fps', ['resolution'], namespace=NAMESPACE, registry=registry)
    probe_hdmi_status = Gauge('hdmi_status', 'Returns information regarding the HDMI channel, sets the value to the current fps', ['resolution'], namespace=NAMESPACE, registry=registry)
    probe_rca_status = Gauge('rca_audio_status', 'Returns the current audio levels for the RCA/line in audio input', ['channel', 'type'], namespace=NAMESPACE, registry=registry)
    probe_xlr_status = Gauge('xlr_audio_status', 'Returns the current audio levels for the XLR audio input', ['channel', 'type'], namespace=NAMESPACE, registry=registry)

    start_time = time.time()
    success = True
    
    try:
        logger.info(f"Probing target : {target}")
        
        # Firmware Version
        try:
            firmware_data = prober.get_firmware_version(target, user, password)
            firmware_version = firmware_data.get('result', 'unknown')
        except Exception as e:
            logger.error(f"Error fetching firmware version: {e}")
            success = False
            firmware_version = None

        # System Info
        system_info = None
        try:
            if success:
                system_info_data = prober.get_system_info(target, user, password)
                system_info = system_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching system info: {e}")

        # Storage Info
        storage_info = None
        try:
            if success:
                storage_info_data = prober.get_storage_info(target, user, password)
                storage_info = storage_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching storage info: {e}")

        # Channel Info
        channel_info = None
        try:
            if success:
                channel_info_data = prober.get_channel_info(target, user, password)
                channel_info = channel_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching channel info: {e}")

        # Recorder Info
        recorder_info = None
        try:
            if success: 
                recorder_info_data = prober.get_recorder_info(target, user, password)
                recorder_info = recorder_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching recorder info: {e}")

        # SDI Info
        sdi_info = None
        try:
            if success:
                sdi_info_data = prober.get_sdi_status(target, user, password)
                sdi_info = sdi_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching SDI info: {e}")

        # HDMI Info
        hdmi_info = None
        try:
            if success:
                hdmi_info_data = prober.get_hdmi_status(target, user, password)
                hdmi_info = hdmi_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching HDMI info: {e}")

        # RCA Info
        rca_info = None
        try:
            if success:
                rca_info_data = prober.get_rca_volume_status(target, user, password)
                rca_info = rca_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching RCA info: {e}")

        # XLR Info
        xlr_info = None
        try:
            if success:
                xlr_info_data = prober.get_xlr_volume_status(target, user, password)
                xlr_info = xlr_info_data.get('result')
        except Exception as e:
            logger.error(f"Error fetching XLR info: {e}")


        # Update Metrics
        
        if success and firmware_version and system_info:
            probe_info.labels(firmware_version=firmware_version, uptime=str(system_info.get('uptime', 0))).set(1)

        if system_info:
            probe_cpu.labels(type="load").inc(float(system_info.get('cpu_load', 0)))
            # Bool2int logic
            load_high = 1 if system_info.get('cpu_load_high') else 0
            probe_cpu.labels(type="load_high").inc(load_high)
            probe_cpu_temp.set(float(system_info.get('cputemp', 0)))

        if storage_info:
            probe_storage.labels(type="total").inc(float(storage_info.get('total', 0)))
            probe_storage.labels(type="free").inc(float(storage_info.get('free', 0)))

        if channel_info:
            for channel in channel_info:
                c_id = channel.get('id')
                status = channel.get('status', {})
                state = status.get('state')
                
                probe_channels.labels(id=c_id, status=state, type="nosignal").set(float(status.get('nosignal', 0)))
                probe_channels.labels(id=c_id, status=state, type="bitrate").set(float(status.get('bitrate', 0)))
                probe_channels.labels(id=c_id, status=state, type="duration").set(float(status.get('duration', 0)))

        if recorder_info:
            for recorder in recorder_info:
                r_id = recorder.get('id')
                status = recorder.get('status', {})
                state = status.get('state')
                val = 0 if state == "stopped" else 1
                probe_recorder.labels(id=r_id).set(val)

        if sdi_info and len(sdi_info) > 0:
            # Go code accesses index 0
            sdi_item = sdi_info[0]
            video_status = sdi_item.get('status', {}).get('video', {})
            probe_sdi_status.labels(resolution=video_status.get('resolution', 'unknown')).set(float(video_status.get('actual_fps', 0)))

        if hdmi_info and len(hdmi_info) > 0:
            hdmi_item = hdmi_info[0]
            video_status = hdmi_item.get('status', {}).get('video', {})
            probe_hdmi_status.labels(resolution=video_status.get('resolution', 'unknown')).set(float(video_status.get('actual_fps', 0)))

        if rca_info:
            peaks = rca_info.get('peak', [])
            rms = rca_info.get('rms', [])
            if peaks and len(peaks) >= 2:
                probe_rca_status.labels(channel="left", type="peak").set(float(peaks[0]))
                probe_rca_status.labels(channel="right", type="peak").set(float(peaks[1]))
            if rms and len(rms) >= 2:
                probe_rca_status.labels(channel="left", type="rms").set(float(rms[0]))
                probe_rca_status.labels(channel="right", type="rms").set(float(rms[1]))

        if xlr_info:
            peaks = xlr_info.get('peak', [])
            rms = xlr_info.get('rms', [])
            if peaks and len(peaks) >= 2:
                probe_xlr_status.labels(channel="left", type="peak").set(float(peaks[0]))
                probe_xlr_status.labels(channel="right", type="peak").set(float(peaks[1]))
            if rms and len(rms) >= 2:
                probe_xlr_status.labels(channel="left", type="rms").set(float(rms[0]))
                probe_xlr_status.labels(channel="right", type="rms").set(float(rms[1]))

        probe_success.set(1 if success else 0)

    except Exception as e:
        logger.error(f"Probe failed with unexpected error: {e}")
        probe_success.set(0)
    
    duration = time.time() - start_time
    probe_duration.set(duration)
    logger.info(f"Probe finished, duration: {duration}")
    
    return registry