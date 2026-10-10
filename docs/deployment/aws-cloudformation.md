# Deploying Personal Lifecycle Tracker to AWS via CloudFormation

This guide covers deploying the **Personal Lifecycle Tracker** to Amazon Web Services using **AWS CloudFormation** across two independent environments:
1. **Development Environment (`dev`)**: [`cloudformation/aws-ec2-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose.yaml) — Default environment `dev`, isolated VPC CIDR `10.1.0.0/16`.
2. **Production Environment Copy (`production`)**: [`cloudformation/aws-ec2-compose-prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose-prod.yaml) — Default environment `production`, isolated VPC CIDR `10.0.0.0/16`.

Both templates deploy self-contained, Free-Tier eligible infrastructure stacks without needing external tools or Terraform state management.

---

## Comparison Matrix

| Property | Development (`aws-ec2-compose.yaml`) | Production (`aws-ec2-compose-prod.yaml`) |
|---|---|---|
| **Default Stack Name** | `personal-lifecycle-tracker-dev` | `personal-lifecycle-tracker-prod` |
| **Environment Parameter** | `dev` | `production` |
| **VPC CIDR** | `10.1.0.0/16` | `10.0.0.0/16` |
| **Subnet CIDR** | `10.1.1.0/24` | `10.0.1.0/24` |
| **Instance Type** | `t3.micro` | `t3.micro` (or `t3.small`) |
| **Default Branch** | `main` (or `dev`) | `main` |
| **App Port** | `80` (or `8088`) | `80` |

---

## Deployment Option 1: AWS Management Console (1-Click Upload)

1. **Log in to the AWS Console**:
   Navigate to the [AWS CloudFormation Console](https://console.aws.amazon.com/cloudformation).

2. **Create Stack**:
   - Click **"Create stack"** -> **"With new resources (standard)"**.
   - Under *Prerequisite - Prepare template*, choose **"Choose an existing template"**.
   - Under *Template source*, choose **"Upload a template file"**.
   - Select:
     - For Dev: [`cloudformation/aws-ec2-compose.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose.yaml)
     - For Production: [`cloudformation/aws-ec2-compose-prod.yaml`](file:///home/manish/AI-Practice/DataTalks/ai-dev-tools-zoomcamp-2026/project/personal-lifecycle-tracker/cloudformation/aws-ec2-compose-prod.yaml)
   - Click **Next**.

3. **Specify Stack Details**:
   - **Stack name**: `personal-lifecycle-tracker-dev` (or `personal-lifecycle-tracker-prod`)
   - **Environment**: `dev` or `production`
   - **InstanceType**: `t3.micro`
   - **AllowedCIDR**: `0.0.0.0/0`
   - **AppPort**: `80`
   - Click **Next**.

4. **Review and Acknowledge**:
   - Check the box: **"I acknowledge that AWS CloudFormation might create IAM resources."**
   - Click **Submit**.

---

## Deployment Option 2: AWS CLI

### Deploy Dev Environment:
```bash
aws cloudformation create-stack \
  --stack-name personal-lifecycle-tracker-dev \
  --template-body file://cloudformation/aws-ec2-compose.yaml \
  --parameters \
      ParameterKey=Environment,ParameterValue=dev \
      ParameterKey=VpcCidr,ParameterValue=10.1.0.0/16 \
      ParameterKey=SubnetCidr,ParameterValue=10.1.1.0/24 \
      ParameterKey=InstanceType,ParameterValue=t3.micro \
      ParameterKey=AppPort,ParameterValue=80 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

### Deploy Production Environment Copy:
```bash
aws cloudformation create-stack \
  --stack-name personal-lifecycle-tracker-prod \
  --template-body file://cloudformation/aws-ec2-compose-prod.yaml \
  --parameters \
      ParameterKey=Environment,ParameterValue=production \
      ParameterKey=VpcCidr,ParameterValue=10.0.0.0/16 \
      ParameterKey=SubnetCidr,ParameterValue=10.0.1.0/24 \
      ParameterKey=InstanceType,ParameterValue=t3.micro \
      ParameterKey=AppPort,ParameterValue=80 \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

---

## Access & Maintenance

### 1. Connecting to Server Shell via AWS Systems Manager
```bash
# Connect to Dev EC2
aws ssm start-session \
  --target $(aws cloudformation describe-stacks --stack-name personal-lifecycle-tracker-dev --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" --output text --region us-east-1) \
  --region us-east-1

# Connect to Production EC2
aws ssm start-session \
  --target $(aws cloudformation describe-stacks --stack-name personal-lifecycle-tracker-prod --query "Stacks[0].Outputs[?OutputKey=='InstanceId'].OutputValue" --output text --region us-east-1) \
  --region us-east-1
```

### 2. Inspecting Running Containers on Host
```bash
sudo docker compose -f /opt/personal-lifecycle-tracker/docker-compose.prod.yml ps
```

---

## Tear Down Stacks

```bash
# Destroy Dev
aws cloudformation delete-stack --stack-name personal-lifecycle-tracker-dev --region us-east-1

# Destroy Production
aws cloudformation delete-stack --stack-name personal-lifecycle-tracker-prod --region us-east-1
```
