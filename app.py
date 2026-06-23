import streamlit as st
from supabase import create_client, Client
from datetime import datetime, date
import urllib.parse

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
    "TMOD": "main", "GE": "main", "Table Topic Master": "main",
    "Timer": "aux", "Grammarian": "aux", "Ah Counter": "aux", "ALQ Master": "aux", "Other": "aux",
    "Prepared Speeches": "speaker", "Evaluators": "evaluator", "Table Topic Speakers": "tt_speaker",
}

ALL_ROLES = list(ROLE_CATEGORY_MAP.keys())
VOTING_CATEGORIES = {
    "Best Main Role Player": "main", "Best Supporting/Auxiliary Role Player": "aux",
    "Best Speaker": "speaker", "Best Evaluator": "evaluator", "Best Table Topic Speaker": "tt_speaker",
}
JOIN_TIMELINE_OPTIONS = ["Within this month", "Next month", "Sometime later"]
EXCOM_ROLES = ["SAA", "VP Membership", "VP Education", "President", "Secretary", "VP PR", "Treasurer"]

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

def find_member(identifier):
    norm = identifier.lower().strip()
    r = get_sb().table("members").select("*").ilike("email", norm).execute()
    if r.data: return r.data[0]
    r = get_sb().table("members").select("*").eq("phone", norm).execute()
    return r.data[0] if r.data else None

def update_member_birthday(member_id, day, month):
    get_sb().table("members").update({"birthday_day": day, "birthday_month": month}).eq("id", member_id).execute()

# ── Roster & Attendance management ───────────────────────────────────────────
def add_new_member(name, phone, email, b_day, b_month, is_active):
    get_sb().table("members").insert({
        "name": name, "phone": phone, "email": email.lower().strip(),
        "birthday_day": b_day, "birthday_month": b_month, "is_active": is_active,
        "joining_date": today()
    }).execute()

def update_member_status(member_id, is_active):
    get_sb().table("members").update({"is_active": is_active}).eq("id", member_id).execute()

def get_all_members():
    r = get_sb().table("members").select("*").order("name").execute()
    return r.data or []

def already_attended(member_id):
    r = get_sb().table("attendance").select("id").eq("member_id", member_id).eq("date", today()).execute()
    return len(r.data) > 0

def mark_attendance(member):
    get_sb().table("attendance").insert({
        "date": today(), "timestamp": now_ts(), "member_id": member["id"], "name": member["name"], "email": member["email"],
    }).execute()

# ── Guests & Scheduler ────────────────────────────────────────────────────────
def save_guest(name, phone, source):
    r = get_sb().table("guests").insert({"date": today(), "timestamp": now_ts(), "name": name, "phone": phone, "how_heard": source}).execute()
    return r.data[0]["id"] if r.data else None

def get_guests_by_date(selected_date):
    r = get_sb().table("guests").select("*").eq("date", str(selected_date)).execute()
    return r.data or []

def update_guest_lead(guest_id, planning, timeline, vpm_ok):
    get_sb().table("guests").update({"planning_to_join": planning, "join_timeline": timeline, "vpm_contact_ok": vpm_ok}).eq("id", guest_id).execute()

def save_meeting_schedule(meeting_date, role_data):
    get_sb().table("meeting_schedules").upsert({"meeting_date": str(meeting_date), "roles_json": role_data}).execute()

def get_meeting_schedule(meeting_date):
    r = get_sb().table("meeting_schedules").select("*").eq("meeting_date", str(meeting_date)).execute()
    return r.data[0] if r.data else None

def save_meeting_meta(meeting_num, meeting_date):
    get_sb().table("meetings").upsert({"meeting_number": meeting_num, "date": str(meeting_date)}).execute()

# ── Speakers / Roles ──────────────────────────────────────────────────────────
def get_today_speakers():
    r = get_sb().table("today_speakers").select("*").eq("date", today()).execute()
    return r.data or []

