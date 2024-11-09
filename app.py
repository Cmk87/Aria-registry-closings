import streamlit as st
st.set_page_config(layout="wide", page_title="ARIA Registry Closings Extractor")

import pandas as pd
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from io import BytesIO
import folium
from streamlit_folium import folium_static
import json

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
# CSS Styles
st.markdown("""
    <style>
    /* Container width control */
    .block-container {
        max-width: 1200px;
        padding-top: 1rem;
    }
    
    /* Input field width control */
    .stSelectbox, .stTextInput {
        max-width: 500px !important;
    }
    
    /* Smaller font for tables */
    .dataframe {
        font-size: 0.8rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Alternating row colors */
    .dataframe tbody tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .dataframe tbody tr:nth-child(odd) {
        background-color: white;
    }
    
    /* Make sliders smaller */
    .stSlider {
        max-width: 400px;
    }
    
    /* Two-column layout for tables */
    .table-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 20px;
        margin-top: 1rem;
    }
    
    .table-section {
        padding: 1rem;
        background: white;
        border-radius: 5px;
    }
    
    /* Copy button styling */
    .copy-button {
        margin-top: 0.5rem;
        margin-bottom: 1rem;
    }

    /* Smaller font for main title */
    .main-title {
        font-size: 1.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    /* Smaller font for table titles */
    .table-title {
        font-size: 1.2rem !important;
        margin-bottom: 0.5rem !important;
    }
    </style>
""", unsafe_allow_html=True)
def login_page():
    st.title("ARIA Registry Closings Extractor")
    st.image("22_AriaHome_Logotipo_Blanco.png", width=300)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        password = st.text_input("Enter your password", type="password")
        if st.button("Login"):
            if password == "Closings_24":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password!")

def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    return output

def geocode_address(address):
    geolocator = Nominatim(user_agent="chris.karpfen@gmail.com")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None

def generate_street_view_link_by_address(street, number):
    return f"https://www.google.com/maps/search/{street.replace(' ', '+')}+{number},+Madrid"

def generate_input_street_view_link(address):
    return f"https://www.google.com/maps/search/{address.replace(' ', '+')},+Madrid"

def generate_google_search_link(street, number):
    query = f"idealista {street} {number} Madrid"
    return f"https://www.google.com/search?q={query.replace(' ', '+')}"

def format_price(value):
    return format(int(value), ',').replace(',', ' ')
def create_copy_button(data, button_text="Copy to Clipboard"):
    """Create a button that copies formatted data to clipboard using JavaScript"""
    # Format the data for clipboard
    formatted_rows = []
    for _, row in data.iterrows():
        formatted_row = [
            row['Date'],
            row['Street'],
            str(row['Nr']),
            row['Price'],  
            str(row['m2']),
            row['Price psm'], 
            str(row['Const. Year']),
            str(row['Distance (m)'])
        ]
        formatted_rows.append('\t'.join(formatted_row))
    
    # Create header
    header = ['Date', 'Street', 'Nr', 'Price', 'm2', 'Price psm', 'Const. Year', 'Distance (m)']
    formatted_text = '\t'.join(header) + '\n' + '\n'.join(formatted_rows)
    
    # Properly escape the text for JavaScript
    formatted_text = formatted_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace("'", "\\'")
    
    # Create the button with unique ID
    button_id = f"copy_button_{id(data)}"
    
    copy_js = f"""
        <div>
            <button id="{button_id}" 
                style="
                    background-color: #ffffff;
                    color: #000000;
                    padding: 0.5rem 1rem;
                    border: 1px solid #cccccc;
                    border-radius: 4px;
                    cursor: pointer;
                    margin: 0.5rem 0;
                    min-width: 150px;
                "
                onclick='
                    navigator.clipboard.writeText(`{formatted_text}`).then(function() {{
                        document.getElementById("{button_id}").innerHTML = "✓ Copied!";
                        setTimeout(function() {{
                            document.getElementById("{button_id}").innerHTML = "{button_text}";
                        }}, 2000);
                    }});
                '
            >{button_text}</button>
        </div>
    """
    return copy_js

