"""Visual identity for Kannada Digitizer.

Concept: from palm leaf to pixel. Karnataka's written heritage lives on palm-leaf
manuscripts (ಓಲೆಗರಿ): narrow strips with a punched string-hole. The interface borrows
that vocabulary for the text plate and animates one moment, a scan beam turning a worn
leaf into crisp digital text.

Palette (all taken from the subject):
  soapstone  #E6EAE3  page          (Hoysala temple stone)
  ink        #13201B  sidebar/text  (deep lamp-black green)
  palm leaf  #D6CE9B  text plates
  turmeric   #E8A317  accent        (flag yellow)
  kumkuma    #A31F1A  actions       (flag red)
"""
import html

import streamlit as st

FONTS = ("https://fonts.googleapis.com/css2?"
         "family=Bricolage+Grotesque:opsz,wght@12..96,500..800"
         "&family=Figtree:wght@400;500;600"
         "&family=Noto+Serif+Kannada:wght@400..800"
         "&family=Noto+Sans+Kannada:wght@400..700&display=swap")

CSS = """
@import url('__FONTS__');
:root{
  --soap:#E6EAE3; --soap2:#D8DED4; --ink:#13201B; --ink2:#2B3A33; --silver:#8C9A92;
  --leaf:#D6CE9B; --leaf2:#BDB27A; --leafink:#34240F;
  --turmeric:#E8A317; --kumkuma:#A31F1A;
  --display:'Bricolage Grotesque','Figtree','Noto Sans Kannada',system-ui,sans-serif;
  --body:'Figtree','Noto Sans Kannada',system-ui,sans-serif;
  --manu:'Noto Serif Kannada','Noto Sans Kannada',Georgia,serif;
}
html,body,[data-testid="stAppViewContainer"],.stApp{font-family:var(--body);color:var(--ink);}
.stApp{background:var(--soap);}
.stApp::before{content:"";position:fixed;inset:0 0 auto 0;height:5px;z-index:1000000;
  background:linear-gradient(var(--turmeric) 0 50%,var(--kumkuma) 50% 100%);}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1160px;padding-top:2.6rem;padding-bottom:5rem;}

strong,b{font-weight:700;}
h1,h2,h3{font-family:var(--display);letter-spacing:-.02em;color:var(--ink);font-weight:700;}
h1{font-size:2.3rem;line-height:1.1;}
h3{font-size:1.25rem;}
p,li,label,span{font-family:var(--body);}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--ink);border-right:0;}
[data-testid="stSidebar"] *{color:#E4EAE3;}
[data-testid="stSidebar"] hr{border-color:rgba(255,255,255,.12);}
[data-testid="stSidebar"] [role="radiogroup"]{gap:.15rem;}
[data-testid="stSidebar"] [role="radiogroup"] label{padding:.6rem .85rem;border-radius:4px;
  border-left:3px solid transparent;transition:background .15s;cursor:pointer;width:100%;}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{background:rgba(255,255,255,.06);}
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-child{display:none;}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){
  background:rgba(232,163,23,.14);border-left-color:var(--turmeric);}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) p{color:#fff;font-weight:600;}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]{padding:.6rem .85rem;border-radius:4px;
  border-left:3px solid transparent;cursor:pointer;width:100%;transition:background .15s;}
[data-testid="stSidebar"] label[data-testid="stRadioOption"]:hover{background:rgba(255,255,255,.06);}
[data-testid="stSidebar"] label[data-testid="stRadioOption"] > div > div:first-child{display:none;}
[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"]{
  background:rgba(232,163,23,.14);border-left-color:var(--turmeric);}
[data-testid="stSidebar"] label[data-testid="stRadioOption"][data-selected="true"] p{color:#fff;font-weight:600;}
.brand{display:flex;gap:.8rem;align-items:center;margin:.4rem 0 1.4rem;}
.brand-mark{width:44px;height:30px;border-radius:5px;background:var(--leaf);position:relative;flex:none;
  box-shadow:inset 0 0 0 1px var(--leaf2);}
.brand-mark::before{content:"";position:absolute;left:6px;top:50%;width:6px;height:6px;margin-top:-3px;
  border-radius:50%;background:var(--ink);}
.brand-mark::after{content:"ಅ";position:absolute;right:7px;top:50%;transform:translateY(-52%);
  font:700 15px/1 var(--manu);color:var(--leafink);}
.stApp .brand-name{font:700 1.08rem/1.1 var(--display);color:#fff;letter-spacing:-.01em;}
.stApp .brand-kn{font:500 .82rem/1.3 'Noto Sans Kannada',sans-serif;color:#9FB0A6;margin-top:.1rem;}
.stApp .status{display:flex;align-items:center;gap:.55rem;font-size:.9rem;color:#C7D2CB;}
.dot{width:9px;height:9px;border-radius:50%;background:#6E7D75;flex:none;}
.dot.on{background:var(--turmeric);box-shadow:0 0 0 4px rgba(232,163,23,.2);}

/* ---------- hero ---------- */
.hero{display:grid;grid-template-columns:1.1fr .9fr;gap:2.6rem;align-items:center;
  padding:.4rem 0 2.2rem;border-bottom:1px solid var(--soap2);margin-bottom:1.6rem;}
.stApp .hero-title{font:800 clamp(2.1rem,4.6vw,3.5rem)/1.04 var(--display);letter-spacing:-.035em;margin:0 0 1rem;color:var(--ink);}
.stApp .hero-sub{font-size:1.1rem;line-height:1.6;color:var(--ink2);max-width:34rem;margin:0;}
.leaf{position:relative;height:150px;border-radius:12px;overflow:hidden;
  background:
   repeating-linear-gradient(to bottom,rgba(110,90,30,.09) 0 1px,transparent 1px 7px),
   linear-gradient(180deg,#E0D8A6,var(--leaf) 55%,#C9BF86);
  box-shadow:inset 0 0 0 1px var(--leaf2),0 18px 30px -18px rgba(19,32,27,.45);}
.leaf-hole{position:absolute;left:22px;top:50%;width:16px;height:16px;margin-top:-8px;border-radius:50%;
  background:var(--soap);box-shadow:inset 0 2px 3px rgba(0,0,0,.35);}
.leaf-text{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  padding-left:44px;font:700 clamp(2rem,4.2vw,3.1rem)/1 var(--manu);white-space:nowrap;}
.leaf-text.rough{color:#8A7A48;opacity:.55;filter:blur(1.6px);transform:rotate(-1.6deg) skewX(-3deg);
  clip-path:inset(0 0 0 0);animation:wornout 3.4s .7s cubic-bezier(.6,0,.3,1) forwards;}
.leaf-text.crisp{color:var(--leafink);clip-path:inset(0 100% 0 0);animation:reveal 3.4s .7s cubic-bezier(.6,0,.3,1) forwards;}
.beam{position:absolute;top:0;bottom:0;left:0;width:3px;background:var(--kumkuma);opacity:0;
  box-shadow:0 0 22px 7px rgba(232,163,23,.55);animation:sweep 3.4s .7s cubic-bezier(.6,0,.3,1) forwards;}
@keyframes reveal{to{clip-path:inset(0 0 0 0);}}
@keyframes wornout{to{clip-path:inset(0 0 0 100%);}}
@keyframes sweep{0%{left:0;opacity:1}92%{opacity:1}100%{left:calc(100% - 3px);opacity:0}}
@media (prefers-reduced-motion:reduce){
  .leaf-text.crisp{animation:none;clip-path:none;}.leaf-text.rough{display:none;}.beam{display:none;}}
@media (max-width:860px){.hero{grid-template-columns:1fr;gap:1.6rem;}}

/* ---------- step rail ---------- */
.rail{display:flex;gap:0;margin:0 0 1.8rem;}
.rail-step{flex:1;display:flex;align-items:center;gap:.7rem;color:var(--silver);position:relative;}
.rail-step:not(:last-child)::after{content:"";height:2px;flex:1;margin:0 .9rem;background:var(--soap2);}
.rail-num{width:34px;height:34px;border-radius:50%;display:grid;place-items:center;flex:none;
  font:700 1.05rem/1 var(--manu);border:2px solid var(--soap2);background:var(--soap);}
.stApp .rail-label{font-weight:600;font-size:.98rem;}
.rail-step.done{color:var(--ink);}
.rail-step.done .rail-num{background:var(--ink);border-color:var(--ink);color:#fff;}
.rail-step.done::after{background:var(--ink);}
.rail-step.now{color:var(--ink);}
.rail-step.now .rail-num{background:var(--turmeric);border-color:var(--turmeric);color:var(--ink);
  box-shadow:0 0 0 5px rgba(232,163,23,.22);}
@media (max-width:700px){.rail-label{display:none;}.rail-step:not(:last-child)::after{margin:0 .4rem;}}

/* ---------- upload ---------- */
[data-testid="stFileUploaderDropzone"]{background:rgba(255,255,255,.45);border:2px dashed var(--silver);
  border-radius:8px;padding:1.5rem;}
[data-testid="stFileUploaderDropzone"]:hover{border-color:var(--kumkuma);background:rgba(255,255,255,.7);}
.stApp .try-label{font-size:.95rem;color:var(--ink2);margin:1.1rem 0 .4rem;}

/* ---------- buttons ---------- */
.stButton > button,.stDownloadButton > button{border-radius:5px;font-weight:600;font-family:var(--body);
  border:1.5px solid var(--ink);background:transparent;color:var(--ink);transition:background .15s,color .15s,transform .1s;}
.stButton > button:hover,.stDownloadButton > button:hover{background:var(--ink);color:#fff;border-color:var(--ink);}
.stButton > button:active{transform:translateY(1px);}
.stButton > button[kind="primary"]{background:var(--kumkuma);border-color:var(--kumkuma);color:#fff;
  padding:.62rem 1.6rem;font-size:1.02rem;box-shadow:0 8px 18px -10px rgba(163,31,26,.8);}
.stButton > button[kind="primary"]:hover{background:#85150F;border-color:#85150F;}
.stButton > button:focus-visible,.stDownloadButton > button:focus-visible{outline:3px solid var(--turmeric);outline-offset:2px;}
.stButton > button:disabled{opacity:.45;}

/* ---------- result header ---------- */
.result{display:flex;gap:1.5rem;align-items:center;padding:1.2rem 0 1.6rem;}
.ring{position:relative;width:104px;height:104px;flex:none;}
.ring svg{transform:rotate(-90deg);}
.stApp .ring-num{position:absolute;inset:0;display:grid;place-items:center;font:800 1.5rem/1 var(--display);color:var(--ink);}
.stApp .ring-cap{font-size:.78rem;color:var(--ink2);margin-top:.25rem;text-align:center;}
.stApp .verdict{font:800 1.8rem/1.1 var(--display);letter-spacing:-.02em;margin:0 0 .35rem;}
.stApp .hint{color:var(--ink2);margin:0 0 .8rem;max-width:36rem;line-height:1.5;}
.stApp .chips{display:flex;flex-wrap:wrap;gap:.45rem;}
.stApp .chip{font-size:.85rem;font-weight:500;padding:.22rem .7rem;border-radius:99px;background:var(--soap2);color:var(--ink);}
.stApp .chip.vision{background:var(--ink);color:#fff;}

/* ---------- plates ---------- */
.stApp .plate-title{font:700 1.15rem/1.2 var(--display);margin:1.5rem 0 .7rem;}
[data-testid="stTextArea"] textarea{
  font-family:var(--manu);font-size:1.3rem;line-height:2.05;color:var(--leafink);
  background:
   radial-gradient(circle at 1.5rem 18%,var(--soap) 0 .52rem,rgba(0,0,0,.32) .58rem,transparent .66rem),
   radial-gradient(circle at 1.5rem 82%,var(--soap) 0 .52rem,rgba(0,0,0,.32) .58rem,transparent .66rem),
   repeating-linear-gradient(to bottom,rgba(110,90,30,.08) 0 1px,transparent 1px 7px),
   linear-gradient(180deg,#DDD5A3,var(--leaf));
  border:1px solid var(--leaf2);border-radius:10px;padding:1.2rem 1.3rem 1.2rem 3.4rem;
  box-shadow:0 18px 30px -22px rgba(19,32,27,.55);}
[data-testid="stTextArea"] textarea:focus{border-color:var(--kumkuma);box-shadow:0 0 0 3px rgba(163,31,26,.18);}
[data-testid="stImage"] img{border:9px solid #fff;border-radius:2px;
  box-shadow:0 1px 0 rgba(0,0,0,.18),0 18px 28px -18px rgba(19,32,27,.55);}
mark{background:#F2C94C;color:var(--ink);padding:0 3px;border-radius:3px;}
.big{font-family:var(--manu);font-size:1.15rem;line-height:2;}

/* ---------- tabs, expanders, alerts ---------- */
[data-baseweb="tab-list"]{gap:1.4rem;border-bottom:1px solid var(--soap2);}
button[data-baseweb="tab"]{padding:.6rem 0;font-weight:600;font-family:var(--body);background:transparent;}
[data-baseweb="tab-highlight"]{background:var(--kumkuma)!important;height:3px!important;}
[data-testid="stExpander"]{border:1px solid var(--soap2);border-left:4px solid var(--turmeric);border-radius:4px;background:rgba(255,255,255,.35);}
[data-testid="stAlert"] *{color:var(--ink)!important;}
[data-testid="stAlert"]{border-radius:4px;background:rgba(232,163,23,.12);color:var(--ink);border:0;border-left:4px solid var(--turmeric);}
div[data-baseweb="progress-bar"] > div > div{background:var(--turmeric)!important;}
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:6px;}
hr{border-color:var(--soap2);}

.stApp .pagehead{margin:.2rem 0 1.4rem;}
.stApp .pagehead h1{margin:0 0 .35rem;}
.stApp .pagehead p{margin:0;color:var(--ink2);font-size:1.05rem;}
.stApp .stApp .bars{margin:.4rem 0 2rem;max-width:760px;}
.bars h4{font:700 1.02rem var(--display);margin:1.1rem 0 .5rem;}
.bar-row{display:grid;grid-template-columns:150px 1fr 64px;gap:.9rem;align-items:center;margin:.38rem 0;font-size:.95rem;}
.bar-row b{font:700 1.02rem var(--display);text-align:right;}
.bar{height:16px;border-radius:3px;background:var(--soap2);overflow:hidden;}
.bar i{display:block;height:100%;background:var(--kumkuma);border-radius:3px;}
.bar.good i{background:var(--ink);}
.legend{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:1.4rem;margin:.6rem 0 1.2rem;}
.stApp .legend b{font:700 1.08rem var(--display);display:block;margin-bottom:.3rem;}
.stApp .legend span{color:var(--ink2);line-height:1.5;font-size:.97rem;}
/* ================= readable in ANY browser mode (light or dark) =================
   Streamlit follows the visitor's system theme, which can paint pale text on our light page.
   So every visible piece of main-area text and every widget is coloured explicitly here. */
:root{color-scheme:light;}
.stApp [data-testid="stMain"] :where(p,span,label,li,small,h1,h2,h3,h4,h5,h6,summary,td,th,strong,em,div[data-testid="stCaptionContainer"]){color:var(--ink);}
.stApp [data-testid="stMain"] a{color:var(--kumkuma);}
.stApp [data-testid="stMain"] [data-testid="stCaptionContainer"] *{color:var(--ink2);}
.stApp [data-testid="stMain"] [data-testid="stWidgetLabel"] *{color:var(--ink);font-weight:600;}
.stApp [data-testid="stMain"] [data-testid="stTooltipIcon"] svg{color:var(--silver);}

/* toolbar: hide Streamlit's Deploy / menu chrome so it looks like a product */
[data-testid="stToolbarActions"],[data-testid="stMainMenu"],[data-testid="stAppDeployButton"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"]{display:none!important;}
/* NOTE: the toolbar itself must stay: it holds the button that re-opens the sidebar. */
@media (min-width:992px){[data-testid="stSidebarCollapseButton"]{display:none!important;}}   /* keep the menu always visible on wide screens */
.st-key-mobilenav{display:none;}
@media (max-width:991px){.st-key-mobilenav{display:block;margin:.9rem 0 1.2rem;}}
/* camera mode: the picker is really a camera button, so say so and drop the drag-and-drop hint */
.st-key-camwrap [data-testid="stFileUploaderDropzone"]{justify-content:center;text-align:center;}
.st-key-camwrap [data-testid="stFileUploaderDropzoneInstructions"]{display:none!important;}
.st-key-camwrap [data-testid="stFileUploaderDropzone"] button,
.st-key-camwrap [data-testid="stFileUploaderDropzone"] button *{font-size:0!important;}
.st-key-camwrap [data-testid="stFileUploaderDropzone"] button::after{content:"Open camera";font-size:1.05rem;
  font-weight:700;color:var(--ink);}

/* ---- upload: a large, obvious drop slot with a gold call-to-action ---- */
.stApp [data-testid="stFileUploaderDropzone"]{background:#F6F5EA;border:2px dashed var(--leaf2);
  border-radius:10px;padding:1.6rem 1.8rem;display:flex;align-items:center;gap:1.4rem;min-height:110px;}
.stApp [data-testid="stFileUploaderDropzone"]:hover{border-color:var(--kumkuma);background:#FBFAF0;}
.stApp [data-testid="stFileUploaderDropzone"] button{background:var(--turmeric)!important;color:var(--ink)!important;
  border:0!important;border-radius:6px!important;padding:.7rem 1.6rem!important;font-weight:700!important;font-size:1.02rem!important;
  box-shadow:0 10px 18px -10px rgba(185,127,0,.9);transition:transform .12s,background .15s;}
.stApp [data-testid="stFileUploaderDropzone"] button:hover{background:#F2B52B!important;transform:translateY(-2px);}
.stApp [data-testid="stFileUploaderDropzone"] button *{color:var(--ink)!important;}
.stApp [data-testid="stFileUploaderDropzoneInstructions"] *{color:var(--ink2)!important;font-size:.95rem;}
.stApp [data-testid="stFileUploaderFile"]{background:#fff;border:1px solid var(--soap2);border-radius:6px;padding:.3rem .6rem;}
.stApp [data-testid="stFileUploaderFile"] *{color:var(--ink)!important;}

/* ---- toggle and checkboxes ---- */
.stApp [data-testid="stCheckbox"] label > div:nth-child(2){background:#fff!important;border:2px solid var(--ink2)!important;}
.stApp [data-testid="stCheckbox"] label:has(input:checked) > div:nth-child(2){background:var(--kumkuma)!important;border-color:var(--kumkuma)!important;}
.stApp [data-testid="stCheckbox"] label:has(input[role="switch"]) > div:nth-child(2){background:#B9C4BD!important;border-color:#B9C4BD!important;}
.stApp [data-testid="stCheckbox"] label:has(input[role="switch"]:checked) > div:nth-child(2){background:var(--kumkuma)!important;border-color:var(--kumkuma)!important;}
.stApp [data-testid="stCheckbox"] label:has(input[role="switch"]) > div:nth-child(2) > div{background:#fff!important;box-shadow:0 1px 3px rgba(0,0,0,.35);}
.stApp [data-testid="stCheckbox"] label:has(input:disabled){opacity:.5;}

/* ---- tabs ---- */
.stApp [data-testid="stMain"] button[data-baseweb="tab"] *{color:var(--ink2)!important;font-weight:600;}
.stApp [data-testid="stMain"] button[data-baseweb="tab"][aria-selected="true"] *{color:var(--ink)!important;font-weight:700;}
.stApp [data-testid="stMain"] button[data-baseweb="tab"]:hover *{color:var(--kumkuma)!important;}

/* ---- inputs ---- */
.stApp [data-baseweb="input"]{background:#fff!important;border:1.5px solid var(--silver)!important;border-radius:6px!important;}
.stApp [data-baseweb="input"] [data-baseweb="base-input"]{background:transparent!important;border:0!important;}
.stApp [data-testid="stTextInputRootElement"],.stApp [data-testid="stNumberInputContainer"]{background:#fff!important;border:1.5px solid var(--silver)!important;border-radius:6px!important;}
.stApp [data-testid="stTextInputRootElement"]:focus-within,.stApp [data-testid="stNumberInputContainer"]:focus-within{border-color:var(--kumkuma)!important;box-shadow:0 0 0 3px rgba(163,31,26,.15);}
.stApp [data-testid="stTextAreaRootElement"]{background:transparent!important;border:0!important;box-shadow:none!important;}
.stApp [data-baseweb="input"]:focus-within{border-color:var(--kumkuma)!important;box-shadow:0 0 0 3px rgba(163,31,26,.15);}
.stApp [data-testid="stMain"] input{background:#fff!important;color:var(--ink)!important;-webkit-text-fill-color:var(--ink);}
.stApp [data-testid="stMain"] input::placeholder{color:#6B7A72!important;-webkit-text-fill-color:#6B7A72;}
.stApp [data-testid="stTextArea"] [data-baseweb="textarea"],.stApp [data-testid="stTextArea"] [data-baseweb="base-input"]{background:transparent!important;border:0!important;box-shadow:none!important;}

/* ---- expanders, status panel, alerts, code ---- */
.stApp [data-testid="stExpander"] summary,.stApp [data-testid="stExpander"] summary *{color:var(--ink)!important;font-weight:600;}
.stApp [data-testid="stExpander"] details{background:rgba(255,255,255,.4);}
.stApp [data-testid="stStatus"],.stApp [data-testid="stExpander"][data-testid="stStatus"]{border-left:4px solid var(--turmeric);}
.stApp [data-testid="stAlert"]{background:rgba(232,163,23,.14)!important;}
.stApp [data-testid="stCode"] pre,.stApp [data-testid="stCode"] code{background:#F1EEC9!important;color:var(--leafink)!important;
  font-family:var(--manu)!important;font-size:1.1rem!important;line-height:1.9!important;}
.stApp [data-testid="stCode"] pre{border:1px solid var(--leaf2);border-radius:8px;}
.stApp [data-testid="stCode"] code *{color:var(--leafink)!important;}
.stApp [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,.45);border-color:var(--soap2);}

/* ---- buttons: text must stay legible in every state ---- */
.stApp .stButton > button[kind="primary"] *,.stApp .stButton > button[kind="primary"]:hover *{color:#fff!important;}
.stApp .stButton > button[kind="secondary"]:hover *,.stApp .stDownloadButton > button:hover *{color:#fff!important;}
.stApp .stButton > button[kind="secondary"] *,.stApp .stDownloadButton > button *{color:var(--ink);}
.stApp .stButton > button:disabled,.stApp .stButton > button:disabled *{color:#5B6A62!important;}
.stApp .stButton > button[kind="primary"]:disabled{background:#CDD3CC!important;border-color:#CDD3CC!important;box-shadow:none!important;}
.stApp .stButton > button[kind="primary"]:disabled *{color:#4A5851!important;}

/* ---- gentle interactivity (answers a hover or a click, nothing plays by itself) ---- */
.stApp [data-testid="stImage"] img{transition:transform .18s,box-shadow .18s;}
.stApp [data-testid="stImage"]:hover img{transform:translateY(-3px);box-shadow:0 1px 0 rgba(0,0,0,.18),0 24px 30px -18px rgba(19,32,27,.6);}
.stApp .stButton > button,.stApp .stDownloadButton > button{min-height:2.7rem;}
.stApp [data-testid="stToast"]{border-left:4px solid var(--turmeric);}
.stApp .chip.vision{background:var(--ink);color:#fff;}
.stApp .chip.vision *{color:#fff;}

/* ================= workspace: compact bar, view switch, text plates ================= */
.stApp .bar-compact{display:flex;align-items:center;gap:1rem;}
.stApp .bar-compact .ring{width:62px;height:62px;}
.stApp .bar-compact .ring svg{width:62px;height:62px;}
.stApp .bar-compact .ring-num{font-size:1.02rem;}
.stApp .bar-compact .verdict{font:800 1.25rem/1.1 var(--display);margin:0 0 .3rem;}
.stApp .bar-compact .chips{gap:.35rem;}
.stApp .bar-compact .chip{font-size:.78rem;padding:.12rem .55rem;}

.leafplate{position:relative;border-radius:10px;border:1px solid var(--leaf2);padding:1.3rem 1.5rem 1.3rem 3.4rem;
  background:
   radial-gradient(circle at 1.5rem 12%,var(--soap) 0 .52rem,rgba(0,0,0,.32) .58rem,transparent .66rem),
   radial-gradient(circle at 1.5rem 88%,var(--soap) 0 .52rem,rgba(0,0,0,.32) .58rem,transparent .66rem),
   repeating-linear-gradient(to bottom,rgba(110,90,30,.08) 0 1px,transparent 1px 7px),
   linear-gradient(180deg,#DDD5A3,var(--leaf));
  box-shadow:0 18px 30px -22px rgba(19,32,27,.55);color:var(--leafink);}
.stApp .leafplate p{color:var(--leafink);font:500 1.12rem/1.85 var(--body);margin:0 0 .8rem;}
.stApp .leafplate p:last-child{margin-bottom:0;}
.stApp .leafplate.kn p{font:500 1.3rem/2.05 var(--manu);}
.leafnote{font-size:.85rem;color:var(--ink2);margin:.55rem 0 0;}

.pairs{border:1px solid var(--leaf2);border-radius:10px;overflow:hidden;box-shadow:0 18px 30px -22px rgba(19,32,27,.55);}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:0;border-top:1px solid rgba(110,90,30,.22);}
.pair:first-child{border-top:0;}
.pair > div{padding:.8rem 1.1rem;}
.stApp .pair .kn{font:600 1.18rem/1.7 var(--manu);color:var(--leafink);background:linear-gradient(180deg,#DDD5A3,var(--leaf));}
.stApp .pair .en{font:500 1.02rem/1.65 var(--body);color:var(--ink);background:#F6F5EA;}
.pairhead{display:grid;grid-template-columns:1fr 1fr;background:var(--ink);}
.stApp .pairhead div{padding:.5rem 1.1rem;font:700 .85rem var(--body);color:#fff;}
@media (max-width:700px){.pair{grid-template-columns:1fr;}.pairhead{display:none;}}

/* view switch (Streamlit builds it as a button group) */
.stApp [data-testid="stButtonGroup"] button{background:#fff!important;border:1.5px solid var(--silver)!important;
  color:var(--ink)!important;font-weight:600;border-radius:6px!important;min-height:2.5rem;padding:.3rem 1.1rem;}
.stApp [data-testid="stButtonGroup"] button *{color:var(--ink)!important;}
.stApp [data-testid="stButtonGroup"] button:hover{border-color:var(--ink)!important;}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"],
.stApp [data-testid="stButtonGroup"] button[aria-pressed="true"]{background:var(--ink)!important;border-color:var(--ink)!important;}
.stApp [data-testid="stButtonGroup"] button[aria-checked="true"] *,
.stApp [data-testid="stButtonGroup"] button[aria-pressed="true"] *{color:#fff!important;}

/* popover (Download menu) renders in a portal outside .stApp, so it is styled directly */
[data-testid="stPopover"] > button,[data-testid="stPopoverButton"]{background:transparent!important;border:1.5px solid var(--ink)!important;
  border-radius:5px!important;color:var(--ink)!important;font-weight:600;min-height:2.7rem;}
[data-testid="stPopover"] > button *,[data-testid="stPopoverButton"] *{color:var(--ink)!important;}
[data-testid="stPopoverBody"]{background:#fff!important;border:1px solid var(--soap2);border-radius:8px;}
[data-testid="stPopoverBody"] p,[data-testid="stPopoverBody"] span,[data-testid="stPopoverBody"] label{color:var(--ink)!important;}
[data-testid="stPopoverBody"] button{background:#fff!important;border:1.5px solid var(--ink)!important;border-radius:5px!important;
  color:var(--ink)!important;font-weight:600;}
[data-testid="stPopoverBody"] button *{color:var(--ink)!important;}
[data-testid="stPopoverBody"] button:hover{background:var(--ink)!important;}
[data-testid="stPopoverBody"] button:hover *{color:#fff!important;}

"""


