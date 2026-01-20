import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

requests.packages.urllib3.disable_warnings()

def do_request(target, user, password, method="GET"):
    url = target
    try:
        logger.info(f"Probing url : {url}")
        response = requests.request(
            method,
            url,
            auth=(user, password),
            verify=False,  # InsecureSkipVerify: true
            timeout=5 # Good practice to add timeout
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise
    except requests.exceptions.Timeout as e:
        logger.error(f"Request timed out: {e}")
        raise

def get_firmware_version(target, user, password):
    url = f"{target}/api/system/firmware/version"
    return do_request(url, user, password)

def get_firmware_update_availability(target, user, password):
    url = f"{target}/api/system/firmware/update/control/check"
    return do_request(url, user, password, method="POST")

def get_storage_info(target, user, password):
    url = f"{target}/api/system/storages/main/status"
    return do_request(url, user, password)

def get_system_info(target, user, password):
    url = f"{target}/api/system/status"
    return do_request(url, user, password)

def get_recorder_info(target, user, password):
    url = f"{target}/api/recorders/status"
    return do_request(url, user, password)

def get_channel_info(target, user, password):
    url = f"{target}/api/channels/status?publishers=true"
    return do_request(url, user, password)

def get_hdmi_status(target, user, password):
    url = f"{target}/api/sources/status?ids=D2P0.hdmi-a"
    return do_request(url, user, password)

def get_sdi_status(target, user, password):
    url = f"{target}/api/sources/status?ids=D2P0.sdi"
    return do_request(url, user, password)

def get_rca_volume_status(target, user, password):
    url = f"{target}/api/sources/D2P0.analog-a/audiolevels"
    return do_request(url, user, password)

def get_xlr_volume_status(target, user, password):
    url = f"{target}/api/sources/D2P0.analog-b/audiolevels"
    return do_request(url, user, password)

def get_finished_events(target, user, password):
    url = f"{target}/api/schedule/events?status=finished"
    result = do_request(url, user, password)
    finished_recordings = len(result.get("result"))
    logger.info(result.get("result")[-1])
    last_recording = result.get("result")[-1].get("start")

    return {
            "number": finished_recordings,
            "last_recording": last_recording
    }
    

def get_scheduled_events(target, user, password):
    url = f"{target}/api/schedule/events?status=scheduled"
    result = do_request(url, user, password)
    scheduled_recordings = len(result.get("result"))

    return scheduled_recordings;