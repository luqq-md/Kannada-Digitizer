"""ಕನ್ನಡ ಡಿಜಿಟೈಸರ್ - Kannada Digitizer (Streamlit app).

Run:  streamlit run app.py
"""
from pathlib import Path

import streamlit as st

import ai_tools
import exports
import llm
import ocr_pipeline as ocr
import storage
import theme

st.set_page_config(page_title="Kannada Digitizer · ಕನ್ನಡ ಡಿಜಿಟೈಸರ್", page_icon="📜", layout="wide")
storage.init_db()
theme.inject()

# ------------------------------------------------------------------ sidebar
theme.sidebar_brand()
page = st.sidebar.radio("Go to", ["Digitize", "Library & Search", "About"],
                        label_visibility="collapsed")
st.sidebar.divider()
theme.sidebar_status(llm.label() if llm.available() else None)

ss = st.session_state

SAMPLE_DIR = Path(__file__).parent / "samples"
SAMPLES = [("Tilted notice", "notice_tilted.png"),
           ("Noisy textbook page", "textbook_noisy.png"),
           ("Phone-style photo, white on dark", "hard_letter_a.png")]

NEEDS_KEY = "Add a free GEMINI_API_KEY in the app's Secrets to turn this on."


def run_ai(fn, *args, spinner="Thinking…"):
    """Run an AI call; show a plain-language message instead of a crash if it fails."""
    try:
        with st.spinner(spinner):
            return fn(*args)
    except llm.AIError as e:
        st.error(str(e))
    except Exception as e:                      # never show a raw traceback to visitors
        st.error(f"Something went wrong ({type(e).__name__}). Please try again.")
    return None


# ============================================================== DIGITIZE
def digitize_page():
    theme.hero()
    rail = st.container()

    theme.plate_title("Add your page")
    files = st.file_uploader("Drop a photo, scan or PDF here, or browse",
                             type=["png", "jpg", "jpeg", "webp", "pdf"],
                             accept_multiple_files=True)
    use_cam = st.toggle("Use the camera instead")
    cam = st.camera_input("Camera", label_visibility="collapsed") if use_cam else None

    avail = [(l, f) for l, f in SAMPLES if (SAMPLE_DIR / f).exists()]
    if avail and not files and not cam:
        st.markdown('<p class="try-label">No file handy? Try a sample.</p>', unsafe_allow_html=True)
        for col, (label, fname) in zip(st.columns(len(avail)), avail):
            with col:
                st.image(str(SAMPLE_DIR / fname), width="stretch")
                chosen = ss.get("sample") == fname
                if st.button(("Selected: " if chosen else "") + label, key="s_" + fname,
                             type="primary" if chosen else "secondary", width="stretch"):
                    ss.sample = fname
                    st.rerun()

    ai_on = ocr.vision_available()
    c1, c2, c3 = st.columns(3)
    use_pre = c1.checkbox("Clean the image first", True,
                          help="Straightens the page, flips light-on-dark text, removes glare.")
    allow_v = c2.checkbox("Let the AI reader help on hard pages", True, disabled=not ai_on,
                          help="" if ai_on else NEEDS_KEY)
    force_v = c3.checkbox("Handwriting mode (AI reader always)", False, disabled=not ai_on,
                          help="" if ai_on else NEEDS_KEY)

    ready = bool(files or cam or ss.get("sample"))
    if st.button("Digitize this page", type="primary", disabled=not ready):
        images, names = [], []
        for f in (files or []):
            for im in ocr.load_pages(f.getvalue(), f.name):
                images.append(im)
                names.append(f.name)
        if cam:
            images.append(ocr.load_pages(cam.getvalue(), "camera.jpg")[0])
            names.append("camera photo")
        if not images and ss.get("sample"):
            sp = SAMPLE_DIR / ss.sample
            images.extend(ocr.load_pages(sp.read_bytes(), sp.name))
            names.append(sp.name)

        results = []
        with st.status("Reading your page…", expanded=True) as status:
            for i, im in enumerate(images):
                if len(images) > 1:
                    st.write(f"**Page {i + 1} of {len(images)}**")
                results.append(ocr.process_page(im, use_pre, allow_v, force_v, on_step=st.write))
            status.update(label="Finished reading", state="complete", expanded=False)

        ss.images, ss.results = images, results
        ss.title = names[0].rsplit(".", 1)[0] if names else "document"
        ss.text = "\n\n".join(r.text for r in results)
        for k in ("translation", "corrected", "summary", "answer", "audio", "facts", "pdf"):
            ss.pop(k, None)
        ss.saved_id = None
        st.toast("Page read. Check the text below, then save or download it.", icon="✅")

    with rail:
        theme.steps(3 if "results" in ss else 1)

    if "results" not in ss:
        st.info("Choose a file or a sample, then press Digitize. A clear, well-lit photo works best.")
        return

    results, images = ss.results, ss.images
    avg = sum(r.avg_conf for r in results) / len(results)
    engines = ", ".join(sorted({r.engine for r in results}))
    theme.result_header(avg, len(images), engines, results[0].variant)

    left, right = st.columns(2)
    idx = 0
    with left:
        theme.plate_title("Your photo")
        if len(images) > 1:
            idx = st.number_input("Page", 1, len(images), 1) - 1
        st.image(images[idx], width="stretch")
        with st.expander("See what the reader saw (cleaned and cropped)"):
            st.caption(f"Cleanup chosen automatically: {results[idx].variant}")
            st.image(results[idx].preprocessed, width="stretch")
    with right:
        theme.plate_title("Digital text")
        t_edit, t_check, t_copy = st.tabs(["Edit", "Check doubtful words", "Copy"])
        with t_edit:
            ss.text = st.text_area("Extracted text", ss.text, height=400,
                                   label_visibility="collapsed")
        with t_check:
            if results[idx].words:
                st.caption("Words the reader was unsure about are marked in yellow.")
                st.markdown(f'<div class="big">{ocr.highlight_html(results[idx].words)}</div>',
                            unsafe_allow_html=True)
            else:
                st.info("No word-by-word confidence is available for this page.")
        with t_copy:
            st.caption("Use the copy icon at the top right of the box.")
            st.code(ss.text, language=None, wrap_lines=True)

    theme.plate_title("Keep it")
    a, b = st.columns([2, 1])
    ss.title = a.text_input("Document name", ss.title)
    b.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
    if b.button("Save to library", width="stretch"):
        tr = ss.get("translation") or ""
        if not ai_tools.translation_ok(tr):
            with st.spinner("Translating so you can also search in English…"):
                tr = ai_tools.translate(ss.text)
        tr = tr if ai_tools.translation_ok(tr) else ""
        if ss.get("saved_id"):
            storage.update_document(ss.saved_id, text=ss.text, translation=tr)
        else:
            ss.saved_id = storage.add_document(ss.title, ss.text, engines, avg,
                                               len(images), tr)
        st.toast("Saved to your library." if tr else
                 "Saved. English translation was unavailable, so search works in Kannada only.",
                 icon="📚")

    d1, d2, d3 = st.columns(3)
    d1.download_button("Download text (.txt)", exports.to_txt(ss.text), f"{ss.title}.txt",
                       width="stretch")
    d2.download_button("Download Word (.docx)", exports.to_docx(ss.title, ss.text),
                       f"{ss.title}.docx", width="stretch")
    if ss.get("pdf"):
        d3.download_button("Download searchable PDF", ss.pdf, f"{ss.title}.pdf", width="stretch")
    elif d3.button("Make a searchable PDF", width="stretch"):
        with st.spinner("Building the PDF…"):
            ss.pdf = exports.to_searchable_pdf(images)
        st.rerun()

    understand_tools(ss.text)


