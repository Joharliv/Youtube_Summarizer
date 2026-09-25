#  Video Digest - AI YouTube Summarizer

<div align="center">

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge\&logo=flask\&logoColor=white)](https://flask.palletsprojects.com/)
[![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge\&logo=javascript\&logoColor=black)](https://developer.mozilla.org/en-US/docs/Web/JavaScript)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge\&logo=html5\&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge\&logo=css3\&logoColor=white)](https://developer.mozilla.org/en-US/docs/Web/CSS)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-8E75B2?style=for-the-badge\&logo=google\&logoColor=white)](https://ai.google.dev/)
[![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge)](https://groq.com/)

> **Turn long YouTube videos into concise AI-powered summaries and ask questions about the video.**
</div>

## 🚀 Live Demo

**[Try Video Digest](https://youtube-summarizer-s0lk.onrender.com)**

## ✨ Features

* 🎬 Generate AI summaries from YouTube videos
* 💬 Ask questions about the video through an AI chat
* 🌍 Generate summaries and answers in multiple languages
* 📝 Automatically retrieve YouTube transcripts
* 🎙️ Use Whisper for videos without available captions
* ⚡ Gemini-powered summarization and Q&A
* 📱 Responsive dark-themed interface

## 🛠️ Tech Stack

**Frontend:** HTML, CSS, JavaScript
**Backend:** Python, Flask
**AI:** Google Gemini, Groq Whisper
**Video/Audio:** YouTube Transcript API, yt-dlp, FFmpeg
**Deployment:** Render

## 📁 Project Structure

```text
Youtube Summarizer/
├── app.py
├── requirements.txt
├── templates/
│   └── index.html
└── static/
    ├── script.js
    └── style.css
```

## ⚙️ Run Locally

```bash
git clone https://github.com/YOUR_USERNAME/Youtube-Summarizer.git
cd Youtube-Summarizer
pip install -r requirements.txt
python app.py
```

Create a `.env` file with:

```env
GEMINI_API_KEY=your_gemini_api_key
GROQ_API_KEY=your_groq_api_key
```

Then open:

```text
http://127.0.0.1:5000
```

## 👩‍💻 Developer

**Liv Johar**
B.E. Computer Science Engineering — Artificial Intelligence & Machine Learning
Chitkara University, Punjab

---

## 📌 Status

**Completed**
