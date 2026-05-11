# Markdown to Speech Converter

A modern web-based application that converts Markdown content into high-quality speech audio files using Google Text-to-Speech (gTTS) and optional AI optimization with OpenAI GPT-4o.

## Features

- **Upload or paste** Markdown files (`.md`, `.markdown`, `.txt`)
- **11 languages**: English, German, French, Spanish, Italian, Portuguese, Dutch, Russian, Chinese, Japanese, Korean
- **AI optimization** via OpenAI GPT-4o — expands abbreviations, converts numbers to words, adds pronunciation guides
- **Smart caching** — avoids redundant OpenAI API calls (30-day cache)
- **Chunked processing** — handles large documents reliably
- **Audio preview** — listen directly in the browser and download as MP3
- **Encrypted API key storage** — your OpenAI key is stored locally, encrypted

## Requirements

- Python 3.8+
- FFmpeg (for combining audio chunks)
- OpenAI API key (optional, for AI optimization)

## Quick Start

```bash
# Install FFmpeg (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Run the app
chmod +x run_tts.sh
./run_tts.sh
```

The app opens at http://localhost:8501

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run tts_streamlit.py
```

## Usage

1. Open the app in your browser
2. Upload a `.md` file or paste Markdown content
3. (Optional) Enter your OpenAI API key in the sidebar to enable GPT-4o optimization
4. Select language and chunk size
5. Click **Convert to Speech**
6. Download or preview the generated MP3

## Writing Instructions in Markdown

The app accepts standard Markdown. Tips for best speech output:

- Use headings (`#`, `##`) to structure sections — they are stripped before synthesis
- Write numbers as words when precision matters (e.g., "one hundred" instead of "100")
- Avoid tables and code blocks unless using AI optimization (it converts them to speech-friendly text)
- Use plain prose paragraphs for clearest output

## Project Source

Based on [dmikey/markdown-to-speech](https://github.com/dmikey/markdown-to-speech).
