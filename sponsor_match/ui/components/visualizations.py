"""
sponsor_match/ui/components/visualizations.py

High-performance visualizations using Altair.
Replaces slower Plotly charts for better performance with 82,776 companies.
"""
import altair as alt
import pandas as pd
import streamlit as st
from typing import Optional, Dict, List


def create_scatter_plot(
    df: pd.DataFrame,
    x_col: str = 'revenue',
    y_col: str = 'employees',
    color_col: str = 'industry',
    size_col: Optional[str] = None,
    title: str = 'Company Performance Matrix'
) -> alt.Chart:
    """
    Create fast, interactive scatter plot with Altair.
    Handles large datasets efficiently.

    Args:
        df: DataFrame with company data
        x_col: Column for x-axis
        y_col: Column for y-axis
        color_col: Column for color encoding
        size_col: Optional column for size encoding
        title: Chart title

    Returns:
        Altair chart object
    """
    # Sample data if too large for performance
    if len(df) > 5000:
        df_sample = df.sample(n=5000, random_state=42)
        title += " (Sample)"
    else:
        df_sample = df

    # Base chart
    base = alt.Chart(df_sample).mark_circle(size=60)

    # Encodings
    encodings = {
        'x': alt.X(f'{x_col}:Q', title=x_col.replace('_', ' ').title()),
        'y': alt.Y(f'{y_col}:Q', title=y_col.replace('_', ' ').title()),
        'color': alt.Color(f'{color_col}:N', legend=alt.Legend(title=color_col.title())),
        'tooltip': [
            alt.Tooltip('name:N', title='Company'),
            alt.Tooltip(f'{x_col}:Q', title=x_col.title(), format=',.0f'),
            alt.Tooltip(f'{y_col}:Q', title=y_col.title(), format=',.0f'),
            alt.Tooltip(f'{color_col}:N', title=color_col.title())
        ]
    }

    # Add size encoding if specified
    if size_col:
        encodings['size'] = alt.Size(f'{size_col}:Q', scale=alt.Scale(range=[50, 500]))
        encodings['tooltip'].append(alt.Tooltip(f'{size_col}:Q', title=size_col.title()))

    # Create chart
    chart = base.encode(**encodings).interactive().properties(
        width=700,
        height=400,
        title=title
    )

    return chart


def create_bar_chart(
    df: pd.DataFrame,
    category_col: str = 'size_bucket',
    title: str = 'Company Size Distribution'
) -> alt.Chart:
    """
    Create responsive bar chart for categorical data.

    Args:
        df: DataFrame with company data
        category_col: Column for categories
        title: Chart title

    Returns:
        Altair chart object
    """
    # Count by category
    count_df = df[category_col].value_counts().reset_index()
    count_df.columns = [category_col, 'count']

    # Order categories
    if category_col == 'size_bucket':
        order = ['small', 'medium', 'large', 'enterprise']
        count_df['order'] = count_df[category_col].map({v: i for i, v in enumerate(order)})
        count_df = count_df.sort_values('order')

    # Create chart
    chart = alt.Chart(count_df).mark_bar().encode(
        x=alt.X(f'{category_col}:N',
                title=category_col.replace('_', ' ').title(),
                sort=order if category_col == 'size_bucket' else None),
        y=alt.Y('count:Q', title='Number of Companies'),
        color=alt.Color(f'{category_col}:N',
                       scale=alt.Scale(scheme='blues'),
                       legend=None),
        tooltip=[
            alt.Tooltip(f'{category_col}:N', title='Category'),
            alt.Tooltip('count:Q', title='Count', format=',')
        ]
    ).properties(
        width=400,
        height=300,
        title=title
    )

    return chart


def create_heatmap(
    df: pd.DataFrame,
    lat_col: str = 'latitude',
    lon_col: str = 'longitude',
    value_col: str = 'score',
    title: str = 'Geographic Distribution Heatmap'
) -> alt.Chart:
    """
    Create geographic heatmap using hexbins for performance.

    Args:
        df: DataFrame with location data
        lat_col: Column for latitude
        lon_col: Column for longitude
        value_col: Column for values (e.g., score)
        title: Chart title

    Returns:
        Altair chart object
    """
    # Sample if too large
    if len(df) > 10000:
        df_sample = df.sample(n=10000, random_state=42)
    else:
        df_sample = df

    # Create hexbin chart
    chart = alt.Chart(df_sample).mark_circle(size=10, opacity=0.6).encode(
        x=alt.X(f'{lon_col}:Q',
                title='Longitude',
                scale=alt.Scale(domain=[df[lon_col].min(), df[lon_col].max()])),
        y=alt.Y(f'{lat_col}:Q',
                title='Latitude',
                scale=alt.Scale(domain=[df[lat_col].min(), df[lat_col].max()])),
        color=alt.Color(f'mean({value_col}):Q',
                       scale=alt.Scale(scheme='viridis'),
                       title=f'Avg {value_col.title()}'),
        size=alt.Size('count():Q',
                     scale=alt.Scale(range=[10, 200]),
                     legend=None),
        tooltip=[
            alt.Tooltip('count():Q', title='Companies'),
            alt.Tooltip(f'mean({value_col}):Q', title=f'Avg {value_col}', format='.2f')
        ]
    ).properties(
        width=600,
        height=600,
        title=title
    )

    return chart