def understand_tools(text):
    theme.plate_title("Understand it")
    t1, t2, t3, t4, t5 = st.tabs(["English", "Summary", "Key facts", "Listen", "Ask"])

    with t1:
        if st.button("Translate to English"):
            ss.corrected = ""
            if llm.available():
                try:
                    with st.spinner("Translating by meaning…"):
                        ss.corrected, ss.translation = ai_tools.smart_translate(text)
                except Exception as e:
                    st.warning("The AI helper was unavailable, so this is the free word-by-word "
                               f"translation. ({e})")
                    with st.spinner("Translating…"):
                        ss.translation = ai_tools.translate_free(text)
            else:
                with st.spinner("Translating…"):
                    ss.translation = ai_tools.translate_free(text)
        if ss.get("translation"):
            st.markdown("**English meaning**")
            st.write(ss.translation)
            if ss.get("corrected"):
                with st.expander("Kannada with the reading mistakes fixed"):
                    st.write(ss.corrected)
                    if st.button("Use this corrected text"):
                        ss.text = ss.corrected
                        st.rerun()
        if not llm.available():
            st.caption("This is word-by-word and cannot fix reading mistakes. "
                       "A free Gemini key gives natural, meaning-aware translation.")

    with t2:
        if not llm.available():
            st.info(NEEDS_KEY)
        elif st.button("Summarize"):
            res = run_ai(ai_tools.summarize, text, spinner="Summarizing…")
            if res:
                ss.summary = res
        if ss.get("summary"):
            st.write(ss.summary)

    with t3:
        if not llm.available():
            st.info(NEEDS_KEY)
        elif st.button("Find dates, names and actions"):
            res = run_ai(ai_tools.key_facts, text, spinner="Reading carefully…")
            if res:
                ss.facts = res
        if ss.get("facts"):
            st.write(ss.facts)

    with t4:
        if st.button("Read aloud in Kannada"):
            try:
                with st.spinner("Preparing the audio…"):
                    ss.audio = ai_tools.speak(text)
            except Exception:
                st.error("Audio could not be created. It needs an internet connection; try again.")
        if ss.get("audio"):
            st.audio(ss.audio, format="audio/mp3")

    with t5:
        if not llm.available():
            st.info(NEEDS_KEY)
        else:
            q = st.text_input("Ask about this document, in Kannada or English",
                              placeholder="For example: What is the last date mentioned?")
            if st.button("Ask") and q:
                res = run_ai(ai_tools.ask, text, q, spinner="Looking through the document…")
                if res:
                    ss.answer = res
            if ss.get("answer"):
                st.write(ss.answer)


