from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import pymupdf
from dotenv import load_dotenv
import os
from urllib.parse import urlparse, parse_qs

# Load HF_TOKEN from backend/.env
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))
HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not found. Please set it in backend/.env")

app = Flask(__name__)
cors = CORS(app)

# Single shared client — pointed at Hugging Face Inference API
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN
)

# Maximum characters of source text to send to the model
MAX_TEXT_LENGTH = 12000

import re
from collections import Counter

def extractive_summary(text, max_sentences=3):
    """Fallback extractive summarizer in case the external API is unreachable or rate-limited."""
    # Split text into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    if len(sentences) <= max_sentences:
        return text.strip()
    words = re.findall(r'\w+', text.lower())
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
        'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'that', 'this',
        'it', 'as', 'from', 'be', 'have', 'has', 'had', 'not', 'can', 'will'
    }
    keywords = [w for w in words if w not in stopwords and len(w) > 2]
    freq = Counter(keywords)
    scored = []
    for i, s in enumerate(sentences):
        score = sum(freq.get(w, 0) for w in re.findall(r'\w+', s.lower()))
        scored.append((score, i, s))
    top = sorted(sorted(scored, key=lambda x: x[0], reverse=True)[:max_sentences], key=lambda x: x[1])
    return ' '.join(s for _, _, s in top)

def get_summary(prompt, raw_text=None):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b:fastest",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes content"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"[Warning] Hugging Face API call failed ({type(e).__name__}: {e}). Using resilient fallback summarizer.")
        source_text = raw_text if raw_text else prompt
        return extractive_summary(source_text)

@app.route('/summarise/text', methods=['POST'])
@app.route('/summarize/text', methods=['POST'])
def summarize_text():
    try:
        data = request.get_json() or {}
        text = data.get('text', '').strip()
        if not text:
            return jsonify({'error': 'No text provided.'}), 400
        text = text[:MAX_TEXT_LENGTH]
        prompt = f"summarize the following text:\n{text}"
        summary = get_summary(prompt, raw_text=text)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': f'Text summarization failed: {str(e)}'}), 500

@app.route('/summarize/pdf', methods=['POST'])
def summarize_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No PDF file uploaded.'}), 400
        file = request.files['file']
        doc = pymupdf.open(stream=file.read(), filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        text = text.strip()
        if not text:
            return jsonify({'error': 'Could not extract any text from the PDF.'}), 400
        text = text[:MAX_TEXT_LENGTH]
        prompt = f"summarize the following pdf text:\n{text}"
        summary = get_summary(prompt, raw_text=text)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': f'PDF summarization failed: {str(e)}'}), 500


def extract_video_id(url):
    """Extract YouTube video ID from any URL format or bare 11-char ID."""
    url = url.strip()
    if re.fullmatch(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    patterns = [
        r'(?:v=|\/v\/|youtu\.be\/|\/embed\/|\/shorts\/|\/live\/)([a-zA-Z0-9_-]{11})',
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    return None


@app.route('/summarize/youtube', methods=['POST'])
@app.route('/summarise/youtube', methods=['POST'])
def summarize_youtube():
    try:
        data = request.get_json() or {}
        url = data.get('url', '').strip()
        if not url:
            return jsonify({'error': 'No YouTube URL provided.'}), 400

        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL. Please provide a valid YouTube link or video ID.'}), 400

        api = YouTubeTranscriptApi()
        transcript = None

        # 1. Try default fetch (English)
        try:
            transcript = api.fetch(video_id)
        except Exception:
            # 2. Fallback: retrieve any available manual or auto-generated transcript
            try:
                transcript_list = api.list(video_id)
                for t in transcript_list:
                    transcript = t.fetch()
                    break
            except Exception:
                pass

        if not transcript:
            return jsonify({'error': 'No captions or transcript available for this video. Please try a video that has closed captions enabled.'}), 400

        text = " ".join(item.text if hasattr(item, 'text') else item.get('text', '') for item in transcript)
        text = text[:MAX_TEXT_LENGTH]
        prompt = f"summarize the following youtube video transcript:\n{text}"
        summary = get_summary(prompt, raw_text=text)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': f'YouTube summarization failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)