import base64
import html
import tempfile
from functools import lru_cache
from pathlib import Path
import streamlit as st
from document_converter import CONVERTERS
 
HERE = Path(__file__).parent
FISH_PATH = HERE / "fish.png"  # the drawing: ink on transparent background
 
MAX_MB = 50  # keeps the free cloud tier from running out of memory
FORMATS = ["TXT", "PDF", "DOCX"]
 
MIMES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
 
# what the fish says, depending on what's going on
SAY_IDLE = "ugh. docs again?"
SAY_READY = "fine. let’s see it."
SAY_WORKING = "converting. don’t rush me."
SAY_DONE = "done. can i go swim now?"
SAY_FAIL = "i broke it. not my fault."
 
 
def load_icon():
    # fish on a yellow tile for the browser tab, falls back to the emoji
    try:
        from PIL import Image
 
        fish = Image.open(FISH_PATH).convert("RGBA")
        size = 256
        tile = Image.new("RGBA", (size, size), (255, 217, 61, 255))
        fish.thumbnail((size - 44, size - 44))
        tile.alpha_composite(fish, ((size - fish.width) // 2, (size - fish.height) // 2))
        return tile
    except Exception:
        return "🐟"
 
 
st.set_page_config(page_title="ihatedocs", page_icon=load_icon(), layout="centered")
 
 
@lru_cache(maxsize=1)
def fish_src():
    try:
        return "data:image/png;base64," + base64.b64encode(FISH_PATH.read_bytes()).decode()
    except OSError:
        return None
 
 
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Caveat+Brush&family=Patrick+Hand&display=swap');
 
:root {
    --ink: #1B1B1B;
    --paper: #FCFAF3;
    --blue: #CFE0EE;
    --margin: #F0A5A5;
    --yellow: #FFD93D;
    --hl: #FFF1A8;
    --wobble: 18px 24px 16px 22px / 22px 16px 24px 18px;
    --marker: 'Caveat Brush', 'Comic Sans MS', cursive;
    --hand: 'Patrick Hand', 'Comic Sans MS', cursive;
}
 
/* strip streamlit chrome */
header[data-testid="stHeader"], [data-testid="stToolbar"], #MainMenu, footer {
    display: none !important;
}
 
/* lined notebook paper with a red margin */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: var(--paper);
    background-image:
        linear-gradient(to right, transparent 0 52px, var(--margin) 52px 54px, transparent 54px),
        repeating-linear-gradient(to bottom, transparent 0 31px, var(--blue) 31px 32px);
    background-attachment: local;
}
.block-container { max-width: 660px; padding-top: 2.6rem; padding-bottom: 3rem; }
 
/* hand-written text on streamlit's own widgets (icons are left alone) */
[data-testid="stMarkdownContainer"] p,
[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"] p,
[data-testid="stAlert"] p,
[data-testid="stFileUploaderDropzone"] span:not([data-testid="stIconMaterial"]),
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderFileName"] {
    font-family: var(--hand);
    font-size: 1.12rem;
}
 
