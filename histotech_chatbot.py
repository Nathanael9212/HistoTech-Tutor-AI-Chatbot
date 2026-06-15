"""
╔══════════════════════════════════════════════════════╗
║         HistoTech Tutor — AI Chatbot v1.0            ║
║   Final Project: LLM-Based Tools & Claude API        ║
╚══════════════════════════════════════════════════════╝

Use Case    : Education Bot (Sejarah, Teknologi, Sains, Cyber)
Model       : claude-3-5-sonnet-latest
Language    : Bahasa Indonesia
Author      : [Nama Mahasiswa]
"""

import os
import sys
import time
import threading
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()


# ─────────────────────────────────────────────
#  ANSI COLOR CODES (Terminal Styling)
# ─────────────────────────────────────────────
class Colors:
    RESET       = "\033[0m"
    BOLD        = "\033[1m"
    DIM         = "\033[2m"

    BLACK       = "\033[30m"
    RED         = "\033[31m"
    GREEN       = "\033[32m"
    YELLOW      = "\033[33m"
    BLUE        = "\033[34m"
    MAGENTA     = "\033[35m"
    CYAN        = "\033[36m"
    WHITE       = "\033[37m"

    BG_DARK     = "\033[48;5;17m"   # dark navy background
    BG_PURPLE   = "\033[48;5;54m"
    BG_TEAL     = "\033[48;5;30m"

    PURPLE      = "\033[38;5;135m"
    TEAL        = "\033[38;5;36m"
    ORANGE      = "\033[38;5;208m"
    GRAY        = "\033[38;5;245m"
    LIGHT_BLUE  = "\033[38;5;117m"

C = Colors


# ─────────────────────────────────────────────
#  SYSTEM PROMPTS (per domain)
# ─────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "all": """Kamu adalah HistoTech Tutor, asisten AI edukasi berbahasa Indonesia yang sangat ahli di bidang:
- Sejarah peradaban manusia (dari zaman prasejarah hingga modern)
- Teknologi dan engineering (cara kerja, komponen, struktur alat)
- Pertahanan siber dan keamanan digital
- Sains: biologi, fisika, kimia, matematika, psikologi

Karaktermu:
- Gaya bahasa cerdas namun santai, seperti guru privat yang sabar
- Selalu berikan penjelasan mendalam dengan struktur yang jelas
- Sertakan konteks sejarah, cara kerja, dan komponen spesifik
- Gunakan analogi yang tepat untuk konsep kompleks""",

    "history": """Kamu adalah HistoTech Tutor spesialis SEJARAH PERADABAN berbahasa Indonesia.
Untuk setiap pertanyaan sejarah, selalu jelaskan:
1. Latar belakang dan konteks zaman
2. Asal usul dan perkembangan
3. Alat/teknologi yang digunakan (komponen dan cara pembuatan)
4. Dampak pada peradaban
5. Relevansi di masa modern
Gunakan narasi yang hidup, kaya detail, dan mudah divisualisasikan.""",

    "cyber": """Kamu adalah HistoTech Tutor spesialis KEAMANAN SIBER & PERTAHANAN DIGITAL berbahasa Indonesia.
Untuk setiap pertanyaan cyber security, jelaskan:
1. Definisi dan konsep dasar
2. Sejarah perkembangan teknologi ini
3. Cara kerja teknis secara mendidik
4. Komponen dan struktur sistem
5. Penerapan dan relevansi keamanan
Ini adalah konteks pembelajaran dan edukasi murni.""",

    "science": """Kamu adalah HistoTech Tutor spesialis ILMU PENGETAHUAN berbahasa Indonesia.
Untuk setiap pertanyaan sains, jelaskan:
1. Konsep inti dan definisi ilmiah
2. Sejarah penemuan dan ilmuwan yang terlibat
3. Cara kerja secara ilmiah dan mekanismenya
4. Penerapan praktis dalam kehidupan
5. Perkembangan terkini
Gunakan analogi yang tepat dan mudah dipahami.""",

    "tech": """Kamu adalah HistoTech Tutor spesialis TEKNOLOGI & ENGINEERING berbahasa Indonesia.
