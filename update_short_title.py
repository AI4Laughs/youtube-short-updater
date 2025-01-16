def main():
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

        top_comment_snippet = comment_response["items"][0]["snippet"]["topLevelComment"]["snippet"]
        commenter_display_name = top_comment_snippet.get("authorDisplayName", "Someone")
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

        view_count = video_response["items"][0]["statistics"].get("viewCount", "0")
        print(f"View count: {view_count}")

        # Create new title
        new_title = f"This Short has {view_count} views thanks to {commenter_display_name} #shorts"
        print(f"New title: {new_title}")

        # Preserve existing snippet data
        current_snippet = video_response["items"][0]["snippet"]
        current_snippet["title"] = new_title

        # Update the video
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
