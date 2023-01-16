import docker
import os
import pathlib
import subprocess

from termcolor import cprint
from typing import Dict, Optional, Tuple

from .config import (
    DOCKER_COMPOSE_FILE_BASE,
    DOCKER_COMPOSE_FILE_DEV,
    DOCKER_COMPOSE_FILE_PROD,
    DOCKER_COMPOSE_SERVICES,
    COMPOSE, BENTO_SERVICES_DATA,
)
from .state import MODE_DEV, MODE_PROD, get_state, set_state_services

__all__ = [
    "run_service",
    "stop_service",
    "restart_service",
    "clean_service",
    "work_on_service",
    "enter_shell_for_service",
    "run_as_shell_for_service",
]

BENTO_SERVICES_DATA_BY_KIND = {
    v["service_kind"]: {**v, "compose_id": k}
    for k, v in BENTO_SERVICES_DATA.items()
}


compose_with_files_dev = (*COMPOSE, "-f", DOCKER_COMPOSE_FILE_BASE, "-f", DOCKER_COMPOSE_FILE_DEV)
compose_with_files_prod = (*COMPOSE, "-f", DOCKER_COMPOSE_FILE_BASE, "-f", DOCKER_COMPOSE_FILE_PROD)


# TODO: More elegant solution for service-image associations
service_image_vars: Dict[str, Tuple[str, str, Optional[str]]] = {
    "aggregation": ("BENTOV2_AGGREGATION_IMAGE", "BENTOV2_AGGREGATION_VERSION", "BENTOV2_AGGREGATION_VERSION_DEV"),
    "auth": ("BENTOV2_AUTH_IMAGE", "BENTOV2_AUTH_VERSION", None),
    "beacon": ("BENTO_BEACON_IMAGE", "BENTO_BEACON_VERSION", "BENTO_BEACON_VERSION_DEV"),
    "drop-box": ("BENTOV2_DROP_BOX_IMAGE", "BENTOV2_DROP_BOX_VERSION", "BENTOV2_DROP_BOX_VERSION_DEV"),
    "drs": ("BENTOV2_DRS_IMAGE", "BENTOV2_DRS_VERSION", "BENTOV2_DRS_VERSION_DEV"),
    "event-relay": ("BENTOV2_EVENT_RELAY_IMAGE", "BENTOV2_EVENT_RELAY_VERSION", "BENTOV2_EVENT_RELAY_VERSION_DEV"),
    "gateway": ("BENTOV2_GATEWAY_IMAGE", "BENTOV2_GATEWAY_VERSION", "BENTOV2_GATEWAY_VERSION_DEV"),
    "gohan-api": ("BENTOV2_GOHAN_API_IMAGE", "BENTOV2_GOHAN_API_VERSION", "BENTOV2_GOHAN_API_VERSION_DEV"),
    "gohan-elasticsearch": ("BENTOV2_GOHAN_ES_IMAGE", "BENTOV2_GOHAN_ES_VERSION", None),
    "katsu": ("BENTOV2_KATSU_IMAGE", "BENTOV2_KATSU_VERSION", "BENTOV2_KATSU_VERSION_DEV"),
    "notification": ("BENTOV2_NOTIFICATION_IMAGE", "BENTOV2_NOTIFICATION_VERSION", "BENTOV2_NOTIFICATION_VERSION_DEV"),
    "public": ("BENTO_PUBLIC_IMAGE", "BENTO_PUBLIC_VERSION", "BENTO_PUBLIC_VERSION_DEV"),
    "service-registry": ("BENTOV2_SERVICE_REGISTRY_IMAGE", "BENTOV2_SERVICE_REGISTRY_VERSION",
                         "BENTOV2_SERVICE_REGISTRY_VERSION_DEV"),
    "wes": ("BENTOV2_WES_IMAGE", "BENTOV2_WES_VERSION", "BENTOV2_WES_VERSION_DEV"),
}


docker_client = docker.from_env()


def translate_service_aliases(service: str):
    if service in BENTO_SERVICES_DATA_BY_KIND:
        return BENTO_SERVICES_DATA_BY_KIND[service]["compose_id"]

    return service


def check_service_is_compose(compose_service: str):
    if compose_service not in DOCKER_COMPOSE_SERVICES:
        cprint(f"  {compose_service} not in Docker Compose services: {DOCKER_COMPOSE_SERVICES}")
        exit(1)


def _run_service_in_dev_mode(compose_service: str):
    print(f"Running {compose_service} in development mode...")
    subprocess.check_call((*compose_with_files_dev, "up", "-d", compose_service))


def _run_service_in_prod_mode(compose_service: str):
    print(f"Running {compose_service} in production mode...")
    subprocess.check_call((*compose_with_files_prod, "up", "-d", compose_service))


def run_service(compose_service: str):
    compose_service = translate_service_aliases(compose_service)

    service_state = get_state()["services"]

    # TODO: Look up dev/prod mode based on compose_service

    if compose_service == "all":
        # special: run everything
        subprocess.check_call((
            *compose_with_files_prod,
            "up", "-d",
            *(s for s in DOCKER_COMPOSE_SERVICES if service_state.get(s, {}).get("mode") != "dev")
        ))

        for service, service_settings in service_state.items():
            if service_settings["mode"] == MODE_DEV:
                _run_service_in_dev_mode(service)

        return

    if compose_service not in DOCKER_COMPOSE_SERVICES:
        cprint(f"  {compose_service} not in list of services: {DOCKER_COMPOSE_SERVICES}", "red")
        exit(1)

    if service_state[compose_service]["mode"] == MODE_DEV:
        _run_service_in_dev_mode(compose_service)
    else:
        _run_service_in_prod_mode(compose_service)


