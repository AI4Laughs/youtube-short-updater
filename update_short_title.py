import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import datetime

# Constants
SCOPES = ['https://www.googleapis.com/auth/youtube.force-ssl']
VIDEO_ID = os.getenv('MY_VIDEO_ID')

def get_authenticated_service():
    """Set up YouTube API authentication with detailed logging."""
    creds = None
    
    print(f"Starting authentication at {datetime.datetime.now()}")
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in directory: {os.listdir()}")

    # Load credentials from oauth2.json
    try:
        with open('oauth2.json', 'r') as f:
            creds_data = json.load(f)
            print("Successfully loaded oauth2.json")
            print(f"Credential keys present: {list(creds_data.keys())}")
            creds = Credentials.from_authorized_user_info(creds_data, SCOPES)
            print(f"Credentials loaded. Valid: {creds.valid}, Expired: {getattr(creds, 'expired', 'Unknown')}")
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

    # Refresh expired credentials
    if not creds or not creds.valid:
        if creds and getattr(creds, 'expired', False) and getattr(creds, 'refresh_token', None):
            try:
                print("Attempting to refresh expired credentials...")
                creds.refresh(Request())
                print("Successfully refreshed credentials")
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                return None
        else:
            print("Invalid credentials. Please ensure oauth2.json is properly configured.")
            if creds:
                print(f"Refresh token present: {'refresh_token' in creds_data}")
            return None

    try:
        service = build('youtube', 'v3', credentials=creds)
        print("Successfully built YouTube service")
        return service
    except Exception as e:
        print(f"Error building service: {e}")
        return None

def get_video_details(youtube, video_id):
    """Get video statistics and details."""
    try:
        video_request = youtube.videos().list(
            part="statistics,snippet",
            id=video_id
        )
        return video_request.execute()
    except Exception as e:
        print(f"Error getting video details: {e}")
        return None

def get_latest_comment(youtube, video_id):
    """Get the latest comment from the video."""
    try:
        comment_request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            order="time",
            maxResults=1
        )
        return comment_request.execute()
    except Exception as e:
        print(f"Error getting latest comment: {e}")
        return None

def update_video_title(youtube, video_id, new_title, current_snippet):
    """Update the video title."""
    try:
        update_request = youtube.videos().update(
            part="snippet",
            body={
                "id": video_id,
                "snippet": current_snippet
            }
        )
        return update_request.execute()
    except Exception as e:
        print(f"Error updating video title: {e}")
        return None

def main():
    print(f"\n{'='*50}")
    print(f"Script started at {datetime.datetime.now()}")
    print(f"{'='*50}\n")

    # Validate environment variables
    if not VIDEO_ID:
        print("Error: VIDEO_ID environment variable not set.")
        return

    print(f"Using video ID: {VIDEO_ID}")

    # Initialize YouTube API
    print("\nStarting YouTube API authentication...")
    youtube = get_authenticated_service()
    if not youtube:
        print("Failed to authenticate with YouTube API.")
        return

    print("Authenticated successfully with YouTube API.")

    try:
        # Get latest comment
        print("\nFetching the latest comment...")
        comment_response = get_latest_comment(youtube, VIDEO_ID)
        if not comment_response or not comment_response.get("items"):
            print("No comments found on the video.")
            return

        # Extract commenter name
        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "UnknownUser")
        print(f"Latest commenter: {commenter_display_name}")

        # Get video details
        print("\nFetching video details...")
        video_response = get_video_details(youtube, VIDEO_ID)
        if not video_response or not video_response.get("items"):
            print("Video details not found or insufficient permissions.")
            return

        # Extract view count
        view_count = video_response["items"][0]["statistics"].get("viewCount", "0")
        print(f"Current view count: {view_count}")

        # Create new title
        new_title = f"This Short has {view_count} views thanks to {commenter_display_name} #shorts"
        print(f"New title will be: {new_title}")

        # Get current snippet
        current_snippet = video_response["items"][0]["snippet"]
        old_title = current_snippet.get("title", "Unknown")
        print(f"Current title is: {old_title}")

        # Only update if title is different
        if old_title == new_title:
            print("\nTitle is already up to date. No changes needed.")
            return

        # Update title
        current_snippet["title"] = new_title
        print("\nUpdating video title...")
        update_response = update_video_title(youtube, VIDEO_ID, new_title, current_snippet)
        
        if update_response:
            print(f"\nSuccess! Updated video title to: {new_title}")
        else:
            print("\nFailed to update video title.")

    except HttpError as e:
        print(f"\nHTTP error occurred: {e.resp.status} {e.content}")
        if hasattr(e, 'error_details'):
            print(f"Error details: {e.error_details}")
    except Exception as e:
        print(f"\nUnexpected error occurred: {type(e).__name__}: {str(e)}")

    print(f"\n{'='*50}")
    print(f"Script completed at {datetime.datetime.now()}")
    print(f"{'='*50}\n")

if __name__ == "__main__":
    main()
