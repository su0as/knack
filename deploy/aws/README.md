# Deploying Knack on AWS (OpenCV AI Competition 2026)

One small Graviton instance runs everything: the Knack console (public, read-only without a passcode) and practice
runs whose perception is OpenCV 5 on rendered RGB-D frames. Model calls go to Nebius Token Factory.

## Cost guardrails (set these first)
- Account on the **Free plan** (no charges possible; credits only).
- AWS Budgets: alerts at $1, $5 and $10 actual cost to the account email.
- One region: `ap-southeast-1` (Singapore). One instance, no autoscaling, no GPUs, no databases, no NAT gateway, no load balancer.
- Instance: `t4g.medium` (2 Arm vCPU, 4 GiB), 20 GiB gp3. About $0.034/hour, roughly $25/month, paid from credits.
- Stop the instance after judging (9 Nov). Terminating it deletes the disk.

## Security
- No SSH: the security group opens only TCP 80. Admin access is AWS Systems Manager Session Manager.
- Secrets: `/knack/NEBIUS_API_KEY` and `/knack/PASSCODE` are SSM SecureString parameters, read once at boot into
  `/etc/knack.env` (mode 640, root:knack). Nothing secret is in the repo, the AMI or the user data.
- Instance role (least privilege): `AmazonSSMManagedInstanceCore` plus an inline policy allowing `ssm:GetParameter`
  on `arn:aws:ssm:ap-southeast-1:<account>:parameter/knack/*` and `s3:PutObject`/`s3:ListBucket` on the runs bucket.
- Public console: anyone can browse every run; starting a new run needs the passcode, is capped at $0.10, and only one
  run can start every two minutes.

## Steps
1. SSM Parameter Store: create `/knack/NEBIUS_API_KEY` and `/knack/PASSCODE` (SecureString).
2. S3: create a private bucket `knack-runs-<account-id>` (block all public access on).
3. IAM: role `knack-ec2` for EC2 with the policies above.
4. EC2: launch `t4g.medium`, Ubuntu Server 24.04 LTS (arm64), 20 GiB gp3, role `knack-ec2`, security group inbound TCP 80
   from 0.0.0.0/0 only, user data = `deploy/aws/user-data.sh` with `BUCKET=knack-runs-<account-id>` set at the top.
5. Open `http://<public-ip>/` after about 5 minutes. The first practice run appears in the run list.