def _h(s: str) -> str:
    """Join an HTML snippet onto one line so Markdown never treats it as code."""
    return " ".join(line.strip() for line in s.strip().splitlines())


def inject() -> None:
    st.markdown("<style>" + CSS.replace("__FONTS__", FONTS) + "</style>", unsafe_allow_html=True)


def sidebar_brand() -> None:
    st.sidebar.markdown(_h("""
      <div class="brand"><div class="brand-mark"></div>
        <div><div class="brand-name">Kannada Digitizer</div>
        <div class="brand-kn">ಕನ್ನಡ ಡಿಜಿಟೈಸರ್</div></div></div>"""), unsafe_allow_html=True)


def sidebar_status(label: str | None) -> None:
    on = bool(label)
    text = f"AI helper ready ({html.escape(label)})" if on else "AI helper off, basic mode"
    st.sidebar.markdown(
        f'<div class="status"><span class="dot {"on" if on else ""}"></span>{text}</div>',
        unsafe_allow_html=True)


def hero() -> None:
    st.markdown(_h("""
      <section class="hero">
        <div>
          <h1 class="hero-title">Kannada on paper,<br>now searchable.</h1>
          <p class="hero-sub">Upload a photo, scan or PDF. Get clean text you can edit,
          search, translate and listen to.</p>
        </div>
        <div class="leaf" role="img" aria-label="A palm-leaf strip turning into clear digital text">
          <div class="leaf-hole"></div>
          <div class="leaf-text rough">ಕರ್ನಾಟಕದ ಜ್ಞಾನ</div>
          <div class="leaf-text crisp">ಕರ್ನಾಟಕದ ಜ್ಞಾನ</div>
          <div class="beam"></div>
        </div>
      </section>"""), unsafe_allow_html=True)


