# 🎬 YT-DLP Flask Downloader API

A lightweight Flask-based backend service to download YouTube videos using **yt-dlp** with:

* ⚡ Background downloads (non-blocking)
* 📊 Real-time progress tracking
* 🎯 Resolution-based download
* 🔁 Smart fallback handling
* 📁 Organized file storage

---

## 🚀 Features

* Download videos in specific resolution (`720p`, `1080p`, etc.)
* Track download progress in real-time
* Get actual downloaded resolution
* Runs downloads asynchronously
* Handles unavailable resolutions automatically

---

# 📦 Installation & Setup

---

## 🟢 Option 1: Clone & Run (Recommended)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/vikranthsalian/yt-downloader-py.git
cd yt-downloader-py
```

---

### 2️⃣ Create virtual environment (optional but recommended)

```bash
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
```

---

### 3️⃣ Install dependencies

```bash
pip install flask yt-dlp
```

---

### 4️⃣ Run the server

```bash
python app.py
```

Server will start at:

```text
http://127.0.0.1:8888
```

---

## ⚡ Option 2: Run Without Cloning

### 1️⃣ Install dependencies

```bash
pip install flask yt-dlp
```

---

### 2️⃣ Run directly from GitHub

```bash
curl -s https://raw.githubusercontent.com/vikranthsalian/yt-downloader-py/main/app.py | python3
```

---

### 🔥 Optional: Create global command

```bash
nano ~/yt-downloader
```

Paste:

```bash
#!/bin/bash
curl -s https://raw.githubusercontent.com/vikranthsalian/yt-downloader-py/main/app.py | python3
```

Then:

```bash
chmod +x ~/yt-downloader
sudo mv ~/yt-downloader /usr/local/bin/
```

Now run:

```bash
yt-downloader
```

---

# 📡 API Usage

---

## 🔽 1. Start Download

```bash
curl -X POST http://127.0.0.1:8888/download/1080p \
-H "Content-Type: application/json" \
-d '{"url":"https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### ✅ Response

```json
{
  "message": "Download started",
  "video_id": "VIDEO_ID"
}
```

---

## 📊 2. Check Progress

```bash
curl http://127.0.0.1:8888/progress/VIDEO_ID
```

### ✅ Response

```json
{
  "video_id": "VIDEO_ID",
  "progress": "45.3%"
}
```

---

## 📄 3. Get Result

```bash
curl http://127.0.0.1:8888/result/VIDEO_ID
```

### ✅ Response

```json
{
  "requested_resolution": "1080p",
  "actual_resolution": "720p"
}
```

---

# 📁 Downloaded Files

```text
downloads/
 └── 1080p/
      └── video files
```

---

# ⚠️ Notes

* Some resolutions may not be available → fallback will be used
* Downloads run in background threads
* Progress is stored in memory (resets on restart)
* Works best with standard YouTube URLs

---

# 🧠 Tips

* Replace `VIDEO_ID` with actual video ID
* Example:

  ```
  https://www.youtube.com/watch?v=dQw4w9WgXcQ
  ```

---

# 🔥 Future Improvements

* Download queue system
* Cancel download API
* File metadata (size, duration)
* Flutter frontend (🔥)
* Docker support

---

# 📜 Disclaimer

This project is for educational purposes only.
Ensure compliance with YouTube’s Terms of Service before using.
