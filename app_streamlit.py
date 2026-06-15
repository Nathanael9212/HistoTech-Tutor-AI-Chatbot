"""
HistoTech Tutor — Streamlit Web App
Final Project: LLM-Based Tools & Claude API

Run: streamlit run app_streamlit.py
"""

import os
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

def markdown_to_html(text):
    import re
    # Escape HTML tags
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Headers
    text = re.sub(r'^###[ \t]+(.*?)$', r'<h5 style="margin: 8px 0 4px 0; font-size: 1.1em;">\1</h5>', text, flags=re.MULTILINE)
    text = re.sub(r'^##[ \t]+(.*?)$', r'<h4 style="margin: 10px 0 6px 0; font-size: 1.2em;">\1</h4>', text, flags=re.MULTILINE)
    text = re.sub(r'^#[ \t]+(.*?)$', r'<h3 style="margin: 12px 0 8px 0; font-size: 1.3em;">\1</h3>', text, flags=re.MULTILINE)
    
    # Bold
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong>\1</strong>', text)
    
    # Italic
    text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
    text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
    
    # Code block
    text = re.sub(
        r'```(?:[a-zA-Z0-9_-]+)?\n(.*?)\n```', 
        r'<pre style="background: #eef1f6; padding: 10px; border-radius: 6px; overflow-x: auto; font-family: monospace; font-size: 0.9em; margin: 8px 0; border: 1px solid #ddd; color: #212529;"><code>\1</code></pre>', 
        text, 
        flags=re.DOTALL
    )
    
    # Inline code
    text = re.sub(
        r'`(.*?)`', 
        r'<code style="background: #eef1f6; padding: 2px 5px; border-radius: 4px; font-family: monospace; font-size: 0.9em; border: 1px solid #ddd; color: #212529;">\1</code>', 
        text
    )
    
    # Lists
    lines = text.split('\n')
    in_list = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('- ') or stripped.startswith('* '):
            if not in_list:
                new_lines.append('<ul style="margin: 6px 0; padding-left: 20px;">')
                in_list = True
            new_lines.append(f'<li style="margin-bottom: 4px;">{stripped[2:]}</li>')
        else:
            if in_list:
                new_lines.append('</ul>')
                in_list = False
            new_lines.append(line)
    if in_list:
        new_lines.append('</ul>')
    text = '\n'.join(new_lines)
    
    # Newlines
    text = text.replace("\n", "<br>")
    return text


