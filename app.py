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

st.set_page_config(page_title="Kannada Digitizer", page_icon="📜", layout="wide")
storage.init_db()

st.markdown("""
<style>
mark {background:#ffe08a; padding:0 2px; border-radius:3px}
.big {font-size:1.05rem; line-height:1.9}
</style>""", unsafe_allow_html=True)

st.sidebar.title("📜 Kannada Digitizer")
st.sidebar.caption("ಕನ್ನಡ ಡಿಜಿಟೈಸರ್ · Free Karnataka's knowledge from paper.")
page = st.sidebar.radio("Go to", ["Digitize", "Library & Search", "About"])
st.sidebar.divider()
import llm
st.sidebar.write("AI helper:", f"✅ {llm.label()}" if llm.available() else "⚪ off (set GEMINI_API_KEY — free)")
ss = st.session_state
SAMPLE_DIR = Path(__file__).parent / "samples"
SAMPLES = [("📄 Tilted notice", "notice_tilted.png"),
           ("📰 Noisy textbook page", "textbook_noisy.png"),
           ("📱 Phone-style photo (white on dark)", "hard_letter_a.png")]

def digitize_page():
    st.title("ಕನ್ನಡ ಪಠ್ಯ ಡಿಜಿಟೈಸ್ ಮಾಡಿ · Digitize Kannada text")
    st.write("Upload a photo, scan or PDF. Get clean, editable, searchable Kannada text.")

    files = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"],
                             accept_multiple_files=True)
    cam = st.camera_input("…or take a photo", label_visibility="collapsed") \
        if st.toggle("Use camera") else None

    avail = [(l, f) for l, f in SAMPLES if (SAMPLE_DIR / f).exists()]
    if avail and not files:
        st.caption("No file handy? Try a sample, then press Digitize:")
        for col, (label, fname) in zip(st.columns(len(avail)), avail):
            if col.button(label, key="s_" + fname):
                ss.sample = fname
        if ss.get("sample"):
            st.info(f"Sample selected: {ss.sample}. Press **Digitize**, or upload your own file.")

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

    if "results" not in ss:
        st.info("👆 Upload something to begin. Tip: a clear, well-lit photo works best.")
        return

    results, images = ss.results, ss.images
    avg = sum(r.avg_conf for r in results) / len(results)
    engines = ", ".join(sorted({r.engine for r in results}))
    m1, m2, m3 = st.columns(3)
    m1.metric("Pages", len(images))
    m2.metric("Average confidence", f"{avg:.0f}%")
    m3.metric("Engine used", engines)

    left, right = st.columns(2)
    with left:
        st.subheader("Original")
        idx = st.number_input("Page", 1, len(images), 1) - 1 if len(images) > 1 else 0
        st.image(images[idx], width="stretch")
        with st.expander("See what the computer read (auto-cleaned and cropped)", expanded=True):
            st.caption(f"Method chosen automatically: {results[idx].variant}")
            st.image(results[idx].preprocessed, width="stretch")
    with right:
        st.subheader("Extracted text (editable)")
        ss.text = st.text_area("text", ss.text, height=420, label_visibility="collapsed")
        if results[idx].words:
            with st.expander("Highlight uncertain words (yellow = please check)"):
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

    st.subheader("Download")
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
    st.subheader("Understand it")
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

def library_page():
    st.title("Library & Search")
    q = st.text_input("🔎 Search all documents (Kannada or English)", placeholder="ಉದಾ: ಪರೀಕ್ಷೆ")
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
        st.info("No documents yet. Digitize one and press **Save to library**.")
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
def about_page():
    st.title("About this project")
    st.markdown("""
**Problem:** Karnataka's knowledge is trapped on paper: notices, textbooks, newspapers,
handwritten records. It cannot be searched, copied, translated or read aloud.

**Solution:** Kannada Digitizer turns images, scans and PDFs into editable, searchable text,
then helps people *understand* it: translate, summarize, find key facts, listen, ask questions.

**Who it helps:** students, elders who struggle with small print, non-Kannada speakers,
researchers and government offices digitizing records.
""")
    st.subheader("How it works")
    st.graphviz_chart("""
digraph G {
  rankdir=LR; bgcolor="transparent";
  node [shape=box, style="rounded,filled", fillcolor="#fff3d6", fontname="Helvetica", color="#c98a00"];
  edge [color="#888888", fontname="Helvetica", fontsize=10];
  A [label="Photo / scan / PDF"];
  B [label="Clean-up\n(flip colours, straighten,\nremove glare)"];
  C [label="Tesseract\n(Kannada OCR)"];
  D [label="Find the text area\ncrop + re-read"];
  E [label="AI vision fallback\n(handwriting)", fillcolor="#e3f0ff", color="#3b7dd8"];
  F [label="Editable text"];
  G [label="Search · Export\nTranslate · Facts · Listen · Ask", fillcolor="#e6f6e6", color="#3a9a3a"];
  A -> B -> C -> D -> F -> G;
  C -> E [style=dashed, label="low confidence"];
  E -> F [style=dashed];
}
""")
    st.subheader("Measured accuracy")
    st.markdown("""
Character error rate on 15 test images (clean, tilted, noisy, and light-on-dark phone-style
photos). **Lower is better.**

| | Plain Tesseract | This pipeline |
|---|---|---|
| All 15 images (average) | 37.3% | **0.3%** |
| 6 hard phone-style images | 70.2% | **0.3%** |

**Be aware:** these test images are *synthetic* (computer-made text, then degraded), so real
photos are harder. On two real, low-resolution phone-screen photos the pipeline recovered
about 79% of the words, with small spelling slips. Handwriting needs the AI vision fallback.
""")


{"Digitize": digitize_page, "Library & Search": library_page, "About": about_page}[page]()
