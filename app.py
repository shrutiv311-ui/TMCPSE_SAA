import streamlit as st
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(
    page_title="Toastmasters Pune South East",
    page_icon="🎤",
    layout="centered",
    initial_sidebar_state="collapsed",
)

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
</style>
""", unsafe_allow_html=True)

# ── Supabase ──────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_sb() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

def today():
    return datetime.now().strftime("%Y-%m-%d")

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def find_member(identifier):
    norm = identifier.lower().strip().replace(" ", "").replace("-", "")
    r = get_sb().table("members").select("*").ilike("email", norm).execute()
    if r.data:
        return r.data[0]
    r = get_sb().table("members").select("*").eq("phone", norm).execute()
    return r.data[0] if r.data else None

def already_attended(member_id):
    r = get_sb().table("attendance").select("id").eq("member_id", member_id).eq("date", today()).execute()
    return len(r.data) > 0

def mark_attendance(member):
    get_sb().table("attendance").insert({
        "date": today(), "timestamp": now_ts(),
        "member_id": member["id"], "name": member["name"], "email": member["email"],
    }).execute()

def save_guest(name, phone, source):
    get_sb().table("guests").insert({
        "date": today(), "timestamp": now_ts(),
        "name": name, "phone": phone, "how_heard": source,
    }).execute()

def get_today_speakers():
    r = get_sb().table("today_speakers").select("*").eq("date", today()).execute()
    return r.data or []

def set_today_speakers(speakers_list):
    get_sb().table("today_speakers").delete().eq("date", today()).execute()
    rows = [{"date": today(), "speaker_name": s["name"], "role": s["role"]} for s in speakers_list]
    if rows:
        get_sb().table("today_speakers").insert(rows).execute()

def get_feedback_by_user(user_id):
    r = get_sb().table("feedback").select("speaker_name").eq("user_id", user_id).eq("date", today()).execute()
    return {row["speaker_name"] for row in (r.data or [])}

def save_feedback(user_id, user_name, speaker_name, speaker_role, text):
    get_sb().table("feedback").insert({
        "date": today(), "timestamp": now_ts(), "user_id": user_id,
        "user_name": user_name, "speaker_name": speaker_name,
        "speaker_role": speaker_role, "feedback_text": text,
    }).execute()

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

def get_today_stats():
    sb = get_sb()
    a = sb.table("attendance").select("id", count="exact").eq("date", today()).execute()
    g = sb.table("guests").select("id", count="exact").eq("date", today()).execute()
    f = sb.table("feedback").select("id", count="exact").eq("date", today()).execute()
    return (a.count or 0), (g.count or 0), (f.count or 0)

# ── Session defaults ──────────────────────────────────────────────────────────
for k, v in {"page": "login", "user_type": None, "user_id": None,
              "user_name": None, "already_attended": False, "admin_mode": False}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Router ────────────────────────────────────────────────────────────────────
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

        tab1, tab2, tab3 = st.tabs(["Today's Roles", "Voting Control", "Live Stats"])

        with tab1:
            st.markdown(f"**Date:** {today()}")
            ROLES = ["Prepared Speaker","Table Topics Speaker","Evaluator",
                     "General Evaluator","Role Player","Toastmaster of the Day",
                     "Timer","Grammarian","Ah-Counter","Word of the Day","Other"]
            if speakers:
                st.markdown("**Currently saved:**")
                for sp in speakers:
                    st.markdown(f"🎙️ **{sp['speaker_name']}** — *{sp['role']}*")
                st.markdown("---")
            st.markdown("#### Add / Update Today's Speakers")
            st.caption("Fill all names then click Save — replaces today's list.")
            if "num_rows" not in st.session_state:
                st.session_state.num_rows = max(len(speakers), 3)
            entries = []
            for i in range(st.session_state.num_rows):
                ex_name = speakers[i]["speaker_name"] if i < len(speakers) else ""
                ex_role = speakers[i]["role"]          if i < len(speakers) else "Prepared Speaker"
                c1, c2 = st.columns([2, 1])
                with c1:
                    nm = st.text_input(f"Name {i+1}", value=ex_name,
                        key=f"sp_n_{i}", placeholder=f"Name {i+1}", label_visibility="collapsed")
                with c2:
                    ri = ROLES.index(ex_role) if ex_role in ROLES else 0
                    rl = st.selectbox(f"Role {i+1}", ROLES, index=ri,
                        key=f"sp_r_{i}", label_visibility="collapsed")
                if nm.strip():
                    entries.append({"name": nm.strip(), "role": rl})
            ca, cb = st.columns(2)
            with ca:
                if st.button("+ Add Row", use_container_width=True, key="add_row_btn"):
                    st.session_state.num_rows = min(st.session_state.num_rows + 1, 15)
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
            st.markdown("#### Live Vote Tally")
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

        with tab3:
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
                gst = get_sb().table("guests").select("timestamp,name,phone,how_heard").eq("date", today()).execute()
                st.markdown("**Guests**")
                st.dataframe(pd.DataFrame(gst.data or []), use_container_width=True)
            except Exception as e:
                st.warning(str(e))

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
                    "already_attended": already,
                })
                st.rerun()
            else:
                st.session_state.page = "guest_form"
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
            save_guest(name.strip(), phone.strip(), source)
            st.session_state.update({
                "page": "dashboard", "user_type": "guest",
                "user_id": f"guest_{phone.strip()}", "user_name": name.strip(),
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

    try:
        speakers      = get_today_speakers()
        voting_open   = get_voting_open()
        gave_feedback = get_feedback_by_user(user_id)
        already_voted = get_votes_by_user(user_id)
    except Exception as e:
        st.error(f"Could not load meeting data: {e}")
        st.stop()

    # ── Feedback ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🗣️ Speaker Feedback</div>', unsafe_allow_html=True)

    if not speakers:
        st.info("No speakers added for today's meeting yet.")
    else:
        for sp in speakers:
            sp_name = sp["speaker_name"]
            sp_role = sp["role"]
            with st.expander(f"**{sp_name}** — {sp_role}", expanded=True):
                if sp_name in gave_feedback:
                    st.success("✅ You already submitted feedback for this speaker.")
                else:
                    fb = st.text_area("Feedback", key=f"fb_{sp_name}",
                        placeholder="What did they do well? What could be improved?",
                        height=100, label_visibility="collapsed")
                    if st.button(f"Submit Feedback for {sp_name}", key=f"btn_{sp_name}"):
                        if not fb.strip():
                            st.warning("Please write something first.")
                        else:
                            save_feedback(user_id, user_name, sp_name, sp_role, fb.strip())
                            st.success("✅ Feedback submitted!")
                            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Voting ────────────────────────────────────────────────────────────
    st.markdown('<div class="section-title">🏆 Vote for Best Roles</div>', unsafe_allow_html=True)

    if not voting_open:
        st.markdown("""<div class="locked-box">
          <div style="font-size:2.5rem">🔒</div>
          <p style="font-size:1.1rem;font-weight:600;margin:0.5rem 0;">Voting is not open yet</p>
          <p style="color:#888;margin:0">The SAA will unlock voting at the end of the meeting.</p>
        </div>""", unsafe_allow_html=True)
    else:
        all_names = [s["speaker_name"] for s in speakers]
        by_role   = lambda kw: [s["speaker_name"] for s in speakers
                                if kw.lower() in s["role"].lower()]
        categories = {
            "Best Speaker":              by_role("speaker") or all_names,
            "Best Evaluator":            by_role("eval")    or all_names,
            "Best Table Topics Speaker": by_role("table")   or all_names,
            "Best Role Player":          by_role("role")    or all_names,
        }
        remaining = {c: n for c, n in categories.items() if c not in already_voted}

        if not remaining:
            st.success("🎉 You have cast all your votes! Thank you.")
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

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("Sign Out", key="signout_btn"):
        for k in ["page","user_type","user_id","user_name","already_attended"]:
            st.session_state.pop(k, None)
        st.session_state.page = "login"
        st.rerun()
