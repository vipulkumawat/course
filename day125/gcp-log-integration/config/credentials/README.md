# Service Account Credentials

Place your GCP service account JSON files here.

## Required IAM Roles

Your service account needs the following roles:
- `roles/logging.viewer` - Read access to logs
- `roles/pubsub.subscriber` - For Pub/Sub integration (optional)

## How to Create Service Account

1. Go to GCP Console → IAM & Admin → Service Accounts
2. Click "Create Service Account"
3. Grant required roles
4. Create JSON key
5. Download and place in this directory

## Security Best Practices

- Never commit service account keys to version control
- Use `.gitignore` to exclude this directory
- Rotate keys every 90 days
- Use Workload Identity in Kubernetes environments
