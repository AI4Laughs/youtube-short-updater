import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
VIDEO_ID = os.getenv('MY_VIDEO_ID')  # Ensure this is set in your GitHub secrets or environment

def get_authenticated_service():
    """Set up YouTube API authentication."""
    creds = None

    # Load credentials from oauth2.json
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    # Refresh expired credentials
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        else:
            print("Invalid credentials. Please ensure oauth2.json is properly configured.")
            return None

    try:
        return build('youtube', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error building service: {e}")
        return None

def main():
    # Validate environment variables
    if not VIDEO_ID:
        print("Error: VIDEO_ID environment variable not set.")
        return

    print(f"Using video ID: {VIDEO_ID}")

    print("Starting YouTube API authentication...")
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate with YouTube API.")
        return

    print("Authenticated successfully.")

    try:
        # Fetch the latest comment
        print("Fetching the latest comment...")
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=VIDEO_ID,
            order="time",
            maxResults=1
        )
        comment_response = comment_request.execute()
        print(f"Comment response: {json.dumps(comment_response, indent=2)}")

        if not comment_response.get("items"):
            print("No comments found on the video.")
            return

        # Extract the commenter name
        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")
        print(f"Latest commenter: {commenter_display_name}")

        # Fetch video statistics
        print("Fetching video statistics...")
        video_request = youtube.videos().list(
            part="statistics",
            id=VIDEO_ID
        )
        video_response = video_request.execute()
        print(f"Video response: {json.dumps(video_response, indent=2)}")

        if not video_response.get("items"):
            print("Video not found or insufficient permissions.")
            return

        # Extract view count
        view_count = video_response["items"][0]["statistics"].get("viewCount", "0")
        print(f"View count: {view_count}")

        # Create the new title
        new_title = f"This Short has {view_count} views thanks to {commenter_display_name} #shorts"
        print(f"New title: {new_title}")

        # Get current video details to preserve other snippet data
        video_details_request = youtube.videos().list(
            part="snippet",
            id=VIDEO_ID
        )
        video_details_response = video_details_request.execute()

        if not video_details_response.get("items"):
            print("Video details not found or insufficient permissions.")
            return

        current_snippet = video_details_response["items"][0]["snippet"]
        current_snippet["title"] = new_title

        # Update the video title
        print("Updating video title...")
        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": VIDEO_ID,
                "snippet": current_snippet
            }
        )
        update_response = update_request.execute()
        print(f"Update response: {json.dumps(update_response, indent=2)}")
        print(f"Success! Updated video title to: {new_title}")

    except HttpError as e:
        print(f"HTTP error: {e.resp.status}, {e.content}")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    main()
