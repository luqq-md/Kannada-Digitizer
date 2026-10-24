"""ಕನ್ನಡ ಡಿಜಿಟೈಸರ್ - Kannada Text Digitizer (Streamlit app).

Run:  streamlit run app.py
"""
import os
from pathlib import Path

import streamlit as st

import ai_tools
import exports
import ocr_pipeline as ocr
import storage
import theme

st.set_page_config(page_title="Kannada Digitizer · ಕನ್ನಡ ಡಿಜಿಟೈಸರ್", page_icon="📜", layout="wide")
storage.init_db()
theme.inject()



# ------------------------------------------------------------------ sidebar
import llm
theme.sidebar_brand()
page = st.sidebar.radio("Go to", ["Digitize", "Library & Search", "About"], label_visibility="collapsed")
st.sidebar.divider()
theme.sidebar_status(llm.label() if llm.available() else None)

ss = st.session_state

SAMPLE_DIR = Path(__file__).parent / "samples"
SAMPLES = [("📄 Tilted notice", "notice_tilted.png"),
           ("📰 Noisy textbook page", "textbook_noisy.png"),
           ("📱 Phone-style photo (white on dark)", "hard_letter_a.png")]


# ============================================================== DIGITIZE
def digitize_page():
    theme.hero()
    rail = st.container()

    files = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"],
                             accept_multiple_files=True)
    cam = st.camera_input("…or take a photo", label_visibility="collapsed") \
        if st.toggle("Use camera") else None

    avail = [(l, f) for l, f in SAMPLES if (SAMPLE_DIR / f).exists()]
    if avail and not files:
        st.markdown('<p class="try-label">No file handy? Pick a sample, then press Digitize.</p>', unsafe_allow_html=True)
        for col, (label, fname) in zip(st.columns(len(avail)), avail):
            if col.button(label, key="s_" + fname):
                ss.sample = fname
        if ss.get("sample"):
            st.info(f"Sample chosen: {ss.sample}. Press Digitize, or upload your own file instead.")

    c1, c2, c3 = st.columns(3)
    use_pre = c1.checkbox("Clean image first (recommended)", True)
    allow_v = c2.checkbox("Auto-use vision model for hard pages", True,
                          disabled=not ocr.vision_available())
    force_v = c3.checkbox("Handwriting mode (always use vision model)", False,
                          disabled=not ocr.vision_available())

    if st.button("🔍 Digitize", type="primary", disabled=not (files or cam or ss.get("sample"))):
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
        bar = st.progress(0.0, "Reading…")
        for i, im in enumerate(images):
            results.append(ocr.process_page(im, use_pre, allow_v, force_v))
            bar.progress((i + 1) / len(images), f"Page {i + 1} of {len(images)}")
        bar.empty()

        ss.images, ss.results = images, results
        ss.title = names[0].rsplit(".", 1)[0] if names else "document"
        ss.text = "\n\n".join(r.text for r in results)
        ss.pop("translation", None)
        ss.pop("summary", None)
        ss.pop("answer", None)
        ss.pop("audio", None)
        ss.pop("facts", None)
        ss.saved_id = None

    with rail:
        theme.steps(3 if "results" in ss else 1)

    if "results" not in ss:
        st.info("Upload a file or pick a sample to begin. A clear, well-lit photo works best.")
        return

    results, images = ss.results, ss.images
    avg = sum(r.avg_conf for r in results) / len(results)
    engines = ", ".join(sorted({r.engine for r in results}))
    theme.result_header(avg, len(images), engines, results[0].variant)

    left, right = st.columns(2)
    with left:
        theme.plate_title("Your photo")
        idx = st.number_input("Page", 1, len(images), 1) - 1 if len(images) > 1 else 0
        st.image(images[idx], width="stretch")
        with st.expander("See what the reader saw (cleaned and cropped)", expanded=False):
            st.caption(f"Method chosen automatically: {results[idx].variant}")
            st.image(results[idx].preprocessed, width="stretch")
    with right:
        theme.plate_title("Digital text. Edit anything that looks wrong.")
        ss.text = st.text_area("text", ss.text, height=420, label_visibility="collapsed")
        if results[idx].words:
            with st.expander("Show uncertain words in yellow"):
                st.markdown(f'<div class="big">{ocr.highlight_html(results[idx].words)}</div>',
                            unsafe_allow_html=True)

    st.divider()
    a, b, c, d = st.columns(4)
    ss.title = a.text_input("Document name", ss.title)
    if b.button("💾 Save to library"):
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
        st.success("Saved! Search it in the Library (Kannada or English)."
                   if tr else "Saved! (English translation unavailable right now, "
                              "so search works in Kannada only.)")

    theme.plate_title("Take it with you")
    d1, d2, d3 = st.columns(3)
    d1.download_button("⬇ Text (.txt)", exports.to_txt(ss.text), f"{ss.title}.txt")
    d2.download_button("⬇ Word (.docx)", exports.to_docx(ss.title, ss.text), f"{ss.title}.docx")
    if d3.button("Prepare searchable PDF"):
        with st.spinner("Building PDF…"):
            ss.pdf = exports.to_searchable_pdf(images)
    if ss.get("pdf"):
        d3.download_button("⬇ Searchable PDF", ss.pdf, f"{ss.title}.pdf")

    understand_tools(ss.text)


