from flask import Flask, request, jsonify
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_DIR = "./downloads"


def get_video_info(url):
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True
        }

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
        ydl_opts = {"quiet": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        resolutions = list(set([
            f"{f.get('height')}p"
            for f in info.get("formats", [])
            if f.get("height")
        ]))

        return sorted(resolutions), None

    except Exception as e:
        return None, str(e)


def download_video(url, resolution):
    try:
        height = resolution.replace("p", "")

     ydl_opts = {
        "format": f"bestvideo[height<={height}]+bestaudio/best",
        "outtmpl": os.path.join(DOWNLOAD_DIR, "%(id)s/%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
    
        # 🔥 Fix 403
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
     }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return True, None

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
        return jsonify({"message": f"Downloaded in {resolution}"}), 200
    else:
        return jsonify({"error": error}), 500


if __name__ == "__main__":
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    port = int(os.environ.get("PORT", 8888))
    app.run(host="0.0.0.0", port=port)
