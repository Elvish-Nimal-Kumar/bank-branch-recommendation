import streamlit as st
import pandas as pd
import numpy as np
import requests

from sklearn.metrics.pairwise import haversine_distances

import folium
from streamlit_folium import st_folium


# -----------------------------------
# Load Dataset
# -----------------------------------

data = pd.read_csv("final_bank_recommendation_data.csv")


# -----------------------------------
# Page Title
# -----------------------------------

st.title("Bank Branch Recommendation System")

st.write(
    "Find suitable bank branches based on your location and preferences."
)


# -----------------------------------
# Address to Coordinates
# -----------------------------------

def get_coordinates(address, pincode):

    search_query = f"{address}, {pincode}, Tamil Nadu, India"

    url = "https://nominatim.openstreetmap.org/search"

    params = {
        "q": search_query,
        "format": "json",
        "limit": 1
    }

    headers = {
        "User-Agent": "BankBranchRecommendationSystem/1.0"
    }

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=10
    )

    if response.status_code != 200:
        return None, None

    results = response.json()

    if len(results) == 0:
        return None, None

    latitude = float(results[0]["lat"])
    longitude = float(results[0]["lon"])

    return latitude, longitude


# -----------------------------------
# User Inputs
# -----------------------------------

st.subheader("Customer Details")


address = st.text_input(
    "Address",
    placeholder="Example: Tambaram, Chennai"
)


pincode = st.text_input(
    "Pincode",
    placeholder="Example: 600045"
)


bank_preference = st.selectbox(
    "Bank Preference",
    ["Any", "Public", "Private"]
)


max_distance = st.text_input(
    "Maximum Distance (km)",
    value="10"
)


# -----------------------------------
# Button State
# -----------------------------------

if "show_results" not in st.session_state:
    st.session_state.show_results = False


if st.button("Find Recommended Banks"):

    st.session_state.show_results = True


# -----------------------------------
# Recommendation Process
# -----------------------------------

if st.session_state.show_results:

    # -----------------------------------
    # Validate Inputs
    # -----------------------------------

    if address.strip() == "":
        st.error("Please enter your address.")
        st.stop()


    if pincode.strip() == "":
        st.error("Please enter your pincode.")
        st.stop()


    if not pincode.isdigit() or len(pincode) != 6:
        st.error("Please enter a valid 6-digit pincode.")
        st.stop()


    try:
        max_distance = float(max_distance)

    except ValueError:
        st.error("Please enter a valid maximum distance.")
        st.stop()


    # -----------------------------------
    # Convert Address to Coordinates
    # -----------------------------------

    with st.spinner("Finding your location..."):

        latitude, longitude = get_coordinates(
            address,
            pincode
        )


    # -----------------------------------
    # Location Not Found
    # -----------------------------------

    if latitude is None or longitude is None:

        st.error(
            "We couldn't find this address. "
            "Please check the address and pincode and try again."
        )

        st.stop()


    # -----------------------------------
    # Show Detected Location
    # -----------------------------------

    st.success(
        f"Location found: "
        f"{latitude:.4f}, {longitude:.4f}"
    )


    # -----------------------------------
    # Calculate Distance
    # -----------------------------------

    customer_location = np.radians(
        [[latitude, longitude]]
    )


    branch_locations = np.radians(
        data[["lattitude", "longitude"]].values
    )


    distances = haversine_distances(
        customer_location,
        branch_locations
    ) * 6371


    data["customer_distance_km"] = distances[0]


    # -----------------------------------
    # Apply Bank Preference
    # -----------------------------------

    if bank_preference == "Public":

        data = data[
            data["bank_group"] == "Public Sector Banks"
        ]


    elif bank_preference == "Private":

        data = data[
            data["bank_group"] == "Private Sector Banks"
        ]


    # -----------------------------------
    # Apply Maximum Distance
    # -----------------------------------

    data = data[
        data["customer_distance_km"] <= max_distance
    ].copy()


    # -----------------------------------
    # Calculate Recommendation Score
    # -----------------------------------

    data["distance_score"] = (
        1 / (1 + data["customer_distance_km"])
    )


    data["recommendation_score"] = (
        data["suitability_score"] * 0.7
        + data["distance_score"] * 30
    )


    # -----------------------------------
    # Sort Recommendations
    # -----------------------------------

    recommendations = data.sort_values(
        "recommendation_score",
        ascending=False
    )


    # -----------------------------------
    # Recommendation Results
    # -----------------------------------

    st.subheader("Recommended Bank Branches")


    st.write(
        f"{len(recommendations)} branches found "
        f"within {max_distance} km"
    )


    # -----------------------------------
    # No Results
    # -----------------------------------

    if len(recommendations) == 0:

        st.warning(
            "No bank branches found within the selected distance."
        )


    # -----------------------------------
    # Recommendation Cards
    # -----------------------------------

    for _, row in recommendations.head(10).iterrows():

        st.markdown("---")

        st.subheader(row["bank"])


        st.write(
            f"**Branch:** {row['branch']}"
        )


        st.write(
            f"**Bank Type:** {row['bank_group']}"
        )


        st.write(
            f"**Distance:** "
            f"{row['customer_distance_km']:.2f} km"
        )


        st.write(
            f"**Suitability:** "
            f"{row['suitability']}"
        )


        st.write(
            f"**Suitability Score:** "
            f"{row['suitability_score']:.2f}"
        )


        st.write(
            f"**Nearest Bus:** "
            f"{row['nearest_bus_km']:.2f} km"
        )


        st.write(
            f"**Nearest Railway:** "
            f"{row['nearest_railway_km']:.2f} km"
        )


        st.write(
            f"**Nearest Metro:** "
            f"{row['nearest_metro_km']:.2f} km"
        )


        st.write(
            f"**Nearby Branches:** "
            f"{int(row['nearby_branch_count'])}"
        )


        st.write(
            f"**Nearest Major Road:** "
            f"{row['nearest_major_road_km']:.2f} km"
        )


    # -----------------------------------
    # Interactive Map
    # -----------------------------------

    if len(recommendations) > 0:

        st.subheader("Branch Location Map")


        # Create map
        branch_map = folium.Map(
            location=[
                latitude,
                longitude
            ],
            zoom_start=12
        )


        # -----------------------------------
        # Customer Location
        # -----------------------------------

        folium.Marker(
            [
                latitude,
                longitude
            ],
            popup="Customer Location",
            tooltip="Your Location",
            icon=folium.Icon(
                color="red",
                icon="user"
            )
        ).add_to(branch_map)


        # -----------------------------------
        # Recommended Branches
        # -----------------------------------

        for _, row in recommendations.head(10).iterrows():

            popup_text = f"""
            <b>{row['bank']}</b><br>
            Branch: {row['branch']}<br>
            Bank Type: {row['bank_group']}<br>
            Distance: {row['customer_distance_km']:.2f} km<br>
            Suitability: {row['suitability']}<br>
            Suitability Score: {row['suitability_score']:.2f}
            """


            folium.Marker(
                [
                    row["lattitude"],
                    row["longitude"]
                ],
                popup=folium.Popup(
                    popup_text,
                    max_width=300
                ),
                tooltip=row["bank"],
                icon=folium.Icon(
                    color="blue",
                    icon="bank"
                )
            ).add_to(branch_map)


        # -----------------------------------
        # Display Map
        # -----------------------------------

        st_folium(
            branch_map,
            width=900,
            height=600
        )


    # -----------------------------------
    # OpenStreetMap Attribution
    # -----------------------------------

    st.caption(
        "Location search powered by OpenStreetMap Nominatim. "
        "Map data © OpenStreetMap contributors."
    )