def steps(now: int) -> None:
    """Upload, Read, Check, Use: a real sequence, so Kannada numerals are earned."""
    names = ["Upload", "Read", "Check", "Use"]
    nums = "೧೨೩೪"
    out = []
    for i, (n, k) in enumerate(zip(names, nums), start=1):
        cls = "done" if i < now else ("now" if i == now else "")
        out.append(f'<div class="rail-step {cls}"><div class="rail-num">{k}</div>'
                   f'<div class="rail-label">{n}</div></div>')
    st.markdown('<div class="rail">' + "".join(out) + "</div>", unsafe_allow_html=True)


def result_header(avg: float, pages: int, engines: str, variant: str) -> None:
    pct = max(0, min(100, round(avg)))
    if pct >= 90:
        verdict, hint, color = "Clean read", "The text looks solid. A quick look is still wise before you share it.", "#13201B"
    elif pct >= 70:
        verdict, hint, color = "Good read", "Check the words marked in yellow below. Those are the ones the reader doubted.", "#E8A317"
    else:
        verdict, hint, color = "Rough read", "This page was hard. Check every line, or turn on handwriting mode for the AI reader.", "#A31F1A"
    c = 2 * 3.14159 * 44
    dash = c * pct / 100
    ring = (f'<div><div class="ring"><svg width="104" height="104" viewBox="0 0 104 104">'
            f'<circle cx="52" cy="52" r="44" fill="none" stroke="#D8DED4" stroke-width="9"/>'
            f'<circle cx="52" cy="52" r="44" fill="none" stroke="{color}" stroke-width="9" '
            f'stroke-linecap="round" stroke-dasharray="{dash:.1f} {c:.1f}"/></svg>'
            f'<div class="ring-num">{pct}%</div></div><div class="ring-cap">reader confidence</div></div>')
    vision = engines.lower().startswith("vision") or variant == "vision"
    chips = (f'<span class="chip">{pages} page{"s" if pages != 1 else ""}</span>'
             f'<span class="chip {"vision" if vision else ""}">Read by {"AI vision" if vision else "Tesseract"}</span>'
             f'<span class="chip">Cleanup: {html.escape(variant)}</span>')
    st.markdown(f'<div class="result">{ring}<div><p class="verdict">{verdict}</p>'
                f'<p class="hint">{hint}</p><div class="chips">{chips}</div></div></div>',
                unsafe_allow_html=True)


def about_legend(items) -> None:
    cells = "".join(f"<div><b>{html.escape(t)}</b><span>{html.escape(d)}</span></div>" for t, d in items)
    st.markdown(f'<div class="legend">{cells}</div>', unsafe_allow_html=True)


def accuracy_bars(groups) -> None:
    """groups: [(title, [(label, pct, is_ours), ...]), ...]  (character error rate, lower is better)"""
    out = []
    for title, rows in groups:
        out.append(f"<h4>{html.escape(title)}</h4>")
        for label, pct, ours in rows:
            w = max(pct, 1.2)
            out.append(f'<div class="bar-row"><span>{html.escape(label)}</span>'
                       f'<div class="bar {"good" if ours else ""}"><i style="width:{w}%"></i></div>'
                       f'<b>{pct:g}%</b></div>')
    st.markdown('<div class="bars">' + "".join(out) + "</div>", unsafe_allow_html=True)


def result_bar(avg: float, pages: int, engines: str, variant: str) -> None:
    """Compact confidence summary for the top bar of the workspace."""
    pct = max(0, min(100, round(avg)))
    if pct >= 90:
        verdict, color = "Clean read", "#13201B"
    elif pct >= 70:
        verdict, color = "Good read", "#E8A317"
    else:
        verdict, color = "Rough read", "#A31F1A"
    c = 2 * 3.14159 * 44
    ring = (f'<div class="ring"><svg width="62" height="62" viewBox="0 0 104 104">'
            f'<circle cx="52" cy="52" r="44" fill="none" stroke="#D8DED4" stroke-width="10"/>'
            f'<circle cx="52" cy="52" r="44" fill="none" stroke="{color}" stroke-width="10" '
            f'stroke-linecap="round" stroke-dasharray="{c * pct / 100:.1f} {c:.1f}"/></svg>'
            f'<div class="ring-num">{pct}%</div></div>')
    vision = engines.lower().startswith("vision") or variant == "vision"
    chips = (f'<span class="chip">{pages} page{"s" if pages != 1 else ""}</span>'
             f'<span class="chip {"vision" if vision else ""}">{"AI vision" if vision else "Tesseract"}</span>')
    hint = {"Clean read": "Looks solid", "Good read": "Check the yellow words",
            "Rough read": "Please review every line"}[verdict]
    st.markdown(f'<div class="bar-compact">{ring}<div><p class="verdict">{verdict}</p>'
                f'<div class="chips"><span class="chip">{hint}</span>{chips}</div></div></div>',
                unsafe_allow_html=True)