def set_today_speakers(speakers_list):
    get_sb().table("today_speakers").delete().eq("date", today()).execute()
    rows = []
    for s in speakers_list:
        rows.append({
            "date": today(), "speaker_name": s["name"], "role": s["role"],
            "role_category": ROLE_CATEGORY_MAP.get(s["role"], "other"), "disqualified": s.get("disqualified", False),
        })
    if rows: get_sb().table("today_speakers").insert(rows).execute()

# ── Feedback & Votes ──────────────────────────────────────────────────────────
def get_feedback_by_user(user_id):
    r = get_sb().table("feedback").select("speaker_name").eq("user_id", user_id).eq("date", today()).execute()
    return {row["speaker_name"] for row in (r.data or [])}

def save_structured_feedback(user_id, user_name, speaker_name, speaker_role, content, structure, interaction, confidence, overall, extra_text):
    get_sb().table("feedback").insert({
        "date": today(), "timestamp": now_ts(), "user_id": user_id, "user_name": user_name, "speaker_name": speaker_name, "speaker_role": speaker_role,
        "rating_content": content, "rating_structure": structure, "rating_interaction": interaction, "rating_confidence": confidence, "rating_overall": overall, "feedback_text": extra_text or "",
    }).execute()

def get_feedback_for_speaker(speaker_name):
    r = get_sb().table("feedback").select("*").eq("date", today()).eq("speaker_name", speaker_name).execute()
    return r.data or []

def get_votes_by_user(user_id):
    r = get_sb().table("votes").select("category").eq("user_id", user_id).eq("date", today()).execute()
    return {row["category"] for row in (r.data or [])}

def save_vote(user_id, user_name, category, nominee):
    get_sb().table("votes").insert({"date": today(), "timestamp": now_ts(), "user_id": user_id, "user_name": user_name, "category": category, "nominee": nominee}).execute()

def get_vote_tally():
    r = get_sb().table("votes").select("category, nominee").eq("date", today()).execute()
    tally = {}
    for row in (r.data or []):
        cat, nom = row["category"], row["nominee"]
        tally.setdefault(cat, {})
        tally[cat][nom] = tally[cat].get(nom, 0) + 1
    return tally

def save_meeting_rating(user_id, user_name, user_type, overall_rating, general_feedback):
    get_sb().table("meeting_ratings").insert({"date": today(), "timestamp": now_ts(), "user_id": user_id, "user_name": user_name, "user_type": user_type, "overall_rating": overall_rating, "general_feedback": general_feedback or ""}).execute()

def has_rated_meeting(user_id):
    r = get_sb().table("meeting_ratings").select("id").eq("user_id", user_id).eq("date", today()).execute()
    return len(r.data) > 0

def get_voting_open():
    r = get_sb().table("meeting_config").select("value").eq("key", "VotingOpen").execute()
    return r.data[0]["value"].strip().lower() == "yes" if r.data else False

def set_voting_open(flag):
    val = "Yes" if flag else "No"
    existing = get_sb().table("meeting_config").select("id").eq("key", "VotingOpen").execute()
    if existing.data: get_sb().table("meeting_config").update({"value": val}).eq("key", "VotingOpen").execute()
    else: get_sb().table("meeting_config").insert({"key": "VotingOpen", "value": val}).execute()

def get_today_stats():
    sb = get_sb()
    a = sb.table("attendance").select("id", count="exact").eq("date", today()).execute()
    g = sb.table("guests").select("id", count="exact").eq("date", today()).execute()
    f = sb.table("feedback").select("id", count="exact").eq("date", today()).execute()
    return (a.count or 0), (g.count or 0), (f.count or 0)

# ══════════════════════════════════════════════════════════════════════════════
# EMAIL CONTROLS (CASE-INSENSITIVE FALLBACK ROUTINES)
# ══════════════════════════════════════════════════════════════════════════════

def find_speaker_email(speaker_name):
    """Fixed: Trims spaces and performs a clean case-insensitive check against rosters"""
    norm_name = speaker_name.strip().lower()
    r = get_sb().table("members").select("email,name").execute()
    for row in (r.data or []):
        if row.get("name", "").strip().lower() == norm_name:
            return row["email"]
    return None

