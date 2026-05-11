from flask import Flask, request, send_file, render_template_string
import markdown
from gtts import gTTS
from bs4 import BeautifulSoup
import io
import os

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

app = Flask(__name__)

LANGUAGES = {
    "English": "en",
    "German": "de",
    "French": "fr",
    "Spanish": "es",
    "Italian": "it",
    "Portuguese": "pt",
    "Dutch": "nl",
    "Russian": "ru",
    "Chinese (Simplified)": "zh-cn",
    "Japanese": "ja",
    "Korean": "ko",
}

HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Markdown to Speech</title>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: #0f0f10;
      color: #e8e8e8;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 2rem 1rem;
    }
    h1 { font-size: 1.8rem; margin-bottom: 0.25rem; color: #fff; }
    .subtitle { color: #888; margin-bottom: 2rem; font-size: 0.95rem; }
    .card {
      background: #1a1a1c;
      border: 1px solid #2e2e32;
      border-radius: 12px;
      padding: 1.75rem;
      width: 100%;
      max-width: 760px;
    }
    label { display: block; font-size: 0.85rem; color: #aaa; margin-bottom: 0.4rem; margin-top: 1.2rem; }
    label:first-of-type { margin-top: 0; }
    textarea, input[type=text], input[type=number], input[type=password], select {
      width: 100%;
      background: #111113;
      border: 1px solid #2e2e32;
      border-radius: 8px;
      color: #e8e8e8;
      padding: 0.65rem 0.75rem;
      font-size: 0.9rem;
      outline: none;
      transition: border-color 0.2s;
      font-family: inherit;
    }
    textarea { resize: vertical; min-height: 220px; }
    textarea:focus, input:focus, select:focus { border-color: #5865f2; }
    select option { background: #1a1a1c; }
    .row { display: flex; gap: 1rem; }
    .row > * { flex: 1; }
    .hint { font-size: 0.78rem; color: #666; margin-top: 0.3rem; }
    button[type=submit] {
      margin-top: 1.5rem;
      width: 100%;
      padding: 0.75rem;
      background: #5865f2;
      color: #fff;
      border: none;
      border-radius: 8px;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.2s, opacity 0.2s;
    }
    button[type=submit]:hover { background: #4752c4; }
    button[type=submit]:disabled { opacity: 0.5; cursor: not-allowed; }
    .file-upload { display: flex; align-items: center; gap: 0.75rem; }
    .file-upload input[type=file] { display: none; }
    .file-btn {
      padding: 0.5rem 1rem;
      background: #25252a;
      border: 1px solid #2e2e32;
      border-radius: 8px;
      color: #ccc;
      cursor: pointer;
      font-size: 0.85rem;
      white-space: nowrap;
      transition: background 0.2s;
    }
    .file-btn:hover { background: #2e2e35; }
    #filename { font-size: 0.85rem; color: #888; }
    .flash {
      margin-bottom: 1rem;
      padding: 0.7rem 1rem;
      border-radius: 8px;
      font-size: 0.9rem;
    }
    .flash.error { background: #3a1515; border: 1px solid #7a2020; color: #f87171; }
    .spinner { display: none; }
    .converting .spinner { display: inline-block; }
    .converting .btn-label { display: none; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner svg { animation: spin 0.8s linear infinite; vertical-align: middle; }
  </style>
</head>
<body>
  <h1>Markdown to Speech</h1>
  <p class="subtitle">Convert Markdown text to an MP3 audio file</p>

  <div class="card">
    {% if error %}
    <div class="flash error">{{ error }}</div>
    {% endif %}

    <form method="POST" enctype="multipart/form-data" id="tts-form">
      <label for="md-upload">Upload a Markdown file (optional)</label>
      <div class="file-upload">
        <label class="file-btn" for="md-upload">Choose file</label>
        <input type="file" id="md-upload" name="md_file" accept=".md,.markdown,.txt" />
        <span id="filename">No file chosen</span>
      </div>

      <label for="content">Markdown content</label>
      <textarea id="content" name="content" placeholder="Paste your Markdown here, or upload a file above...">{{ content or '' }}</textarea>

      <div class="row">
        <div>
          <label for="language">Language</label>
          <select id="language" name="language">
            {% for name, code in languages.items() %}
            <option value="{{ code }}" {% if code == selected_lang %}selected{% endif %}>{{ name }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="chunk_size">Chunk size (characters)</label>
          <input type="number" id="chunk_size" name="chunk_size" value="1000" min="200" max="5000" step="100" />
          <p class="hint">Larger = fewer requests, slower per chunk</p>
        </div>
      </div>

      {% if openai_available %}
      <label for="openai_key">OpenAI API key (optional — enables GPT-4o text optimization)</label>
      <input type="password" id="openai_key" name="openai_key" placeholder="sk-..." autocomplete="off" />
      {% endif %}

      <button type="submit" id="submit-btn">
        <span class="btn-label">Convert to Speech</span>
        <span class="spinner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/>
          </svg>
          Converting...
        </span>
      </button>
    </form>
  </div>

  <script>
    const fileInput = document.getElementById('md-upload');
    const filenameSpan = document.getElementById('filename');
    const textarea = document.getElementById('content');

    fileInput.addEventListener('change', () => {
      const file = fileInput.files[0];
      if (!file) return;
      filenameSpan.textContent = file.name;
      const reader = new FileReader();
      reader.onload = e => { textarea.value = e.target.result; };
      reader.readAsText(file);
    });

    document.getElementById('tts-form').addEventListener('submit', () => {
      const btn = document.getElementById('submit-btn');
      btn.disabled = true;
      btn.classList.add('converting');
    });
  </script>
</body>
</html>
"""


def clean_markdown(text):
    html = markdown.markdown(text)
    soup = BeautifulSoup(html, "html.parser")
    return soup.get_text(separator=" ")


def optimize_for_speech(content, api_key):
    if not OPENAI_AVAILABLE or not api_key:
        return content

    client = openai.OpenAI(api_key=api_key)
    prompt = (
        "Optimize the following text for text-to-speech: expand abbreviations, "
        "convert numbers to words, replace symbols with spoken equivalents, and "
        "describe code blocks instead of reading syntax. Return only the optimized text.\n\n"
    )

    max_chunk = 3000
    chunks = [content[i:i + max_chunk] for i in range(0, len(content), max_chunk)]
    results = []
    for chunk in chunks:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You optimize text for speech synthesis. Return only the result."},
                {"role": "user", "content": prompt + chunk},
            ],
            temperature=0.3,
            max_tokens=4000,
        )
        results.append(resp.choices[0].message.content)
    return "\n".join(results)


def text_to_mp3_bytes(text, lang, chunk_size):
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
    # Concatenate raw MP3 bytes — valid because MP3 frames are self-delimiting
    audio = io.BytesIO()
    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue
        buf = io.BytesIO()
        gTTS(chunk, lang=lang).write_to_fp(buf)
        audio.write(buf.getvalue())
    audio.seek(0)
    return audio


@app.route("/", methods=["GET", "POST"])
def index():
    error = None
    content = ""
    selected_lang = "en"

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        selected_lang = request.form.get("language", "en")
        chunk_size = int(request.form.get("chunk_size", 1000))
        openai_key = request.form.get("openai_key", "").strip()

        if not content:
            error = "Please paste some Markdown content or upload a file."
        else:
            try:
                plain = clean_markdown(content)

                if openai_key and OPENAI_AVAILABLE:
                    plain = optimize_for_speech(plain, openai_key)

                audio = text_to_mp3_bytes(plain, selected_lang, chunk_size)
                return send_file(
                    audio,
                    mimetype="audio/mpeg",
                    as_attachment=True,
                    download_name="output.mp3",
                )
            except Exception as e:
                error = f"Conversion failed: {e}"

    return render_template_string(
        HTML,
        error=error,
        content=content,
        languages=LANGUAGES,
        selected_lang=selected_lang,
        openai_available=OPENAI_AVAILABLE,
    )


if __name__ == "__main__":
    app.run(debug=True)
