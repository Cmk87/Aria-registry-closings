import pandas as pd
import streamlit as st
from geopy.distance import geodesic
from geopy.geocoders import Nominatim
from io import BytesIO  # Import BytesIO for Excel file creation

# Load your data
@st.cache_data  # Updated cache function
def load_data():
    df = pd.read_excel('madrid_properties.xlsx', sheet_name='Madrid', header=1)
    # Drop rows where Latitude or Longitud is missing (NaN)
    df = df.dropna(subset=['Latitude', 'Longitud'])
    return df

df = load_data()

# Function to geocode an address
def geocode_address(address):
    geolocator = Nominatim(user_agent="chris.karpfen@gmail.com")  # Custom user-agent with your email
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    else:
        return None

# Function to generate Google Maps Street View link
def generate_street_view_link(lat, lon):
    return f"https://www.google.com/maps?q=&layer=c&cbll={lat},{lon}"

# Function to generate a Google Maps Street View link for the input address
def generate_input_street_view_link(address):
    geolocator = Nominatim(user_agent="chris.karpfen@gmail.com")
    location = geolocator.geocode(address)
    if location:
        return f"https://www.google.com/maps?q=&layer=c&cbll={location.latitude},{location.longitude}"
    else:
        return None

# Function to create an Excel file in memory and return it
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False)
    writer.close()  # Use .close() instead of .save()
    output.seek(0)
    return output

# Function to calculate properties within a radius
def find_properties_within_radius(df, lat, lon, radius, min_size, max_size, num_results):
    def calculate_distance(row):
        property_coords = (row['Latitude'], row['Longitud'])
        return geodesic((lat, lon), property_coords).meters

    # Filter by distance and m2 size
    df['distance'] = df.apply(calculate_distance, axis=1).round(0).astype(int)  # Round distance to remove decimals
    nearby_properties = df[(df['distance'] <= radius) & (df['m2'] >= min_size) & (df['m2'] <= max_size)]
    
    # Sort by price and limit the number of results based on the dropdown
    nearby_properties = nearby_properties.sort_values(by='Price', ascending=False).head(num_results)
    
    # Return m2 and Price without decimals
    nearby_properties['m2'] = nearby_properties['m2'].astype(int)
    nearby_properties['Price'] = nearby_properties['Price'].round(0).astype(int)
    
    # Generate Street View links
    nearby_properties['Street View'] = nearby_properties.apply(
        lambda row: f'<a href="{generate_street_view_link(row["Latitude"], row["Longitud"])}" target="_blank">View</a>', axis=1
    )
    
    return nearby_properties

# Function to filter properties on the same street
def find_properties_on_street(df, lat, lon, street_name, min_size, max_size, num_results):
    def calculate_distance(row):
        property_coords = (row['Latitude'], row['Longitud'])
        return geodesic((lat, lon), property_coords).meters

    street_properties = df[(df['Street'].str.contains(street_name, case=False)) & 
                           (df['m2'] >= min_size) & (df['m2'] <= max_size)]
    street_properties['distance'] = street_properties.apply(calculate_distance, axis=1).round(0).astype(int)  # Add distance to output
    
    street_properties = street_properties.sort_values(by='Price', ascending=False).head(num_results)
    
    # Return m2 and Price without decimals
    street_properties['m2'] = street_properties['m2'].astype(int)
    street_properties['Price'] = street_properties['Price'].round(0).astype(int)
    
    # Generate Street View links
    street_properties['Street View'] = street_properties.apply(
        lambda row: f'<a href="{generate_street_view_link(row["Latitude"], row["Longitud"])}" target="_blank">View</a>', axis=1
    )
    
    return street_properties

# Custom background color (dark grey) and column width adjustments
st.markdown("""
    <style>
    body {
        background-color: #2E2E2E;  /* Dark grey background */
    }
    .title h1 {
        font-size: 2rem;  /* Reduced font size by about 30% */
        color: white;  /* Ensure title text is visible on dark background */
    }
    table td:nth-child(1), table td:nth-child(2) {
        white-space: nowrap;  /* Prevent line breaks in the first two columns (Date and Street) */
        max-width: 200px;  /* Adjust this width for a better fit */
    }
    </style>
    """, unsafe_allow_html=True)

# Display the logo at the top (50% smaller)
st.image("22_AriaHome_Logotipo_Blanco.png", width=300)  # Adjusted width to make the logo smaller

# Streamlit app layout
st.markdown('<div class="title"><h1>ARIA Registry Closings Extractor</h1></div>', unsafe_allow_html=True)

# Inputs for address, radius, m2, and number of results
street_list = df['Street'].unique().tolist()
street = st.selectbox("Enter Street (start typing for suggestions):", street_list)
number = st.text_input("Enter Number (e.g., 30):", "30")
radius = st.slider("Search Radius (in meters):", min_value=100, max_value=500, step=100, value=300)
m2_range = st.slider("Apartment Size (m2):", min_value=50, max_value=400, step=10, value=(50, 200))  # Step set to 10m2
num_results = st.selectbox("Number of Results to Display:", [10, 20, 30, 40, 50], index=1)  # Default set to 20

# Construct the full address for geocoding
address = f"{street} {number}, Madrid"

if st.button('Search Properties'):
    # Geocode the address to get latitude and longitude
    location = geocode_address(address)
    input_street_view_link = generate_input_street_view_link(address)

    if location:
        lat, lon = location
        min_size, max_size = m2_range

        # First Output: Properties within the specified radius
        st.subheader(f"Highest Closings within {radius} meters of {address}")
        if input_street_view_link:
            st.markdown(f"**Input Address Street View Link:** [View Street View]({input_street_view_link})")
        
        radius_results = find_properties_within_radius(df, lat, lon, radius, min_size, max_size, num_results)

        # Modify the "Date" column header to include the format "yyyy-mm-dd"
        radius_results.columns = radius_results.columns.str.replace('Date', 'Date (yyyy-mm-dd)')

        # Display the dataframe, removing row numbers and adding clickable street view links
        st.write(radius_results[['Date (yyyy-mm-dd)', 'Street', 'Nr', 'Price', 'm2', 'Const. Year', 'distance', 'Street View']].to_html(index=False, escape=False), unsafe_allow_html=True)

        # Button to download to Excel (without resetting the output)
        st.download_button(
            label="Download Radius Results as Excel",
            data=to_excel(radius_results),
            file_name="radius_results.xlsx"
        )

        # Second Output: Properties on the same street
        st.subheader(f"Highest Closings on {street}")
        street_results = find_properties_on_street(df, lat, lon, street, min_size, max_size, num_results)

        # Modify the "Date" column header to include the format "yyyy-mm-dd"
        street_results.columns = street_results.columns.str.replace('Date', 'Date (yyyy-mm-dd)')

        # Display the dataframe, removing row numbers and adding clickable street view links
        st.write(street_results[['Date (yyyy-mm-dd)', 'Street', 'Nr', 'Price', 'm2', 'Const. Year', 'distance', 'Street View']].to_html(index=False, escape=False), unsafe_allow_html=True)

        # Button to download to Excel (without resetting the output)
        st.download_button(
            label="Download Street Results as Excel",
            data=to_excel(street_results),
            file_name="street_results.xlsx"
        )
    else:
        st.write("Address could not be geocoded. Please try again.")
