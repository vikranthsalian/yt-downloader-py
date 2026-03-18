from flask import Flask, request, jsonify
import yt_dlp
import os
import re
import sys
import threading

app = Flask(__name__)

DOWNLOAD_DIR = "./downloads"

# 🔥 In-memory progress store
DOWNLOAD_PROGRESS = {}


# 🔧 Common yt-dlp config
def get_ydl_opts(extra_opts=None):
    base_opts = {
        "quiet": True,

        # 🔥 Fix 403
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11)"
        },

        # 🔥 Android client
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }

    if extra_opts:
        base_opts.update(extra_opts)

    return base_opts


# 🎯 Extract video ID
def get_video_id(url):
    match = re.search(r"v=([\w-]+)", url)
    return match.group(1) if match else "unknown"


# 📊 Progress hook
def progress_hook(video_id):
    def hook(d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%').strip()
            speed = d.get('_speed_str', '').strip()
            eta = d.get('_eta_str', '').strip()

            DOWNLOAD_PROGRESS[video_id] = percent

            print(f"[{video_id}] {percent} | Speed: {speed} | ETA: {eta}")
            sys.stdout.flush()

        elif d['status'] == 'finished':
            DOWNLOAD_PROGRESS[video_id] = "100%"
            print(f"[{video_id}] Download completed ✅")
            sys.stdout.flush()

    return hook


# 📄 Video info
def get_video_info(url):
    try:
        ydl_opts = get_ydl_opts({"skip_download": True})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        return {
            "title": info.get("title"),
            "author": info.get("uploader"),
            "length": info.get("duration"),
            "views": info.get("view_count"),
            "description": info.get("description"),
            "publish_date": info.get("upload_date"),
        }, None

    except Exception as e:
        return None, str(e)


# 📺 Available resolutions
def get_available_resolutions(url):
    try:
        ydl_opts = get_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        resolutions = sorted(set([
            f"{f.get('height')}p"
            for f in info.get("formats", [])
            if f.get("height")
        ]))

        return resolutions, None

    except Exception as e:
        return None, str(e)


# ⬇️ Actual download logic (runs in thread)
def download_video(url, resolution):
    try:
        height = resolution.replace("p", "")
        video_id = get_video_id(url)

        DOWNLOAD_PROGRESS[video_id] = "0%"
        output_path = os.path.join(DOWNLOAD_DIR, resolution, "%(id)s")
        os.makedirs(output_path, exist_ok=True)

        ydl_opts = get_ydl_opts({
            "format": f"bestvideo[height<={height}]+bestaudio/best/best",
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [progress_hook(video_id)],
        })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception:
            # 🔥 fallback
            fallback_opts = get_ydl_opts({
                "format": "best",
                "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s/%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook(video_id)],
            })

            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])

    except Exception as e:
        print(f"[ERROR] {e}")


# 🌐 Routes

@app.route("/")
def home():
    return "YT-DLP API running 🚀"


@app.route("/video_info", methods=["POST"])
def video_info():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    info, error = get_video_info(url)

    if info:
        return jsonify(info), 200
    else:
        return jsonify({"error": error}), 500


@app.route("/available_resolutions", methods=["POST"])
def available_resolutions():
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    resolutions, error = get_available_resolutions(url)

    if resolutions:
        return jsonify({"available_resolutions": resolutions}), 200
    else:
        return jsonify({"error": error}), 500


@app.route("/download/<resolution>", methods=["POST"])
def download(resolution):
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    video_id = get_video_id(url)

    # 🔥 Run in background thread
    thread = threading.Thread(
        target=download_video,
        args=(url, resolution),
        daemon=True
    )
    thread.start()

    return jsonify({
        "message": "Download started",
        "video_id": video_id
    }), 200


@app.route("/progress/<video_id>", methods=["GET"])
def get_progress(video_id):
    return jsonify({
        "video_id": video_id,
        "progress": DOWNLOAD_PROGRESS.get(video_id, "0%")
    })


# 🚀 Run server
if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 8888))
    app.run(host="0.0.0.0", port=port)
