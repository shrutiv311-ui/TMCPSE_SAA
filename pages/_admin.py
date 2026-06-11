import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def render_admin():
    import app as A

    try:
        ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
    except Exception:
        ADMIN_PASSWORD = "toastmasters2024"

    # ── Auth gate ───────────────────────────────────────────────────────────
    if not st.session_state.get("admin_mode"):
        st.markdown("""
        <div class="tm-card" style="max-width:400px;margin:3rem auto;">
          <div class="tm-header">
            <div style="font-size:2rem">🔐</div>
            <div class="tm-club-name" style="font-size:1.2rem">Admin Panel</div>
            <div class="tm-tagline">SAA Access Only</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        with st.form("admin_login"):
            pwd = st.text_input("Password", type="password", placeholder="Enter admin password")
            if st.form_submit_button("Enter Admin Panel →", use_container_width=True):
                if pwd == ADMIN_PASSWORD:
                    st.session_state.admin_mode = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
        return

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="tm-card" style="padding:1.2rem 1.8rem;margin-bottom:1rem;">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div class="tm-club-name" style="font-size:1rem">🎤 Toastmasters Pune South East</div>
          <div class="tm-tagline" style="font-size:0.65rem">Sergeant-at-Arms Panel</div>
        </div>
        <div class="badge">Admin</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    try:
        speakers    = A.get_today_speakers()
        voting_open = A.get_voting_open()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    tab1, tab2, tab3 = st.tabs(["📋 Today's Roles", "🗳️ Voting Control", "📊 Live Stats"])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — SPEAKERS
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        st.markdown(f"**Date:** {A.today()}")

        ROLES = [
            "Prepared Speaker", "Table Topics Speaker", "Evaluator",
            "General Evaluator", "Role Player", "Toastmaster of the Day",
            "Timer", "Grammarian", "Ah-Counter", "Word of the Day", "Other",
        ]

        if speakers:
            st.markdown("**Currently saved:**")
            for sp in speakers:
                st.markdown(f"🎙️ **{sp['speaker_name']}** — *{sp['role']}*")
            st.markdown("---")

        st.markdown("#### Add / Update Today's Speakers & Role Players")
        st.caption("Fill in all names and click Save — this replaces today's list.")

        if "num_rows" not in st.session_state:
            st.session_state.num_rows = max(len(speakers), 3)

        entries = []
        for i in range(st.session_state.num_rows):
            ex_name = speakers[i]["speaker_name"] if i < len(speakers) else ""
            ex_role = speakers[i]["role"]          if i < len(speakers) else "Prepared Speaker"
            c1, c2 = st.columns([2, 1])
            with c1:
                name = st.text_input(f"Name {i+1}", value=ex_name,
                    key=f"sp_n_{i}", placeholder=f"Speaker {i+1}",
                    label_visibility="collapsed")
            with c2:
                role_idx = ROLES.index(ex_role) if ex_role in ROLES else 0
                role = st.selectbox(f"Role {i+1}", ROLES, index=role_idx,
                    key=f"sp_r_{i}", label_visibility="collapsed")
            if name.strip():
                entries.append({"name": name.strip(), "role": role})

        ca, cb = st.columns(2)
        with ca:
            if st.button("＋ Add Row", use_container_width=True):
                st.session_state.num_rows = min(st.session_state.num_rows + 1, 15)
                st.rerun()
        with cb:
            if st.button("💾 Save Speakers", use_container_width=True):
                if not entries:
                    st.warning("Enter at least one name.")
                else:
                    try:
                        A.set_today_speakers(entries)
                        st.success(f"✅ Saved {len(entries)} entries.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — VOTING CONTROL
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        st.markdown("#### Master Voting Switch")
        color  = "#2d7a2d" if voting_open else "#722F37"
        label  = "🟢 VOTING IS OPEN" if voting_open else "🔴 VOTING IS CLOSED"
        st.markdown(f"""
        <div style="background:{color}22;border:2px solid {color};
             border-radius:4px;padding:1rem;text-align:center;margin:1rem 0;">
          <strong style="color:{color};font-size:1.1rem">{label}</strong>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("🔓 Open Voting",  use_container_width=True, disabled=voting_open):
                A.set_voting_open(True);  st.success("Voting is now OPEN!"); st.rerun()
        with c2:
            if st.button("🔒 Close Voting", use_container_width=True, disabled=not voting_open):
                A.set_voting_open(False); st.info("Voting closed.");          st.rerun()

        st.markdown("---")
        st.markdown("#### Live Vote Tally")
        try:
            tally = A.get_vote_tally()
            if not tally:
                st.info("No votes yet.")
            else:
                for cat, counts in tally.items():
                    st.markdown(f"**{cat}**")
                    for nom, cnt in sorted(counts.items(), key=lambda x: -x[1]):
                        bar = "█" * cnt
                        st.markdown(f"&nbsp;&nbsp;{nom}: {bar} ({cnt})")
        except Exception as e:
            st.warning(f"Could not load tally: {e}")

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — LIVE STATS
    # ══════════════════════════════════════════════════════════════════════
    with tab3:
        try:
            m_cnt, g_cnt, fb_cnt = A.get_today_stats()
            c1, c2, c3 = st.columns(3)
            c1.metric("👥 Members In",     m_cnt)
            c2.metric("🌟 Guests Today",   g_cnt)
            c3.metric("💬 Feedback Given", fb_cnt)
        except Exception as e:
            st.warning(f"Stats error: {e}")

        st.markdown("---")
        st.markdown("**Attendance**")
        try:
            import pandas as pd
            att = A.get_attendance_list()
            st.dataframe(pd.DataFrame(att), use_container_width=True) if att else st.info("No check-ins yet.")
        except Exception as e:
            st.warning(str(e))

        st.markdown("**Guests**")
        try:
            import pandas as pd
            guests = A.get_guest_list()
            st.dataframe(pd.DataFrame(guests), use_container_width=True) if guests else st.info("No guests yet.")
        except Exception as e:
            st.warning(str(e))

    st.markdown("<br>")
    if st.button("← Exit Admin Panel"):
        st.session_state.admin_mode = False
        st.rerun()
