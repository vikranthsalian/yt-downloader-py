from flask import Flask, request, jsonify
from pytubefix import YouTube
from pytubefix.cli import on_progress
import re
import os

app = Flask(__name__)

def create_yt(url, po_token=None):
    """
    Helper to create a YouTube instance with optional po_token.
    """
    # proxy = {
    #     "http": "socks5://127.0.0.1:9050",
    #     "https": "socks5://127.0.0.1:9050"
    #     }
    
    # url = "url"
    
   
    yt = YouTube(url, on_progress_callback = on_progress)
    print(yt.title)
    return yt


def download_video(url, resolution, po_token=None):
    try:
        yt = create_yt(url, po_token)

        # Debug: Print all available streams
        print(f"Available progressive streams for {url}:")
        for stream in yt.streams.filter(progressive=True, file_extension='mp4'):
            print(f"  - {stream.resolution} - {stream.mime_type}")
        
        stream = yt.streams.filter(
            progressive=True,
            file_extension='mp4',
            resolution=resolution
        ).first()

        if stream:
            out_dir = f"./downloads/{url.split('v=')[1].split('&')[0]}"
            os.makedirs(out_dir, exist_ok=True)
            stream.download(output_path=out_dir)
            return True, None
        else:
            print(f"\nTrying non-progressive streams:")
            for stream in yt.streams.filter(file_extension='mp4', res=resolution):
                print(
                    f"  - {stream.resolution} - {stream.mime_type} "
                    f"- audio: {stream.includes_audio_track}"
                )
            
            return False, "Video with the specified resolution not found."
    except Exception as e:
        return False, str(e)

def get_video_info(url, po_token=None):
    try:
        yt = create_yt(url, po_token)
        stream = yt.streams.first()
        video_info = {
            "title": yt.title,
            "author": yt.author,
            "length": yt.length,
            "views": yt.views,
            "description": yt.description,
            "publish_date": yt.publish_date,
        }
        return video_info, None
    except Exception as e:
        return None, str(e)

def is_valid_youtube_url(url):
    pattern = r"^(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+(&\S*)?$"
    return re.match(pattern, url) is not None

@app.route('/download/<resolution>', methods=['POST'])
def download_by_resolution(resolution):
    data = request.get_json() or {}
    url = data.get('url')
    po_token = data.get('po_token')  # optional

    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    # if not is_valid_youtube_url(url):
    #     return jsonify({"error": "Invalid YouTube URL."}), 400
    
    success, error_message = download_video(url, resolution, po_token)
    
    if success:
        return jsonify({"message": f"Video with resolution {resolution} downloaded successfully."}), 200
    else:
        return jsonify({"error": error_message}), 500

@app.route('/video_info', methods=['POST'])
def video_info():
    data = request.get_json() or {}
    url = data.get('url')
    po_token = data.get('po_token')  # optional
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    info, error_message = get_video_info(url, po_token)
    
    if info:
        return jsonify(info), 200
    else:
        return jsonify({"error": error_message}), 500

@app.route('/available_resolutions', methods=['POST'])
def available_resolutions():
    data = request.get_json() or {}
    url = data.get('url')
    po_token = data.get('po_token')  # optional
    
    if not url:
        return jsonify({"error": "Missing 'url' parameter in the request body."}), 400

    if not is_valid_youtube_url(url):
        return jsonify({"error": "Invalid YouTube URL."}), 400
    
    try:
        yt = create_yt(url, po_token)
        progressive_resolutions = list(set([
            stream.resolution 
            for stream in yt.streams.filter(progressive=True, file_extension='mp4')
            if stream.resolution
        ]))
        all_resolutions = list(set([
            stream.resolution 
            for stream in yt.streams.filter(file_extension='mp4')
            if stream.resolution
        ]))
        return jsonify({
            "progressive": sorted(progressive_resolutions),
            "all": sorted(all_resolutions)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
