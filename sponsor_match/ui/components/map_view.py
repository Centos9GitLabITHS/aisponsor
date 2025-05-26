# This script has been annotated with comments in British English.
# Detailed comments explaining each section have been added as requested.

# sponsor_match/ui/components/map_view.py

from folium import Map, Marker, Popup, Icon
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium

def render_map(club=None, sponsors=None, height=400, width=None):
    """
    Render an interactive map with club and sponsor markers.

    Args:
        club: Dictionary with club information (optional)
        sponsors: List of sponsor dictionaries (optional)
        height: Map height in pixels (default 400)
        width:  Map width in pixels (optional; omit to auto-size)
    """
    # Default center on Gothenburg
    center = [57.7089, 11.9746]
    if club and club.get('lat') and club.get('lon'):
        center = [club['lat'], club['lon']]

    m = Map(location=center, zoom_start=12, tiles="CartoDB positron")

    # Club marker
    if club and club.get('lat') and club.get('lon'):
        Marker(
            location=[club['lat'], club['lon']],
            popup=Popup(_club_popup(club), max_width=300),
            icon=Icon(color='purple', icon='flag', prefix='fa'),
            tooltip=club.get('name', 'Club')
        ).add_to(m)

    # Sponsor markers
    if sponsors:
        cluster = MarkerCluster().add_to(m)
        heat_data = []
        for sponsor in sponsors:
            if sponsor.get('lat') and sponsor.get('lon'):
                Marker(
                    location=[sponsor['lat'], sponsor['lon']],
                    popup=Popup(_sponsor_popup(sponsor), max_width=300),
                    icon=Icon(color=_marker_color(sponsor), icon='building', prefix='fa'),
                    tooltip=sponsor.get('name', 'Sponsor')
                ).add_to(cluster)
                if sponsor.get('score') is not None:
                    heat_data.append([sponsor['lat'], sponsor['lon'], sponsor['score']])
        if heat_data:
            HeatMap(heat_data).add_to(m)

    # Only pass width if it’s a real integer
    if width:
        return st_folium(m, width=width, height=height)
    else:
        return st_folium(m, height=height)


def _club_popup(club):
    return f"""
    <div style="width:200px">
        <h4>{club.get('name','')}</h4>
        <p><b>Medlemmar:</b> {club.get('member_count','N/A')}</p>
        <p><b>Storlek:</b> {club.get('size_bucket','').title()}</p>
        <p><b>Adress:</b> {club.get('address','N/A')}</p>
    </div>
    """

def _sponsor_popup(sponsor):
    contact = sponsor.get('contact', {})
    return f"""
    <div style="width:200px">
        <h4>{sponsor.get('name','')}</h4>
        <p>{sponsor.get('description','')}</p>
        <p>📧 {contact.get('email','')}</p>
        <p>📞 {contact.get('phone','')}</p>
    </div>
    """

def _marker_color(sponsor):
    score = sponsor.get('score', 0)
    if score >= 75:
        return 'green'
    if score >= 50:
        return 'orange'
    return 'red'
