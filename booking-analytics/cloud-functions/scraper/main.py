import os
import json
import time
from datetime import datetime
import base64
import requests
from google.cloud import storage
from flask import Flask, request
import pytz

app = Flask(__name__)

# Use environment variables for configuration (more secure and flexible)
BUCKET_NAME = os.environ.get("BUCKET_NAME")
PROJECT_ID = os.environ.get("PROJECT_ID")  # Optional: for explicit project specification

# Validate required environment variables
if not BUCKET_NAME:
    raise ValueError("BUCKET_NAME environment variable is required")


def load_sources_from_gcs(bucket_name, path="config/sources.json"):  # Define a function to load the sources from the gcs bucket
    try:
        client = storage.Client()  # Create a client
        bucket = client.bucket(bucket_name)  # Get the bucket from the client
        blob = bucket.blob(path)  # Create a blob for the path
        
        if not blob.exists():
            raise FileNotFoundError(f"Config file {path} not found in bucket {bucket_name}")
            
        data = blob.download_as_text()  # Download the data from the blob
        return json.loads(data)  # Return the data as a list of dictionaries
    except Exception as e:
        print(f"Error loading sources: {e}")
        return []  # or raise depending on your needs


def upload_result_to_gcs(source_name, data):  # Define a function to upload the result to the gcs bucket
    try:
        timestamp = datetime.now(pytz.timezone("Australia/Sydney")).isoformat()  # Get the current timestamp in ISO format
        filename = f"data/{source_name}/{timestamp}.json"    # Updated to use data folder for HTML data

        storage_client = storage.Client()  # Create a client
        bucket = storage_client.bucket(BUCKET_NAME)  # Get the bucket from the client
        blob = bucket.blob(filename)  # Create a blob for the filename

        blob.upload_from_string(json.dumps(data), content_type="application/json")  # Upload the data to the blob
        print(f"Uploaded result for {source_name} to {filename}")  # Print a message to the console
    except Exception as e:
        print(f"Error uploading result for {source_name}: {e}")  # Print error message if upload fails


def fetch_html_with_retries(url, max_retries=3, backoff=2):  # Define a function to fetch the html from the url with retries    
    for attempt in range(1, max_retries + 1):  # Loop through the attempts
        try:
            response = requests.get(url, timeout=10)  # Get the response from the url
            response.raise_for_status()  # Raise an exception for bad status codes
            return {
                "status": "success",
                "html": response.text,  # Get the text from the response
                "http_status": response.status_code,  # Get the status code from the response
                "error_message": None  # Set the error message to None
            }
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "html": None,  # Set the html to None
                "http_status": e.response.status_code,  # Get the status code from the response
                "error_message": str(e)  # Set the error message to the exception
            }
        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                time.sleep(backoff ** attempt)  # Exponential backoff
            else:
                return {
                    "status": "error",
                    "html": None,
                    "http_status": None,
                    "error_message": f"Request failed after {max_retries} attempts: {str(e)}"
                }
            
            
def scrape_sites():
    results = []

    sources = load_sources_from_gcs(BUCKET_NAME)

    for source in sources:
        result = fetch_html_with_retries(source["url"])
        payload = {
            "source": source["name"],
            "url": source["url"],
            "scraped_at": datetime.now(pytz.timezone("Australia/Sydney")).isoformat(),
            "status": result["status"],
            "html": result["html"],
            "http_status": result["http_status"],
            "error_message": result["error_message"]
        }

        upload_result_to_gcs(source["name"], payload)
        results.append({source["name"]: payload["status"]})

    print("Scraping complete.")


@app.route("/", methods=["POST"])
def receive_pubsub():
    try:
        envelope = request.get_json()

        if not envelope or "message" not in envelope:
            return "Invalid Pub/Sub message format", 400

        pubsub_message = envelope["message"]

        # Parse payload if present
        payload = {}
        if "data" in pubsub_message:
            try:
                payload_bytes = base64.b64decode(pubsub_message["data"])
                payload = json.loads(payload_bytes.decode("utf-8"))
            except (ValueError, json.JSONDecodeError) as e:
                print(f"Error decoding Pub/Sub data: {e}")
                return "Invalid Pub/Sub data format", 400

        attributes = pubsub_message.get("attributes", {})
        trigger_type = attributes.get("trigger", "unspecified")

        print(f"Received trigger: {trigger_type}")
        print(f"Payload: {payload}")

        # Only run scraper for daily-scrape trigger
        if trigger_type == "daily-scrape":
            scrape_sites()
            return "Scraping completed", 200
        else:
            print(f"Ignoring trigger type: {trigger_type}")
            return "Trigger ignored", 200

    except Exception as e:
        print(f"Error processing Pub/Sub message: {e}")
        return "Internal server error", 500


@app.route("/health", methods=["GET"])  # Define the route for the health_check function for cloud run
def health_check():
    sydney_tz = pytz.timezone("Australia/Sydney")
    return {"status": "healthy", "timestamp": datetime.now(sydney_tz).isoformat()}, 200  # Return a healthy status and the current timestamp
