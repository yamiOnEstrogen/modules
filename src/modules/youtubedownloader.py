import os
import sys

import requests
from googleapiclient.discovery import build
from pytube import Playlist, YouTube
from tqdm import tqdm

# Module Information
info = {
    "name": "YouTube Downloader",
    "description": "Download YouTube videos.",
    "author": "Yami",
    "version": "1.0.0",
    "dependencies": ["pytube", "google-api-python-client", "tqdm"],
}

# Constants
FALLBACK_RES = "720p"
DEFAULT_RES = "1080p"
DEFAULT_FOLDER = None
MAX_RETRIES = 3



def sanitize_filename(title):
    """Sanitize the title of the video."""
    invalid_chars = ["\\", "/", ":", "*", "?", '"', "<", ">", "|"]
    for char in invalid_chars:
        title = title.replace(char, "_")
    return title


def get_video_data(video_url):
    """Get data of the video."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    youtube = build("youtube", "v3", developerKey=api_key)
    video_id = YouTube(video_url).video_id
    request = youtube.videos().list(part="snippet", id=video_id)
    response = request.execute()
    return response["items"][0]["snippet"] if response["items"] else None

def get_playlist_title(url):
    """Get the title of the playlist."""
    api_key = os.environ.get("YOUTUBE_API_KEY")
    youtube = build("youtube", "v3", developerKey=api_key)
    playlist_id = Playlist(url).playlist_id
    request = youtube.playlists().list(part="snippet", id=playlist_id)
    response = request.execute()
    return (
        response["items"][0]["snippet"]["localized"]["title"]
        if response["items"]
        else None
    )


def plexify(url, folder=DEFAULT_FOLDER):
    data = get_video_data(url)
    if data is None:
        raise ValueError("Unable to retrieve video data.")
    title = sanitize_filename(data["title"])
    thumbnail_url = data["thumbnails"]["maxres"]["url"]
    thumbnail_filename = "poster.jpg"

    if folder:
        os.makedirs(os.path.join(folder, title), exist_ok=True)
        thumbnail_filename = os.path.join(folder, title, thumbnail_filename)

        print("Downloading thumbnail...")
        thumbnail_response = requests.get(thumbnail_url, stream=True, timeout=10)
        with open(thumbnail_filename, "wb") as file:
            for data in thumbnail_response.iter_content(chunk_size=1024):
                if data:
                    file.write(data)
                else:
                    break
        print(f"Thumbnail downloaded: {thumbnail_filename}")

        # Download video and place it in the folder
        download_single_video(url, os.path.join(folder, title))
        
    else:
        raise ValueError("Folder name not provided.")

def download_playlist_videos(playlist_url, folder=DEFAULT_FOLDER, res=DEFAULT_RES):
    """Download videos from a YouTube playlist."""
    try:
        playlist_title = get_playlist_title(playlist_url)
        if playlist_title is None:
            raise ValueError("Unable to retrieve playlist title.")
        print(f"Playlist Title: {playlist_title}")

        if not folder:
            folder = playlist_title

        os.makedirs(folder, exist_ok=True)

        playlist = Playlist(playlist_url)
        for video_url in playlist.video_urls:
            download_single_video(video_url, folder, res)
    except Exception as e:
        print(f"Error downloading playlist videos: {e}")


def download_single_video(video_url, folder=DEFAULT_FOLDER, res=DEFAULT_RES):
    """Download a single YouTube video."""
    try:
        yt = YouTube(video_url)
        video_stream = yt.streams.filter(
            progressive=True, file_extension="mp4", resolution=res
        ).first()

        if video_stream is None:
            print(
                f"Video with resolution '{res}' not available. Downloading with fallback resolution: {FALLBACK_RES}."
            )
            res = FALLBACK_RES
            video_stream = yt.streams.filter(
                progressive=True, file_extension="mp4", resolution=FALLBACK_RES
            ).first()

        if video_stream is None:
            raise ValueError("No suitable video streams found.")
        title = sanitize_filename(yt.title)
        filepath = os.path.join(folder, f"{title}.mp4") if folder else f"{title}.mp4"

        response = requests.get(video_stream.url, stream=True, timeout=10)
        total_size_in_bytes = int(response.headers.get("content-length", 0))
        block_size = 1024

        with tqdm(
            total=total_size_in_bytes,
            unit="iB",
            unit_scale=True,
            desc=f"Downloading '{yt.title}' :: {res}",
        ) as bar, open(filepath, "wb") as file:
            for data in response.iter_content(chunk_size=block_size):
                if data:
                    bar.update(len(data))
                    file.write(data)

        print(f"\nDownloaded: {yt.title} at {res}")
    except requests.exceptions.ChunkedEncodingError as e:
        print(f"Error downloading video: {e}. Retrying...")
        download_single_video(video_url, folder, res)
    except Exception as e:
        print(f"Error downloading video: {e}")


def main():
    """Main function to initiate video download."""
    youtube_api_key = os.environ.get("YOUTUBE_API_KEY")
    if not youtube_api_key:
        print(
            "YouTube API Key not found. Please set the environment variable 'YOUTUBE_API_KEY'."
        )
        sys.exit(1)

    url = input("Enter YouTube URL(s) separated by commas: ")
    folder = input("Enter folder name (leave blank for default): ")
    res = input("Enter resolution (leave blank for default): ")
    use_plex_format = input("Use Plex format? (y/n): ")

    if not res:
        res = DEFAULT_RES
    if not folder:
        folder = DEFAULT_FOLDER

    if not folder and not DEFAULT_FOLDER:
        folder = input("Enter folder name: ")

    urls = url.split(",")
    for single_url in urls:
        single_url = single_url.strip()
        if "playlist" in single_url.lower():
            download_playlist_videos(single_url, folder, res)
        else:
            if use_plex_format.lower() == "y":
                plexify(single_url, folder)
            else:
                download_single_video(single_url, folder, res)