# ================================================================ LIBRARY
def library_page():
    theme.page_head("Library", "Everything you saved. Search in Kannada or English.")
    q = st.text_input("Search your documents", placeholder="Try ಪರೀಕ್ಷೆ or exam")
    if q:
        hits = storage.search(q)
        st.caption(f"{len(hits)} result{'s' if len(hits) != 1 else ''}")
        for h in hits:
            with st.container(border=True):
                st.markdown(f"**{h['title']}**  matched in {h['matched']}")
                st.write(h["snippet"])
    docs = storage.list_documents()
    if not docs:
        st.info("Nothing saved yet. Digitize a page and press Save to library. "
                "It will appear here, searchable in Kannada and English.")
    for d in docs:
        with st.expander(f"{d['title']}: {d['pages']} page(s), {d['avg_conf']:.0f}% confidence, "
                         f"{d['created'][:10]}"):
            full = storage.get_document(d["id"])
            st.text_area("Text", full["text"], height=200, key=f"t{d['id']}")
            if full["translation"]:
                st.caption("English translation")
                st.write(full["translation"])
            c1, c2 = st.columns(2)
            if c1.button("Save edits", key=f"s{d['id']}"):
                storage.update_document(d["id"], text=ss[f"t{d['id']}"])
                st.toast("Changes saved.", icon="✅")
            if c2.button("Delete", key=f"x{d['id']}"):
                storage.delete_document(d["id"])
                st.rerun()


# ================================================================== ABOUT
def about_page():
    theme.page_head("About this project", "Why it exists, how it works, and how well it works.")
    theme.about_legend([
        ("The problem", "Karnataka's knowledge sits on paper: notices, textbooks, newspapers and "
                        "handwritten records. It cannot be searched, copied, translated or read aloud."),
        ("What this does", "It turns photos, scans and PDFs into editable, searchable Kannada text, "
                           "then helps you understand it: translate, summarize, find key facts, listen, ask."),
        ("Who it helps", "Students, elders who struggle with small print, people learning Kannada, "
                         "researchers, and offices digitizing records."),
    ])
    theme.plate_title("How it works")
    st.graphviz_chart("""
digraph G {
  rankdir=LR; bgcolor="transparent"; nodesep=0.35; ranksep=0.45;
  node [shape=box, style="rounded,filled", fillcolor="#EFE7B8", fontname="Helvetica", fontsize=15, color="#BDB27A", margin="0.18,0.12"];
  edge [color="#2B3A33", fontname="Helvetica", fontsize=12];
  A [label="Photo, scan\\nor PDF"];
  B [label="Clean-up\\nflip colours,\\nstraighten,\\nremove glare"];
  C [label="Tesseract\\nKannada reader"];
  D [label="Find the text,\\ncrop and\\nread again"];
  E [label="AI reader\\nfor handwriting", fillcolor="#13201B", fontcolor="white", color="#13201B"];
  F [label="Editable\\ntext"];
  G [label="Search, export,\\ntranslate, key facts,\\nlisten, ask", fillcolor="#E8A317", color="#B97F00"];
  A -> B -> C -> D -> F -> G;
  C -> E [style=dashed, label=" low\\n confidence"];
  E -> F [style=dashed];
}
""")
    theme.plate_title("Measured accuracy")
    st.caption("Character error rate on 15 test images. Lower is better.")
    theme.accuracy_bars([
        ("All 15 images, average", [("Plain Tesseract", 37.3, False), ("This pipeline", 0.3, True)]),
        ("The 6 hardest, phone-style photos (white text on dark, tilted, glare)",
         [("Plain Tesseract", 70.2, False), ("This pipeline", 0.3, True)]),
    ])
    st.markdown(
        "**Read this honestly.** The test images are synthetic: computer-made Kannada, then degraded "
        "to look like phone photos. Real photos are harder. On two real, low-resolution phone-screen "
        "photos the pipeline recovered about 79% of the words, with small spelling slips. "
        "Handwriting depends on the AI reader.")


{"Digitize": digitize_page, "Library & Search": library_page, "About": about_page}[page]()
