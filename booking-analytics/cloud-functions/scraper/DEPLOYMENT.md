# Deployment Guide - Cloud Run with GitHub Integration

This guide walks you through deploying your web scraper to Google Cloud Run using Cloud Build and GitHub integration for automatic deployments.

## 📋 Prerequisites

- Google Cloud Project with billing enabled
- GitHub repository with your code
- `gcloud` CLI installed and authenticated
- Required APIs enabled (see setup section)

## 🚀 Setup Steps

### 1. Enable Required APIs

```bash
# Enable necessary Google Cloud APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 2. Create Service Account

```bash
# Create service account for the scraper
gcloud iam service-accounts create scraper-service \
  --display-name="Web Scraper Service Account" \
  --description="Service account for web scraper Cloud Run service"

# Get your project ID
PROJECT_ID=$(gcloud config get-value project)

# Grant necessary permissions to the service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:scraper-service@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Grant Cloud Build service account the necessary permissions
CLOUD_BUILD_SA="$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/storage.admin"
```

### 3. Create GCS Bucket

```bash
# Create bucket for storing scraping results (already created)
# Your bucket: sports-booking-webscraper

# Create the config directory and upload sources.json
gsutil cp sources.json gs://sports-booking-webscraper/config/sources.json

# Verify bucket structure
gsutil ls gs://sports-booking-webscraper/
# Should show:
# gs://sports-booking-webscraper/config/
# gs://sports-booking-webscraper/data/    (will be created when scraper runs)
```

### 4. Configure GitHub Integration

#### Option A: Using Google Cloud Console (Recommended)
1. Go to [Cloud Build Triggers](https://console.cloud.google.com/cloud-build/triggers)
2. Click "Create Trigger"
3. Select "GitHub" as source
4. Authenticate and select your repository
5. Configure the trigger settings (see configuration below)

#### Option B: Using gcloud CLI
```bash
# Connect your GitHub repository (interactive process)
gcloud builds connections create github "my-github-connection" --region=us-central1

# Create the trigger
gcloud builds triggers create github \
  --name="deploy-web-scraper" \
  --repo-name="your-repo-name" \
  --repo-owner="your-github-username" \
  --branch-pattern="^main$" \
  --build-config="cloudbuild.yaml" \
  --region=us-central1
```

### 5. Update Configuration Variables

Edit the `cloudbuild.yaml` file and update these substitution variables:

```yaml
substitutions:
  _PROJECT_ID: 'sports-booking-465210'            # ✓ Already updated
  _REGION: 'us-central1'                          # ← Change if needed
  _SERVICE_NAME: 'web-scraper'                    # ← Customize if needed
  _BUCKET_NAME: 'sports-booking-webscraper'       # ✓ Already updated
  # ... other variables
```

## 🔧 Trigger Configuration

When setting up your Cloud Build trigger, use these settings:

### Basic Settings
- **Name**: `deploy-web-scraper`
- **Region**: `us-central1` (or your preferred region)
- **Event**: Push to a branch
- **Source**: GitHub repository
- **Branch**: `^main$` (regex pattern for main branch)

### Configuration
- **Type**: Cloud Build configuration file
- **Location**: `cloudbuild.yaml`

### Substitution Variables (Override defaults)
Add these in the trigger configuration:
```
_PROJECT_ID: sports-booking-465210
_BUCKET_NAME: sports-booking-webscraper
_REGION: us-central1
_SERVICE_NAME: web-scraper
```

### Advanced Settings
- **Service Account**: Use default Cloud Build service account
- **Machine Type**: `E2_HIGHCPU_8`
- **Disk Size**: `100 GB`
- **Timeout**: `20m`

## 🔒 Security Configuration

### Environment Variables
The deployment automatically sets these environment variables:
- `BUCKET_NAME`: Your GCS bucket name for storing results
- `PORT`: Set to 8080 (Cloud Run default)

### Service Account Permissions
The scraper service account has these permissions:
- `roles/storage.admin`: Read/write access to GCS buckets
- Access to download sources config and upload results

### Network Security
- Service is configured to allow unauthenticated requests (public access)
- To restrict access, remove `--allow-unauthenticated` and configure IAM

## 📦 Deployment Process

### Automatic Deployment
1. Push code to `main` branch in GitHub
2. Cloud Build trigger automatically starts
3. Process runs:
   - Tests are executed
   - Docker image is built
   - Image is pushed to Container Registry
   - Service is deployed to Cloud Run
   - Health check verifies deployment

### Manual Deployment
```bash
# Trigger build manually
gcloud builds triggers run deploy-web-scraper --branch=main

# Or run cloud build directly
gcloud builds submit --config=cloudbuild.yaml \
  --substitutions=_PROJECT_ID=sports-booking-465210,_BUCKET_NAME=sports-booking-webscraper
```

## 🔍 Monitoring and Verification

### Check Deployment Status
```bash
# Check Cloud Run service status
gcloud run services describe web-scraper --region=us-central1

# Check recent deployments
gcloud run revisions list --service=web-scraper --region=us-central1

# View logs
gcloud logs read "resource.type=cloud_run_revision" --limit=50
```

### Test the Service
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe web-scraper \
  --region=us-central1 \
  --format='value(status.url)')

# Test health endpoint
curl $SERVICE_URL/health

# Test scraping endpoint
curl $SERVICE_URL/
```

## 🛠️ Configuration Options

### Resource Limits
Adjust these in `cloudbuild.yaml` based on your needs:

```yaml
substitutions:
  _MEMORY: '1Gi'          # 512Mi, 1Gi, 2Gi, 4Gi
  _CPU: '1'               # 1, 2, 4, 8
  _CONCURRENCY: '80'      # Max requests per instance
  _TIMEOUT: '900'         # Max request duration (seconds)
  _MAX_INSTANCES: '10'    # Scale up limit
```

### Build Optimization
For faster builds:
```yaml
options:
  machineType: 'E2_HIGHCPU_32'  # Use more powerful machine
  diskSizeGb: 200               # Increase disk if needed
```

## 🐛 Troubleshooting

### Common Issues

**1. Build Fails with Permission Denied**
```bash
# Check Cloud Build service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
  --filter="bindings.members:$CLOUD_BUILD_SA"
```

**2. Deployment Fails**
```bash
# Check Cloud Build logs
gcloud builds log --region=us-central1 [BUILD_ID]

# Check if image exists
gcloud container images list --repository=gcr.io/$PROJECT_ID
```

**3. Service Won't Start**
```bash
# Check Cloud Run logs
gcloud logs read "resource.type=cloud_run_revision" \
  --filter="resource.labels.service_name=web-scraper"
```

**4. Tests Fail During Build**
- Check test output in Cloud Build logs
- Verify `requirements-dev.txt` is correct
- Ensure all dependencies are properly specified

### Debug Commands
```bash
# Test build locally
docker build -t test-scraper .
docker run -p 8080:8080 -e BUCKET_NAME=test-bucket test-scraper

# Validate cloudbuild.yaml
gcloud builds submit --config=cloudbuild.yaml --dry-run

# Check service account key
gcloud iam service-accounts keys list \
  --iam-account=scraper-service@$PROJECT_ID.iam.gserviceaccount.com
```

## 📊 Cost Optimization

### Cloud Run Pricing
- **CPU**: $0.000024 per vCPU-second
- **Memory**: $0.0000025 per GiB-second  
- **Requests**: $0.40 per million requests
- **Minimum instances**: Keep at 0 to avoid charges when idle

### Build Optimization
- Use caching for faster builds
- Optimize Docker layers
- Use smaller base images when possible

### Monitoring Costs
```bash
# Check current month usage
gcloud billing budgets list

# Set up budget alerts for the project
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Web Scraper Budget" \
  --budget-amount=50USD
```

## 🔄 Updates and Maintenance

### Updating the Service
1. Make changes to your code
2. Update tests if needed
3. Push to `main` branch
4. Automatic deployment will start

### Rolling Back
```bash
# List revisions
gcloud run revisions list --service=web-scraper --region=us-central1

# Roll back to previous revision
gcloud run services update-traffic web-scraper \
  --to-revisions=REVISION_NAME=100 \
  --region=us-central1
```

### Scaling Configuration
```bash
# Update scaling settings
gcloud run services update web-scraper \
  --min-instances=0 \
  --max-instances=20 \
  --region=us-central1
```

## 📚 Additional Resources

- [Cloud Build Documentation](https://cloud.google.com/build/docs)
- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [GitHub Integration Guide](https://cloud.google.com/build/docs/automating-builds/create-github-app-triggers)
- [IAM Best Practices](https://cloud.google.com/iam/docs/using-iam-securely)

## 🆘 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review Cloud Build and Cloud Run logs
3. Verify IAM permissions and service account configuration
4. Test components individually (Docker build, local run, etc.) 