import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
import smtplib
from email.mime.text import MIMEText

st.set_page_config(
    page_title="Toastmasters Pune South East",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; }
.tm-card {
    background: #fff; border: 2px solid #1a1a2e; border-radius: 4px;
    padding: 2.5rem; margin: 0 auto 1.5rem auto;
    max-width: 520px; box-shadow: 6px 6px 0px #722F37;
}
.tm-club-name {
    font-family: 'Playfair Display', serif; font-size: 1.6rem;
    font-weight: 900; color: #1a1a2e; line-height: 1.2; letter-spacing: -0.5px;
    text-align: center;
}
.tm-tagline {
    font-size: 0.8rem; color: #722F37; letter-spacing: 3px;
    text-transform: uppercase; margin-top: 0.4rem; text-align: center;
}
.tm-divider {
    height: 3px; background: linear-gradient(90deg, #722F37, #1a1a2e);
    border: none; margin: 1.2rem auto; width: 60px;
}
.badge {
    display: inline-block; background: #722F37; color: white;
    font-size: 0.7rem; letter-spacing: 2px; text-transform: uppercase;
    padding: 3px 10px; border-radius: 2px; margin-bottom: 0.8rem;
}
.stButton > button {
    background: #1a1a2e !important; color: white !important;
    border: none !important; border-radius: 3px !important;
    font-family: 'DM Sans', sans-serif !important; font-weight: 500 !important;
    letter-spacing: 1px !important; text-transform: uppercase !important;
    font-size: 0.8rem !important; width: 100%;
}
.stButton > button:hover { background: #722F37 !important; }
.section-title {
    font-family: 'Playfair Display', serif; font-size: 1.3rem;
    font-weight: 700; color: #1a1a2e; border-left: 4px solid #722F37;
    padding-left: 0.8rem; margin: 1.5rem 0 1rem 0;
}
.locked-box {
    text-align: center; padding: 2rem; background: #f0f0f0;
    border: 2px dashed #aaa; border-radius: 4px; color: #666;
}
.connect-card {
    background: #f9f7f4; border: 1.5px solid #722F37; border-radius: 4px;
    padding: 1.2rem 1.5rem; margin: 1rem 0;
}
.connect-link {
    display:block; text-decoration:none; background:#1a1a2e; color:white !important;
    padding:0.6rem 1rem; border-radius:3px; margin:0.4rem 0; text-align:center;
    font-size:0.85rem; letter-spacing:1px; text-transform:uppercase;
}
.connect-link:hover { background:#722F37; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# CONFIG / CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════

SOCIAL_LINKS = {
    "linkedin":  "https://www.linkedin.com/in/toastmasters-club-of-pune-south-east-a6345a18b/",
    "instagram": "https://www.instagram.com/tmcpse",
    "whatsapp":  "https://chat.whatsapp.com/AdT6GJMdAjR5a9XkHWWcia?s=cl&p=i&ilr=2",
    "meetup": "https://www.meetup.com/Toastmasters-Club-of-Pune-South-East/",
}

ROLE_CATEGORY_MAP = {
    # Best Main Role Players
    "TMOD": "main",
    "GE": "main",
    "Table Topic Master": "main",
    
    # Best Supporting/Auxiliary Role Players
    "Timer": "aux",
    "Grammarian": "aux",
    "Ah Counter": "aux",
    "ALQ Master": "aux",
    "Other": "aux",  # catch-all for any other supporting roles
    
    # Speaker & Evaluator roles
    "Prepared Speeches": "speaker",
    "Evaluators": "evaluator",
    "Table Topic Speakers": "tt_speaker",
}

ALL_ROLES = list(ROLE_CATEGORY_MAP.keys())

VOTING_CATEGORIES = {
    "Best Main Role Player":              "main",
    "Best Supporting/Auxiliary Role Player": "aux",
    "Best Speaker":                       "speaker",
    "Best Evaluator":                     "evaluator",
    "Best Table Topic Speaker":           "tt_speaker",
}

JOIN_TIMELINE_OPTIONS = ["Within this month", "Next month", "Sometime later"]

# ══════════════════════════════════════════════════════════════════════════════
# SUPABASE HELPERS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def get_sb() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def today():
    return datetime.now().strftime("%Y-%m-%d")

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ── Members ───────────────────────────────────────────────────────────────────
def find_member(identifier):
    norm = identifier.lower().strip().replace(" ", "").replace("-", "")
    r = get_sb().table("members").select("*").ilike("email", norm).execute()
    if r.data:
        return r.data[0]
    r = get_sb().table("members").select("*").eq("phone", norm).execute()
    return r.data[0] if r.data else None

def update_member_birthday(member_id, day, month):
    get_sb().table("members").update({
        "birthday_day": day, "birthday_month": month
    }).eq("id", member_id).execute()

# ── Attendance ───────────────────────────────────────────────────────────────
def already_attended(member_id):
    r = get_sb().table("attendance").select("id").eq("member_id", member_id).eq("date", today()).execute()
    return len(r.data) > 0

def mark_attendance(member):
    get_sb().table("attendance").insert({
        "date": today(), "timestamp": now_ts(),
        "member_id": member["id"], "name": member["name"], "email": member["email"],
    }).execute()

# ── Guests ────────────────────────────────────────────────────────────────────
def save_guest(name, phone, source):
    """Insert guest, return new row id."""
    r = get_sb().table("guests").insert({
        "date": today(), "timestamp": now_ts(),
        "name": name, "phone": phone, "how_heard": source,
    }).execute()
    return r.data[0]["id"] if r.data else None

def update_guest_lead(guest_id, planning, timeline, vpm_ok):
    get_sb().table("guests").update({
        "planning_to_join": planning,
        "join_timeline": timeline,
        "vpm_contact_ok": vpm_ok,
    }).eq("id", guest_id).execute()

# ── Speakers / roles ──────────────────────────────────────────────────────────
def get_today_speakers():
    r = get_sb().table("today_speakers").select("*").eq("date", today()).execute()
    return r.data or []

def set_today_speakers(speakers_list):
    """speakers_list: [{"name":.., "role":.., "disqualified": bool}, ...]"""
    get_sb().table("today_speakers").delete().eq("date", today()).execute()
    rows = []
    for s in speakers_list:
        rows.append({
            "date": today(),
            "speaker_name": s["name"],
            "role": s["role"],
            "role_category": ROLE_CATEGORY_MAP.get(s["role"], "other"),
            "disqualified": s.get("disqualified", False),
        })
    if rows:
        get_sb().table("today_speakers").insert(rows).execute()

# ── Feedback (structured) ────────────────────────────────────────────────────
def get_feedback_by_user(user_id):
    r = get_sb().table("feedback").select("speaker_name").eq("user_id", user_id).eq("date", today()).execute()
    return {row["speaker_name"] for row in (r.data or [])}

def save_structured_feedback(user_id, user_name, speaker_name, speaker_role,
                               content, structure, interaction, confidence, overall, extra_text):
    get_sb().table("feedback").insert({
        "date": today(), "timestamp": now_ts(), "user_id": user_id,
        "user_name": user_name, "speaker_name": speaker_name,
        "speaker_role": speaker_role,
        "rating_content": content, "rating_structure": structure,
        "rating_interaction": interaction, "rating_confidence": confidence,
        "rating_overall": overall,
        "feedback_text": extra_text or "",
    }).execute()

def get_feedback_for_speaker(speaker_name):
    r = get_sb().table("feedback").select("*").eq("date", today()).eq("speaker_name", speaker_name).execute()
    return r.data or []

# ── Votes ─────────────────────────────────────────────────────────────────────
def get_votes_by_user(user_id):
    r = get_sb().table("votes").select("category").eq("user_id", user_id).eq("date", today()).execute()
    return {row["category"] for row in (r.data or [])}

def save_vote(user_id, user_name, category, nominee):
    get_sb().table("votes").insert({
        "date": today(), "timestamp": now_ts(), "user_id": user_id,
        "user_name": user_name, "category": category, "nominee": nominee,
    }).execute()

def get_vote_tally():
    r = get_sb().table("votes").select("category, nominee").eq("date", today()).execute()
    tally = {}
    for row in (r.data or []):
        cat, nom = row["category"], row["nominee"]
        tally.setdefault(cat, {})
        tally[cat][nom] = tally[cat].get(nom, 0) + 1
    return tally

# ── Meeting-level rating ─────────────────────────────────────────────────────
def save_meeting_rating(user_id, user_name, user_type, overall_rating, general_feedback):
    get_sb().table("meeting_ratings").insert({
        "date": today(), "timestamp": now_ts(),
        "user_id": user_id, "user_name": user_name, "user_type": user_type,
        "overall_rating": overall_rating, "general_feedback": general_feedback or "",
    }).execute()

def has_rated_meeting(user_id):
    r = get_sb().table("meeting_ratings").select("id").eq("user_id", user_id).eq("date", today()).execute()
    return len(r.data) > 0

# ── Voting config ─────────────────────────────────────────────────────────────
def get_voting_open():
    r = get_sb().table("meeting_config").select("value").eq("key", "VotingOpen").execute()
    return r.data[0]["value"].strip().lower() == "yes" if r.data else False

def set_voting_open(flag):
    val = "Yes" if flag else "No"
    existing = get_sb().table("meeting_config").select("id").eq("key", "VotingOpen").execute()
    if existing.data:
        get_sb().table("meeting_config").update({"value": val}).eq("key", "VotingOpen").execute()
    else:
        get_sb().table("meeting_config").insert({"key": "VotingOpen", "value": val}).execute()

# ── Stats ─────────────────────────────────────────────────────────────────────
def get_today_stats():
    sb = get_sb()
    a = sb.table("attendance").select("id", count="exact").eq("date", today()).execute()
    g = sb.table("guests").select("id", count="exact").eq("date", today()).execute()
    f = sb.table("feedback").select("id", count="exact").eq("date", today()).execute()
    return (a.count or 0), (g.count or 0), (f.count or 0)

# ══════════════════════════════════════════════════════════════════════════════
# EMAIL (anonymous feedback delivery)
# ══════════════════════════════════════════════════════════════════════════════

def send_email(to_email, subject, body):
    """Send plain-text email via Resend API."""
    import requests
    
    api_key = st.secrets["RESEND_API_KEY"]
    email_from = st.secrets["EMAIL_FROM"]
    
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "from": email_from,
            "to": to_email,
            "subject": subject,
            "text": body,
        }
    )
    
    if response.status_code != 200:
        raise Exception(f"Resend error: {response.text}")

def find_speaker_email(speaker_name):
    """Look up email by matching speaker_name to a member's name."""
    r = get_sb().table("members").select("email,name").ilike("name", speaker_name).execute()
    if r.data:
        return r.data[0]["email"]
    return None

def already_emailed(speaker_name):
    r = get_sb().table("feedback_email_log").select("id").eq("date", today()).eq("speaker_name", speaker_name).execute()
    return len(r.data) > 0

def mark_emailed(speaker_name):
    get_sb().table("feedback_email_log").insert({
        "date": today(), "speaker_name": speaker_name, "sent_at": now_ts(),
    }).execute()

def send_feedback_emails():
    """For each prepared speaker today, email aggregated anonymous feedback."""
    speakers = [s for s in get_today_speakers() if s.get("role_category") == "speaker"]
    results = []  # (name, status_message)

    for sp in speakers:
        name = sp["speaker_name"]
        if already_emailed(name):
            results.append((name, "Already sent earlier — skipped."))
            continue

        fb_list = get_feedback_for_speaker(name)
        if not fb_list:
            results.append((name, "No feedback received — skipped."))
            continue

        email = find_speaker_email(name)
        if not email:
            results.append((name, "⚠️ No email found in Members table — skipped."))
            continue

        # Build body
        lines = []
        lines.append("Hi,")
        lines.append("")
        lines.append("It was great to hear your speech at our recent Toastmasters "
                      "Pune South East meeting! You have received "
                      f"{len(fb_list)} feedback(s) as below:")
        lines.append("")
        for i, fb in enumerate(fb_list, start=1):
            scores = (
                f"Content {fb.get('rating_content','-')}/3, "
                f"Structure {fb.get('rating_structure','-')}/3, "
                f"Interaction {fb.get('rating_interaction','-')}/3, "
                f"Confidence {fb.get('rating_confidence','-')}/3, "
                f"Overall {fb.get('rating_overall','-')}/5"
            )
            comment = (fb.get("feedback_text") or "").strip()
            comment_str = comment if comment else "(no additional comments)"
            lines.append(f"{i}. [{scores}] - Comments: {comment_str}")
        lines.append("")
        lines.append("Keep up the great work!")
        lines.append("- Toastmasters Pune South East")

        body = "\n".join(lines)

        try:
            send_email(email, "Your Speech Feedback — Toastmasters Pune South East", body)
            mark_emailed(name)
            results.append((name, f"✅ Sent to {email} ({len(fb_list)} feedback(s))"))
        except Exception as e:
            results.append((name, f"❌ Failed: {e}"))

    return results

# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

for k, v in {
    "page": "login", "user_type": None, "user_id": None, "user_name": None,
    "already_attended": False, "admin_mode": False,
    "guest_id": None, "member_id": None,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

is_admin = st.query_params.get("admin", "") == "1"
page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ══════════════════════════════════════════════════════════════════════════════
if is_admin:
    try:
        ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        ADMIN_PASSWORD = "toastmasters2024"

    if not st.session_state.admin_mode:
        st.markdown("""
        <div class="tm-card" style="max-width:400px;margin:3rem auto;">
          <div style="text-align:center">
            <div style="font-size:2rem">🔐</div>
            <div class="tm-club-name" style="font-size:1.2rem">Admin Panel</div>
            <div class="tm-tagline">SAA Access Only</div>
          </div>
        </div>""", unsafe_allow_html=True)
        with st.form("admin_login_form"):
            pwd = st.text_input("Password", type="password", key="admin_pwd_input")
            if st.form_submit_button("Enter Admin Panel", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    else:
        st.markdown("""
        <div class="tm-card" style="padding:1.2rem 1.8rem;margin-bottom:1rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div class="tm-club-name" style="font-size:1rem;text-align:left">
                Toastmasters Pune South East</div>
              <div class="tm-tagline" style="font-size:0.65rem;text-align:left">
                Sergeant-at-Arms Panel</div>
            </div>
            <div class="badge">Admin</div>
          </div>
        </div>""", unsafe_allow_html=True)

        try:
            speakers    = get_today_speakers()
            voting_open = get_voting_open()
        except Exception as e:
            st.error(f"Error loading data: {e}")
            st.stop()

        tab1, tab2, tab3, tab4 = st.tabs(
            ["Today's Roles", "Voting Control", "Live Stats", "Send Feedback Emails"]
        )

        # ── TAB 1: Today's Roles ────────────────────────────────────────────
        with tab1:
            st.markdown(f"**Date:** {today()}")
            st.caption("Standard roles — select from the dropdown for accurate vote-category mapping.")

            if speakers:
                st.markdown("**Currently saved:**")
                for sp in speakers:
                    dq = " 🚫 DISQUALIFIED" if sp.get("disqualified") else ""
                    st.markdown(f"🎙️ **{sp['speaker_name']}** — *{sp['role']}*{dq}")
                st.markdown("---")

            st.markdown("#### Add / Update Today's Speakers & Role Players")
            st.caption("Fill all names, set role + disqualification, then click Save — replaces today's list.")

            if "num_rows" not in st.session_state:
                st.session_state.num_rows = max(len(speakers), 3)

            entries = []
            for i in range(st.session_state.num_rows):
                ex = speakers[i] if i < len(speakers) else {}
                ex_name = ex.get("speaker_name", "")
                ex_role = ex.get("role", "Prepared Speeches")
                ex_dq   = ex.get("disqualified", False)

                c1, c2, c3 = st.columns([2, 2, 1])
                with c1:
                    nm = st.text_input(f"Name {i+1}", value=ex_name,
                        key=f"sp_n_{i}", placeholder=f"Name {i+1}", label_visibility="collapsed")
                with c2:
                    ri = ALL_ROLES.index(ex_role) if ex_role in ALL_ROLES else ALL_ROLES.index("Prepared Speeches")
                    rl = st.selectbox(f"Role {i+1}", ALL_ROLES, index=ri,
                        key=f"sp_r_{i}", label_visibility="collapsed")
                with c3:
                    dq = st.checkbox("DQ (Timer)", value=ex_dq, key=f"sp_dq_{i}")

                if nm.strip():
                    entries.append({"name": nm.strip(), "role": rl, "disqualified": dq})

            ca, cb = st.columns(2)
            with ca:
                if st.button("+ Add Row", use_container_width=True, key="add_row_btn"):
                    st.session_state.num_rows = min(st.session_state.num_rows + 1, 30)
                    st.rerun()
            with cb:
                if st.button("Save Speakers", use_container_width=True, key="save_spk_btn"):
                    if not entries:
                        st.warning("Enter at least one name.")
                    else:
                        try:
                            set_today_speakers(entries)
                            st.success(f"Saved {len(entries)} entries.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        # ── TAB 2: Voting Control ────────────────────────────────────────────
        with tab2:
            st.markdown("#### Master Voting Switch")
            col = "#2d7a2d" if voting_open else "#722F37"
            lbl = "VOTING IS OPEN" if voting_open else "VOTING IS CLOSED"
            st.markdown(f"""<div style="background:{col}22;border:2px solid {col};
                border-radius:4px;padding:1rem;text-align:center;margin:1rem 0;">
                <strong style="color:{col};font-size:1.1rem">{lbl}</strong></div>""",
                unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Open Voting", use_container_width=True,
                             disabled=voting_open, key="open_vote_btn"):
                    set_voting_open(True); st.rerun()
            with c2:
                if st.button("Close Voting", use_container_width=True,
                             disabled=not voting_open, key="close_vote_btn"):
                    set_voting_open(False); st.rerun()

            st.markdown("---")
            col_a, col_b = st.columns([3,1])
            with col_a:
                st.markdown("#### Live Vote Tally")
            with col_b:
                if st.button("🔄 Refresh", key="refresh_tally_btn", use_container_width=True):
                    st.rerun()
            try:
                tally = get_vote_tally()
                if not tally:
                    st.info("No votes yet.")
                else:
                    for cat, counts in tally.items():
                        st.markdown(f"**{cat}**")
                        for nom, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                            st.markdown(f"&nbsp;&nbsp;{nom}: {'█' * cnt} ({cnt})")
            except Exception as e:
                st.warning(str(e))

            st.markdown("---")
            st.markdown("#### Overall Meeting Ratings")
            try:
                mr = get_sb().table("meeting_ratings").select("*").eq("date", today()).execute()
                ratings = mr.data or []
                if ratings:
                    avg = sum(r["overall_rating"] for r in ratings) / len(ratings)
                    st.metric("Average Rating", f"{avg:.1f} / 5", help=f"Based on {len(ratings)} responses")
                    for r in ratings:
                        if r.get("general_feedback"):
                            st.markdown(f"- *{r['user_name']}* ({r['user_type']}): {r['general_feedback']}")
                else:
                    st.info("No meeting ratings yet.")
            except Exception as e:
                st.warning(str(e))

        # ── TAB 3: Live Stats ────────────────────────────────────────────────
        with tab3:
            col_a, col_b = st.columns([3,1])
            with col_b:
                if st.button("🔄 Refresh", key="refresh_stats_btn", use_container_width=True):
                    st.rerun()
            try:
                mc, gc, fc = get_today_stats()
                c1, c2, c3 = st.columns(3)
                c1.metric("Members In",     mc)
                c2.metric("Guests Today",   gc)
                c3.metric("Feedback Given", fc)
            except Exception as e:
                st.warning(str(e))

            st.markdown("---")
            try:
                import pandas as pd
                att = get_sb().table("attendance").select("timestamp,name,email").eq("date", today()).execute()
                st.markdown("**Attendance**")
                st.dataframe(pd.DataFrame(att.data or []), use_container_width=True)

                gst = get_sb().table("guests").select(
                    "timestamp,name,phone,how_heard,planning_to_join,join_timeline,vpm_contact_ok"
                ).eq("date", today()).execute()
                st.markdown("**Guests & Leads**")
                df_g = pd.DataFrame(gst.data or [])
                st.dataframe(df_g, use_container_width=True)

                # Highlight high-intent leads
                if not df_g.empty and "vpm_contact_ok" in df_g.columns:
                    hot = df_g[df_g["vpm_contact_ok"] == "Yes, absolutely"]
                    if not hot.empty:
                        st.markdown("**🔥 Hot Leads (VPM follow-up requested):**")
                        st.dataframe(hot, use_container_width=True)
            except Exception as e:
                st.warning(str(e))

        # ── TAB 4: Send Feedback Emails ─────────────────────────────────────
        with tab4:
            st.markdown("#### Send Anonymous Feedback Emails")
            st.caption(
                "Sends each Prepared Speaker an aggregated, anonymous summary of "
                "today's feedback. Speakers with 0 feedback are skipped automatically. "
                "Already-sent speakers won't be emailed twice."
            )
            speakers_today = [s for s in speakers if s.get("role_category") == "speaker"]
            if not speakers_today:
                st.info("No Prepared Speeches configured for today.")
            else:
                st.markdown("**Today's Prepared Speakers:**")
                for s in speakers_today:
                    fb_count = len(get_feedback_for_speaker(s["speaker_name"]))
                    sent = "✅ already sent" if already_emailed(s["speaker_name"]) else ""
                    st.markdown(f"- {s['speaker_name']}: {fb_count} feedback(s) {sent}")

                if st.button("📧 Send Feedback Emails Now", key="send_fb_emails_btn"):
                    with st.spinner("Sending emails..."):
                        results = send_feedback_emails()
                    for name, status in results:
                        st.write(f"**{name}**: {status}")

        if st.button("Exit Admin Panel", key="exit_admin_btn"):
            st.session_state.admin_mode = False
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "login":
    st.markdown("""
    <div class="tm-card">
      <div style="text-align:center;margin-bottom:2rem">
        <div style="font-size:2.8rem;margin-bottom:0.3rem">🎤</div>
        <div class="tm-club-name">Toastmasters<br>Pune South East</div>
        <hr class="tm-divider">
        <div class="tm-tagline">Where Leaders Are Made</div>
      </div>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="badge">Check In</div>', unsafe_allow_html=True)
    st.markdown("**Enter your email or phone number to check in for today's meeting.**")

    with st.form("checkin_form"):
        identifier = st.text_input("Email or Phone",
            placeholder="e.g. john@email.com  or  9876543210",
            label_visibility="collapsed", key="checkin_id")
        submitted = st.form_submit_button("Check In", use_container_width=True)

    if submitted:
        if not identifier.strip():
            st.error("Please enter your email or phone number.")
        else:
            with st.spinner("Checking..."):
                try:
                    member = find_member(identifier.strip())
                except Exception as e:
                    st.error(f"Connection error: {e}")
                    st.stop()

            if member:
                already = already_attended(member["id"])
                if not already:
                    mark_attendance(member)
                st.session_state.update({
                    "page": "dashboard", "user_type": "member",
                    "user_id": str(member["id"]), "user_name": member["name"],
                    "already_attended": already, "member_id": member["id"],
                })
                # Check birthday
                if member.get("birthday_day") is None or member.get("birthday_month") is None:
                    st.session_state.page = "birthday_prompt"
                st.rerun()
            else:
                st.session_state.page = "guest_form"
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# BIRTHDAY PROMPT (member, only if missing)
# ══════════════════════════════════════════════════════════════════════════════
elif page == "birthday_prompt":
    st.markdown("""
    <div class="tm-card">
      <div style="text-align:center;margin-bottom:1rem">
        <div style="font-size:2rem">🎂</div>
        <div class="tm-club-name" style="font-size:1.2rem">Help us celebrate you!</div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("Please share your birthday (date & month only — no year needed) "
                "so we can celebrate with you during our monthly socials.")

    with st.form("birthday_form"):
        c1, c2 = st.columns(2)
        with c1:
            day = st.selectbox("Day", list(range(1, 32)), key="bday_day")
        with c2:
            month = st.selectbox("Month", [
                "January","February","March","April","May","June","July",
                "August","September","October","November","December"
            ], key="bday_month")
        c1b, c2b = st.columns(2)
        with c1b:
            submitted = st.form_submit_button("Save & Continue", use_container_width=True)
        with c2b:
            skipped = st.form_submit_button("Skip for now", use_container_width=True)

    if submitted:
        month_num = ["January","February","March","April","May","June","July",
                      "August","September","October","November","December"].index(month) + 1
        try:
            update_member_birthday(st.session_state.member_id, day, month_num)
        except Exception as e:
            st.warning(f"Could not save birthday: {e}")
        st.session_state.page = "dashboard"
        st.rerun()

    if skipped:
        st.session_state.page = "dashboard"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# GUEST FORM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "guest_form":
    st.markdown("""
    <div class="tm-card">
      <div style="text-align:center;margin-bottom:1rem">
        <div style="font-size:2rem">🎉</div>
        <div class="tm-club-name" style="font-size:1.2rem">Welcome, Guest!</div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("Looks like you're new here — great to have you! Please tell us a little about yourself.")

    with st.form("guest_form"):
        name   = st.text_input("Your Full Name *",  placeholder="Priya Sharma", key="g_name")
        phone  = st.text_input("Phone Number *",    placeholder="9876543210",   key="g_phone")
        source = st.selectbox("How did you hear about us? *",
            ["-- Select --","Google","Friend / Word of Mouth","LinkedIn",
             "Instagram","Facebook","WhatsApp Group","Event Listing","Other"],
            key="g_source")
        submitted = st.form_submit_button("Join Today's Meeting", use_container_width=True)

    if submitted:
        errors = []
        if not name.strip():          errors.append("Name is required.")
        if not phone.strip():         errors.append("Phone number is required.")
        if source == "-- Select --":  errors.append("Please select how you heard about us.")
        for e in errors:
            st.error(e)
        if not errors:
            guest_id = save_guest(name.strip(), phone.strip(), source)
            st.session_state.update({
                "page": "dashboard", "user_type": "guest",
                "user_id": f"guest_{phone.strip()}", "user_name": name.strip(),
                "guest_id": guest_id,
            })
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
elif page == "dashboard":
    user_name = st.session_state.user_name
    user_type = st.session_state.user_type
    user_id   = st.session_state.user_id
    already   = st.session_state.already_attended

    if user_type == "member":
        msg = (f"👋 Welcome back, <strong>{user_name}</strong>! Attendance already recorded."
               if already else
               f"✅ Attendance marked! Welcome, <strong>{user_name}</strong>!")
        bc, bg = "#2d7a2d", "#f0f7f0"
    else:
        msg = f"🎉 Welcome, <strong>{user_name}</strong>! Glad you joined us today."
        bc, bg = "#722F37", "#fff7f5"

    st.markdown(f"""
    <div class="tm-card" style="padding:1.2rem 1.8rem;">
      <div style="display:flex;align-items:center;gap:1rem;">
        <div style="font-size:2rem">🎤</div>
        <div>
          <div class="tm-club-name" style="font-size:1.1rem;text-align:left">
            Toastmasters Pune South East</div>
          <div class="tm-tagline" style="font-size:0.7rem;text-align:left">{today()}</div>
        </div>
      </div>
    </div>
    <div style="background:{bg};border-left:4px solid {bc};padding:0.9rem 1.2rem;
         border-radius:3px;margin-bottom:1.5rem;">{msg}</div>
    """, unsafe_allow_html=True)

    # ── Guest: Connect with Us ──────────────────────────────────────────────
    if user_type == "guest":
        st.markdown('<div class="section-title">🔗 Connect with Us</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="connect-card">
          <p style="margin-top:0">Stay in the loop with our upcoming meetings and events!</p>
          <a class="connect-link" href="{SOCIAL_LINKS['linkedin']}" target="_blank">Follow us on LinkedIn</a>
          <a class="connect-link" href="{SOCIAL_LINKS['instagram']}" target="_blank">Follow us on Instagram</a>
          <a class="connect-link" href="{SOCIAL_LINKS['whatsapp']}" target="_blank">Join our WhatsApp Community</a>
        </div>
        """, unsafe_allow_html=True)

    # ── Member: PR Boost ─────────────────────────────────────────────────────
    if user_type == "member":
        st.markdown('<div class="section-title">📣 Help Our Club Grow</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="connect-card">
          <p style="margin-top:0">Follow our social media handles, and like/share our latest
          posts to help our PR reach more people!</p>
          <a class="connect-link" href="{SOCIAL_LINKS['linkedin']}" target="_blank">LinkedIn</a>
          <a class="connect-link" href="{SOCIAL_LINKS['instagram']}" target="_blank">Instagram</a>
          <a class="connect-link" href="{SOCIAL_LINKS['whatsapp']}" target="_blank">WhatsApp Community</a>
        </div>
        """, unsafe_allow_html=True)

    # ── Load meeting data ─────────────────────────────────────────────────────
    try:
        speakers      = get_today_speakers()
        voting_open   = get_voting_open()
        gave_feedback = get_feedback_by_user(user_id)
        already_voted = get_votes_by_user(user_id)
    except Exception as e:
        st.error(f"Could not load meeting data: {e}")
        st.stop()

    # ══════════════════════════════════════════════════════════════════════
    # SPEAKER FEEDBACK (Prepared Speeches ONLY, structured ratings)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🗣️ Speaker Feedback</div>', unsafe_allow_html=True)

    prepared_speakers = [s for s in speakers if s.get("role_category") == "speaker"
                          and not s.get("disqualified")]

    if not prepared_speakers:
        st.info("No Prepared Speeches have been added for today's meeting yet.")
    else:
        RATING_3 = [1, 2, 3]
        RATING_5 = [1, 2, 3, 4, 5]

        for sp in prepared_speakers:
            sp_name = sp["speaker_name"]
            sp_role = sp["role"]
            with st.expander(f"**{sp_name}** — {sp_role}", expanded=True):
                if sp_name in gave_feedback:
                    st.success("✅ You already submitted feedback for this speaker.")
                else:
                    st.markdown("**Rate the following (1 = needs work, 3 = excellent):**")
                    c1, c2 = st.columns(2)
                    with c1:
                        content = st.radio("Content", RATING_3, horizontal=True,
                            key=f"content_{sp_name}", index=2)
                        interaction = st.radio("Interaction", RATING_3, horizontal=True,
                            key=f"interaction_{sp_name}", index=2)
                    with c2:
                        structure = st.radio("Structure", RATING_3, horizontal=True,
                            key=f"structure_{sp_name}", index=2)
                        confidence = st.radio("Confidence", RATING_3, horizontal=True,
                            key=f"confidence_{sp_name}", index=2)

                    overall = st.radio("Overall Speech Rating (1-5)", RATING_5,
                        horizontal=True, key=f"overall_{sp_name}", index=4)

                    extra = st.text_area("Any special/additional feedback? (optional)",
                        key=f"extra_{sp_name}", placeholder="Optional comments...", height=80)

                    if st.button(f"Submit Feedback for {sp_name}", key=f"btn_{sp_name}"):
                        save_structured_feedback(
                            user_id, user_name, sp_name, sp_role,
                            content, structure, interaction, confidence, overall, extra.strip()
                        )
                        st.success("✅ Feedback submitted! Thank you.")
                        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # VOTING (5 categories, disqualified filtered out)
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🏆 Vote for Best Roles</div>', unsafe_allow_html=True)

    if not voting_open:
        st.markdown("""<div class="locked-box">
          <div style="font-size:2.5rem">🔒</div>
          <p style="font-size:1.1rem;font-weight:600;margin:0.5rem 0;">Voting is not open yet</p>
          <p style="color:#888;margin:0">The SAA will unlock voting at the end of the meeting.
          This page updates automatically — no need to refresh!</p>
        </div>""", unsafe_allow_html=True)
        st.caption("⏳ Checking voting status... (auto-refreshes every 15s)")
        st.markdown(
            "<script>setTimeout(function(){window.location.reload();}, 15000);</script>",
            unsafe_allow_html=True,
        )
    else:
        eligible = [s for s in speakers if not s.get("disqualified")]

        def nominees_for(category_key):
            return [s["speaker_name"] for s in eligible
                    if s.get("role_category") == category_key]

        categories = {cat: nominees_for(key) for cat, key in VOTING_CATEGORIES.items()}
        remaining = {c: n for c, n in categories.items() if c not in already_voted and n}

        already_done = {c for c in categories if c in already_voted}
        no_nominees  = {c for c, n in categories.items() if not n and c not in already_voted}

        if already_done:
            for c in already_done:
                st.markdown(f"✅ **{c}** — already voted")
        if no_nominees:
            for c in no_nominees:
                st.caption(f"*No eligible nominees for {c} yet.*")

        if not remaining:
            st.success("🎉 You have cast all available votes! Thank you.")
        else:
            st.markdown("*Cast your votes below — one per category.*")
            with st.form("voting_form"):
                selections = {}
                for cat, nominees in remaining.items():
                    selections[cat] = st.selectbox(f"🏅 {cat}",
                        ["-- Select --"] + nominees, key=f"v_{cat}")
                if st.form_submit_button("Submit Votes", use_container_width=True):
                    missing = [c for c, s in selections.items() if s == "-- Select --"]
                    if missing:
                        st.warning(f"Please select for: {', '.join(missing)}")
                    else:
                        for cat, sel in selections.items():
                            save_vote(user_id, user_name, cat, sel)
                        st.success("✅ Votes submitted! Thank you!")
                        st.rerun()

    # ══════════════════════════════════════════════════════════════════════
    # OVERALL MEETING RATING (mandatory) + optional general feedback
    # ══════════════════════════════════════════════════════════════════════
    if voting_open:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">⭐ Overall Meeting Experience</div>', unsafe_allow_html=True)

        if has_rated_meeting(user_id):
            st.success("✅ Thanks — you've already rated today's meeting!")
            # If guest and rated but hasn't done lead form yet, show it
            if user_type == "guest" and st.session_state.get("guest_id") and not st.session_state.get("lead_form_done"):
                st.session_state.page = "guest_followup"
                st.rerun()
        else:
            with st.form("meeting_rating_form"):
                overall_meeting = st.radio(
                    "Overall Meeting Experience (1-5) *",
                    [1, 2, 3, 4, 5], horizontal=True, key="overall_meeting_rating", index=4
                )
                general_fb = st.text_area(
                    "General feedback/suggestions for the complete meeting (optional)",
                    key="general_meeting_feedback", height=90,
                    placeholder="Anything you'd like to share about today's meeting..."
                )
                if st.form_submit_button("Submit Meeting Rating", use_container_width=True):
                    save_meeting_rating(user_id, user_name, user_type, overall_meeting, general_fb.strip())
                    st.success("✅ Thank you for your feedback!")
                    if user_type == "guest" and st.session_state.get("guest_id"):
                        st.session_state.page = "guest_followup"
                    st.rerun()

    # ── Sign out ──────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sign Out", key="signout_btn"):
        for k in ["page","user_type","user_id","user_name","already_attended",
                  "guest_id","member_id","lead_form_done"]:
            st.session_state.pop(k, None)
        st.session_state.page = "login"
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# GUEST FOLLOW-UP / LEAD GENERATION FORM
# ══════════════════════════════════════════════════════════════════════════════
elif page == "guest_followup":
    st.markdown("""
    <div class="tm-card">
      <div style="text-align:center;margin-bottom:1rem">
        <div style="font-size:2rem">🌟</div>
        <div class="tm-club-name" style="font-size:1.2rem">Before You Go...</div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.markdown("We'd love to know if Toastmasters Pune South East might be a fit for you!")

    with st.form("guest_lead_form"):
        planning = st.radio(
            "Are you planning to join our club?",
            ["Yes", "No", "Thinking about it"], key="planning_join"
        )

        timeline = None
        if planning in ("Yes", "Thinking about it"):
            timeline = st.selectbox(
                "When are you tentatively planning to join?",
                ["-- Select --"] + JOIN_TIMELINE_OPTIONS, key="join_timeline"
            )

        vpm_ok = st.radio(
            "Are you okay if our VP Membership connects with you to understand "
            "your requirements from the club and guide you with more information?",
            ["Yes, absolutely", "I'll reach out myself"], key="vpm_contact"
        )

        submitted = st.form_submit_button("Submit & Finish", use_container_width=True)

    if submitted:
        if planning in ("Yes", "Thinking about it") and timeline == "-- Select --":
            st.warning("Please select a tentative joining timeline.")
        else:
            try:
                update_guest_lead(
                    st.session_state.guest_id, planning,
                    timeline if planning in ("Yes","Thinking about it") else None,
                    vpm_ok
                )
            except Exception as e:
                st.warning(f"Could not save your response: {e}")
            st.session_state.lead_form_done = True
            st.session_state.page = "thank_you"
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# THANK YOU PAGE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "thank_you":
    st.markdown(f"""
    <div class="tm-card" style="text-align:center">
      <div style="font-size:3rem">🙏</div>
      <div class="tm-club-name" style="font-size:1.4rem">Thank You!</div>
      <p style="margin-top:1rem">We hope you enjoyed today's meeting at
      Toastmasters Pune South East. We look forward to seeing you again soon!</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="connect-card" style="text-align:center">
      <a class="connect-link" href="{SOCIAL_LINKS['linkedin']}" target="_blank">Follow us on LinkedIn</a>
      <a class="connect-link" href="{SOCIAL_LINKS['instagram']}" target="_blank">Follow us on Instagram</a>
      <a class="connect-link" href="{SOCIAL_LINKS['whatsapp']}" target="_blank">Join our WhatsApp Community</a>
    </div>
    """, unsafe_allow_html=True)

    if st.button("Done", key="done_btn"):
        for k in ["page","user_type","user_id","user_name","already_attended",
                  "guest_id","member_id","lead_form_done"]:
            st.session_state.pop(k, None)
        st.session_state.page = "login"
        st.rerun()
