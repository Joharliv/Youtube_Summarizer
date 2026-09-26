import glob
import os
import re
import shutil
import subprocess
import tempfile

import yt_dlp
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from google import genai
from google.genai import types
from groq import Groq
from youtube_transcript_api import YouTubeTranscriptApi

load_dotenv()

app = Flask(__name__)
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))  # summaries + chat
groq = Groq(api_key=os.getenv("GROQ_API_KEY"))              # speech-to-text
# Model names change often; if this one errors, copy a current name from Google AI Studio.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
MAX_CHARS = 120_000     # cap very long transcripts
MAX_MINUTES = 90        # limit for videos WITHOUT captions (protects the free limits)
transcripts = {}        # in-memory cache: video_id -> transcript text

# Path to a YouTube cookies.txt file (Netscape format), used to authenticate
# yt-dlp's requests so YouTube doesn't treat them as bot traffic. On Render,
# upload the file as a "Secret File" named youtube_cookies.txt; it will be
# mounted at /etc/secrets/youtube_cookies.txt automatically. Locally this
# path just won't exist, and the code below skips it, which is fine.
COOKIE_FILE = os.getenv("YOUTUBE_COOKIE_FILE", "/etc/secrets/youtube_cookies.txt")


def extract_video_id(url):
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})", url or "")
    return m.group(1) if m else None


def captions_transcript(video_id):
    available = YouTubeTranscriptApi().list(video_id)
    try:
        chosen = available.find_transcript(["en", "hi", "pa"])
    except Exception:
        chosen = next(iter(available))  # any language; Gemini handles translation
    return " ".join(s.text for s in chosen.fetch())


def whisper_transcript(url):
    """No captions: download the audio, cut it into 10-minute pieces, transcribe each."""
    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "format": "bestaudio/best",
            "outtmpl": f"{tmp}/audio.%(ext)s",
            "quiet": True,
            "no_warnings": True,

            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web_safari"]
                }
            },

            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "32"
                }
            ],

            "postprocessor_args": [
                "-ac", "1",
                "-ar", "16000"
            ],
        }

        # Render's Secret Files are mounted read-only, but yt-dlp needs to write
        # back to the cookie file (YouTube rotates session cookies on use). So
        # copy it into this request's writable temp dir first, and point yt-dlp
        # at that copy instead of the read-only original.
        if os.path.exists(COOKIE_FILE):
            writable_cookie_file = f"{tmp}/youtube_cookies.txt"
            shutil.copyfile(COOKIE_FILE, writable_cookie_file)
            opts["cookiefile"] = writable_cookie_file
            print(f"[yt-dlp] Using cookie file (writable copy): {writable_cookie_file}")
        else:
            print(f"[yt-dlp] No cookie file found at: {COOKIE_FILE}")

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if (info.get("duration") or 0) > MAX_MINUTES * 60:
                raise ValueError(f"Videos without captions can be up to {MAX_MINUTES} minutes long.")
            ydl.download([url])
        subprocess.run(
            ["ffmpeg", "-y", "-i", f"{tmp}/audio.mp3", "-f", "segment",
             "-segment_time", "600", "-c", "copy", f"{tmp}/part_%03d.mp3"],
            check=True, capture_output=True,
        )
        texts = []
        for path in sorted(glob.glob(f"{tmp}/part_*.mp3")):
            with open(path, "rb") as f:
                result = groq.audio.transcriptions.create(
                    file=(os.path.basename(path), f.read()), model="whisper-large-v3-turbo"
                )
            texts.append(result.text)
        return " ".join(texts)


def get_transcript(video_id):
    if video_id in transcripts:
        return transcripts[video_id]
    try:
        text = captions_transcript(video_id)
    except Exception:
        text = whisper_transcript(f"https://www.youtube.com/watch?v={video_id}")
    text = text[:MAX_CHARS]
    transcripts[video_id] = text
    return text


def transcript_or_error(video_id):
    try:
        return get_transcript(video_id), None
    except ValueError as e:
        return None, str(e)
    except FileNotFoundError:
        return None, "ffmpeg is not installed, so videos without captions can't be processed."
    except yt_dlp.utils.DownloadError as e:
        # Log the real error server-side so we can diagnose it (check Render logs),
        # while still showing users a friendlier message than the raw traceback.
        print(f"[yt-dlp DownloadError] {e}")
        return None, (
            "Couldn't download the audio for this video right now (YouTube is blocking "
            "the request). This can happen even when the video has no captions available. "
            "Please try a different video, or try again later."
        )
    except Exception as e:
        return None, f"Couldn't get captions or audio for this video: {e}"


def ask_ai(system, messages):
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
    ]
    reply = gemini.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return reply.text


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/summarize")
def summarize():

    data = request.get_json(force=True)

    video_id = extract_video_id(data.get("url"))
    language = (data.get("language") or "English").strip()

    if not video_id:
        return jsonify(error="That doesn't look like a YouTube link."), 400

    text, err = transcript_or_error(video_id)

    if err:
        return jsonify(error=err), 422

    system = (
        f"You summarize YouTube videos from their transcript. "
        f"The user's selected output language is: {language}. "

        f"IMPORTANT LANGUAGE RULE: "
        f"Write the ENTIRE response in {language}. "
        f"Do not write the summary in English unless {language} is English. "
        f"Translate the overview, headings, key points, bullet points, and final takeaway "
        f"into {language}. "

        "Keep proper nouns, names, brand names, and necessary technical terms unchanged "
        "when translating them would be unnatural. "

        "Structure the response as follows: "
        "a 2-3 sentence overview, "
        "then 5-8 key points using '- ' bullets "
        "(use **bold** for important terms), "
        "then one final takeaway sentence. "

        f"All of these sections must be written in {language}."
    )

    try:

        summary = ask_ai(
            system,
            [
                {
                    "role": "user",
                    "content": f"Transcript:\n{text}"
                }
            ]
        )

    except Exception as e:

        return jsonify(
            error=f"AI request failed: {e}"
        ), 502

    return jsonify(
        video_id=video_id,
        summary=summary
    )

@app.post("/api/chat")
def chat():
    data = request.get_json(force=True)
    video_id = data.get("video_id")
    question = (data.get("question") or "").strip()
    language = (data.get("language") or "English").strip()
    history = data.get("history") or []
    if not video_id or not question:
        return jsonify(error="Missing video or question."), 400

    text, err = transcript_or_error(video_id)
    if err:
        return jsonify(error=err), 422

    system = (
        "You answer questions about one YouTube video, using only its transcript below. "
        f"Reply in {language}. If the transcript doesn't cover the question, say so plainly.\n\n"
        f"Transcript:\n{text}"
    )
    messages = [{"role": m["role"], "content": m["content"]} for m in history[-10:]]
    messages.append({"role": "user", "content": question})
    try:
        answer = ask_ai(system, messages)
    except Exception as e:
        return jsonify(error=f"AI request failed: {e}"), 502
    return jsonify(answer=answer)


if __name__ == "__main__":
    app.run(debug=True)