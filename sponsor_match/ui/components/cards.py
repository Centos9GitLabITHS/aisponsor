# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

"""
Card UI components for SponsorMatch application.
"""
import streamlit as st


def render_info_card(icon, title, text):
    """
    Render an information card with icon, title and text.

    Args:
        icon: Emoji or icon character
        title: Card title
        text: Card description text
    """
    st.markdown(
        f"""
        <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;
                    padding:1.5rem;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,0.05);">
          <div style="font-size:2rem;color:#2563eb;margin-bottom:0.5rem;">{icon}</div>
          <div style="font-size:1.125rem;font-weight:600;color:#1e40af;margin-bottom:0.5rem;">{title}</div>
          <div style="font-size:0.875rem;color:#4b5563;">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sponsor_card(sponsor):
    """
    Render a sponsor card with company information and contact button.

    Args:
        sponsor: Dictionary containing sponsor information
    """
    # Extract sponsor details, with defaults for missing values
    name = sponsor.get('name', 'Unknown Sponsor')
    description = sponsor.get('description', 'No description available.')
    score = sponsor.get('score', 0)
    revenue = sponsor.get('revenue_ksek', 'N/A')
    employees = sponsor.get('employees', 'N/A')
    industry = sponsor.get('industry', 'N/A')

    # Format score as percentage
    score_display = f"{score:.0%}" if isinstance(score, (int, float)) else "N/A"

    # Create formatted card with all information
    st.markdown(
        f"""
        <div style="background:white;padding:1.5rem;border-radius:8px;
                    box-shadow:0 1px 3px rgba(0,0,0,0.1);margin-bottom:1rem;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;">
            <div style="font-size:1.125rem;font-weight:700;color:#1e40af;">{name}</div>
            <div style="background:#dbeafe;color:#1e40af;padding:0.25rem 0.5rem;
                        border-radius:9999px;font-size:0.75rem;font-weight:600;">
              {score_display} match
            </div>
          </div>
          <div style="font-size:0.875rem;color:#4b5563;margin-bottom:0.75rem;">{description}</div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:0.5rem;
                      font-size:0.75rem;color:#6b7280;margin-bottom:1rem;">
            <div>
              <div style="font-weight:600;">Omsättning</div>
              <div>{revenue} tkr</div>
            </div>
            <div>
              <div style="font-weight:600;">Anställda</div>
              <div>{employees}</div>
            </div>
            <div>
              <div style="font-weight:600;">Bransch</div>
              <div>{industry}</div>
            </div>
          </div>
          <div style="display:flex;gap:0.5rem;">
            <button style="flex:1;background:#2563eb;color:white;padding:0.5rem 1rem;
                           border:none;border-radius:4px;font-weight:500;cursor:pointer;">
              📧 Kontakta
            </button>
            <button style="flex:1;background:#f3f4f6;color:#374151;padding:0.5rem 1rem;
                           border:none;border-radius:4px;font-weight:500;cursor:pointer;">
              ℹ️ Detaljer
            </button>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_stat_card(title, value, description=None, trend=None):
    """
    Render a statistic card with optional trend indicator.

    Args:
        title: Stat title
        value: Main value to display
        description: Optional description or context
        trend: Optional trend value (positive or negative number)
    """
    # Determine trend styling
    trend_html = ""
    if trend is not None:
        trend_color = "#10b981" if trend > 0 else "#ef4444"  # Green or red
        trend_arrow = "↑" if trend > 0 else "↓"
        trend_html = f"""
        <div style="color:{trend_color};font-size:0.875rem;font-weight:600;">
          {trend_arrow} {abs(trend):.1f}%
        </div>
        """

    # Description HTML if provided
    desc_html = f"""
    <div style="color:#6b7280;font-size:0.75rem;">
      {description}
    </div>
    """ if description else ""

    # Render the card
    st.markdown(
        f"""
        <div style="background:white;padding:1.25rem;border-radius:8px;
                    box-shadow:0 1px 3px rgba(0,0,0,0.1);height:100%;">
          <div style="color:#6b7280;font-size:0.875rem;margin-bottom:0.5rem;">
            {title}
          </div>
          <div style="display:flex;align-items:baseline;gap:0.5rem;">
            <div style="font-size:1.5rem;font-weight:700;color:#111827;">
              {value}
            </div>
            {trend_html}
          </div>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )
