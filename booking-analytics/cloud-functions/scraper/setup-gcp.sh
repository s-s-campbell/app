#!/bin/bash

# setup-gcp.sh - Automated setup script for Web Scraper deployment to Cloud Run
# Usage: ./setup-gcp.sh PROJECT_ID BUCKET_NAME [REGION]

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required arguments are provided
if [ $# -lt 2 ]; then
    print_error "Usage: $0 PROJECT_ID BUCKET_NAME [REGION]"
    print_error "Example: $0 my-project-123 my-scraper-bucket us-central1"
    exit 1
fi

PROJECT_ID=$1
BUCKET_NAME=$2
REGION=${3:-us-central1}

print_status "Setting up Web Scraper deployment for project: $PROJECT_ID"
print_status "Bucket name: $BUCKET_NAME"
print_status "Region: $REGION"

# Set the project
print_status "Setting project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
print_status "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable secretmanager.googleapis.com

print_status "✓ APIs enabled successfully"

# Create service account
print_status "Creating service account..."
if gcloud iam service-accounts describe scraper-service@$PROJECT_ID.iam.gserviceaccount.com &>/dev/null; then
    print_warning "Service account scraper-service already exists, skipping creation"
else
    gcloud iam service-accounts create scraper-service \
      --display-name="Web Scraper Service Account" \
      --description="Service account for web scraper Cloud Run service"
    
    print_status "✓ Service account created"
fi

# Grant permissions to service account
print_status "Granting permissions to service account..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:scraper-service@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin" \
  --quiet

print_status "✓ Service account permissions granted"

# Grant permissions to Cloud Build service account
print_status "Configuring Cloud Build service account..."
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
CLOUD_BUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/run.admin" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/iam.serviceAccountUser" \
  --quiet

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$CLOUD_BUILD_SA" \
  --role="roles/storage.admin" \
  --quiet

print_status "✓ Cloud Build service account configured"

# Create GCS bucket
print_status "Creating GCS bucket..."
if gsutil ls gs://$BUCKET_NAME &>/dev/null; then
    print_warning "Bucket gs://$BUCKET_NAME already exists, skipping creation"
else
    gsutil mb -l $REGION gs://$BUCKET_NAME
    print_status "✓ Bucket created: gs://$BUCKET_NAME"
fi

# Upload sources.json if it exists
if [ -f "sources.json" ]; then
    print_status "Uploading sources.json to bucket..."
    gsutil cp sources.json gs://$BUCKET_NAME/config/sources.json
    print_status "✓ sources.json uploaded to gs://$BUCKET_NAME/config/sources.json"
else
    print_warning "sources.json not found in current directory"
    print_warning "Make sure to upload your sources configuration to gs://$BUCKET_NAME/config/sources.json"
fi

# Create a sample sources.json if it doesn't exist
if [ ! -f "sources.json" ]; then
    print_status "Creating sample sources.json file..."
    cat > sources.json << EOF
[
  {
    "name": "example-site",
    "url": "https://httpbin.org/html"
  },
  {
    "name": "test-api",
    "url": "https://httpbin.org/json"
  }
]
EOF
    print_status "✓ Sample sources.json created"
    print_status "Uploading sample sources.json to bucket..."
    gsutil cp sources.json gs://$BUCKET_NAME/config/sources.json
fi

# Update cloudbuild.yaml with actual values
if [ -f "cloudbuild.yaml" ]; then
    print_status "Updating cloudbuild.yaml with your project configuration..."
    
    # Create a backup
    cp cloudbuild.yaml cloudbuild.yaml.backup
    
    # Replace placeholder values
    sed -i.tmp "s/your-project-id/$PROJECT_ID/g" cloudbuild.yaml
    sed -i.tmp "s/your-scraper-bucket/$BUCKET_NAME/g" cloudbuild.yaml
    sed -i.tmp "s/us-central1/$REGION/g" cloudbuild.yaml
    
    # Clean up temp files
    rm -f cloudbuild.yaml.tmp
    
    print_status "✓ cloudbuild.yaml updated with your configuration"
else
    print_warning "cloudbuild.yaml not found in current directory"
fi

# Print summary
print_status ""
print_status "🎉 Setup completed successfully!"
print_status ""
print_status "📋 Summary of created resources:"
print_status "  • Project: $PROJECT_ID"
print_status "  • Service Account: scraper-service@$PROJECT_ID.iam.gserviceaccount.com"
print_status "  • GCS Bucket: gs://$BUCKET_NAME"
print_status "  • Region: $REGION"
print_status ""
print_status "📝 Next steps:"
print_status "  1. Push your code to GitHub"
print_status "  2. Set up Cloud Build GitHub trigger:"
print_status "     → Go to: https://console.cloud.google.com/cloud-build/triggers"
print_status "     → Click 'Create Trigger'"
print_status "     → Connect your GitHub repository"
print_status "     → Use cloudbuild.yaml configuration"
print_status "  3. Push to main branch to trigger automatic deployment"
print_status ""
print_status "🔗 Useful links:"
print_status "  • Cloud Console: https://console.cloud.google.com/home/dashboard?project=$PROJECT_ID"
print_status "  • Cloud Build: https://console.cloud.google.com/cloud-build/dashboard?project=$PROJECT_ID"
print_status "  • Cloud Run: https://console.cloud.google.com/run?project=$PROJECT_ID"
print_status "  • Cloud Storage: https://console.cloud.google.com/storage/browser?project=$PROJECT_ID"
print_status ""
print_status "✨ Your web scraper is ready for deployment!" 