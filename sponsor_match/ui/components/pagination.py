"""
sponsor_match/ui/components/pagination.py

Efficient pagination component for handling 82,776 companies
"""
import streamlit as st
import pandas as pd
from typing import Optional


def paginate_dataframe(
        df: pd.DataFrame,
        page_size: int = 50,
        key_prefix: str = "page"
) -> pd.DataFrame:
    """
    Implement efficient pagination with session state.
    Handles large datasets without performance degradation.

    Args:
        df: DataFrame to paginate
        page_size: Number of items per page
        key_prefix: Prefix for session state keys (for multiple paginators)

    Returns:
        Paginated slice of the DataFrame
    """
    # Initialise page in session state
    page_key = f'{key_prefix}_number'
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    # Calculate total pages
    total_rows = len(df)
    total_pages = (total_rows // page_size) + (1 if total_rows % page_size else 0)

    # Ensure page is within valid range
    if st.session_state[page_key] > total_pages:
        st.session_state[page_key] = total_pages
    elif st.session_state[page_key] < 1:
        st.session_state[page_key] = 1

    # Calculate indices
    start_idx = (st.session_state[page_key] - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)

    # Pagination controls in columns
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])

    with col1:
        if st.button("⏮️ First",
                     disabled=(st.session_state[page_key] == 1),
                     key=f"{key_prefix}_first"):
            st.session_state[page_key] = 1
            st.rerun()

    with col2:
        if st.button("◀️ Prev",
                     disabled=(st.session_state[page_key] == 1),
                     key=f"{key_prefix}_prev"):
            st.session_state[page_key] -= 1
            st.rerun()

    with col3:
        # Direct page input with better formatting
        new_page = st.number_input(
            f"Page {st.session_state[page_key]} of {total_pages}",
            min_value=1,
            max_value=total_pages,
            value=st.session_state[page_key],
            key=f"{key_prefix}_input",
            label_visibility="visible"
        )
        if new_page != st.session_state[page_key]:
            st.session_state[page_key] = new_page
            st.rerun()

    with col4:
        if st.button("Next ▶️",
                     disabled=(st.session_state[page_key] == total_pages),
                     key=f"{key_prefix}_next"):
            st.session_state[page_key] += 1
            st.rerun()

    with col5:
        if st.button("Last ⏭️",
                     disabled=(st.session_state[page_key] == total_pages),
                     key=f"{key_prefix}_last"):
            st.session_state[page_key] = total_pages
            st.rerun()

    # Show row information
    st.caption(f"Showing {start_idx + 1}-{end_idx} of {total_rows} items")

    # Return paginated slice
    return df.iloc[start_idx:end_idx]


def paginate_results(
        results: list,
        page_size: int = 20,
        key_prefix: str = "results"
) -> list:
    """
    Paginate a list of results (for non-DataFrame data).

    Args:
        results: List to paginate
        page_size: Number of items per page
        key_prefix: Prefix for session state keys

    Returns:
        Paginated slice of the list
    """
    # Convert to DataFrame for reuse of pagination logic
    df = pd.DataFrame(results)
    paginated_df = paginate_dataframe(df, page_size, key_prefix)

    # Convert back to list of dictionaries
    return paginated_df.to_dict('records')


def get_page_info(
        total_items: int,
        page_size: int = 50,
        key_prefix: str = "page"
) -> dict:
    """
    Get current pagination information.

    Returns:
        Dictionary with page info (current_page, total_pages, start_idx, end_idx)
    """
    page_key = f'{key_prefix}_number'
    if page_key not in st.session_state:
        st.session_state[page_key] = 1

    total_pages = (total_items // page_size) + (1 if total_items % page_size else 0)
    current_page = st.session_state[page_key]
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, total_items)

    return {
        'current_page': current_page,
        'total_pages': total_pages,
        'start_idx': start_idx,
        'end_idx': end_idx,
        'page_size': page_size,
        'total_items': total_items
    }


# AgGrid pagination for advanced features
def create_aggrid_config(page_size: int = 50):
    """
    Create AgGrid configuration with pagination.

    Returns:
        Dictionary with AgGrid options
    """
    return {
        'pagination': True,
        'paginationPageSize': page_size,
        'paginationAutoPageSize': False,
        'defaultColDef': {
            'filter': True,
            'sortable': True,
            'resizable': True
        },
        'enableRangeSelection': True,
        'suppressMenuHide': True,
        'animateRows': True,
        'rowSelection': 'single'
    }