def send_email(to_email, subject, body):
    import requests
    api_key = st.secrets["RESEND_API_KEY"]
    email_from = st.secrets["EMAIL_FROM"]
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"from": email_from, "to": to_email, "subject": subject, "text": body}
    )
    if response.status_code != 200: raise Exception(f"Resend error: {response.text}")

def already_emailed(speaker_name):
    r = get_sb().table("feedback_email_log").select("id").eq("date", today()).eq("speaker_name", speaker_name).execute()
    return len(r.data) > 0

def mark_emailed(speaker_name):
    get_sb().table("feedback_email_log").insert({"date": today(), "speaker_name": speaker_name, "sent_at": now_ts()}).execute()

def send_feedback_emails():
    speakers = [s for s in get_today_speakers() if s.get("role_category") == "speaker"]
    results = []
    for sp in speakers:
        name = sp["speaker_name"]
        if already_emailed(name):
            results.append((name, "Already sent — skipped."))
            continue
        fb_list = get_feedback_for_speaker(name)
        if not fb_list:
            results.append((name, "No feedback received — skipped."))
            continue
        email = find_speaker_email(name)
        if not email:
            results.append((name, "⚠️ no email found in Members table - skipped"))
            continue

        lines = ["Hi,", "", f"It was great to hear your speech at our Toastmasters Pune South East meeting! Feedback summary:", ""]
        for i, fb in enumerate(fb_list, start=1):
            scores = f"Content {fb.get('rating_content','-')}/3, Structure {fb.get('rating_structure','-')}/3, Interaction {fb.get('rating_interaction','-')}/3, Overall {fb.get('rating_overall','-')}/5"
            comment = (fb.get("feedback_text") or "").strip()
            lines.append(f"{i}. [{scores}] - Comments: {comment if comment else '(no comments)'}")
        lines.append("\nKeep it up!\n- Toastmasters Pune South East")
        body = "\n".join(lines)
        try:
            send_email(email, "Your Speech Feedback — TMCPSE", body)
            mark_emailed(name)
            results.append((name, f"✅ Sent successfully to {email}"))
        except Exception as e: results.append((name, f"❌ Failed: {e}"))
    return results

# ══════════════════════════════════════════════════════════════════════════════
# SESSION INITIALIZATION & STAGING
# ══════════════════════════════════════════════════════════════════════════════

for k, v in {"page": "login", "user_type": None, "user_id": None, "user_name": None, "already_attended": False, "excom_role": None, "guest_id": None, "member_id": None}.items():
    if k not in st.session_state: st.session_state[k] = v

is_admin = st.query_params.get("admin", "") == "1"
page = st.session_state.page