def create_distribution_chart(
    df: pd.DataFrame,
    value_col: str,
    title: str,
    bins: int = 30
) -> alt.Chart:
    """
    Create histogram for value distributions.

    Args:
        df: DataFrame with data
        value_col: Column to plot distribution
        title: Chart title
        bins: Number of bins

    Returns:
        Altair chart object
    """
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X(f'{value_col}:Q',
                bin=alt.Bin(maxbins=bins),
                title=value_col.replace('_', ' ').title()),
        y=alt.Y('count()',
                title='Frequency'),
        color=alt.value('#2563eb'),
        tooltip=[
            alt.Tooltip(f'{value_col}:Q', title=value_col.title(), bin=True),
            alt.Tooltip('count()', title='Count')
        ]
    ).properties(
        width=500,
        height=300,
        title=title
    )

    return chart


def create_time_series(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    group_col: Optional[str] = None,
    title: str = 'Time Series'
) -> alt.Chart:
    """
    Create time series line chart.

    Args:
        df: DataFrame with time series data
        date_col: Date column
        value_col: Value column
        group_col: Optional grouping column
        title: Chart title

    Returns:
        Altair chart object
    """
    base = alt.Chart(df).mark_line(point=True)

    encodings = {
        'x': alt.X(f'{date_col}:T', title='Date'),
        'y': alt.Y(f'{value_col}:Q', title=value_col.replace('_', ' ').title()),
        'tooltip': [
            alt.Tooltip(f'{date_col}:T', title='Date'),
            alt.Tooltip(f'{value_col}:Q', title=value_col.title(), format=',.0f')
        ]
    }

    if group_col:
        encodings['color'] = alt.Color(f'{group_col}:N', title=group_col.title())
        encodings['tooltip'].append(alt.Tooltip(f'{group_col}:N', title=group_col.title()))

    chart = base.encode(**encodings).properties(
        width=700,
        height=300,
        title=title
    )

    return chart


def create_correlation_matrix(
    df: pd.DataFrame,
    numeric_cols: List[str],
    title: str = 'Feature Correlation Matrix'
) -> alt.Chart:
    """
    Create correlation matrix heatmap.

    Args:
        df: DataFrame with numeric data
        numeric_cols: List of numeric columns to correlate
        title: Chart title

    Returns:
        Altair chart object
    """
    # Calculate correlations
    corr_df = df[numeric_cols].corr()

    # Reshape for Altair
    corr_data = []
    for i, col1 in enumerate(numeric_cols):
        for j, col2 in enumerate(numeric_cols):
            corr_data.append({
                'var1': col1,
                'var2': col2,
                'correlation': corr_df.iloc[i, j]
            })

    corr_data_df = pd.DataFrame(corr_data)

    # Create heatmap
    chart = alt.Chart(corr_data_df).mark_rect().encode(
        x=alt.X('var1:N', title=''),
        y=alt.Y('var2:N', title=''),
        color=alt.Color('correlation:Q',
                       scale=alt.Scale(scheme='redblue', domain=[-1, 1]),
                       title='Correlation'),
        tooltip=[
            alt.Tooltip('var1:N', title='Variable 1'),
            alt.Tooltip('var2:N', title='Variable 2'),
            alt.Tooltip('correlation:Q', title='Correlation', format='.3f')
        ]
    ).properties(
        width=500,
        height=500,
        title=title
    )

    return chart


# Composite visualization functions
def create_analytics_dashboard(
    df: pd.DataFrame,
    title: str = "Analytics Dashboard"
) -> Dict[str, alt.Chart]:
    """
    Create a complete analytics dashboard with multiple charts.

    Args:
        df: DataFrame with company/sponsor data
        title: Dashboard title

    Returns:
        Dictionary of chart objects
    """
    charts = {}

    # Size distribution
    charts['size_dist'] = create_bar_chart(
        df,
        category_col='size_bucket',
        title='Company Size Distribution'
    )

    # Score distribution (if available)
    if 'score' in df.columns:
        charts['score_dist'] = create_distribution_chart(
            df,
            value_col='score',
            title='Match Score Distribution'
        )

    # Geographic scatter (if coordinates available)
    if 'latitude' in df.columns and 'longitude' in df.columns:
        charts['geo_scatter'] = alt.Chart(df.sample(n=min(1000, len(df)))).mark_circle(size=30).encode(
            x=alt.X('longitude:Q', scale=alt.Scale(domain=[11.8, 12.1])),
            y=alt.Y('latitude:Q', scale=alt.Scale(domain=[57.6, 57.8])),
            color=alt.Color('size_bucket:N'),
            tooltip=['name:N', 'size_bucket:N']
        ).properties(
            width=400,
            height=400,
            title='Geographic Distribution (Sample)'
        )

    return charts
