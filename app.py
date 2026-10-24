"""ಕನ್ನಡ ಡಿಜಿಟೈಸರ್ - Kannada Text Digitizer (Streamlit app).

Run:  streamlit run app.py
"""
import os

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

# ------------------------------------------------------------------ sidebar
st.sidebar.title("📜 Kannada Digitizer")
st.sidebar.caption("Free Karnataka's knowledge from paper.")
page = st.sidebar.radio("Go to", ["Digitize", "Library & Search", "About"])
st.sidebar.divider()
import llm
st.sidebar.write("AI helper:", f"✅ {llm.label()}" if llm.available() else "⚪ off (set GEMINI_API_KEY — free)")

ss = st.session_state


# ============================================================== DIGITIZE
def digitize_page():
    st.title("Digitize Kannada text")
    st.write("Upload a photo, scan or PDF. Get clean, editable, searchable Kannada text.")

    files = st.file_uploader("Upload image or PDF", type=["png", "jpg", "jpeg", "webp", "pdf"],
                             accept_multiple_files=True)
    cam = st.camera_input("…or take a photo", label_visibility="collapsed") \
        if st.toggle("Use camera") else None

    c1, c2, c3 = st.columns(3)
    use_pre = c1.checkbox("Clean image first (recommended)", True)
    allow_v = c2.checkbox("Auto-use vision model for hard pages", True,
                          disabled=not ocr.vision_available())
    force_v = c3.checkbox("Handwriting mode (always use vision model)", False,
                          disabled=not ocr.vision_available())

    if st.button("🔍 Digitize", type="primary", disabled=not (files or cam)):
        images, names = [], []
        for f in (files or []):
            for im in ocr.load_pages(f.getvalue(), f.name):
                images.append(im)
                names.append(f.name)
        if cam:
            images.append(ocr.load_pages(cam.getvalue(), "camera.jpg")[0])
            names.append("camera photo")

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
    t1, t2, t3, t4 = st.tabs(["🌐 English", "📝 Summary", "🔊 Listen", "💬 Ask"])
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
        if st.button("Read aloud in Kannada"):
            try:
                with st.spinner("Generating audio…"):
                    ss.audio = ai_tools.speak(text)
            except Exception as e:
                st.error(f"Audio needs an internet connection. ({e})")
        if ss.get("audio"):
            st.audio(ss.audio, format="audio/mp3")
    with t4:
        q = st.text_input("Ask a question about this document (Kannada or English)")
        if st.button("Ask") and q:
            with st.spinner("Thinking…"):
                ss.answer = ai_tools.ask(text, q)
        if ss.get("answer"):
            st.write(ss.answer)


# ================================================================ LIBRARY
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


# ================================================================== ABOUT
def about_page():
    st.title("About this project")
    st.markdown("""
**Problem:** Karnataka's knowledge is trapped on paper: notices, textbooks, newspapers,
handwritten records. It cannot be searched, copied, translated or read aloud.

**Solution:** Kannada Digitizer turns images, scans and PDFs into editable, searchable text,
then helps people *understand* it: translate, summarize, listen, ask questions.

**Pipeline:** upload → OpenCV cleanup (denoise, deskew, binarize) → Tesseract (Kannada)
→ vision-model fallback for handwriting → Unicode clean-up → edit → search / export.

**Who it helps:** students, elders who struggle with small print, non-Kannada speakers,
researchers and government offices digitizing records.
""")


{"Digitize": digitize_page, "Library & Search": library_page, "About": about_page}[page]()
