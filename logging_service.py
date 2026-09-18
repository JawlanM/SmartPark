from datetime import datetime, timezone, timedelta

request_logs = []

def log_request(uuid, endpoint, requested_n, status="success", severity="INFO"):
    log_entry = {
        "timestamp": datetime.now(timezone.utc),
        "uuid": uuid,
        "endpoint": endpoint,
        "severity": severity,
        "service_name": "smartpark-api",
        "requested_n": requested_n,
        "status": status
    } 

    request_logs.append(log_entry)

    return log_entry

def get_users_last_30_seconds():
    current_time = datetime.now(timezone.utc)

    cutoff_time = current_time - timedelta(seconds=30)

    recent_users = set()

    for log in request_logs:
        if log["timestamp"] >= cutoff_time:
            recent_users.add(log["uuid"])

    return len(recent_users)