def create_map(center_lat, center_lon, properties_df, radius, input_address):
    m = folium.Map(location=[center_lat, center_lon], zoom_start=15)
    
    # Add center point (input address)
    folium.Marker(
        [center_lat, center_lon],
        popup=input_address,
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    # Add search radius circle
    folium.Circle(
        location=[center_lat, center_lon],
        radius=radius,
        color='red',
        fill=True,
        fill_color='red',
        fill_opacity=0.1
    ).add_to(m)
    
    # Add property markers
    for idx, row in properties_df.iterrows():
        formatted_date = pd.to_datetime(row['Date']).strftime('%Y-%m-%d')
        formatted_price = format(row['Price'], ',').replace(',', ' ')
        formatted_price_psm = format(row['Price psm'], ',').replace(',', ' ')
        
        popup_html = f"""
            <strong>Date:</strong> {formatted_date}<br>
            <strong>Address:</strong> {row['Street']} {row['Nr']}<br>
            <strong>Price:</strong> €{formatted_price}<br>
            <strong>Size:</strong> {row['m2']}m²<br>
            <strong>Price/m²:</strong> €{formatted_price_psm}<br>
            <strong>Year:</strong> {row['Const. Year']}<br>
            <strong>Distance:</strong> {row['distance']}m
        """
        folium.CircleMarker(
            location=[row['Latitude'], row['Longitud']],
            radius=8,
            popup=folium.Popup(popup_html, max_width=300),
            color='blue',
            fill=True,
            fill_color='blue'
        ).add_to(m)
    
    return m
def find_properties_within_radius(df, lat, lon, radius, min_size, max_size, num_results):
    def calculate_distance(row):
        property_coords = (row['Latitude'], row['Longitud'])
        return geodesic((lat, lon), property_coords).meters

    df['distance'] = df.apply(calculate_distance, axis=1).round(0).astype(int)
    nearby_properties = df[(df['distance'] <= radius) & (df['m2'] >= min_size) & (df['m2'] <= max_size)]
    nearby_properties = nearby_properties.sort_values(by='Price', ascending=False).head(num_results)
    
    nearby_properties['m2'] = nearby_properties['m2'].astype(int)
    nearby_properties['Price'] = nearby_properties['Price'].round(0).astype(int)
    nearby_properties['Price psm'] = (nearby_properties['Price'] / nearby_properties['m2']).round(0).astype(int)
    
    return nearby_properties

def find_properties_on_street(df, lat, lon, street_name, min_size, max_size, num_results):
    def calculate_distance(row):
        property_coords = (row['Latitude'], row['Longitud'])
        return geodesic((lat, lon), property_coords).meters

    street_properties = df[(df['Street'].str.contains(street_name, case=False)) & 
                         (df['m2'] >= min_size) & (df['m2'] <= max_size)]
    street_properties['distance'] = street_properties.apply(calculate_distance, axis=1).round(0).astype(int)
    
    street_properties = street_properties.sort_values(by='Price', ascending=False).head(num_results)
    
    street_properties['m2'] = street_properties['m2'].astype(int)
    street_properties['Price'] = street_properties['Price'].round(0).astype(int)
    street_properties['Price psm'] = (street_properties['Price'] / street_properties['m2']).round(0).astype(int)
    
    return street_properties
def main():
    # Load data
    @st.cache_data
    def load_data():
        df = pd.read_excel('madrid_properties.xlsx', sheet_name='Madrid', header=1)
        df = df.dropna(subset=['Latitude', 'Longitud'])
        return df

    if not st.session_state.logged_in:
        login_page()
        return

    df = load_data()

    # Display logo and title
    st.image("22_AriaHome_Logotipo_Blanco.png", width=300)
    st.markdown('<p class="main-title">ARIA Registry Closings Extractor</p>', unsafe_allow_html=True)

    # Input section
    street_list = df['Street'].unique().tolist()
    street = st.selectbox("Street (start typing for suggestions):", street_list)
    number = st.text_input("Number:", "30")
    
    col1, col2 = st.columns(2)
    with col1:
        radius = st.select_slider(
            "Search Radius (meters):",
            options=[100, 200, 300, 400, 500],
            value=300
        )
    with col2:
        m2_range = st.slider(
            "Apartment Size (m2):",
            min_value=50,
            max_value=500,
            step=50,
            value=(50, 200)
        )
    
    num_results = st.selectbox("Number of Results to Display:", [10, 20, 30, 40, 50], index=1)
    
    if st.button('Search Properties'):
        address = f"{street} {number}, Madrid"
        location = geocode_address(address)
        
        if location:
            lat, lon = location
            min_size, max_size = m2_range
            
            # Store results in session state to prevent reset on download
            st.session_state.radius_results = find_properties_within_radius(df, lat, lon, radius, min_size, max_size, num_results)
            st.session_state.street_results = find_properties_on_street(df, lat, lon, street, min_size, max_size, num_results)
            
            # Display map
            st.subheader("Closings within radius")
            map_data = pd.concat([st.session_state.radius_results, st.session_state.street_results]).drop_duplicates()
            folium_map = create_map(lat, lon, map_data, radius, address)
            folium_static(folium_map)

            # Display links
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Street View:** [View]({generate_input_street_view_link(address)})")
            with col2:
                st.markdown(f"**Idealista Data:** [Search]({generate_google_search_link(street, number)})")

            # Display tables side by side using grid layout
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
# Left table
            st.markdown('<div class="table-section">', unsafe_allow_html=True)
            st.markdown(f'<p class="table-title">Highest Closings within {radius}m</p>', unsafe_allow_html=True)
            
            radius_table = st.session_state.radius_results.copy()
            radius_table = radius_table.rename(columns={'distance': 'Distance (m)'})
            radius_table['Price'] = radius_table['Price'].apply(format_price)
            radius_table['Price psm'] = radius_table['Price psm'].apply(format_price)
            radius_table['Date'] = pd.to_datetime(radius_table['Date']).dt.strftime('%Y-%m-%d')
            
            # Display table
            table_cols = ['Date', 'Street', 'Nr', 'Price', 'm2', 'Price psm', 'Const. Year', 'Distance (m)']
            st.write(radius_table[table_cols].style.hide(axis="index").to_html(), unsafe_allow_html=True)
            
            # Buttons in columns
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    "Download Results",
                    data=to_excel(st.session_state.radius_results),
                    file_name="radius_results.xlsx",
                    mime="application/vnd.ms-excel"
                )
            with col2:
                st.components.v1.html(create_copy_button(radius_table[table_cols], "Copy to Clipboard"), height=50)
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Right table
            st.markdown('<div class="table-section">', unsafe_allow_html=True)
            st.markdown(f'<p class="table-title">Highest Closings on {street}</p>', unsafe_allow_html=True)
            
            street_table = st.session_state.street_results.copy()
            street_table = street_table.rename(columns={'distance': 'Distance (m)'})
            street_table['Price'] = street_table['Price'].apply(format_price)
            street_table['Price psm'] = street_table['Price psm'].apply(format_price)
            street_table['Date'] = pd.to_datetime(street_table['Date']).dt.strftime('%Y-%m-%d')
            
            # Display table
            st.write(street_table[table_cols].style.hide(axis="index").to_html(), unsafe_allow_html=True)
            
            # Buttons in columns
            col1, col2 = st.columns([1, 1])
            with col1:
                st.download_button(
                    "Download Results",
                    data=to_excel(st.session_state.street_results),
                    file_name="street_results.xlsx",
                    mime="application/vnd.ms-excel"
                )
            with col2:
                st.components.v1.html(create_copy_button(street_table[table_cols], "Copy to Clipboard"), height=50)
            st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.write("Address could not be geocoded. Please try again.")

if __name__ == "__main__":
    main()
