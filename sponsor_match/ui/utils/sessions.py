"""
Utilities for managing Streamlit session state.
"""
import streamlit as st


def get_session_data(key, default=None):
    """
    Get data from session state with fallback to default.

    Args:
        key: Session state key
        default: Default value if key doesn't exist

    Returns:
        Value from session state or default
    """
    return st.session_state.get(key, default)


def set_session_data(key, value):
    """
    Set data in session state.

    Args:
        key: Session state key
        value: Value to store
    """
    st.session_state[key] = value


def clear_session_data(key=None):
    """
    Clear data from session state.

    Args:
        key: Specific key to clear, or None to clear all app-specific keys
    """
    if key is not None and key in st.session_state:
        del st.session_state[key]
    elif key is None:
        # Clear all app-specific keys (doesn't affect Streamlit's internal keys)
        app_keys = [k for k in st.session_state.keys()
                    if not k.startswith('_') and k not in ['formSubmitter', 'formKey']]
        for k in app_keys:
            del st.session_state[k]