def english_plate(text: str, note: str = "") -> None:
    """The English meaning on a palm-leaf plate, one paragraph per line break."""
    paras = "".join(f"<p>{html.escape(p)}</p>" for p in text.split("\n") if p.strip())
    extra = f'<p class="leafnote">{html.escape(note)}</p>' if note else ""
    st.markdown(f'<div class="leafplate">{paras}</div>{extra}', unsafe_allow_html=True)


def kannada_plate(inner_html: str) -> None:
    st.markdown(f'<div class="leafplate kn">{inner_html}</div>', unsafe_allow_html=True)


def pairs_view(pairs) -> None:
    """Each Kannada line with its English meaning beside it."""
    rows = "".join(f'<div class="pair"><div class="kn">{html.escape(k)}</div>'
                   f'<div class="en">{html.escape(e)}</div></div>' for k, e in pairs)
    st.markdown('<div class="pairs"><div class="pairhead"><div>Kannada</div><div>English</div></div>'
                + rows + "</div>", unsafe_allow_html=True)


def page_head(title: str, sub: str) -> None:
    st.markdown(f'<div class="pagehead"><h1>{html.escape(title)}</h1><p>{html.escape(sub)}</p></div>',
                unsafe_allow_html=True)


def plate_title(text: str) -> None:
    st.markdown(f'<p class="plate-title">{html.escape(text)}</p>', unsafe_allow_html=True)