# ══════════════════════════════════════════════════════════════════════════════
# ROLE-BASED EXCOM ADMIN PANEL (HORIZONTAL NAVIGATION MENU)
# ══════════════════════════════════════════════════════════════════════════════
if is_admin:
    if not st.session_state.excom_role:
        st.markdown('<div class="tm-card" style="max-width:400px;margin:3rem auto;text-align:center;">🔐 <h3>ExCom Dashboard Entry</h3></div>', unsafe_allow_html=True)
        with st.form("excom_login_form"):
            chosen_role = st.selectbox("Select Your ExCom Role", EXCOM_ROLES)
            pwd = st.text_input("Security Access Password", type="password")
            if st.form_submit_button("Authenticate Access"):
                if pwd == st.secrets.get("ADMIN_PASSWORD", "toastmasters2024"):
                    st.session_state.excom_role = chosen_role
                    st.rerun()
                else: st.error("Incorrect password credentials.")
    else:
        current_role = st.session_state.excom_role
        st.markdown(f'<div class="tm-card" style="padding:1.2rem; margin-bottom:10px;"><h4 style="margin:0;color:#1a1a2e;">🎤 Toastmasters Pune South East</h4><span class="badge">{current_role} Workspace</span></div>', unsafe_allow_html=True)
        
        # ── Mobile-Safe Navigation Bar Alternative (No Sidebar Clutter) ──────
        if current_role == "SAA":
            current_tab = st.radio("Navigation Control Panel", ["Today's Roles", "Voting Controls", "Live Statistics", "⚙️ Meeting Generator", "Send Emails"], horizontal=True)
        elif current_role == "VP Membership":
            current_tab = st.radio("Navigation Control Panel", ["👤 Member Roster", "Guest Outreach & Data"], horizontal=True)
        elif current_role == "VP Education":
            current_tab = st.radio("Navigation Control Panel", ["📅 Agenda Booking Grid", "Learning Pathways Track"], horizontal=True)
        else:
            current_tab = "Home Dashboard"
            st.info(f"Welcome {current_role}. Custom admin workspace modules coming soon!")

        # ── SAA MODULE EXECUTION ZONE ────────────────────────────────────────
        if current_role == "SAA":
            if current_tab == "Today's Roles":
                speakers = get_today_speakers()
                st.write(f"**Meeting Execution Date:** {today()}")
                if speakers:
                    st.markdown("**Active Roleplayers Loaded:**")
                    for s in speakers:
                        st.markdown(f"- 🎙️ **{s['speaker_name']}** — *{s['role']}* {'(🚫 DQ)' if s['disqualified'] else ''}")
                
                st.markdown("---")
                st.subheader("Modify Live Setup & Add Table Topic Volunteers")
                if "num_rows" not in st.session_state: st.session_state.num_rows = max(len(speakers), 4)
                entries = []
                for i in range(st.session_state.num_rows):
                    ex = speakers[i] if i < len(speakers) else {}
                    c1, c2, c3 = st.columns([2, 2, 1])
                    with c1: nm = st.text_input(f"Name {i+1}", value=ex.get("speaker_name", ""), key=f"saa_n_{i}", label_visibility="collapsed")
                    with c2: 
                        idx = ALL_ROLES.index(ex.get("role", "Prepared Speeches")) if ex.get("role") in ALL_ROLES else 0
                        rl = st.selectbox(f"Role {i+1}", ALL_ROLES, index=idx, key=f"saa_r_{i}", label_visibility="collapsed")
                    with c3: dq = st.checkbox("DQ", value=ex.get("disqualified", False), key=f"saa_q_{i}")
                    if nm.strip(): entries.append({"name": nm.strip(), "role": rl, "disqualified": dq})
                
                if st.button("+ Append Entry Slot"):
                    st.session_state.num_rows += 1
                    st.rerun()
                if st.button("Commit Grid Configuration"):
                    set_today_speakers(entries)
                    st.success("Successfully synchronized configuration with live ballot engine.")
                    st.rerun()

            elif current_tab == "Voting Controls":
                v_open = get_voting_open()
                st.write(f"Ballot Collection State: **{'OPEN' if v_open else 'CLOSED'}**")
                if st.button("Open Voting System", disabled=v_open): set_voting_open(True); st.rerun()
                if st.button("Lock Ballots", disabled=not v_open): set_voting_open(False); st.rerun()
                
                st.markdown("---")
                st.subheader("Live Ballot Tally Results")
                tally = get_vote_tally()
                if not tally: st.info("No user submission criteria matched yet.")
                else:
                    for cat, data in tally.items():
                        st.markdown(f"**{cat}**")
                        for k, v in data.items(): st.write(f" {k}: {'█'*v} ({v} votes)")

            elif current_tab == "Live Statistics":
                mc, gc, fc = get_today_stats()
                st.metric("Checked-in Members", mc)
                st.metric("Total Guests Logged", gc)
                st.metric("Submitted Feedbacks", fc)

            elif current_tab == "⚙️ Meeting Generator":
                st.subheader("Dynamic Room Registration & Asset Suite")
                m_num = st.number_input("Chapter Meeting ID #", value=714, step=1)
                m_date = st.date_input("Scheduled Execution Date", value=date.today())
                if st.button("Deploy Dynamic Check-In Infrastructure"):
                    save_meeting_meta(m_num, m_date)
                    app_url = f"https://tmcpse-welcome.streamlit.app/?meeting_id={m_num}"
                    encoded_url = urllib.parse.quote_plus(app_url)
                    qr_api = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={encoded_url}"
                    st.success("Attendance database index matrix allocated.")
                    st.markdown(f"**Live Meeting Registration URL:** [{app_url}]({app_url})")
                    st.image(qr_api, caption=f"Scan to Check-In for Meeting {m_num}")

            elif current_tab == "Send Emails":
                if st.button("📧 Dispatch Aggregated Feedback Packages"):
                    with st.spinner("Processing automated templates..."): logs = send_feedback_emails()
                    for spk, state in logs: st.write(f"**{spk}**: {state}")

        # ── VP MEMBERSHIP MANAGEMENT HUB ─────────────────────────────────────
        elif current_role == "VP Membership":
            if current_tab == "👤 Member Roster":
                st.subheader("Enroll New Member Profile")
                with st.form("add_member_form"):
                    n = st.text_input("Full Name")
                    p = st.text_input("Mobile Contact Number")
                    e = st.text_input("Email Address Address")
                    bd = st.selectbox("Birth Day (Optional)", [None] + list(range(1, 32)))
                    bm = st.selectbox("Birth Month (Optional)", [None] + list(range(1, 13)))
                    act = st.checkbox("Mark as Active Status", value=True)
                    if st.form_submit_button("Provision Account"):
                        if n and p and e:
                            add_new_member(n, p, e, bd, bm, act)
                            st.success("Profile written to membership ledger databases.")
                            st.rerun()
                        else: st.error("Please fill required fields (Name, Phone, Email).")
                
                st.markdown("---")
                st.subheader("Current Operational Club Roster")
                roster = get_all_members()
                for mem in roster:
                    c1, c2 = st.columns([3, 1])
                    with c1: st.write(f"👤 **{mem['name']}** ({mem['email']}) — {'🟢 Active' if mem['is_active'] else '🔴 Inactive'}")
                    with c2:
                        target_state = not mem['is_active']
                        btn_label = "Deactivate" if mem['is_active'] else "Activate"
                        if st.button(btn_label, key=f"t_status_{mem['id']}"):
                            update_member_status(mem['id'], target_state)
                            st.rerun()

            elif current_tab == "Guest Outreach & Data":
                st.subheader("Historical Lead Retrospective Extraction")
                sel_d = st.date_input("Select Event Date", value=date.today())
                guests = get_guests_by_date(sel_d)
                if guests:
                    st.write(guests)
                    import pandas as pd
                    st.download_button("Download Guest Matrix CSV", data=pd.DataFrame(guests).to_csv(index=False), file_name=f"Guests_{sel_d}.csv")
                else: st.info("No alternative guest matrices found matching selected timestamps.")

        # ── VP EDUCATION CONTROL MODULE ──────────────────────────────────────
        elif current_role == "VP Education":
            if current_tab == "📅 Agenda Booking Grid":
                st.subheader("Forward Schedule Projections Grid")
                f_date = st.date_input("Target Saturday Date", value=date.today())
                agenda_fields = ["TMOD", "General Evaluator", "Timer", "Ah Counter", "Grammarian", "Table Topic Master", "Speaker 1", "Speaker 2", "Speaker 3", "Speaker 4", "Evaluator 1", "Evaluator 2", "Evaluator 3", "Evaluator 4"]
                
                saved_sched = get_meeting_schedule(f_date) or {}
                roles_json = saved_sched.get("roles_json", {})
                
                with st.form("agenda_booking_form"):
                    current_payload = {}
                    for field in agenda_fields:
                        current_payload[field] = st.text_input(field, value=roles_json.get(field, ""))
                    if st.form_submit_button("Commit Scheduled Matrix Assignments"):
                        save_meeting_schedule(f_date, current_payload)
                        st.success("Master projection sheet configuration cataloged.")
            
            elif current_tab == "Learning Pathways Track":
                st.info("Pathways curriculum tracking sub-matrices staging pipeline active. Integration operational shortly.")

        if st.button("Terminate Administrative Session"):
            st.session_state.excom_role = None
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# MEMBER & GUEST INTERFACE PIPELINES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "login":
    st.markdown('<div class="tm-card"><div style="text-align:center;margin-bottom:2rem"><div style="font-size:2.8rem;">🎤</div><div class="tm-club-name">Toastmasters<br>Pune South East</div><hr class="tm-divider"><div class="tm-tagline">Where Leaders Are Made</div></div></div>', unsafe_allow_html=True)
    st.markdown('<strong>Check-In Verification Portal</strong>', unsafe_allow_html=True)
    with st.form("checkin_form"):
        ident = st.text_input("Enter Email or Registered Phone Number")
        if st.form_submit_button("Verify & Check-In"):
            if not ident.strip(): st.error("Input sequence must contain identifiers.")
            else:
                member = find_member(ident.strip())
                if member:
                    if not member.get("is_active", True):
                        st.error("Account membership inactive. Please contact the VP Membership regarding administrative dues status.")
                        st.stop()
                    already = already_attended(member["id"])
                    if not already: mark_attendance(member)
                    st.session_state.update({"page": "dashboard", "user_type": "member", "user_id": str(member["id"]), "user_name": member["name"], "already_attended": already, "member_id": member["id"]})
                    if member.get("birthday_day") is None: st.session_state.page = "birthday_prompt"
                    st.rerun()
                else:
                    st.session_state.page = "guest_form"
                    st.rerun()

elif page == "birthday_prompt":
    st.markdown('<div class="tm-card"><div style="text-align:center;">🎂 <h4>Help Us Celebrate You!</h4></div></div>', unsafe_allow_html=True)
    with st.form("b_form"):
        d = st.selectbox("Day", list(range(1, 32)))
        m = st.selectbox("Month", ["January","February","March","April","May","June","July","August","September","October","November","December"])
        if st.form_submit_button("Save Details"):
            m_idx = ["January","February","March","April","May","June","July","August","September","October","November","December"].index(m) + 1
            update_member_birthday(st.session_state.member_id, d, m_idx)
            st.session_state.page = "dashboard"
            st.rerun()

elif page == "guest_form":
    st.markdown('<div class="tm-card"><div style="text-align:center;">🎉 <h4>Welcome, Guest!</h4></div></div>', unsafe_allow_html=True)
    with st.form("g_form"):
        nm = st.text_input("Full Name *")
        ph = st.text_input("Phone Number *")
        src = st.selectbox("How did you find us? *", ["Google","Word of Mouth","LinkedIn","Instagram","Other"])
        if st.form_submit_button("Register Attendance"):
            if nm and ph:
                gid = save_guest(nm, ph, src)
                st.session_state.update({"page": "dashboard", "user_type": "guest", "user_id": f"guest_{ph}", "user_name": nm, "guest_id": gid})
                st.rerun()
            else: st.error("Please complete all fields.")

