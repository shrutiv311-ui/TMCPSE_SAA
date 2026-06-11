import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def render_dashboard():
    import app as A

    user_name = st.session_state.user_name
    user_type = st.session_state.user_type
    user_id   = st.session_state.user_id

    # ── Welcome banner ─────────────────────────────────────────────────────
    already = st.session_state.get("already_attended", False)
    if user_type == "member":
        msg = (f"👋 Welcome back, <strong>{user_name}</strong>! Attendance already recorded."
               if already else
               f"✅ Attendance marked! Welcome, <strong>{user_name}</strong>!")
        border = "#2d7a2d"; bg = "#f0f7f0"; fg = "#1a4a1a"
    else:
        msg = f"🎉 Welcome, <strong>{user_name}</strong>! Glad you joined us today as a guest."
        border = "#722F37"; bg = "#fff7f5"; fg = "#4a1a1a"

    st.markdown(f"""
    <div class="tm-card" style="padding:1.2rem 1.8rem;">
      <div style="display:flex;align-items:center;gap:1rem;">
        <div style="font-size:2rem">🎤</div>
        <div>
          <div class="tm-club-name" style="font-size:1.1rem">Toastmasters Pune South East</div>
          <div class="tm-tagline" style="font-size:0.7rem">{A.today()}</div>
        </div>
      </div>
    </div>
    <div style="background:{bg};border-left:4px solid {border};
         padding:0.9rem 1.2rem;border-radius:3px;margin-bottom:1.5rem;color:{fg};">
      {msg}
    </div>
    """, unsafe_allow_html=True)

    # ── Load data ───────────────────────────────────────────────────────────
    try:
        speakers     = A.get_today_speakers()
        voting_open  = A.get_voting_open()
        gave_feedback = A.get_feedback_by_user(user_id)
        already_voted = A.get_votes_by_user(user_id)
    except Exception as e:
        st.error(f"Could not load meeting data: {e}")
        return

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 1 — FEEDBACK
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🗣️ Speaker Feedback</div>', unsafe_allow_html=True)

    if not speakers:
        st.info("No speakers have been added for today's meeting yet. Check back soon!")
    else:
        for sp in speakers:
            sp_name = sp["speaker_name"]
            sp_role = sp["role"]
            with st.expander(f"**{sp_name}** — {sp_role}", expanded=True):
                if sp_name in gave_feedback:
                    st.success("✅ Feedback submitted for this speaker.")
                else:
                    fb = st.text_area(
                        f"Feedback for {sp_name}",
                        key=f"fb_{sp_name}",
                        placeholder="What did they do well? What could be improved?",
                        height=100, label_visibility="collapsed",
                    )
                    if st.button(f"Submit Feedback for {sp_name}", key=f"btn_{sp_name}"):
                        if not fb.strip():
                            st.warning("Please write something before submitting.")
                        else:
                            try:
                                A.save_feedback(user_id, user_name, sp_name, sp_role, fb.strip())
                                st.success("✅ Feedback submitted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Could not save: {e}")

    st.markdown("<br>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════════════
    # SECTION 2 — VOTING
    # ══════════════════════════════════════════════════════════════════════
    st.markdown('<div class="section-title">🏆 Vote for Best Roles</div>', unsafe_allow_html=True)

    if not voting_open:
        st.markdown("""
        <div class="locked-box">
          <div style="font-size:2.5rem">🔒</div>
          <p style="font-size:1.1rem;font-weight:600;margin:0.5rem 0;">Voting is not open yet</p>
          <p style="color:#888;margin:0">The SAA will unlock voting at the end of the meeting.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        all_names   = [s["speaker_name"] for s in speakers]
        by_role     = lambda kw: [s["speaker_name"] for s in speakers if kw.lower() in s["role"].lower()]

        categories = {
            "Best Speaker":              by_role("speaker") or all_names,
            "Best Evaluator":            by_role("eval")    or all_names,
            "Best Table Topics Speaker": by_role("table")   or all_names,
            "Best Role Player":          by_role("role")    or all_names,
        }

        remaining = {c: n for c, n in categories.items() if c not in already_voted}

        if not remaining:
            st.success("🎉 You've cast all your votes! Thank you for participating.")
        else:
            st.markdown("*Cast your votes below — one per category.*")
            with st.form("voting_form"):
                selections = {}
                for cat, nominees in remaining.items():
                    selections[cat] = st.selectbox(
                        f"🏅 {cat}", ["-- Select --"] + nominees, key=f"v_{cat}"
                    )
                if st.form_submit_button("Submit Votes →", use_container_width=True):
                    missing = [c for c, s in selections.items() if s == "-- Select --"]
                    if missing:
                        st.warning(f"Please select for: {', '.join(missing)}")
                    else:
                        try:
                            for cat, sel in selections.items():
                                A.save_vote(user_id, user_name, cat, sel)
                            st.success("✅ Votes submitted! Thank you!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Could not save votes: {e}")

    # ── Sign out ────────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("← Sign Out"):
        for k in ["logged_in","user_type","user_id","user_name",
                  "already_attended","show_guest_form"]:
            st.session_state.pop(k, None)
        st.rerun()
