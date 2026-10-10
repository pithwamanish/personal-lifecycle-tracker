#!/usr/bin/env python3
"""
AWS Lambda Function Simulation: On-Call Incident Dispatcher.

In AWS Production:
- Triggered by Amazon SNS topic subscription or EventBridge rule.
- Parses the alert payload.
- Invokes AWS ECS / Fargate run_task API to launch an ephemeral container.
"""

import json
import logging
import os
import subprocess
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [LAMBDA] %(message)s")
logger = logging.getLogger("lambda-dispatcher")


def lambda_handler(event, context=None):
    logger.info("Lambda invocation started with event payload.")
    
    # 1. Parse Event from SNS or direct EventBridge invocation
    alert_data = {}
    if "Records" in event and len(event["Records"]) > 0:
        sns_record = event["Records"][0].get("Sns", {})
        raw_msg = sns_record.get("Message", "{}")
        if isinstance(raw_msg, str):
            try:
                alert_data = json.loads(raw_msg)
            except json.JSONDecodeError:
                alert_data = {"summary": raw_msg}
        else:
            alert_data = raw_msg
    elif "detail" in event:
        alert_data = event["detail"]
    else:
        alert_data = event

    alert_name = alert_data.get("alert_name", alert_data.get("alertname", "HighHttpErrorRate"))
    severity = alert_data.get("severity", "critical")
    service_name = alert_data.get("service_name", alert_data.get("service", "api-backend"))
    
    ts = int(time.time())
    incident_id = f"INC-{ts}-{alert_name}"
    logger.info(f"Processed alert: '{alert_name}' [{severity}] for service '{service_name}' -> Incident ID: {incident_id}")

    # 2. Mimic ECS run_task API
    # In cloud: ecs_client.run_task(cluster='on-call-cluster', taskDefinition='on-call-agent:1', launchType='FARGATE', overrides={...})
    # In local simulation: runs an ephemeral Docker container using amazon/aws-cli:latest or docker runner
    s3_endpoint = os.environ.get("S3_ENDPOINT_URL", "http://personal-lifecycle-cloud-emulator:4566")
    s3_bucket = os.environ.get("S3_BUCKET", "lifecycle-on-call-incidents")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sim_dir = os.path.dirname(script_dir)
    fargate_script = os.path.join(sim_dir, "fargate-task", "task-runner.sh")
    
    logger.info("Dispatching AWS ECS / Fargate ephemeral container task...")
    
    docker_cmd = [
        "docker", "run", "--rm",
        "--name", f"fargate-task-{incident_id.lower()}",
        "--network", "personal-lifecycle-observability-net",
        "-e", f"INCIDENT_ID={incident_id}",
        "-e", f"ALERT_NAME={alert_name}",
        "-e", f"SEVERITY={severity}",
        "-e", f"SERVICE_NAME={service_name}",
        "-e", f"S3_ENDPOINT_URL={s3_endpoint}",
        "-e", f"S3_BUCKET={s3_bucket}",
        "-e", "AWS_DEFAULT_REGION=us-east-1",
        "-e", "AWS_ACCESS_KEY_ID=test",
        "-e", "AWS_SECRET_ACCESS_KEY=test",
        "-v", f"{fargate_script}:/task-runner.sh:ro",
        "--entrypoint", "/task-runner.sh",
        "amazon/aws-cli:latest"
    ]
    
    proc = subprocess.run(docker_cmd, capture_output=True, text=True)
    if proc.stdout:
        for line in proc.stdout.strip().split("\n"):
            logger.info(f"[FARGATE-STDOUT] {line}")
    if proc.stderr:
        for line in proc.stderr.strip().split("\n"):
            logger.warning(f"[FARGATE-STDERR] {line}")

    if proc.returncode != 0:
        logger.error(f"Fargate task exited with non-zero code {proc.returncode}")
        return {
            "statusCode": 500,
            "incidentId": incident_id,
            "error": proc.stderr
        }

    task_arn = f"arn:aws:ecs:us-east-1:000000000000:task/{incident_id}"
    logger.info(f"Fargate container task completed and terminated immediately. Task ARN: {task_arn}")

    return {
        "statusCode": 200,
        "incidentId": incident_id,
        "taskArn": task_arn,
        "s3AuditLocation": f"s3://{s3_bucket}/{incident_id}/"
    }


if __name__ == "__main__":
    sample_sns_event = {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps({
                        "alert_name": "HighHttpErrorRate",
                        "severity": "critical",
                        "service_name": "api-backend",
                        "summary": "Elevated HTTP 5xx error rate",
                        "observed_value": 100.0,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    })
                }
            }
        ]
    }
    result = lambda_handler(sample_sns_event)
    print(json.dumps(result, indent=2))