elif page == "dashboard":
    st.write(f"### Welcome {st.session_state.user_name}!")
    
    if st.session_state.user_type == "guest":
        st.markdown(f'<div class="connect-card"><h5>🔗 Stay Connected Community Links</h5><a class="connect-link" href="{SOCIAL_LINKS["whatsapp"]}">Join WhatsApp Hub</a><a class="connect-link" href="{SOCIAL_LINKS["instagram"]}">Follow Instagram Portfolio</a></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="connect-card"><h5>📣 Support Club PR Engagements</h5><a class="connect-link" href="{SOCIAL_LINKS["linkedin"]}">Share via LinkedIn Network</a></div>', unsafe_allow_html=True)

    # ── Feedback Interface Core ──────────────────────────────────────────────
    st.markdown('<div class="section-title">🗣️ Constructive Prepared Speech Appraisals</div>', unsafe_allow_html=True)
    speakers = get_today_speakers()
    prep = [s for s in speakers if s.get("role_category") == "speaker" and not s.get("disqualified")]
    
    if not prep: st.info("No active speech evaluation parameters set for this timeframe.")
    else:
        given = get_feedback_by_user(st.session_state.user_id)
        for s in prep:
            name = s["speaker_name"]
            if name in given: st.success(f"✅ Feedback package delivered for {name}.")
            else:
                with st.expander(f"Submit Assessment for {name}"):
                    c = st.slider("Content Analysis", 1, 3, 3, key=f"c_{name}")
                    st = st.slider("Structural Evaluation", 1, 3, 3, key=f"st_{name}")
                    txt = st.text_area("Observations & Commendations", key=f"t_{name}")
                    if st.button("Transmit Feedback", key=f"b_{name}"):
                        save_structured_feedback(st.session_state.user_id, st.session_state.user_name, name, s["role"], c, st, 3, 3, 5, txt)
                        st.success("Appraisal compiled successfully.")
                        st.rerun()

    # ── Voting Staging Container ─────────────────────────────────────────────
    st.markdown('<div class="section-title">🏆 Cast Ballot Registrations</div>', unsafe_allow_html=True)
    if not get_voting_open():
        st.markdown('<div class="locked-box">🔒 <b>Balloting currently locked.</b><br>The SAA will open access towards the closing segment of the session. Check back soon!</div>', unsafe_allow_html=True)
        if st.button("🔄 Refresh Status Key"): st.rerun()
    else:
        voted = get_votes_by_user(st.session_state.user_id)
        eligible = [s for s in speakers if not s.get("disqualified")]
        
        with st.form("ballot_sub_form"):
            selections = {}
            for cat, key in VOTING_CATEGORIES.items():
                options = [s["speaker_name"] for s in eligible if s.get("role_category") == key]
                if options and cat not in voted:
                    selections[cat] = st.selectbox(f"🏅 {cat}", ["-- Select Nominee --"] + options)
            if st.form_submit_button("Finalize Ballot Entry"):
                for cat, choice in selections.items():
                    if choice != "-- Select Nominee --": save_vote(st.session_state.user_id, st.session_state.user_name, cat, choice)
                st.success("Ballot processing finalized.")
                st.rerun()

    # ── Rating Suite ─────────────────────────────────────────────────────────
    if get_voting_open() and not has_rated_meeting(st.session_state.user_id):
        with st.form("m_rate_f"):
            r = st.radio("Rate overall meeting experience (1-5)", [1,2,3,4,5], horizontal=True)
            f = st.text_area("General observations")
            if st.form_submit_button("Log Evaluation Metrics"):
                save_meeting_rating(st.session_state.user_id, st.session_state.user_name, st.session_state.user_type, r, f)
                if st.session_state.user_type == "guest": st.session_state.page = "guest_followup"
                else: st.session_state.page = "thank_you"
                st.rerun()

    if st.button("Sign Out of Session Dashboard"):
        for k in ["page","user_type","user_id","user_name","member_id","guest_id"]: st.session_state.pop(k, None)
        st.session_state.page = "login"
        st.rerun()

elif page == "guest_followup":
    with st.form("f_g"):
        p = st.radio("Are you planning to join our chapter community?", ["Yes", "No", "Thinking about it"])
        v = st.radio("Are you comfortable if our VP Membership contacts you?", ["Yes, absolutely", "I'll reach out myself"])
        if st.form_submit_button("Complete Registration"):
            update_guest_lead(st.session_state.guest_id, p, "Soon", v)
            st.session_state.page = "thank_you"
            st.rerun()

elif page == "thank_you":
    st.markdown('<div class="tm-card" style="text-align:center;">🙏 <h3>Thank You!</h3><p>We look forward to welcoming you to our next Chapter gathering.</p></div>', unsafe_allow_html=True)
    if st.button("Return to Check-In"):
        st.session_state.page = "login"
        st.rerun()
