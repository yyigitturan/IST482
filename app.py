import streamlit as st
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import time
from dataclasses import dataclass
from typing import List
from scipy.stats import chi2_contingency
import scipy.stats as stats

# ─────────────────────────────────────────────
# SAYFA AYARLARI
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CS Simulation | IST482",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@400;600;700&family=Share+Tech+Mono&display=swap');

html, body, [class*="css"] { font-family: 'Rajdhani', sans-serif; }
.stApp { background: #0a0e1a; color: #e0e6f0; }
h1,h2,h3 { font-family:'Rajdhani',sans-serif; font-weight:700; letter-spacing:2px; text-transform:uppercase; }

.hero-title {
    text-align:center; font-size:3rem; font-weight:700; letter-spacing:6px;
    background:linear-gradient(135deg,#f5a623,#ff4757,#e74c3c);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:0.2rem; text-transform:uppercase;
}
.subtitle {
    text-align:center; font-family:'Share Tech Mono',monospace;
    color:#7f8fa6; font-size:0.85rem; letter-spacing:4px; margin-bottom:2rem;
}

/* ── LIVE FEED ── */
.feed-container {
    background:#080c14;
    border:1px solid #1e2a40;
    border-radius:12px;
    padding:1rem 1.2rem;
    font-family:'Share Tech Mono',monospace;
    font-size:0.82rem;
    line-height:1.85;
    min-height:120px;
}
.feed-kill-a   { color:#74b9ff; }
.feed-kill-b   { color:#ff7675; }
.feed-miss     { color:#4a5568; }
.feed-header   { color:#f9ca24; font-weight:bold; font-size:0.9rem; letter-spacing:2px; }
.feed-result   { color:#a29bfe; font-weight:bold; }

/* ── SCOREBOARD ── */
.scoreboard { background:linear-gradient(135deg,#141a2e,#0d1117); border:2px solid #2d3a5a; border-radius:14px; padding:1.4rem; text-align:center; }
.score-big  { font-size:2.8rem; font-weight:700; letter-spacing:4px; }
.score-a    { color:#3498db; }
.score-b    { color:#e74c3c; }

/* ── PLAYER CARDS ── */
.player-alive { background:rgba(46,213,115,0.08); border:1px solid rgba(46,213,115,0.3); border-radius:8px; padding:0.35rem 0.7rem; margin:0.15rem 0; font-family:'Share Tech Mono',monospace; font-size:0.79rem; }
.player-dead  { background:rgba(231,76,60,0.06); border:1px solid rgba(231,76,60,0.2); border-radius:8px; padding:0.35rem 0.7rem; margin:0.15rem 0; font-family:'Share Tech Mono',monospace; font-size:0.79rem; opacity:0.4; text-decoration:line-through; }

/* ── INFO / WARN ── */
.info-box { background:rgba(52,152,219,0.08); border:1px solid rgba(52,152,219,0.3); border-radius:10px; padding:1rem 1.2rem; margin:0.8rem 0; font-size:0.88rem; line-height:1.7; }
.warn-box { background:rgba(245,166,35,0.08); border:1px solid rgba(245,166,35,0.35); border-radius:10px; padding:1rem 1.2rem; margin:0.8rem 0; font-size:0.88rem; }

/* ── WINNER ── */
.winner-banner { text-align:center; padding:1.3rem; border-radius:16px; margin:1rem 0; font-size:1.6rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; }
.winner-a  { background:linear-gradient(135deg,rgba(52,152,219,0.2),rgba(52,152,219,0.05)); border:2px solid #3498db; color:#74b9ff; }
.winner-b  { background:linear-gradient(135deg,rgba(231,76,60,0.2),rgba(231,76,60,0.05)); border:2px solid #e74c3c; color:#ff7675; }
.winner-tie{ background:linear-gradient(135deg,rgba(162,155,254,0.2),rgba(162,155,254,0.05)); border:2px solid #a29bfe; color:#a29bfe; }

.stat-box    { background:#141a2e; border:1px solid #2d3a5a; border-radius:10px; padding:0.9rem; text-align:center; margin:0.3rem; }
.stat-number { font-size:1.7rem; font-weight:700; color:#f5a623; font-family:'Share Tech Mono',monospace; }
.stat-label  { font-size:0.7rem; color:#7f8fa6; letter-spacing:2px; text-transform:uppercase; }

section[data-testid="stSidebar"] { background:#0d1117; border-right:1px solid #21262d; }
section[data-testid="stSidebar"] .stButton > button { width:100%; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────
WEAPONS = {
    1: {"name": "Tabanca", "emoji": "🔫", "damage": 1, "hit_prob": 0.55, "desc": "Standart; orta hasar, iyi isabet"},
    2: {"name": "Bıçak",   "emoji": "🔪", "damage": 3, "hit_prob": 0.35, "desc": "Tek vuruşta öldürür (3 can), ama zor isabet"},
    3: {"name": "Tüfek",   "emoji": "🎯", "damage": 2, "hit_prob": 0.70, "desc": "Yüksek isabet, 2 can hasar"},
}
PLAYER_NAMES_A = ["Alpha_1","Alpha_2","Alpha_3","Alpha_4","Alpha_5","Alpha_6"]
PLAYER_NAMES_B = ["Bravo_1","Bravo_2","Bravo_3","Bravo_4","Bravo_5","Bravo_6"]

@dataclass
class Player:
    name: str
    team: str
    weapon_id: int
    hp: int = 3
    kills: int = 0
    deaths: int = 0
    shots: int = 0
    hits: int = 0

    @property
    def alive(self): return self.hp > 0
    @property
    def weapon(self): return WEAPONS[self.weapon_id]

    def shoot(self, target: "Player") -> bool:
        self.shots += 1
        w = self.weapon
        hit = random.random() < w["hit_prob"]
        if hit:
            self.hits += 1
            target.hp -= w["damage"]
            if target.hp <= 0:
                target.hp = 0
                target.deaths += 1
                self.kills += 1
        return hit

    def accuracy(self):
        return self.hits / self.shots if self.shots > 0 else 0.0


def make_team(team: str, names: List[str], fixed_weapon: int = None) -> List[Player]:
    players = []
    for name in names:
        wid = fixed_weapon if fixed_weapon else random.choice([1, 2, 3])
        players.append(Player(name=name, team=team, weapon_id=wid))
    return players


def simulate_tick(team_a: List[Player], team_b: List[Player]):
    """One tick: every alive player shoots once. Returns list of event dicts."""
    alive_a = [p for p in team_a if p.alive]
    alive_b = [p for p in team_b if p.alive]
    shooters = alive_a + alive_b
    random.shuffle(shooters)
    events = []
    for shooter in shooters:
        if not shooter.alive:
            continue
        enemies = [p for p in (team_b if shooter.team == "A" else team_a) if p.alive]
        if not enemies:
            continue
        target = random.choice(enemies)
        hit = shooter.shoot(target)
        events.append({
            "shooter": shooter.name,
            "team": shooter.team,
            "weapon_emoji": shooter.weapon["emoji"],
            "target": target.name,
            "hit": hit,
            "damage": shooter.weapon["damage"] if hit else 0,
            "target_hp": target.hp,
            "eliminated": hit and not target.alive,
        })
    return events


# ─────────────────────────────────────────────
# MONTE CARLO
# ─────────────────────────────────────────────
def run_ab_test(n_simulations: int = 1000):
    results = {"A": 0, "B": 0, "TIE": 0}
    score_a_list, score_b_list = [], []
    weapon_win_counts = {1: 0, 2: 0, 3: 0}
    weapon_use_counts = {1: 0, 2: 0, 3: 0}

    progress_bar = st.progress(0, text="Monte Carlo simülasyonu çalışıyor...")

    for i in range(n_simulations):
        team_a = make_team("A", PLAYER_NAMES_A)
        team_b = make_team("B", PLAYER_NAMES_B)
        for p in team_a + team_b:
            weapon_use_counts[p.weapon_id] += 1

        # 1 round per match (matching new game mode)
        reset_a = [Player(name=p.name, team="A", weapon_id=p.weapon_id) for p in team_a]
        reset_b = [Player(name=p.name, team="B", weapon_id=p.weapon_id) for p in team_b]
        tick = 0
        while True:
            alive_a = [p for p in reset_a if p.alive]
            alive_b = [p for p in reset_b if p.alive]
            if not alive_a or not alive_b or tick > 100:
                break
            tick += 1
            simulate_tick(reset_a, reset_b)

        alive_a_f = [p for p in reset_a if p.alive]
        alive_b_f = [p for p in reset_b if p.alive]
        sa = 1 if len(alive_a_f) > len(alive_b_f) else 0
        sb = 1 if len(alive_b_f) > len(alive_a_f) else 0

        score_a_list.append(sa)
        score_b_list.append(sb)

        if sa > sb:
            results["A"] += 1
            for p in team_a:
                weapon_win_counts[p.weapon_id] += 1
        elif sb > sa:
            results["B"] += 1
            for p in team_b:
                weapon_win_counts[p.weapon_id] += 1
        else:
            results["TIE"] += 1

        if (i + 1) % max(1, n_simulations // 20) == 0:
            progress_bar.progress((i + 1) / n_simulations, text=f"Monte Carlo: {i+1}/{n_simulations}")

    progress_bar.empty()
    total = n_simulations
    probs = {k: v / total for k, v in results.items()}
    weapon_eff = {w: weapon_win_counts[w] / weapon_use_counts[w] if weapon_use_counts[w] > 0 else 0.0 for w in [1,2,3]}
    stake = 10
    ev_a = (probs["A"] * stake) + (probs["TIE"] * 0) + (probs["B"] * (-stake))
    ev_b = (probs["B"] * stake) + (probs["TIE"] * 0) + (probs["A"] * (-stake))
    return {"results": results, "probs": probs, "score_a_list": score_a_list, "score_b_list": score_b_list,
            "weapon_eff": weapon_eff, "weapon_use_counts": weapon_use_counts,
            "expected_value_a": ev_a, "expected_value_b": ev_b, "n": total}


# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────
def plot_win_pie(probs):
    fig, ax = plt.subplots(figsize=(4.5, 4.5), facecolor="#0a0e1a")
    labels = ["Takım A Kazanır", "Takım B Kazanır", "Beraberlik"]
    sizes  = [probs["A"], probs["B"], probs["TIE"]]
    colors = ["#3498db", "#e74c3c", "#a29bfe"]
    wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=colors, autopct="%1.1f%%",
        startangle=120, textprops={"color":"#dfe6e9","fontsize":10},
        wedgeprops={"edgecolor":"#0a0e1a","linewidth":2})
    for at in autotexts: at.set_fontsize(11); at.set_fontweight("bold")
    ax.set_title("Kazanma Olasılıkları", color="#f5a623", fontsize=13, pad=14, fontweight="bold")
    return fig


def plot_weapon_eff(weapon_eff):
    fig, ax = plt.subplots(figsize=(6, 3.2), facecolor="#0a0e1a")
    ax.set_facecolor("#0d1117")
    names = [f"{WEAPONS[w]['emoji']} {WEAPONS[w]['name']}" for w in [1,2,3]]
    vals  = [weapon_eff[w] * 100 for w in [1,2,3]]
    colors = ["#f5a623","#e74c3c","#2ecc71"]
    bars = ax.bar(names, vals, color=colors, edgecolor="#0a0e1a", alpha=0.85, width=0.55)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                f"%{val:.1f}", ha="center", va="bottom", color="#dfe6e9", fontsize=10, fontweight="bold")
    ax.set_title("Silah Etkinliği (Kazanan Takımda Kullanım Oranı)", color="#dfe6e9", fontsize=10, fontweight="bold")
    ax.set_ylabel("Etkinlik (%)", color="#7f8fa6", fontsize=9)
    ax.set_ylim(0, max(vals)*1.3 if max(vals) > 0 else 10)
    ax.tick_params(colors="#7f8fa6")
    for sp in ax.spines.values(): sp.set_edgecolor("#2d3a5a")
    fig.tight_layout(pad=1.5)
    return fig


def plot_kill_bars(team_a: List[Player], team_b: List[Player]):
    fig, ax = plt.subplots(figsize=(10, 3), facecolor="#0a0e1a")
    ax.set_facecolor("#0d1117")
    all_players = team_a + team_b
    names  = [p.name for p in all_players]
    kills  = [p.kills for p in all_players]
    colors = ["#3498db" if p.team == "A" else "#e74c3c" for p in all_players]
    ax.bar(names, kills, color=colors, edgecolor="#0a0e1a", alpha=0.85)
    ax.set_title("Oyuncu Kill Sayıları", color="#dfe6e9", fontsize=10, fontweight="bold")
    ax.set_ylabel("Kill", color="#7f8fa6", fontsize=9)
    ax.tick_params(colors="#7f8fa6", axis="both")
    ax.tick_params(axis="x", rotation=30)
    for sp in ax.spines.values(): sp.set_edgecolor("#2d3a5a")
    import matplotlib.patches as mpatches
    pa = mpatches.Patch(color="#3498db", label="Takım A")
    pb = mpatches.Patch(color="#e74c3c", label="Takım B")
    ax.legend(handles=[pa, pb], facecolor="#141a2e", labelcolor="#dfe6e9", fontsize=8)
    fig.tight_layout(pad=1.5)
    return fig


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in [("page","home"), ("match_result",None), ("ab_result",None),
             ("player_name",""), ("user_team","A"), ("user_weapon",1),
             ("live_events",[]), ("live_done",False)]:
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:1rem 0;'>
        <div style='font-size:2.5rem'>🎮</div>
        <div style='font-weight:700; letter-spacing:3px; font-size:1.1rem; color:#f5a623;'>CS SİMÜLASYON</div>
        <div style='font-size:0.7rem; color:#7f8fa6; letter-spacing:2px;'>IST482 · HACETTEPEüNİ</div>
    </div>""", unsafe_allow_html=True)
    st.divider()
    if st.button("🏠  Ana Sayfa",              use_container_width=True): st.session_state.page="home";   st.rerun()
    if st.button("🎮  Oyna (1 El)",            use_container_width=True): st.session_state.page="play";   st.rerun()
    if st.button("🧪  A/B Testi (Monte Carlo)",use_container_width=True): st.session_state.page="ab";     st.rerun()
    if st.button("📐  Teorik Analiz",           use_container_width=True): st.session_state.page="theory"; st.rerun()
    st.divider()
    st.markdown("""<div style='font-size:0.72rem; color:#636e72; line-height:1.7;'>
        <b style='color:#a29bfe'>Hacettepe Üniversitesi</b><br>
        İstatistik Bölümü · IST482<br>
        Benzetim Teknikleri<br>
        <b style='color:#f5a623'>Rasgele Sayı Üretimi Ödevi</b>
    </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════
# HOME
# ══════════════════════════════════════════════
if st.session_state.page == "home":
    st.markdown("<div class='hero-title'>⚔️ CS BATTLE SIM</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>HACETTEPE ÜNİVERSİTESİ · IST482 BENZETİM TEKNİKLERİ · RASGELE SAYI ÜRETİMİ</div>", unsafe_allow_html=True)

    st.markdown("""<div class='info-box'>
    <b style='color:#f5a623'>🎯 Ödev Açıklaması</b><br>
    Bu uygulama <b>rasgele sayı üretimi</b> temelli bir Counter-Strike simülasyonu içermektedir.
    6v6 takım savaşı, olasılıksal silah mekaniği ve Monte Carlo yöntemiyle 
    beklenen kazanç/kayıp analizi sunulmaktadır.<br><br>
    Her maç <b>tek bir el</b>den oluşur. Ateş anları <b>canlı olarak</b> ekrana yansır.
    </div>""", unsafe_allow_html=True)

    c1,c2,c3 = st.columns(3)
    for col,num,lbl in [(c1,"6v6","Takım Boyutu"),(c2,"3","Silah Türü"),(c3,"1","El / Maç")]:
        col.markdown(f"<div class='stat-box'><div class='stat-number'>{num}</div><div class='stat-label'>{lbl}</div></div>", unsafe_allow_html=True)

    st.divider()
    st.subheader("🔫 Silah Sistemi")
    wc1,wc2,wc3 = st.columns(3)
    for col,wid in zip([wc1,wc2,wc3],[1,2,3]):
        w = WEAPONS[wid]
        col.markdown(f"""<div class='stat-box'>
        <b style='font-size:1.3rem'>{w['emoji']} {w['name']}</b><br>
        <span style='color:#7f8fa6; font-size:0.8rem'>Hasar: {w['damage']} can &nbsp;|&nbsp; İsabet: %{int(w['hit_prob']*100)}</span><br>
        <span style='font-size:0.85rem'>{w['desc']}</span>
        </div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("""<div class='info-box'>
    <b style='color:#f5a623'>📐 Temel Formüller</b><br>
    <b>İsabet:</b> <code>U ~ Uniform(0,1)</code> → U &lt; p_isabet ise isabet (Bernoulli deneyi)<br>
    <b>El Kazanma:</b> <code>P(A kazanır) = P(A'da ≥1 hayatta, B'de 0 hayatta)</code><br>
    <b>Beklenen Kazanç:</b> <code>E[X] = P(kazan)·(+S) + P(kaybet)·(−S) + P(bera)·0</code>
    </div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("🎮 Oynamaya Başla", use_container_width=True, type="primary"):
            st.session_state.page = "play"; st.rerun()
    with col_r:
        if st.button("🧪 A/B Testi Çalıştır", use_container_width=True):
            st.session_state.page = "ab"; st.rerun()


# ══════════════════════════════════════════════
# PLAY — 1 ROUND LIVE
# ══════════════════════════════════════════════
elif st.session_state.page == "play":
    st.markdown("<div class='hero-title'>🎮 MAÇA GİR</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>1 EL · CANLI ATEŞ GÜNLÜĞÜ · SONUÇLAR</div>", unsafe_allow_html=True)

    if st.session_state.match_result is None:
        # ── Setup ──
        st.subheader("👤 Oyuncu Ayarları")
        nickname = st.text_input("Nicknamen:", placeholder="Ör: xAce_Tr", max_chars=20)

        st.subheader("🏳️ Takım Seç")
        user_team = st.radio("Hangi takımda?", ["🔵 Takım A", "🔴 Takım B"], horizontal=True)
        chosen_team = "A" if "A" in user_team else "B"

        st.subheader("🔫 Silah Seç")
        weapon_choice = st.radio("Silahını seç:", [
            f"{WEAPONS[1]['emoji']} {WEAPONS[1]['name']} (Hasar:{WEAPONS[1]['damage']} | İsabet:%{int(WEAPONS[1]['hit_prob']*100)})",
            f"{WEAPONS[2]['emoji']} {WEAPONS[2]['name']} (Hasar:{WEAPONS[2]['damage']} | İsabet:%{int(WEAPONS[2]['hit_prob']*100)})",
            f"{WEAPONS[3]['emoji']} {WEAPONS[3]['name']} (Hasar:{WEAPONS[3]['damage']} | İsabet:%{int(WEAPONS[3]['hit_prob']*100)})",
        ], horizontal=True)
        weapon_id = 1 if "Tabanca" in weapon_choice else (2 if "Bıçak" in weapon_choice else 3)

        st.markdown(f"""<div class='warn-box'>
        ⚔️ Seçilen silah: <b>{WEAPONS[weapon_id]['emoji']} {WEAPONS[weapon_id]['name']}</b> &nbsp;|&nbsp;
        Takım: <b>{'🔵 A' if chosen_team=='A' else '🔴 B'}</b><br>
        Botların silahları <b>rasgele</b> atanacak. Maç <b>tek el</b>den oluşur.
        </div>""", unsafe_allow_html=True)

        if st.button("🚀 MAÇI BAŞLAT", type="primary", use_container_width=True):
            # Build teams
            name = nickname.strip() or "Oyuncu"
            team_a = make_team("A", PLAYER_NAMES_A)
            team_b = make_team("B", PLAYER_NAMES_B)
            if chosen_team == "A":
                team_a[0].name = name; team_a[0].weapon_id = weapon_id
            else:
                team_b[0].name = name; team_b[0].weapon_id = weapon_id

            # Pre-simulate all ticks
            sim_a = [Player(name=p.name, team="A", weapon_id=p.weapon_id) for p in team_a]
            sim_b = [Player(name=p.name, team="B", weapon_id=p.weapon_id) for p in team_b]
            all_ticks = []
            tick = 0
            while True:
                alive_a = [p for p in sim_a if p.alive]
                alive_b = [p for p in sim_b if p.alive]
                if not alive_a or not alive_b or tick > 100:
                    break
                tick += 1
                events = simulate_tick(sim_a, sim_b)
                all_ticks.append(events)

            alive_a_f = [p for p in sim_a if p.alive]
            alive_b_f = [p for p in sim_b if p.alive]
            if len(alive_a_f) > len(alive_b_f):
                winner = "A"
            elif len(alive_b_f) > len(alive_a_f):
                winner = "B"
            else:
                winner = "TIE"

            st.session_state.match_result = {
                "winner": winner,
                "all_ticks": all_ticks,
                "team_a": sim_a,
                "team_b": sim_b,
                "user_team": chosen_team,
                "player_name": name,
            }
            st.session_state.live_events = []
            st.session_state.live_done = False
            st.rerun()

    else:
        res = st.session_state.match_result
        winner = res["winner"]
        user_team = res["user_team"]
        team_a = res["team_a"]
        team_b = res["team_b"]
        all_ticks = res["all_ticks"]

        # ── LIVE FEED (stream ticks one by one) ──
        if not st.session_state.live_done:
            st.subheader("📡 CANLI ATEŞ GÜNLÜĞÜ")

            feed_placeholder   = st.empty()
            status_placeholder = st.empty()

            displayed_lines: List[str] = []

            for tick_idx, events in enumerate(all_ticks):
                displayed_lines.append(f"<span class='feed-header'>── TİK {tick_idx+1} ──────────────────</span>")
                for ev in events:
                    w_emoji = ev["weapon_emoji"]
                    shooter = ev["shooter"]
                    target  = ev["target"]
                    css     = "feed-kill-a" if ev["team"] == "A" else "feed-kill-b"
                    if ev["hit"]:
                        if ev["eliminated"]:
                            line = f"<span class='{css}'>☠️ {shooter} [{w_emoji}] → {target} — ELİMİNE edildi!</span>"
                        else:
                            line = f"<span class='{css}'>💥 {shooter} [{w_emoji}] → {target} — -{ev['damage']} can (kalan: {ev['target_hp']})</span>"
                    else:
                        line = f"<span class='feed-miss'>❌ {shooter} [{w_emoji}] → {target} — ıskalandı</span>"
                    displayed_lines.append(line)

                html = "<br>".join(displayed_lines)
                feed_placeholder.markdown(f"<div class='feed-container'>{html}</div>", unsafe_allow_html=True)
                time.sleep(0.18)

            # Final line
            a_count = sum(1 for p in team_a if p.alive)
            b_count = sum(1 for p in team_b if p.alive)
            if winner == "A":
                res_line = "🏆 EL KAZANANI: TAKIM A"
            elif winner == "B":
                res_line = "🏆 EL KAZANANI: TAKIM B"
            else:
                res_line = "🤝 EL BERABERE"
            displayed_lines.append(f"<br><span class='feed-result'>{'━'*38}<br>{res_line}</span>")
            feed_placeholder.markdown(f"<div class='feed-container'>{'<br>'.join(displayed_lines)}</div>", unsafe_allow_html=True)

            st.session_state.live_events = displayed_lines
            st.session_state.live_done = True
            st.rerun()

        else:
            # Feed already done — just show it statically
            html = "<br>".join(st.session_state.live_events)
            st.subheader("📡 ATEŞ GÜNLÜĞÜ")
            st.markdown(f"<div class='feed-container'>{html}</div>", unsafe_allow_html=True)

        # ── WINNER BANNER ──
        if winner == "A":
            cls = "winner-a" if user_team == "A" else "winner-b"
            txt = "🏆 TAKIM A KAZANDI" + (" — SEN KAZANDIN! 🎉" if user_team == "A" else " — SEN KAYBETTİN 😔")
        elif winner == "B":
            cls = "winner-b" if user_team == "B" else "winner-a"
            txt = "🏆 TAKIM B KAZANDI" + (" — SEN KAZANDIN! 🎉" if user_team == "B" else " — SEN KAYBETTİN 😔")
        else:
            cls = "winner-tie"; txt = "🤝 BERABERE"
        st.markdown(f"<div class='winner-banner {cls}'>{txt}</div>", unsafe_allow_html=True)

        # ── İSTATİSTİKLER ──
        st.divider()
        st.subheader("📊 Maç İstatistikleri")

        # Kill chart
        st.pyplot(plot_kill_bars(team_a, team_b))

        # Player stat tables
        col_a, col_b = st.columns(2)
        for col, team, label, card_cls in [
            (col_a, team_a, "🔵 TAKIM A", "feed-kill-a"),
            (col_b, team_b, "🔴 TAKIM B", "feed-kill-b"),
        ]:
            with col:
                st.markdown(f"**{label}**")
                rows = []
                for p in team:
                    rows.append({
                        "Oyuncu": p.name,
                        "Silah": p.weapon["emoji"],
                        "Kill": p.kills,
                        "Atış": p.shots,
                        "İsabet": p.hits,
                        "İsabet%": f"%{p.accuracy()*100:.0f}",
                        "HP": p.hp,
                        "Durum": "✅ Hayatta" if p.alive else "💀 Elendi",
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        # Summary metrics
        st.divider()
        m1,m2,m3,m4 = st.columns(4)
        total_kills_a = sum(p.kills for p in team_a)
        total_kills_b = sum(p.kills for p in team_b)
        alive_a = sum(1 for p in team_a if p.alive)
        alive_b = sum(1 for p in team_b if p.alive)
        for col,num,lbl in [
            (m1, total_kills_a, "Takım A Kill"),
            (m2, total_kills_b, "Takım B Kill"),
            (m3, alive_a, "A Hayatta Kalan"),
            (m4, alive_b, "B Hayatta Kalan"),
        ]:
            col.markdown(f"<div class='stat-box'><div class='stat-number'>{num}</div><div class='stat-label'>{lbl}</div></div>", unsafe_allow_html=True)

        # Accuracy
        st.divider()
        st.markdown("""<div class='info-box'>
        <b style='color:#f5a623'>📐 Rasgele Sayı Üretimi — Bu Elde</b><br>
        Her ateşte Python <code>random.random()</code> ile <code>U ~ Uniform(0,1)</code> üretildi.<br>
        <code>U &lt; p_isabet</code> ise isabet sayıldı → Bu bir <b>Bernoulli(p) deneyi</b>dir.<br>
        Tekrarlanan atışlar <b>Binomial dağılıma</b> yakınsar (Büyük Sayılar Yasası).
        </div>""", unsafe_allow_html=True)

        st.divider()
        if st.button("🔄 Yeni Maç Oyna", type="primary", use_container_width=True):
            st.session_state.match_result = None
            st.session_state.live_events = []
            st.session_state.live_done = False
            st.rerun()


# ══════════════════════════════════════════════
# A/B TEST
# ══════════════════════════════════════════════
elif st.session_state.page == "ab":
    st.markdown("<div class='hero-title'>🧪 A/B TESTİ</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>MONTE CARLO SİMÜLASYONU · OLASILIK ANALİZİ · BEKLENEN KAZANÇ</div>", unsafe_allow_html=True)

    st.markdown("""<div class='info-box'>
    <b style='color:#f5a623'>Monte Carlo Yöntemi</b><br>
    Analitik olarak hesaplanması zor olan olasılıkları <b>çok sayıda rasgele deney</b> yaparak tahmin eder.<br>
    <code>P̂(A kazanır) = (A'nın kazandığı maç sayısı) / (toplam simülasyon sayısı)</code><br>
    Simülasyon sayısı arttıkça tahmin <b>gerçek olasılığa yakınsar</b> (Büyük Sayılar Yasası).<br>
    95% güven aralığı: <code>P̂ ± 1.96·√(P̂(1−P̂)/n)</code>
    </div>""", unsafe_allow_html=True)

    n_sims = st.slider("Simülasyon sayısı:", min_value=100, max_value=5000, value=500, step=100)
    if st.button("▶ Simülasyonu Çalıştır", type="primary", use_container_width=False):
        st.session_state.ab_result = run_ab_test(n_sims)

    if st.session_state.ab_result:
        ab = st.session_state.ab_result
        probs = ab["probs"]
        n = ab["n"]

        st.divider()
        st.subheader("📊 Simülasyon Sonuçları")
        m1,m2,m3,m4 = st.columns(4)
        for col,lbl,val,delta in [
            (m1,"Takım A Kazanma",f"%{probs['A']*100:.1f}",f"{ab['results']['A']} maç"),
            (m2,"Takım B Kazanma",f"%{probs['B']*100:.1f}",f"{ab['results']['B']} maç"),
            (m3,"Beraberlik",     f"%{probs['TIE']*100:.1f}",f"{ab['results']['TIE']} maç"),
            (m4,"Toplam Oyun",   f"{n}","simülasyon"),
        ]:
            col.metric(lbl, val, delta)

        # Confidence intervals
        ci_a = 1.96 * np.sqrt(probs["A"]*(1-probs["A"])/n)
        ci_b = 1.96 * np.sqrt(probs["B"]*(1-probs["B"])/n)
        st.markdown(f"""<div class='info-box'>
        <b>95% Güven Aralıkları (n={n}):</b><br>
        Takım A: %{probs['A']*100:.1f} ± %{ci_a*100:.2f} → [{(probs['A']-ci_a)*100:.1f}%, {(probs['A']+ci_a)*100:.1f}%]<br>
        Takım B: %{probs['B']*100:.1f} ± %{ci_b*100:.2f} → [{(probs['B']-ci_b)*100:.1f}%, {(probs['B']+ci_b)*100:.1f}%]
        </div>""", unsafe_allow_html=True)

        g1, g2 = st.columns([1,1])
        with g1:
            st.markdown("**Kazanma Olasılıkları**")
            st.pyplot(plot_win_pie(probs))
        with g2:
            st.markdown("**Silah Etkinliği**")
            st.pyplot(plot_weapon_eff(ab["weapon_eff"]))

        # Beklenen kazanç tablosu
        st.divider()
        st.subheader("💰 Beklenen Kazanç Analizi")
        stakes = [5, 10, 20, 50, 100]
        rows = []
        for s in stakes:
            ev_a = probs["A"]*s - probs["B"]*s
            ev_b = probs["B"]*s - probs["A"]*s
            rows.append({
                "Bahis (TL)": s,
                "E[X] A'ya yatır": f"{ev_a:+.2f} TL",
                "E[X] B'ye yatır": f"{ev_b:+.2f} TL",
                "Adil Oyun?": "✅" if abs(ev_a) < s*0.05 else "❌",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown(f"""<div class='warn-box'>
        <b>Yorum:</b><br>
        • 10 TL bahiste A takımının beklenen kazancı: <b>{ab['expected_value_a']:+.2f} TL</b><br>
        • 10 TL bahiste B takımının beklenen kazancı: <b>{ab['expected_value_b']:+.2f} TL</b><br>
        • İki takım simetrik bot mekanizmasıyla çalıştığından beklenen kazanç sıfıra yakındır.<br>
        • Küçük sapmalar rastgele silah atamalarından kaynaklanır.
        </div>""", unsafe_allow_html=True)

        # Descriptive stats
        st.divider()
        st.subheader("🔬 İstatistiksel Anlamlılık Testi (Ki-Kare)")

        st.markdown("""<div class='info-box'>
        <b style='color:#f5a623'>H₀ ve H₁ Hipotezleri</b><br>
        <b>H₀:</b> Takım A ve Takım B'nin kazanma olasılıkları arasında anlamlı bir farklılık yoktur.<br>
        <b>H₁:</b> İki takımın kazanma olasılıkları arasında istatistiksel olarak anlamlı farklılık vardır.<br>
        Anlamlılık düzeyi: α = 0.05
        </div>""", unsafe_allow_html=True)

        wins_a   = ab["results"]["A"]
        wins_b   = ab["results"]["B"]

        losses_a = n - wins_a
        losses_b = n - wins_b

        # 2x2 kontenjans tablosu
        contingency = [
            [wins_a, losses_a],
            [wins_b, losses_b]
        ]

        chi2, p_value, dof, expected = chi2_contingency(contingency)

        # Cramér V
        cramer_v = np.sqrt(chi2 / (n * (min(contingency.__len__(), len(contingency[0])) - 1)))

        # Etki büyüklüğü yorumu
        if cramer_v < 0.10:
            effect_label = "Çok Küçük"
            effect_color = "#a29bfe"

        elif cramer_v < 0.30:
            effect_label = "Küçük"
            effect_color = "#74b9ff"

        elif cramer_v < 0.50:
            effect_label = "Orta"
            effect_color = "#f5a623"

        else:
            effect_label = "Büyük"
            effect_color = "#e74c3c"

        reject = p_value < 0.05

        # Sonuç bannerı
        verdict_cls = "winner-a" if reject else "winner-tie"

        verdict_txt = (
            f"H₀ REDDEDİLDİ — İki takım arasında istatistiksel olarak anlamlı farklılık vardır (p={p_value:.4f} < 0.05)"
            if reject else
            f"H₀ REDDEDİLEMEDİ — İki takım arasında anlamlı farklılık yoktur (p={p_value:.4f} ≥ 0.05)"
        )

        st.markdown(
            f"<div class='winner-banner {verdict_cls}'>{verdict_txt}</div>",
            unsafe_allow_html=True
        )

        # Metric kartları
        k1, k2, k3, k4 = st.columns(4)

        k1.metric("Ki-Kare (χ²)", f"{chi2:.4f}")
        k2.metric("p-değeri", f"{p_value:.6f}")
        k3.metric("Serbestlik Derecesi", f"{dof}")
        k4.metric(
            f"Cramér V ({effect_label})",
            f"{cramer_v:.4f}"
        )

        # Beklenen frekanslar
        expected_df = pd.DataFrame(
            expected,
            columns=["Kazandı", "Kazanmadı"],
            index=["Takım A", "Takım B"]
        )

        st.markdown("### 📋 Beklenen Frekanslar")
        st.dataframe(expected_df.style.format("{:.2f}"))

        # Yorum kutusu
        st.markdown(f"""
        <div class='info-box'>
        <b style='color:#f5a623'>📐 Cramér V Etki Büyüklüğü Yorumu</b><br><br>

        Hesaplanan değer:
        <b style='color:{effect_color}'>V = {cramer_v:.4f}</b><br>

        Etki büyüklüğü:
        <b style='color:{effect_color}'>{effect_label}</b><br><br>

        <b>Yorum Skalası</b><br>
        • V &lt; 0.10 → Çok Küçük<br>
        • 0.10 ≤ V &lt; 0.30 → Küçük<br>
        • 0.30 ≤ V &lt; 0.50 → Orta<br>
        • V ≥ 0.50 → Büyük<br><br>

        <b>Kontenjans Tablosu</b><br>
        Takım A → Kazandı: {wins_a} | Kazanmadı: {losses_a}<br>
        Takım B → Kazandı: {wins_b} | Kazanmadı: {losses_b}
        </div>
        """, unsafe_allow_html=True)
        st.subheader("📐 Tanımlayıcı İstatistikler")
        desc = {"": ["Ortalama","Std. Sapma","Min","Max","Medyan"],
                "Takım A": [f"{np.mean(ab['score_a_list']):.2f}",f"{np.std(ab['score_a_list']):.2f}",
                            int(np.min(ab['score_a_list'])),int(np.max(ab['score_a_list'])),f"{np.median(ab['score_a_list']):.1f}"],
                "Takım B": [f"{np.mean(ab['score_b_list']):.2f}",f"{np.std(ab['score_b_list']):.2f}",
                            int(np.min(ab['score_b_list'])),int(np.max(ab['score_b_list'])),f"{np.median(ab['score_b_list']):.1f}"]}
        st.dataframe(pd.DataFrame(desc), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════
# THEORY
# ══════════════════════════════════════════════
elif st.session_state.page == "theory":
    st.markdown("<div class='hero-title'>📐 TEORİK ANALİZ</div>", unsafe_allow_html=True)
    st.markdown("<div class='subtitle'>OLASILIK HESAPLARI · RASGELE SAYILAR · İSTATİSTİKSEL TEMELLER</div>", unsafe_allow_html=True)

    st.subheader("1. Rasgele Sayı Üretimi")
    st.markdown("""<div class='info-box'>
    Python'un <code>random.random()</code> fonksiyonu <b>Mersenne Twister</b> algoritmasıyla
    <code>U ~ Uniform(0,1)</code> dağılımından rasgele sayı üretir.<br><br>
    <b>İsabet kararı:</b> <code>U = random.random()</code> → eğer <code>U &lt; p_isabet</code> ise ateş isabet etti.<br>
    Bu <b>Bernoulli deneyi</b>dir: X ~ Bernoulli(p)<br>
    &nbsp;&nbsp;• P(X=1) = p &nbsp;(isabet) &nbsp;&nbsp;• P(X=0) = 1−p &nbsp;(ıskalama)
    </div>""", unsafe_allow_html=True)

    st.subheader("2. Silah Özellikleri")
    wdf = pd.DataFrame([{
        "Silah": f"{WEAPONS[w]['emoji']} {WEAPONS[w]['name']}",
        "İsabet P(H)": WEAPONS[w]['hit_prob'],
        "Hasar (can)": WEAPONS[w]['damage'],
        "Iskalama P(M)": round(1 - WEAPONS[w]['hit_prob'], 2),
        "HP=3 bitirmek için min. vuruş": -(-3 // WEAPONS[w]['damage']),
    } for w in [1,2,3]])
    st.dataframe(wdf, use_container_width=True, hide_index=True)

    st.subheader("3. Öldürme Olasılığı")
    st.markdown("""<div class='info-box'>
    <b>Tabanca (p=0.55, d=1):</b> 3 isabet gerekir → Min 3 atış<br>
    P(3 ardışık isabet) = 0.55³ ≈ 0.166<br><br>
    <b>Bıçak (p=0.35, d=3):</b> 1 isabet yeter → P(öldürme|ateş) = 0.35<br><br>
    <b>Tüfek (p=0.70, d=2):</b> 2 isabet yeter → P(2 ardışık isabet) = 0.70² = 0.49<br><br>
    Genel formül: P(t atışta öldürme) = P(Binomial(t,p) ≥ ⌈3/d⌉)
    </div>""", unsafe_allow_html=True)

    # Kümülatif öldürme grafiği
    from scipy.stats import binom as scipy_binom
    fig, axes = plt.subplots(1, 3, figsize=(12,3.5), facecolor="#0a0e1a")
    for idx, wid in enumerate([1,2,3]):
        ax = axes[idx]
        ax.set_facecolor("#0d1117")
        w = WEAPONS[wid]
        p = w["hit_prob"]; d = w["damage"]; n_needed = -(-3//d)
        cum_kill = [1 - scipy_binom.cdf(n_needed-1, shot, p) for shot in range(1,12)]
        ax.plot(range(1,12), cum_kill, color=["#f5a623","#e74c3c","#2ecc71"][idx],
                linewidth=2.2, marker="o", markersize=4)
        ax.set_title(f"{w['emoji']} {w['name']}", color="#dfe6e9", fontsize=10, fontweight="bold")
        ax.set_xlabel("Atış Sayısı", color="#7f8fa6", fontsize=8)
        ax.set_ylabel("P(Öldürme)", color="#7f8fa6", fontsize=8)
        ax.set_ylim(0, 1.05); ax.tick_params(colors="#7f8fa6")
        ax.grid(alpha=0.1, color="#2d3a5a")
        for sp in ax.spines.values(): sp.set_edgecolor("#2d3a5a")
    fig.suptitle("Kümülatif Öldürme Olasılığı (t atışa kadar)", color="#f5a623", fontsize=11, fontweight="bold", y=1.02)
    fig.tight_layout(pad=2)
    st.pyplot(fig)

    st.subheader("4. Beklenen Kazanç")
    st.markdown("""<div class='info-box'>
    S TL bahis, A takımına:<br>
    <code>E[X] = P(A)·(+S) + P(TIE)·0 + P(B)·(−S) = S·[P(A) − P(B)]</code><br><br>
    <b>Adil oyun koşulu:</b> E[X] = 0 → P(A) = P(B)<br>
    Simetrik bot kurulumu nedeniyle simülasyon P(A) ≈ P(B) verir.
    </div>""", unsafe_allow_html=True)

    st.subheader("5. Büyük Sayılar Yasası")
    st.markdown("""<div class='info-box'>
    n → ∞ iken &nbsp;<code>X̄ₙ →^(o.s.) μ</code><br><br>
    Monte Carlo'da: <code>P̂(A kazanır) = Σ1(Aᵢ kazandı) / n</code><br>
    95% GA: <code>P̂ ± 1.96·√(P̂(1−P̂)/n)</code><br>
    n=1000 için: ±1.96·√(0.25/1000) ≈ ±%3.1
    </div>""", unsafe_allow_html=True)