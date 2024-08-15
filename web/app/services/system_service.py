from flask import current_app


def get_least_served(container_dict):
    """return least served container"""
    least_served = list(container_dict.keys())[0]
    requests = container_dict[least_served]["requests"]

    for entry in container_dict.keys():
        if container_dict[entry]["requests"] < requests:
            least_served = entry
    current_app.logger.debug(f"least served container is: {least_served}")

    container_dict[least_served]["requests"] += 1
    return least_served
