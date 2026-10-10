# Deploying Personal Lifecycle Tracker to AWS via CloudFormation

This guide covers deploying the **Personal Lifecycle Tracker** to Amazon Web Services using **AWS CloudFormation**.

The template [`cloudformation/aws-ec2-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose.yaml) deploys a self-contained, Free-Tier eligible infrastructure stack without needing external tools or Terraform state management.

---

## What Gets Provisioned

```
┌────────────────────────────────────────────────────────────────────────┐
│ AWS CloudFormation Stack: personal-lifecycle-tracker                   │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │ VPC (10.0.0.0/16) + Internet Gateway + Public Route Table      │   │
│   │                                                                │   │
│   │   ┌────────────────────────────────────────────────────────┐   │   │
│   │   │ Public Subnet (10.0.1.0/24)                            │   │   │
│   │   │                                                        │   │   │
│   │   │   ┌────────────────────────────────────────────────┐   │   │   │
│   │   │   │ Security Group (Ports 80, 443, 8088, 22)       │   │   │   │
│   │   │   │                                                │   │   │   │
│   │   │   │   EC2 Instance (Ubuntu 24.04 LTS, t3.micro)    │   │   │   │
│   │   │   │   ├── Elastic IP                               │   │   │   │
│   │   │   │   ├── IAM Instance Profile (SSM Session Mgr)   │   │   │   │
│   │   │   │   └── Docker Compose Production Stack          │   │   │   │
│   │   │   │       ├── frontend (React 19 + Caddy 2) :80    │   │   │   │
│   │   │   │       ├── backend (FastAPI) :8000              │   │   │   │
│   │   │   │       └── db (PostgreSQL 16) :5432             │   │   │   │
│   │   │   └────────────────────────────────────────────────┘   │   │   │
│   │   └────────────────────────────────────────────────────────┘   │   │
│   └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Deployment Option 1: AWS Management Console (1-Click Upload)

1. **Log in to the AWS Console**:
   Navigate to the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation).

2. **Create Stack**:
   - Click **"Create stack"** -> **"With new resources (standard)"**.
   - Under *Prerequisite - Prepare template*, choose **"Choose an existing template"**.
   - Under *Template source*, choose **"Upload a template file"**.
   - Upload [`cloudformation/aws-ec2-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose.yaml).
   - Click **Next**.

3. **Specify Stack Details**:
   - **Stack name**: `personal-lifecycle-tracker-prod`
   - **InstanceType**: `t3.micro` (or `t4g.micro`, both Free-Tier eligible)
   - **AllowedCIDR**: `0.0.0.0/0` (or restrict to your office/home IP)
   - **AppPort**: `80`
   - **RepoUrl**: `https://github.com/pithwamanish/personal-lifecycle-tracker.git`
   - **RepoBranch**: `main`
   - **KeyName**: (Optional) Select an existing EC2 Key Pair if you prefer SSH, or leave blank to use AWS Systems Manager.
   - Click **Next**.

4. **Configure Stack Options**:
   - Accept default tags and permissions.
   - Click **Next**.

5. **Review and Acknowledge**:
   - Check the box: **"I acknowledge that AWS CloudFormation might create IAM resources."**
   - Click **Submit**.

6. **Monitor & Retrieve Outputs**:
   - The stack status will transition from `CREATE_IN_PROGRESS` to `CREATE_COMPLETE` in ~2 minutes.
   - Go to the **Outputs** tab to retrieve:
     - `ApplicationURL` (e.g. `http://54.210.xx.xx:80`)
     - `HealthCheckURL` (e.g. `http://54.210.xx.xx:80/health`)
     - `SSMConnectCommand` (e.g. `aws ssm start-session --target i-0123456789`)

---

## Deployment Option 2: AWS CLI

You can also deploy the stack from your local terminal using the AWS CLI:

```bash
aws cloudformation create-stack \
  --stack-name personal-lifecycle-tracker-prod \
  --template-body file://cloudformation/aws-ec2-compose.yaml \
  --parameters \
      ParameterKey=InstanceType,ParameterValue=t3.micro \
      ParameterKey=AppPort,ParameterValue=80 \
      ParameterKey=AllowedCIDR,ParameterValue=0.0.0.0/0 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Wait for stack completion:
```bash
aws cloudformation wait stack-create-complete \
  --stack-name personal-lifecycle-tracker-prod \
  --region us-east-1
```

View the generated outputs:
```bash
aws cloudformation describe-stacks \
  --stack-name personal-lifecycle-tracker-prod \
  --query "Stacks[0].Outputs" \
  --output table \
  --region us-east-1
```

---

## Access & Maintenance

### 1. Connecting to the Server Shell (Zero Open Ports)
Connect directly via AWS Systems Manager Session Manager:
```bash
aws ssm start-session \
  --target $(aws cloudformation describe-stacks --stack-name personal-lifecycle-tracker-prod --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" --output text --region us-east-1) \
  --region us-east-1
```

### 2. Inspecting Running Containers on the EC2 Host
```bash
sudo docker compose -f /opt/personal-lifecycle-tracker/docker-compose.prod.yml ps
```

### 3. Viewing Live Production Application Logs
```bash
sudo docker compose -f /opt/personal-lifecycle-tracker/docker-compose.prod.yml logs -f
```

---

## Tear Down Stack
To delete all provisioned AWS resources and stop all charges:
```bash
aws cloudformation delete-stack \
  --stack-name personal-lifecycle-tracker-prod \
  --region us-east-1
```
