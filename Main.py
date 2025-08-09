import os
import pymupdf  # Correct import name
from ebooklib import epub
from bs4 import BeautifulSoup
from transformers import pipeline
from gtts import gTTS
from moviepy import TextClip, AudioFileClip, CompositeVideoClip  # ← Correct moviepy import

# ========== STEP 1: EXTRACT TEXT ==========
def extract_text(file_path):
    if file_path.endswith(".pdf"):
        doc = pymupdf.open(file_path)  # ← Use pymupdf directly
        return "".join(page.get_text() for page in doc)
    elif file_path.endswith(".epub"):
        book = epub.read_epub(file_path)
        text = ""
        for item in book.get_items():
            if item.get_type() == epub.ITEM_DOCUMENT:
                soup = BeautifulSoup(item.get_content(), 'html.parser')
                text += soup.get_text()
        return text
    else:
        raise ValueError("Unsupported file type. Use PDF or EPUB.")

# ========== STEP 2: SUMMARIZE TEXT ==========
def summarize(text):
    summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
    chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
    return " ".join(
        summarizer(chunk, max_length=130, min_length=30, do_sample=False)[0]['summary_text']
        for chunk in chunks
    )

# ========== STEP 3: TEXT-TO-SPEECH (4X SPEED) ==========
def generate_audio(text, output_path="output/fast_audio.mp3"):
    tts = gTTS(text, lang='en', slow=False)
    raw_audio_path = "output/audio.mp3"
    tts.save(raw_audio_path)

    os.system(f'ffmpeg -y -i {raw_audio_path} -filter:a "atempo=2.0,atempo=2.0" {output_path}')
    return output_path

# ========== STEP 4: CREATE SUBTITLES ==========
def generate_srt(text, output_path="output/subs.srt"):
    words = text.split()
    lines = [" ".join(words[i:i+8]) for i in range(0, len(words), 8)]
    srt = ""
    for i, line in enumerate(lines):
        start = i * 2
        end = start + 2
        srt += f"{i+1}\n00:00:{start:02},000 --> 00:00:{end:02},000\n{line}\n\n"
    with open(output_path, "w") as f:
        f.write(srt)
    return output_path

# ========== STEP 5: CREATE VIDEO ==========
def create_video(text, audio_path, output_path="output/final_video.mp4"):
    preview_text = text[:200] + "..."
    audio_clip = AudioFileClip(audio_path)
    txt_clip = TextClip(
        preview_text,
        fontsize=48,
        color='white',
        size=(1280, 720),
        method='caption'
    ).set_duration(audio_clip.duration)
    
    video = txt_clip.set_audio(audio_clip)
    video.write_videofile(output_path, fps=24)
   
# ========== RUN EVERYTHING ==========
def main():
    input_path = "4x reading project/Your_book.pdf/_OceanofPDF.com_Beyond_Good_and_Evil_-_Friedrich_Nietzsche.pdf"  # Change to your .epub or .pdf, add to exact file in 
    os.makedirs("output", exist_ok=True)

    print("[1] Extracting text...")
    text = extract_text(input_path)

    print("[2] Summarizing...")
    summary = summarize(text)

    print("[3] Generating audio at 4x speed...")
    audio_path = generate_audio(summary)

    print("[4] Creating subtitles...")
    generate_srt(summary)

    print("[5] Rendering video...")
    create_video(summary, audio_path)

    print("✅ Done! Video saved to output/final_video.mp4")

if __name__ == "__main__":
    main()