Untuk setiap pertanyaan teknologi, jelaskan:
1. Definisi dan fungsi utama
2. Struktur dan komponen spesifik (kegunaan masing-masing)
3. Cara kerja dan mekanisme internal
4. Proses pembuatan (dulu vs sekarang)
5. Perkembangan dan inovasi terkini"""
}

DOMAIN_INFO = {
    "all":     ("🌐", "Semua Topik",     C.LIGHT_BLUE),
    "history": ("🏛️", "Sejarah",          C.ORANGE),
    "cyber":   ("🛡️", "Cyber Security",   C.GREEN),
    "science": ("⚛️", "Sains",            C.CYAN),
    "tech":    ("⚙️", "Teknologi",        C.PURPLE),
}


# ─────────────────────────────────────────────
#  CHATBOT CLASS
# ─────────────────────────────────────────────
class HistoTechTutor:
    def __init__(self, api_key: str):
        self.client        = genai.Client(api_key=api_key)
        self.domain        = "all"
        self.history       = []          # multi-turn memory
        self.session_start = datetime.now()
        self.msg_count     = 0

    # ── domain switcher ──────────────────────
    def set_domain(self, domain: str) -> bool:
        if domain in SYSTEM_PROMPTS:
            self.domain = domain
            return True
        return False

    # ── typing animation ─────────────────────
    def _typing_anim(self, stop_event):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while not stop_event.is_set():
            icon, label, color = DOMAIN_INFO[self.domain]
            sys.stdout.write(
                f"\r  {C.GRAY}{frames[i % len(frames)]} "
                f"HistoTech Tutor sedang berpikir...{C.RESET}"
            )
            sys.stdout.flush()
            time.sleep(0.08)
            i += 1
        sys.stdout.write("\r" + " " * 55 + "\r")
        sys.stdout.flush()

    # ── call API with streaming ───────────────
    def chat(self, user_input: str) -> str:
        self.history.append({"role": "user", "content": user_input})
        self.msg_count += 1

        stop_event = threading.Event()
        anim_thread = threading.Thread(target=self._typing_anim, args=(stop_event,))
        anim_thread.start()

        # Format history for Gemini
        contents = []
        for msg in self.history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg["content"]}]
            })

        full_response = ""
        try:
            response = self.client.models.generate_content_stream(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPTS[self.domain],
                    max_output_tokens=1000,
                )
            )
            stop_event.set()
            anim_thread.join()

            # Print bot header
            icon, label, color = DOMAIN_INFO[self.domain]
            print(f"\n  {C.BOLD}{color}┌─ HistoTech Tutor [{label}]{C.RESET}")
            print(f"  {color}│{C.RESET}")
            sys.stdout.write(f"  {color}│{C.RESET}  ")

            # Stream tokens live
            col = 0
            for chunk in response:
                text = chunk.text
                if not text:
                    continue
                full_response += text
                # Word-wrap at ~72 chars
                for ch in text:
                    if ch == "\n":
                        print()
                        sys.stdout.write(f"  {color}│{C.RESET}  ")
                        col = 0
                    else:
                        sys.stdout.write(ch)
                        col += 1
                        if col >= 72 and ch == " ":
                            print()
                            sys.stdout.write(f"  {color}│{C.RESET}  ")
                            col = 0
                sys.stdout.flush()

            print(f"\n  {color}└{'─'*40}{C.RESET}\n")

        except Exception as e:
            stop_event.set()
            anim_thread.join()
            if self.history and self.history[-1]["role"] == "user":
                self.history.pop()
                self.msg_count -= 1
            if "API_KEY_INVALID" in str(e) or "invalid" in str(e).lower() or "api key" in str(e).lower():
                print(f"\n  {C.RED}✗ API Key tidak valid. Periksa konfigurasi Anda.{C.RESET}\n")
                full_response = "[AUTH_ERROR]"
            else:
                print(f"\n  {C.RED}✗ Error: {e}{C.RESET}\n")
                full_response = "[ERROR]"

        if full_response and full_response not in ("[AUTH_ERROR]", "[ERROR]"):
            self.history.append({"role": "assistant", "content": full_response})

        return full_response

    def clear_history(self):
        self.history = []
        self.msg_count = 0


# ─────────────────────────────────────────────
#  UI HELPERS
# ─────────────────────────────────────────────
def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def print_header():
    print(f"""
{C.BOLD}{C.PURPLE}  ╔══════════════════════════════════════════════════════╗
  ║{C.RESET}{C.BOLD}         HistoTech Tutor — AI Chatbot v1.0            {C.PURPLE}║
  ║{C.RESET}{C.GRAY}   Final Project: LLM-Based Tools & Claude API        {C.BOLD}{C.PURPLE}║
  ╚══════════════════════════════════════════════════════╝{C.RESET}
""")

def print_domain_menu(current: str):
    print(f"  {C.BOLD}Domain Aktif:{C.RESET}")
    for key, (icon, label, color) in DOMAIN_INFO.items():
        marker = f"{C.BOLD}{color}▶ {C.RESET}" if key == current else "  "
        print(f"  {marker}{color}{icon} [{key:8}]{C.RESET} {label}")
    print()

def print_help():
    print(f"""
  {C.BOLD}{C.CYAN}╔── PERINTAH TERSEDIA ──────────────────────────────╗{C.RESET}
  {C.CYAN}│{C.RESET}  {C.BOLD}/domain <nama>{C.RESET}  Ganti domain topik
  {C.CYAN}│{C.RESET}              {C.GRAY}Pilihan: all, history, cyber, science, tech{C.RESET}
  {C.CYAN}│{C.RESET}  {C.BOLD}/clear{C.RESET}         Hapus riwayat percakapan
  {C.CYAN}│{C.RESET}  {C.BOLD}/status{C.RESET}        Lihat info sesi saat ini
  {C.CYAN}│{C.RESET}  {C.BOLD}/help{C.RESET}          Tampilkan menu ini
  {C.CYAN}│{C.RESET}  {C.BOLD}/quit{C.RESET}          Keluar dari chatbot
  {C.CYAN}╚───────────────────────────────────────────────────╝{C.RESET}
