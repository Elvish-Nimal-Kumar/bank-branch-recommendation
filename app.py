import streamlit as st
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import haversine_distances
import folium
from streamlit_folium import st_folium

# Load dataset
data = pd.read_csv("final_bank_recommendation_data.csv")

st.title("Bank Branch Recommendation System")

st.write(
    "Find suitable bank branches based on your location and preferences."
)

# User Inputs
st.subheader("Customer Details")

latitude = st.text_input(
    "Latitude",
    value="13.0827"
)

longitude = st.text_input(
    "Longitude",
    value="80.2707"
)

bank_preference = st.selectbox(
    "Bank Preference",
    ["Any", "Public", "Private"]
)

max_distance = st.text_input(
    "Maximum Distance (km)",
    value="10"
)

find_banks = st.button("Find Recommended Banks")


if find_banks:

    latitude = float(latitude)
    longitude = float(longitude)
    max_distance = float(max_distance)

    # Calculate distance from customer to every branch
    customer_location = np.radians([[latitude, longitude]])

    branch_locations = np.radians(
        data[["lattitude", "longitude"]].values
    )

    distances = haversine_distances(
        customer_location,
        branch_locations
    ) * 6371

    data["customer_distance_km"] = distances[0]

    # Apply bank preference
    if bank_preference == "Public":
        data = data[
            data["bank_group"] == "Public Sector Banks"
        ]

    elif bank_preference == "Private":
        data = data[
            data["bank_group"] == "Private Sector Banks"
        ]

    # Apply maximum distance
    data = data[
        data["customer_distance_km"] <= max_distance
    ].copy()

    # Calculate recommendation score
    data["distance_score"] = (
        1 / (1 + data["customer_distance_km"])
    )

    data["recommendation_score"] = (
        data["suitability_score"] * 0.7
        + data["distance_score"] * 30
    )

    # Sort recommendations
    recommendations = data.sort_values(
        "recommendation_score",
        ascending=False
    )

    # -----------------------------
    # Recommendation Results
    # -----------------------------

    st.subheader("Recommended Bank Branches")

    st.write(
        f"{len(recommendations)} branches found within "
        f"{max_distance} km"
    )

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


    # -----------------------------
    # Interactive Map
    # -----------------------------

    st.subheader("Branch Location Map")

    # Create map centered on customer
    branch_map = folium.Map(
        location=[latitude, longitude],
        zoom_start=12
    )

    # Customer marker
    folium.Marker(
        [latitude, longitude],
        popup="Customer Location",
        tooltip="Your Location",
        icon=folium.Icon(
            color="red",
            icon="user"
        )
    ).add_to(branch_map)

    # Add recommended branches to map
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

    # Display map
    st_folium(
        branch_map,
        width=900,
        height=600
    )
