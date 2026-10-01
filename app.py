import streamlit as st
import pandas as pd
import numpy as np
import requests

from sklearn.metrics.pairwise import haversine_distances
from streamlit_js_eval import get_geolocation

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
# Session State
# -----------------------------------

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "location_method" not in st.session_state:
    st.session_state.location_method = None

if "current_latitude" not in st.session_state:
    st.session_state.current_latitude = None

if "current_longitude" not in st.session_state:
    st.session_state.current_longitude = None


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
# Customer Location
# -----------------------------------

st.subheader("Customer Location")

st.write("Choose how you want to provide your location.")


location_option = st.radio(
    "Location Method",
    [
        "Use My Current Location",
        "Enter Address"
    ],
    horizontal=True
)


# -----------------------------------
# Current Location
# -----------------------------------

if location_option == "Use My Current Location":

    st.write(
        "Click the button below and allow location access "
        "when your browser asks for permission."
    )

    location = get_geolocation()

    if location:

        if "error" in location:

            st.error(
                "Unable to get your location. "
                "Please allow location access in your browser."
            )

        elif "coords" in location:

            st.session_state.current_latitude = (
                location["coords"]["latitude"]
            )

            st.session_state.current_longitude = (
                location["coords"]["longitude"]
            )

            st.session_state.location_method = "current"

            st.success(
                "Your current location was detected."
            )


# -----------------------------------
# Address
# -----------------------------------

else:

    address = st.text_input(
        "Address",
        placeholder="Example: Tambaram, Chennai"
    )

    pincode = st.text_input(
        "Pincode",
        placeholder="Example: 600045"
    )

    st.session_state.location_method = "address"


# -----------------------------------
# Bank Preferences
# -----------------------------------

st.subheader("Bank Preferences")


bank_preference = st.selectbox(
    "Bank Preference",
    ["Any", "Public", "Private"]
)


max_distance = st.text_input(
    "Maximum Distance (km)",
    value="10"
)


# -----------------------------------
# Find Banks Button
# -----------------------------------

if st.button("Find Recommended Banks"):

    st.session_state.show_results = True


# -----------------------------------
# Recommendation Process
# -----------------------------------

if st.session_state.show_results:

    latitude = None
    longitude = None


    # -----------------------------------
    # Current Location
    # -----------------------------------

    if location_option == "Use My Current Location":

        latitude = st.session_state.current_latitude
        longitude = st.session_state.current_longitude

        if latitude is None or longitude is None:

            st.error(
                "Please allow location access first."
            )

            st.stop()


    # -----------------------------------
    # Address Location
    # -----------------------------------

    else:

        if address.strip() == "":

            st.error(
                "Please enter your address."
            )

            st.stop()


        if pincode.strip() == "":

            st.error(
                "Please enter your pincode."
            )

            st.stop()


        if not pincode.isdigit() or len(pincode) != 6:

            st.error(
                "Please enter a valid 6-digit pincode."
            )

            st.stop()


        with st.spinner("Finding your location..."):

            latitude, longitude = get_coordinates(
                address,
                pincode
            )


        if latitude is None or longitude is None:

            st.error(
                "We couldn't find this address. "
                "Please check the address and pincode."
            )

            st.stop()


    # -----------------------------------
    # Validate Distance
    # -----------------------------------

    try:

        max_distance = float(max_distance)

    except ValueError:

        st.error(
            "Please enter a valid maximum distance."
        )

        st.stop()


    # -----------------------------------
    # Calculate Branch Distance
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
    # Bank Preference
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
    # Maximum Distance
    # -----------------------------------

    data = data[
        data["customer_distance_km"] <= max_distance
    ].copy()


    # -----------------------------------
    # Recommendation Score
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
    # Results
    # -----------------------------------

    st.subheader("Recommended Bank Branches")


    st.write(
        f"{len(recommendations)} branches found "
        f"within {max_distance} km"
    )


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


        branch_map = folium.Map(
            location=[
                latitude,
                longitude
            ],
            zoom_start=12
        )


        # Customer Marker

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


        # Branch Markers

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


        st_folium(
            branch_map,
            width=900,
            height=600
        )


# -----------------------------------
# Attribution
# -----------------------------------

st.caption(
    "Location search powered by OpenStreetMap Nominatim. "
    "Map data © OpenStreetMap contributors."
)
