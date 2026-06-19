import os
import logging

import hvac

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# OpenBao is API-compatible with Vault, so we accept both BAO_* and VAULT_*
# environment variables. BAO_* takes precedence; VAULT_* is the fallback so
# Nomad's native Vault/OpenBao integration vars work out of the box.
BAO_ADDR = os.environ.get("BAO_ADDR") or os.environ.get("VAULT_ADDR")
BAO_TOKEN = os.environ.get("BAO_TOKEN") or os.environ.get("VAULT_TOKEN")
BAO_KV_MOUNT = os.environ.get("BAO_KV_MOUNT", "secret")
BAO_PATH_PREFIX = os.environ.get("BAO_PATH_PREFIX", "")
BAO_CACERT = os.environ.get("BAO_CACERT") or os.environ.get("VAULT_CACERT")


def get_credentials(hostname):
    """Look up (username, password) for a device hostname in OpenBao KV v2.

    Returns a (username, password) tuple, or None if the lookup fails for any
    reason (missing config/token, secret not found, network error). Secret
    values are never logged.
    """
    if not hostname:
        return None

    if not BAO_ADDR or not BAO_TOKEN:
        logger.warning("OpenBao address or token not configured; skipping lookup")
        return None

    # Common path with the hostname as the final segment. strip("/") keeps the
    # path clean when BAO_PATH_PREFIX is empty.
    secret_path = f"{BAO_PATH_PREFIX}/{hostname}".strip("/")

    try:
        # Construct per call so a token re-rendered into the env by Nomad is
        # picked up without restarting the process.
        client = hvac.Client(
            url=BAO_ADDR,
            token=BAO_TOKEN,
            verify=BAO_CACERT if BAO_CACERT else True,
        )
        resp = client.secrets.kv.v2.read_secret_version(
            mount_point=BAO_KV_MOUNT,
            path=secret_path,
        )
        data = resp["data"]["data"]
        return data["username"], data["password"]
    except Exception as e:
        logger.warning(f"OpenBao credential lookup failed for '{secret_path}': {e}")
        return None
