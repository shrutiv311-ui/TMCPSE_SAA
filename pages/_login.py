import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def render_login():
    st.markdown("""
    <div class="tm-card">
      <div class="tm-header">
        <div style="font-size:2.8rem; margin-bottom:0.3rem">🎤</div>
        <div class="tm-club-name">Toastmasters<br>Pune South East</div>
        <hr class="tm-divider">
        <div class="tm-tagline">Where Leaders Are Made</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get("show_guest_form"):
        _render_guest_form()
        return

    st.markdown('<div class="tm-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Check In</div>', unsafe_allow_html=True)
    st.markdown("**Enter your email or phone number to check in for today's meeting.**")

    identifier = st.text_input(
        "Email or Phone",
        placeholder="e.g. john@email.com  or  9876543210",
        label_visibility="collapsed",
        key="login_identifier",
    )
    submit = st.button("Check In ->", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        if not identifier.strip():
            st.error("Please enter your email or phone number.")
            return
        _process_checkin(identifier.strip())


def _process_checkin(identifier: str):
    import app as A

    member = A.find_member(identifier)

    if member:
        already = A.already_attended(member["id"])
        if not already:
            A.mark_attendance(member)
        st.session_state.update({
            "logged_in": True, "user_type": "member",
            "user_id": str(member["id"]), "user_name": member["name"],
            "already_attended": already,
        })
        st.rerun()
    else:
        st.session_state["show_guest_form"] = True
        st.rerun()


def _render_guest_form():
    import app as A

    st.markdown('<div class="tm-card">', unsafe_allow_html=True)
    st.markdown('<div class="badge">Welcome, Guest!</div>', unsafe_allow_html=True)
    st.markdown("Looks like you're new here -- great to have you! Please tell us a little about yourself.")

    with st.form("guest_form"):
        name  = st.text_input("Your Full Name *", placeholder="Priya Sharma", key="guest_name")
        phone = st.text_input("Phone Number *",   placeholder="9876543210",   key="guest_phone")
        source = st.selectbox("How did you hear about us? *", [
            "-- Select --", "Google", "Friend / Word of Mouth", "LinkedIn",
            "Instagram", "Facebook", "WhatsApp Group", "Event Listing", "Other",
        ], key="guest_source")
        submitted = st.form_submit_button("Join Today's Meeting ->", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if submitted:
        errors = []
        if not name.strip():   errors.append("Name is required.")
        if not phone.strip():  errors.append("Phone number is required.")
        if source == "-- Select --": errors.append("Please select how you heard about us.")
        for e in errors:
            st.error(e)
        if errors:
            return

        A.save_guest(name.strip(), phone.strip(), source)
        st.session_state.update({
            "logged_in": True, "user_type": "guest",
            "user_id": f"guest_{phone.strip()}", "user_name": name.strip(),
            "show_guest_form": False,
        })
        st.rerun()