/* wordmark */
.wordmark {
    font-family: var(--marker);
    font-size: clamp(3.2rem, 13vw, 4.6rem);
    line-height: 1;
    text-align: center;
    transform: rotate(-2deg);
    color: var(--ink);
}
.wordmark .hl {
    background: linear-gradient(transparent 52%, var(--yellow) 52% 90%, transparent 90%);
    padding: 0 0.08em;
}
.sub { text-align: center; font-family: var(--hand); font-size: 1.15rem; color: #5a5a5a; margin: 0.5rem 0 0; }
 
/* the fish + speech bubble */
.mascot { display: flex; align-items: center; justify-content: center; gap: 1.5rem; margin: 1rem 0 2rem; }
.fish { width: min(190px, 38vw); height: auto; transform: rotate(-3deg); animation: bob 3.2s ease-in-out infinite; }
.fish-emoji { font-size: 5rem; }
@keyframes bob {
    0%, 100% { transform: rotate(-3deg) translateY(0); }
    50% { transform: rotate(-1deg) translateY(-6px); }
}
@media (prefers-reduced-motion: reduce) { .fish { animation: none; } }
.bubble {
    position: relative;
    background: #fff;
    border: 2.5px solid var(--ink);
    border-radius: var(--wobble);
    padding: 0.7rem 1.1rem;
    font-family: var(--marker);
    font-size: 1.6rem;
    line-height: 1.15;
    max-width: 14rem;
    box-shadow: 3px 3px 0 var(--ink);
}
/* tail pointing at the fish */
.bubble::before, .bubble::after { content: ""; position: absolute; top: 50%; width: 0; height: 0; border-style: solid; }
.bubble::before {
    right: -17px; margin-top: -11px;
    border-width: 11px 0 11px 17px;
    border-color: transparent transparent transparent var(--ink);
}
.bubble::after {
    right: -11px; margin-top: -8px;
    border-width: 8px 0 8px 13px;
    border-color: transparent transparent transparent #fff;
}
 
/* main card, taped to the page */
.st-key-card {
    position: relative;
    background: #fff;
    border: 2.5px solid var(--ink);
    border-radius: var(--wobble);
    padding: 1.8rem 1.6rem 1.5rem;
    box-shadow: 6px 6px 0 var(--ink);
}
.st-key-card::before {
    content: "";
    position: absolute;
    top: -15px; left: 50%;
    width: 120px; height: 30px;
    transform: translateX(-50%) rotate(-3deg);
    background: rgba(255, 217, 61, 0.7);
    border: 1px dashed rgba(27, 27, 27, 0.25);
}
.step { display: flex; align-items: center; gap: 0.6rem; font-family: var(--marker); font-size: 1.45rem; margin: 0.4rem 0 0.4rem; }
.step b {
    display: inline-flex; align-items: center; justify-content: center;
    width: 1.9rem; height: 1.9rem;
    border: 2.5px solid var(--ink); border-radius: 50%;
    background: var(--yellow);
    font-weight: 400; font-size: 1.15rem; line-height: 1;
    transform: rotate(-6deg);
}
 
/* uploader */
[data-testid="stFileUploaderDropzone"], [data-testid="stFileUploadDropzone"] {
    border: 2.5px dashed var(--ink);
    border-radius: var(--wobble);
    background: #FFFDF5;
    padding: 1.4rem;
    transition: background 0.15s ease;
}
[data-testid="stFileUploaderDropzone"]:hover, [data-testid="stFileUploadDropzone"]:hover { background: var(--hl); }
 
/* sticker buttons */
div.stButton > button, div.stDownloadButton > button {
    width: 100%;
    background: #fff;
    border: 2.5px solid var(--ink);
    border-radius: var(--wobble);
    padding: 0.4rem 1rem;
    box-shadow: 4px 4px 0 var(--ink);
    transition: transform 0.08s ease, box-shadow 0.08s ease;
}
div.stButton > button p, div.stDownloadButton > button p {
    font-family: var(--marker);
    font-size: 1.5rem;
    font-weight: 400;
    letter-spacing: 0.02em;
}
button[kind="primary"], button[data-testid="stBaseButton-primary"] { background: var(--yellow) !important; }
button[kind="primary"] *, button[data-testid="stBaseButton-primary"] * { color: var(--ink) !important; }
div.stButton > button:hover:not(:disabled), div.stDownloadButton > button:hover:not(:disabled) {
    transform: translate(-1px, -1px);
    box-shadow: 6px 6px 0 var(--ink);
}
div.stButton > button:active:not(:disabled), div.stDownloadButton > button:active:not(:disabled) {
    transform: translate(3px, 3px);
    box-shadow: 1px 1px 0 var(--ink);
}
div.stButton > button:disabled {
    background: #EFEDE4 !important;
    border-style: dashed;
    box-shadow: none;
    opacity: 0.7;
}
 
/* result */
.st-key-result {
    margin-top: 1.6rem;
    background: var(--hl);
    border: 2.5px dashed var(--ink);
    border-radius: var(--wobble);
    padding: 1.1rem 1.2rem 1.3rem;
    transform: rotate(-0.4deg);
}
.done { display: flex; align-items: center; gap: 0.8rem; margin-bottom: 0.9rem; }
.done .tick {
    width: 2rem; height: 2rem; border-radius: 50%;
    background: var(--ink); color: var(--yellow);
    display: flex; align-items: center; justify-content: center;
    font-family: var(--marker); font-size: 1.3rem; flex-shrink: 0;
}
.done .name { font-family: var(--marker); font-size: 1.45rem; word-break: break-all; line-height: 1.1; }
.done .size { font-family: var(--hand); color: #555; font-size: 1.05rem; }
 
[data-testid="stAlert"] { border: 2.5px solid var(--ink); border-radius: var(--wobble); background: #FFE3DD; }
 
.foot { text-align: center; font-family: var(--hand); font-size: 1.05rem; color: #6a6a6a; margin-top: 2.2rem; line-height: 1.5; }
.foot a { color: var(--ink); text-decoration: underline wavy var(--ink); text-underline-offset: 3px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)
 
 
def hero_html(msg):
    src = fish_src()
    fish = (
        f'<img class="fish" src="{src}" alt="a sleepy fish">'
        if src
        else '<div class="fish fish-emoji">🐟</div>'
    )
    # no blank lines in here, markdown would end the html block
    return (
        '<div class="wordmark">i<span class="hl">hate</span>docs</div>'
        '<div class="sub">a tiny txt / pdf / docx converter</div>'
        f'<div class="mascot"><div class="bubble">{html.escape(msg)}</div>{fish}</div>'
    )
 
 
# the hero is a placeholder so the fish can react once we know what's happening
hero = st.empty()
 
 
def say(msg):
    hero.markdown(hero_html(msg), unsafe_allow_html=True)
 
 
say(SAY_IDLE)
 
 
def step(num, text):
    st.markdown(f'<div class="step"><b>{num}</b>{text}</div>', unsafe_allow_html=True)
 
 
def human_size(n):
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.0f} KB"
    return f"{n / (1024 * 1024):.1f} MB"
 
 
# the last finished conversion lives here so it survives the rerun
# that streamlit does when you click the download button
if "result" not in st.session_state:
    st.session_state.result = None
 
failed = False
 
with st.container(key="card"):
    step(1, "Pick a conversion")
    col_from, col_to = st.columns(2)
    with col_from:
        src = st.segmented_control("From", FORMATS, default="PDF", key="src") or "PDF"
    with col_to:
        targets = [f for f in FORMATS if f != src]
        # key includes src so the "to" picker resets cleanly when "from" changes
        dst = st.segmented_control("To", targets, default=targets[-1], key=f"dst_{src}") or targets[-1]
 
    conv_key = f"{src.lower()}_to_{dst.lower()}"
    ext = src.lower()
 
    step(2, "Drop your file")
    uploaded = st.file_uploader(
        f"Drop your .{ext} file here",
        type=[ext],
        key=f"up_{conv_key}",
        label_visibility="collapsed",
    )
    if conv_key == "pdf_to_docx":
        st.caption("Works best on PDFs with real text. Scanned PDFs (photos of pages) need OCR first.")
 
    # identifies "this file + this conversion" so an old result never shows for a new upload
    signature = (conv_key, uploaded.name, uploaded.size) if uploaded else None
 
    clicked = st.button("Convert", type="primary", disabled=uploaded is None)
 
    if uploaded and clicked:
        st.session_state.result = None
 
        if uploaded.size > MAX_MB * 1024 * 1024:
            failed = True
            st.error(f"That file is too big, the max is {MAX_MB} MB.")
        else:
            say(SAY_WORKING)
            with st.spinner("Converting... (big PDFs can take a minute)"):
                try:
                    # use a temp dir so files get wiped right after conversion
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        tmp_path = Path(tmp_dir)
                        # .name strips any folder parts from the uploaded filename
                        in_file = tmp_path / Path(uploaded.name).name
                        in_file.write_bytes(uploaded.getvalue())
 
                        out_file = CONVERTERS[conv_key](in_file, output_dir=tmp_path)
                        file_bytes = out_file.read_bytes()
 
                    st.session_state.result = {
                        "signature": signature,
                        "name": out_file.name,
                        "data": file_bytes,
                        "mime": MIMES.get(out_file.suffix.lower(), "application/octet-stream"),
                    }
                except Exception as err:
                    failed = True
                    st.error(f"Failed: {err}")
 
result = st.session_state.result
has_result = bool(uploaded and result and result["signature"] == signature)
 
if has_result:
    with st.container(key="result"):
        # filename comes from the user's upload, so escape it before putting it in html
        st.markdown(
            f'<div class="done"><div class="tick">✓</div><div>'
            f'<div class="name">{html.escape(result["name"])}</div>'
            f'<div class="size">{human_size(len(result["data"]))} · ready to download</div>'
            f"</div></div>",
            unsafe_allow_html=True,
        )
        st.download_button(
            label=f"Download {result['name']}",
            data=result["data"],
            file_name=result["name"],
            mime=result["mime"],
            type="primary",
        )
 
st.markdown(
    '<div class="foot">free · no signup · files are processed in temp memory and deleted right away<br>'
    'source on <a href="https://github.com/Al6in-Lab/ihatedocs" target="_blank">github</a></div>',
    unsafe_allow_html=True,
)
 
# final mood for the fish
if failed:
    say(SAY_FAIL)
elif has_result:
    say(SAY_DONE)
elif uploaded:
    say(SAY_READY)
else:
    say(SAY_IDLE)
 