def stop_service(compose_service: str):
    compose_service = translate_service_aliases(compose_service)

    if compose_service == "all":
        # special: stop everything
        subprocess.check_call((*COMPOSE, "down"))
        return

    check_service_is_compose(compose_service)

    print(f"Stopping {compose_service}...")
    subprocess.check_call((*COMPOSE, "stop", compose_service))


def restart_service(compose_service: str):
    stop_service(compose_service)
    run_service(compose_service)


def clean_service(compose_service: str):
    compose_service = translate_service_aliases(compose_service)

    if compose_service == "all":
        # special: stop everything
        for s in DOCKER_COMPOSE_SERVICES:
            clean_service(s)
        return

    check_service_is_compose(compose_service)

    print(f"Stopping {compose_service}...")
    subprocess.check_call((*COMPOSE, "rm", "-svf", compose_service))


def work_on_service(compose_service: str):
    compose_service = translate_service_aliases(compose_service)
    service_state = get_state()["services"]

    if compose_service == "all":
        cprint(f"  Cannot work on all services.", "red")
        exit(1)

    check_service_is_compose(compose_service)

    if compose_service not in BENTO_SERVICES_DATA:
        cprint(f"  {compose_service} not in bento_services.json: {list(BENTO_SERVICES_DATA.keys())}")
        exit(1)

    if not (repo_path := pathlib.Path.cwd() / "repos" / compose_service).exists():
        # Clone the repository if it doesn't already exist
        cprint(f"  Cloning {compose_service} repository into repos/ ...", "blue")
        # TODO: clone ssh...
        subprocess.check_call(("git", "clone", BENTO_SERVICES_DATA[compose_service]["repository"], repo_path))
        # TODO

    # Save state change
    service_state = set_state_services({
        **service_state,
        compose_service: {
            **service_state[compose_service],
            "mode": MODE_DEV,
        },
    })["services"]

    # Clean up existing container
    clean_service(compose_service)

    # Pull new version of production container if needed
    pull_service(compose_service, service_state)

    # Start new dev container
    _run_service_in_dev_mode(compose_service)


def prod_service(compose_service: str):
    compose_service = translate_service_aliases(compose_service)
    service_state = get_state()["services"]

    if compose_service == "all":
        for service in BENTO_SERVICES_DATA:
            prod_service(service)
        return

    check_service_is_compose(compose_service)

    if compose_service not in BENTO_SERVICES_DATA:
        cprint(f"  {compose_service} not in bento_services.json: {list(BENTO_SERVICES_DATA.keys())}")
        exit(1)

    # Save state change
    service_state = set_state_services({
        **service_state,
        compose_service: {
            **service_state[compose_service],
            "mode": MODE_PROD,
        },
    })["services"]

    # Clean up existing container
    clean_service(compose_service)

    # Pull new version of production container if needed
    pull_service(compose_service, service_state)

    # Start new production container
    _run_service_in_prod_mode(compose_service)


def pull_service(compose_service: str, existing_service_state: Optional[dict] = None):
    compose_service = translate_service_aliases(compose_service)
    service_state = existing_service_state or get_state()["services"]

    if compose_service == "all":
        # special: run everything
        subprocess.check_call((*COMPOSE, "pull"))
        return

    check_service_is_compose(compose_service)

    print(f"Pulling {compose_service}...")

    image_t = service_image_vars.get(compose_service)
    if image_t is None:
        cprint(f"  {compose_service} not in service_image_vars keys: {list(service_image_vars.keys())}", "red")
        exit(1)

    image_var, image_version_var, image_dev_version_var = image_t
    service_mode = service_state.get(compose_service, {}).get("mode")

    image_version_var_final: str = image_dev_version_var if service_mode == "dev" else image_version_var

    if image_version_var_final is None:  # occurs if in dev mode (somehow) but with no dev image
        # TODO: Fix the state
        cprint(f"  {compose_service} does not have a dev image", "red")
        exit(1)

    image = os.getenv(image_var)
    image_version = os.getenv(image_version_var_final)

    if image is None:
        cprint(f"  {image_var} is not set", "red")
        exit(1)
    if image_version is None:
        cprint(f"  {image_version_var_final} is not set", "red")
        exit(1)

    # TODO: Pull dev if in dev mode
    subprocess.check_call(("docker", "pull", f"{image}:{image_version}"))  # Use subprocess to get nice output
    subprocess.check_call((
        *(compose_with_files_dev if service_mode == "dev" else compose_with_files_prod),
        "pull", compose_service
    ))


def enter_shell_for_service(compose_service: str, shell: str):
    compose_service = translate_service_aliases(compose_service)

    check_service_is_compose(compose_service)

    cmd = COMPOSE[0]
    compose_args = COMPOSE[1:]
    os.execvp(cmd, (cmd, *compose_args, "exec", "-it", compose_service, shell))  # TODO: Detect shell


def run_as_shell_for_service(compose_service: str, shell: str):
    compose_service = translate_service_aliases(compose_service)

    check_service_is_compose(compose_service)

    cmd = COMPOSE[0]
    compose_args = COMPOSE[1:]
    os.execvp(cmd, (cmd, *compose_args, "run", compose_service, shell))  # TODO: Detect shell