# ── Page config ───────────────────────────────────
st.set_page_config(
    page_title="HistoTech Tutor",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ────────────────────────────────────
st.markdown("""
<style>
  /* Header bot */
  .bot-header {
    background: linear-gradient(135deg, #1a1a2e, #16213e);
    color: white;
    padding: 16px 20px;
    border-radius: 12px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .domain-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    margin-top: 6px;
  }
  /* Chat bubbles */
  .user-bubble {
    background: #1a1a2e;
    color: white;
    padding: 12px 16px;
    border-radius: 16px 16px 4px 16px;
    margin: 8px 0 8px 60px;
    font-size: 14px;
    line-height: 1.6;
  }
  .bot-bubble {
    background: #f8f9fa;
    color: #212529;
    padding: 12px 16px;
    border-radius: 16px 16px 16px 4px;
    margin: 8px 60px 8px 0;
    font-size: 14px;
    line-height: 1.6;
    border: 1px solid #e9ecef;
  }
  .msg-label {
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 4px;
  }
  .user-label { color: rgba(255,255,255,0.6); }
  .bot-label  { color: #7F77DD; }
  /* Stats bar */
  .stat-card {
    text-align: center;
    padding: 10px;
    border-radius: 8px;
    background: #f8f9fa;
    border: 1px solid #e9ecef;
  }
  .stat-val { font-size: 22px; font-weight: 700; }
  .stat-lbl { font-size: 11px; color: #6c757d; }
</style>
""", unsafe_allow_html=True)

# ── System Prompts ────────────────────────────────
SYSTEM_PROMPTS = {
    "🌐 Semua Topik": """Kamu adalah HistoTech Tutor, asisten AI edukasi berbahasa Indonesia yang sangat ahli di bidang sejarah peradaban, teknologi, pertahanan siber, sains (biologi, fisika, kimia, matematika, psikologi). Gaya bahasamu cerdas namun santai seperti guru privat yang sabar. Selalu berikan penjelasan mendalam dan terstruktur dengan konteks sejarah, cara kerja, dan komponen spesifik.""",

    "🏛️ Sejarah": """Kamu adalah HistoTech Tutor spesialis SEJARAH PERADABAN berbahasa Indonesia. Untuk setiap pertanyaan sejarah, jelaskan: latar belakang konteks zaman, asal usul dan perkembangan, alat/teknologi pada zaman tersebut (komponen + cara pembuatan), dampak peradaban, dan relevansi masa modern. Gunakan narasi yang hidup dan kaya detail.""",

    "🛡️ Cyber Security": """Kamu adalah HistoTech Tutor spesialis KEAMANAN SIBER berbahasa Indonesia. Jelaskan: definisi dan konsep dasar, sejarah perkembangan, cara kerja teknis secara mendidik, komponen dan struktur sistem, penerapan keamanan di dunia nyata. Konteks pembelajaran dan edukasi murni.""",

    "⚛️ Sains": """Kamu adalah HistoTech Tutor spesialis ILMU PENGETAHUAN berbahasa Indonesia. Jelaskan: konsep inti ilmiah, sejarah penemuan dan ilmuwan yang terlibat, cara kerja mekanismenya, penerapan praktis, dan perkembangan terkini. Gunakan analogi yang tepat.""",

    "⚙️ Teknologi": """Kamu adalah HistoTech Tutor spesialis TEKNOLOGI & ENGINEERING berbahasa Indonesia. Jelaskan: definisi dan fungsi, struktur dan komponen spesifik (kegunaan masing-masing), cara kerja internal, proses pembuatan (dulu vs sekarang), dan inovasi terkini.""",
}

DOMAIN_COLORS = {
    "🌐 Semua Topik":    "#4dabf7",
    "🏛️ Sejarah":        "#ff922b",
    "🛡️ Cyber Security": "#51cf66",
    "⚛️ Sains":          "#22d3ee",
    "⚙️ Teknologi":      "#a78bfa",
}

# ── Session state ─────────────────────────────────
if "messages"    not in st.session_state: st.session_state.messages    = []
if "domain"      not in st.session_state: st.session_state.domain      = "🌐 Semua Topik"
if "msg_count"   not in st.session_state: st.session_state.msg_count   = 0
if "session_start" not in st.session_state: st.session_state.session_start = datetime.now()

# ── Sidebar ───────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi")

    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        placeholder="AIzaSy..."
    )

    st.divider()

    st.markdown("### 🎯 Domain Topik")
    domain = st.radio(
        "Pilih domain:",
        list(SYSTEM_PROMPTS.keys()),
        index=list(SYSTEM_PROMPTS.keys()).index(st.session_state.domain),
        label_visibility="collapsed"
    )
    st.session_state.domain = domain

    st.divider()

    st.markdown("### 📊 Statistik Sesi")
    duration = datetime.now() - st.session_state.session_start
    mins = int(duration.total_seconds() // 60)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
          <div class="stat-val">{st.session_state.msg_count}</div>
          <div class="stat-lbl">Pesan</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
          <div class="stat-val">{mins}m</div>
          <div class="stat-lbl">Durasi</div>
        </div>""", unsafe_allow_html=True)

    st.divider()

    if st.button("🗑️ Hapus Riwayat", use_container_width=True):
        st.session_state.messages  = []
        st.session_state.msg_count = 0
        st.rerun()

    st.markdown("""
    <div style="font-size:11px; color:#adb5bd; margin-top:12px; text-align:center;">
      Model: gemini-2.5-flash<br>
      HistoTech Tutor v1.0
    </div>""", unsafe_allow_html=True)

# ── Main area ──────────────────────────────────────
color = DOMAIN_COLORS[st.session_state.domain]

st.markdown(f"""
<div class="bot-header">
  <div style="width:46px;height:46px;border-radius:50%;background:linear-gradient(135deg,#7F77DD,#1D9E75);
    display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;color:white;flex-shrink:0;">HT</div>
  <div>
    <div style="font-size:18px;font-weight:700;">HistoTech Tutor</div>
    <div style="font-size:12px;opacity:0.6;">AI Edukasi · Sejarah, Teknologi & Sains</div>
    <div class="domain-badge" style="background:{color}22;color:{color};border:1px solid {color}44;">
      {st.session_state.domain}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Welcome message ───────────────────────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="bot-bubble">
      <div class="msg-label bot-label">HistoTech Tutor · Selamat Datang!</div>
      Halo! Aku adalah <strong>HistoTech Tutor</strong> — asisten AI edukasi yang siap membantumu memahami
      sejarah peradaban, teknologi, pertahanan siber, sains, dan banyak lagi. 🎓<br><br>
      Pilih domain di sidebar untuk fokus topik, atau langsung ketik pertanyaanmu!
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**💡 Coba tanya:**")
    cols = st.columns(2)
    suggestions = [
        "Jelaskan cara kerja enkripsi RSA",
        "Sejarah komputer pertama di dunia?",
        "Bagaimana firewall bekerja?",
        "Teori evolusi Charles Darwin",
    ]
    for i, sug in enumerate(suggestions):
        with cols[i % 2]:
            if st.button(f"→ {sug}", key=f"sug_{i}", use_container_width=True):
                st.session_state._pending_input = sug
                st.rerun()

# ── Render chat history ───────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        content = markdown_to_html(msg["content"])
        st.markdown(f"""
        <div class="user-bubble">
          <div class="msg-label user-label">Kamu</div>
          {content}
        </div>""", unsafe_allow_html=True)
    else:
        content = markdown_to_html(msg["content"])
        st.markdown(f"""
        <div class="bot-bubble">
          <div class="msg-label bot-label">HistoTech Tutor</div>
          {content}
        </div>""", unsafe_allow_html=True)

# ── Handle suggestion click ───────────────────────
pending = getattr(st.session_state, "_pending_input", None)
if pending:
    del st.session_state._pending_input
    user_input = pending
else:
    user_input = None

# ── Chat input ────────────────────────────────────
typed = st.chat_input("Ketik pertanyaanmu di sini...")
if typed:
    user_input = typed

# ── Process and respond ───────────────────────────
if user_input:
    if not api_key:
        st.error("⚠️ Masukkan API Key di sidebar terlebih dahulu!")
    else:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.msg_count += 1

        # Render user bubble immediately
        user_formatted = markdown_to_html(user_input)
        st.markdown(f"""
        <div class="user-bubble">
          <div class="msg-label user-label">Kamu</div>
          {user_formatted}
        </div>""", unsafe_allow_html=True)

        # Call API
        client = genai.Client(api_key=api_key)
        contents = []
        for msg in st.session_state.messages:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        with st.spinner("HistoTech Tutor sedang berpikir..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPTS[st.session_state.domain],
                        max_output_tokens=1000,
                    )
                )
                reply = response.text
                st.session_state.messages.append({"role": "assistant", "content": reply})

                formatted = markdown_to_html(reply)
                st.markdown(f"""
                <div class="bot-bubble">
                  <div class="msg-label bot-label">HistoTech Tutor · {st.session_state.domain}</div>
                  {formatted}
                </div>""", unsafe_allow_html=True)

            except Exception as e:
                if "API_KEY_INVALID" in str(e) or "invalid" in str(e).lower() or "api key" in str(e).lower():
                    st.error("✗ API Key tidak valid!")
                else:
                    st.error(f"✗ Error: {e}")

        st.rerun()
