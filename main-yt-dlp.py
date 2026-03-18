from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_DIR = "./downloads"


# 🔥 Common yt-dlp base config (reuse everywhere)
def get_ydl_opts(extra_opts=None):
    base_opts = {
        "quiet": True,

        # 🔥 Fix 403 (most important)
        "http_headers": {
            "User-Agent": "com.google.android.youtube/17.31.35 (Linux; U; Android 11)"
        },

        # 🔥 Use Android client (very important)
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"]
            }
        }
    }

    if extra_opts:
        base_opts.update(extra_opts)

    return base_opts


def get_video_info(url):
    try:
        ydl_opts = get_ydl_opts({"skip_download": True})

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        video_info = {
            "title": info.get("title"),
            "author": info.get("uploader"),
            "length": info.get("duration"),
            "views": info.get("view_count"),
            "description": info.get("description"),
            "publish_date": info.get("upload_date"),
        }

        return video_info, None

    except Exception as e:
        return None, str(e)


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


def download_video(url, resolution):
    try:
        height = resolution.replace("p", "")

        # 🔥 Try preferred format first
        ydl_opts = get_ydl_opts({
            "format": f"bestvideo[height<={height}]+bestaudio/best",
            "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s/%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
        })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            return True, None

        except Exception:
            # 🔥 Fallback to best (very important)
            fallback_opts = get_ydl_opts({
                "format": "best",
                "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s/%(title)s.%(ext)s"),
            })

            with yt_dlp.YoutubeDL(fallback_opts) as ydl:
                ydl.download([url])

            return True, f"{resolution} not available, downloaded best quality instead"

    except Exception as e:
        return False, str(e)


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

    success, error = download_video(url, resolution)

    if success:
        return jsonify({
            "message": "Download completed",
            "note": error  # might contain fallback info
        }), 200
    else:
        return jsonify({"error": error}), 500


if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 8888))
    app.run(host="0.0.0.0", port=port)
