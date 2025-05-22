"""
Modal dialog components for SponsorMatch application.
"""
import streamlit as st


def show_login_modal():
    """Show a login modal dialog."""
    # Use Streamlit's experimental modal feature if available
    use_experimental = hasattr(st, "modal")

    if use_experimental:
        with st.modal("Logga in", key="login_modal"):
            _render_login_form()
    else:
        # Fallback to expander
        with st.expander("Logga in", expanded=True):
            _render_login_form()


def show_sponsor_modal(sponsor):
    """
    Show a sponsor details modal dialog.

    Args:
        sponsor: Dictionary with sponsor information
    """
    use_experimental = hasattr(st, "modal")
    title = sponsor.get('name', 'Sponsor')

    if use_experimental:
        with st.modal(title, key="sponsor_modal"):
            _render_sponsor_details(sponsor)
    else:
        # Fallback to expander
        with st.expander(title, expanded=True):
            _render_sponsor_details(sponsor)


def show_confirmation_modal(title, message, confirm_text="Bekräfta", cancel_text="Avbryt"):
    """
    Show a confirmation dialog and return the result.

    Args:
        title: Modal title
        message: Message to display
        confirm_text: Text for confirm button
        cancel_text: Text for cancel button

    Returns:
        True if confirmed, False otherwise
    """
    use_experimental = hasattr(st, "modal")

    if use_experimental:
        with st.modal(title, key="confirm_modal"):
            st.write(message)
            col1, col2 = st.columns(2)
            with col1:
                if st.button(cancel_text, key="modal_cancel"):
                    return False
            with col2:
                if st.button(confirm_text, key="modal_confirm", type="primary"):
                    return True
    else:
        # Fallback to regular UI
        st.write(message)
        col1, col2 = st.columns(2)
        with col1:
            if st.button(cancel_text, key="confirm_cancel"):
                return False
        with col2:
            if st.button(confirm_text, key="confirm_confirm", type="primary"):
                return True

    return False


def _render_login_form():
    """Render login form content."""
    st.text_input("E-post", key="login_email")
    st.text_input("Lösenord", type="password", key="login_password")

    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Kom ihåg mig", key="remember_me")
    with col2:
        st.markdown(
            "<div style='text-align:right;'><a href='#'>Glömt lösenord?</a></div>",
            unsafe_allow_html=True
        )

    if st.button("Logga in", type="primary", key="do_login"):
        st.success("Inloggning lyckades!")
        return True

    st.markdown("---")
    st.markdown("Har du inget konto? [Registrera dig här](#)")

    return False


def _render_sponsor_details(sponsor):
    """Render sponsor details content."""
    # Extract sponsor details with defaults
    name = sponsor.get('name', 'Unknown Sponsor')
    description = sponsor.get('description', 'No description available.')
    industry = sponsor.get('industry', 'N/A')
    revenue = sponsor.get('revenue_ksek', 'N/A')
    employees = sponsor.get('employees', 'N/A')
    website = sponsor.get('website', '#')
    email = sponsor.get('contact', {}).get('email', 'kontakt@företag.se')
    phone = sponsor.get('contact', {}).get('phone', 'N/A')

    # Display sponsor information
    st.subheader(name)
    st.write(description)

    # Company details
    st.markdown("### Företagsinformation")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Bransch", industry)
    with col2:
        st.metric("Omsättning", f"{revenue} tkr")
    with col3:
        st.metric("Anställda", employees)

    # Contact information
    st.markdown("### Kontaktuppgifter")
    st.write(f"📧 E-post: {email}")
    st.write(f"📞 Telefon: {phone}")
    if website != '#':
        st.write(f"🌐 [Besök webbplats]({website})")

    # Contact form
    st.markdown("### Skicka meddelande")
    with st.form("contact_form"):
        st.text_area("Meddelande", placeholder="Skriv ditt meddelande här...")
        submitted = st.form_submit_button("Skicka")

        if submitted:
            st.success("Meddelande skickat!")