def understand_tools(text):
    st.divider()
    theme.plate_title("Understand it")
    t1, t2, t3, t4, t5 = st.tabs(["🌐 English", "📝 Summary", "📌 Key facts", "🔊 Listen", "💬 Ask"])
    with t1:
        if st.button("Translate to English"):
            with st.spinner("Translating…"):
                ss.corrected = ""
                if ai_tools.ai_available():
                    try:
                        ss.corrected, ss.translation = ai_tools.smart_translate(text)
                    except Exception:
                        ss.translation = ai_tools.translate(text)
                else:
                    ss.translation = ai_tools.translate(text)
        if ss.get("translation"):
            st.markdown("**English meaning**")
            st.write(ss.translation)
            if ss.get("corrected"):
                with st.expander("Kannada with OCR mistakes fixed"):
                    st.write(ss.corrected)
                    if st.button("Use this corrected text"):
                        ss.text = ss.corrected
                        st.rerun()
        if not ai_tools.ai_available():
            st.caption("💡 Free translation is word-by-word and can't fix OCR mistakes. "
                       "Add a free GEMINI_API_KEY for natural, meaning-aware translation.")
    with t2:
        if st.button("Summarize"):
            with st.spinner("Summarizing…"):
                ss.summary = ai_tools.summarize(text)
        if ss.get("summary"):
            st.write(ss.summary)
    with t3:
        if st.button("Find key facts (dates, names, actions)"):
            with st.spinner("Reading carefully…"):
                ss.facts = ai_tools.key_facts(text)
        if ss.get("facts"):
            st.write(ss.facts)
    with t4:
        if st.button("Read aloud in Kannada"):
            try:
                with st.spinner("Generating audio…"):
                    ss.audio = ai_tools.speak(text)
            except Exception as e:
                st.error(f"Audio needs an internet connection. ({e})")
        if ss.get("audio"):
            st.audio(ss.audio, format="audio/mp3")
    with t5:
        q = st.text_input("Ask a question about this document (Kannada or English)")
        if st.button("Ask") and q:
            with st.spinner("Thinking…"):
                ss.answer = ai_tools.ask(text, q)
        if ss.get("answer"):
            st.write(ss.answer)


# ================================================================ LIBRARY
def library_page():
    theme.page_head("Library", "Everything you saved. Search in Kannada or English.")
    q = st.text_input("Search your documents", placeholder="Try ಪರೀಕ್ಷೆ or exam")
    if q:
        hits = storage.search(q)
        st.caption(f"{len(hits)} result(s)")
        for h in hits:
            with st.container(border=True):
                st.markdown(f"**{h['title']}**  (id {h['id']}) · matched in {h['matched']}")
                st.write(h["snippet"])
    st.divider()
    docs = storage.list_documents()
    if not docs:
        st.info("Nothing saved yet. Digitize a page and press Save to library. It will appear here, searchable in Kannada and English.")
    for d in docs:
        with st.expander(f"📄 {d['title']}  —  {d['pages']} page(s), {d['avg_conf']:.0f}% conf, {d['created'][:10]}"):
            full = storage.get_document(d["id"])
            st.text_area("Text", full["text"], height=200, key=f"t{d['id']}")
            if full["translation"]:
                st.caption("English translation")
                st.write(full["translation"])
            c1, c2 = st.columns(2)
            if c1.button("Save edits", key=f"s{d['id']}"):
                storage.update_document(d["id"], text=ss[f"t{d['id']}"])
                st.success("Updated")
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
  A [label="Photo, scan\nor PDF"];
  B [label="Clean-up\nflip colours,\nstraighten,\nremove glare"];
  C [label="Tesseract\nKannada reader"];
  D [label="Find the text,\ncrop and\nread again"];
  E [label="AI reader\nfor handwriting", fillcolor="#13201B", fontcolor="white", color="#13201B"];
  F [label="Editable\ntext"];
  G [label="Search, export,\ntranslate, key facts,\nlisten, ask", fillcolor="#E8A317", color="#B97F00"];
  A -> B -> C -> D -> F -> G;
  C -> E [style=dashed, label=" low\n confidence"];
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