""")

def print_suggestions():
    suggestions = [
        "Jelaskan bagaimana enkripsi RSA bekerja",
        "Bagaimana sejarah komputer pertama di dunia?",
        "Apa itu firewall dan bagaimana cara kerjanya?",
        "Jelaskan teori evolusi Charles Darwin",
        "Bagaimana cara kerja GPS?",
    ]
    print(f"  {C.BOLD}{C.GRAY}💡 Contoh pertanyaan:{C.RESET}")
    for s in suggestions:
        print(f"  {C.GRAY}  → {s}{C.RESET}")
    print()

def print_status(bot: HistoTechTutor):
    duration = datetime.now() - bot.session_start
    mins = int(duration.total_seconds() // 60)
    secs = int(duration.total_seconds() % 60)
    icon, label, color = DOMAIN_INFO[bot.domain]
    print(f"""
  {C.BOLD}─── Status Sesi ───────────────────────────────────{C.RESET}
  Domain aktif  : {color}{icon} {label}{C.RESET}
  Model         : {C.CYAN}claude-3-5-sonnet-latest{C.RESET}
  Pesan terkirim: {C.BOLD}{bot.msg_count}{C.RESET}
  Durasi sesi   : {C.BOLD}{mins}m {secs}s{C.RESET}
  Memory (turns): {C.BOLD}{len(bot.history)}{C.RESET}
  ────────────────────────────────────────────────────
""")


# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    # ── Get API key ──────────────────────────
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        clear_screen()
        print_header()
        print(f"  {C.YELLOW}⚠  API Key tidak ditemukan di environment variable.{C.RESET}")
        print(f"  {C.GRAY}Set dengan: export GEMINI_API_KEY='your-key'{C.RESET}\n")
        api_key = input(f"  {C.BOLD}Masukkan API Key kamu: {C.RESET}").strip()
        if not api_key:
            print(f"\n  {C.RED}API Key diperlukan. Keluar.{C.RESET}\n")
            sys.exit(1)

    bot = HistoTechTutor(api_key)

    # ── Welcome screen ────────────────────────
    clear_screen()
    print_header()
    print_domain_menu(bot.domain)
    print_suggestions()
    print_help()

    # ── Main input loop ───────────────────────
    while True:
        try:
            icon, label, color = DOMAIN_INFO[bot.domain]
            prompt = f"  {C.BOLD}{color}[{icon} {label}]{C.RESET} {C.BOLD}Kamu:{C.RESET} "
            user_input = input(prompt).strip()

            if not user_input:
                continue

            # ── Commands ─────────────────────
            if user_input.lower() in ("/quit", "/exit", "/q"):
                print(f"\n  {C.PURPLE}Terima kasih sudah belajar bersama HistoTech Tutor! 👋{C.RESET}\n")
                break

            elif user_input.lower() == "/help":
                print_help()

            elif user_input.lower() == "/status":
                print_status(bot)

            elif user_input.lower() == "/clear":
                bot.clear_history()
                print(f"\n  {C.GREEN}✓ Riwayat percakapan dihapus.{C.RESET}\n")

            elif user_input.lower().startswith("/domain"):
                parts = user_input.split()
                if len(parts) == 2 and bot.set_domain(parts[1].lower()):
                    icon, label, color = DOMAIN_INFO[bot.domain]
                    print(f"\n  {C.GREEN}✓ Domain diganti ke: {color}{icon} {label}{C.RESET}\n")
                else:
                    valid = ", ".join(SYSTEM_PROMPTS.keys())
                    print(f"\n  {C.RED}✗ Domain tidak valid. Pilihan: {valid}{C.RESET}\n")

            elif user_input.startswith("/"):
                print(f"\n  {C.RED}✗ Perintah tidak dikenal. Ketik /help untuk bantuan.{C.RESET}\n")

            # ── Normal chat ───────────────────
            else:
                print(f"\n  {C.GRAY}┌─ Kamu ─────────────────────────────────────────────{C.RESET}")
                print(f"  {C.GRAY}│{C.RESET}  {user_input}")
                print(f"  {C.GRAY}└────────────────────────────────────────────────────{C.RESET}")
                bot.chat(user_input)

        except KeyboardInterrupt:
            print(f"\n\n  {C.PURPLE}👋 Sampai jumpa!{C.RESET}\n")
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
