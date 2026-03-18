from flask import Flask, request, jsonify
import yt_dlp
import os
import re
import sys
import threading

app = Flask(__name__)

DOWNLOAD_DIR = "./downloads"

# 🔥 Stores
DOWNLOAD_PROGRESS = {}
DOWNLOAD_RESULT = {}


# 🔧 Common yt-dlp config
def get_ydl_opts(extra_opts=None):
    base_opts = {
        "quiet": True,
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11)"
        },
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


# ⬇️ Download logic
def download_video(url, resolution):
    actual_resolution = None  # ✅ FIX: define at top

    try:
        height = resolution.replace("p", "")
        video_id = get_video_id(url)

        DOWNLOAD_PROGRESS[video_id] = "0%"

        # ✅ Proper path handling
        video_dir = os.path.join(DOWNLOAD_DIR, resolution)
        output_path = os.path.join(video_dir, "%(id)s")
        os.makedirs(output_path, exist_ok=True)

        # 🎯 Capture actual resolution
        def result_hook(d):
            nonlocal actual_resolution
            if d['status'] == 'finished':
                info = d.get("info_dict", {})
                actual_resolution = f"{info.get('height')}p"

        ydl_opts = get_ydl_opts({
            "format": f"bv*[height={height}]+ba/b",
            "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "progress_hooks": [progress_hook(video_id), result_hook],
        })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception:
            print(f"[{video_id}] Fallback triggered")

            fallback_opts = get_ydl_opts({
                "format": f"bv*[height<={height}]+ba/b",
                "outtmpl": os.path.join(output_path, "%(title)s.%(ext)s"),
                "progress_hooks": [progress_hook(video_id), result_hook],
            })

            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])

        # 🔥 Store result
        DOWNLOAD_RESULT[video_id] = {
            "requested_resolution": resolution,
            "actual_resolution": actual_resolution or "unknown"
        }

    except Exception as e:
        print(f"[ERROR] {e}")


# 🌐 Routes

@app.route("/")
def home():
    return "YT-DLP API running 🚀"


@app.route("/download/<resolution>", methods=["POST"])
def download(resolution):
    data = request.get_json() or {}
    url = data.get("url")

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    video_id = get_video_id(url)

    # 🔥 Background thread
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


@app.route("/result/<video_id>", methods=["GET"])
def get_result(video_id):
    return jsonify(
        DOWNLOAD_RESULT.get(video_id, {
            "message": "Download in progress or not found"
        })
    )


# 🚀 Run server
if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 8888))
    app.run(host="0.0.0.0", port=port)
