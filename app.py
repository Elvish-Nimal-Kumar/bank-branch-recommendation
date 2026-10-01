import streamlit as st
import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import haversine_distances
from streamlit_js_eval import get_geolocation

import folium
from streamlit_folium import st_folium


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Bank Branch Recommendation",
    page_icon="🏦",
    layout="wide"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

    /* Main page */
    .main {
        padding-top: 1rem;
    }

    /* Header */
    .main-header {
        padding: 10px 0 25px 0;
    }

    .main-title {
        font-size: 34px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .main-subtitle {
        color: #6b7280;
        font-size: 16px;
    }

    /* Section title */
    .section-title {
        font-size: 22px;
        font-weight: 650;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    /* Recommendation card */
    .bank-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 22px;
        margin: 12px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .bank-name {
        font-size: 21px;
        font-weight: 700;
        margin-bottom: 4px;
    }

    .branch-name {
        color: #6b7280;
        font-size: 14px;
        margin-bottom: 18px;
    }

    .bank-type {
        display: inline-block;
        background: #f3f4f6;
        padding: 5px 10px;
        border-radius: 20px;
        font-size: 12px;
        margin-bottom: 18px;
    }

    /* Metrics */
    .metric-box {
        background: #f8fafc;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
    }

    .metric-label {
        font-size: 12px;
        color: #6b7280;
        margin-bottom: 3px;
    }

    .metric-value {
        font-size: 16px;
        font-weight: 650;
    }

    /* Suitability */
    .suitability-high {
        color: #15803d;
        font-weight: 700;
    }

    .suitability-medium {
        color: #b45309;
        font-weight: 700;
    }

    .suitability-low {
        color: #dc2626;
        font-weight: 700;
    }

    /* Result count */
    .result-count {
        background: #f8fafc;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        padding: 12px 16px;
        margin: 15px 0 20px 0;
        color: #374151;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #9ca3af;
        font-size: 12px;
        padding: 25px 0 10px 0;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# LOAD DATASET
# =========================================================

data = pd.read_csv("final_bank_recommendation_data.csv")


# =========================================================
# HEADER
# =========================================================

st.markdown("""
<div class="main-header">

    <div class="main-title">
        🏦 Bank Branch Recommendation System
    </div>

    <div class="main-subtitle">
        Find suitable bank branches based on your location and preferences.
    </div>

</div>
""", unsafe_allow_html=True)


# =========================================================
# SESSION STATE
# =========================================================

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "current_latitude" not in st.session_state:
    st.session_state.current_latitude = None

if "current_longitude" not in st.session_state:
    st.session_state.current_longitude = None


# =========================================================
# CUSTOMER LOCATION
# =========================================================

st.markdown(
    '<div class="section-title">📍 Customer Location</div>',
    unsafe_allow_html=True
)

location_option = st.radio(
    "Choose your location method",
    [
        "Use My Current Location",
        "Enter Coordinates"
    ],
    horizontal=True
)


# =========================================================
# CURRENT LOCATION
# =========================================================

if location_option == "Use My Current Location":

    st.info(
        "Allow location access in your browser to automatically detect your current location."
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

            st.success(
                "Your current location was detected."
            )


# =========================================================
# ENTER COORDINATES
# =========================================================

else:

    col1, col2 = st.columns(2)

    with col1:

        latitude_input = st.text_input(
            "Latitude",
            placeholder="Example: 13.0827"
        )

    with col2:

        longitude_input = st.text_input(
            "Longitude",
            placeholder="Example: 80.2707"
        )


# =========================================================
# BANK PREFERENCES
# =========================================================

st.markdown(
    '<div class="section-title">🏦 Bank Preferences</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    bank_preference = st.selectbox(
        "Bank Preference",
        ["Any", "Public", "Private"]
    )

with col2:

    max_distance = st.text_input(
        "Maximum Distance (km)",
        value="10"
    )


# =========================================================
# FIND BANKS BUTTON
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)

if st.button(
    "🔎 Find Recommended Banks",
    use_container_width=True
):

    st.session_state.show_results = True


# =========================================================
# RECOMMENDATION PROCESS
# =========================================================

if st.session_state.show_results:

    latitude = None
    longitude = None


    # =====================================================
    # USE CURRENT LOCATION
    # =====================================================

    if location_option == "Use My Current Location":

        latitude = st.session_state.current_latitude
        longitude = st.session_state.current_longitude

        if latitude is None or longitude is None:

            st.error(
                "Please allow location access first."
            )

            st.stop()


    # =====================================================
    # USE ENTERED COORDINATES
    # =====================================================

    else:

        if latitude_input.strip() == "":

            st.error(
                "Please enter your latitude."
            )

            st.stop()


        if longitude_input.strip() == "":

            st.error(
                "Please enter your longitude."
            )

            st.stop()


        try:

            latitude = float(latitude_input)
            longitude = float(longitude_input)

        except ValueError:

            st.error(
                "Please enter valid latitude and longitude values."
            )

            st.stop()


        # Validate latitude

        if latitude < -90 or latitude > 90:

            st.error(
                "Latitude must be between -90 and 90."
            )

            st.stop()


        # Validate longitude

        if longitude < -180 or longitude > 180:

            st.error(
                "Longitude must be between -180 and 180."
            )

            st.stop()


    # =====================================================
    # VALIDATE MAXIMUM DISTANCE
    # =====================================================

    try:

        max_distance = float(max_distance)

    except ValueError:

        st.error(
            "Please enter a valid maximum distance."
        )

        st.stop()


    if max_distance <= 0:

        st.error(
            "Maximum distance must be greater than 0."
        )

        st.stop()


    # =====================================================
    # CALCULATE DISTANCE
    # =====================================================

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


    # =====================================================
    # APPLY BANK PREFERENCE
    # =====================================================

    if bank_preference == "Public":

        data = data[
            data["bank_group"] == "Public Sector Banks"
        ]


    elif bank_preference == "Private":

        data = data[
            data["bank_group"] == "Private Sector Banks"
        ]


    # =====================================================
    # APPLY MAXIMUM DISTANCE
    # =====================================================

    data = data[
        data["customer_distance_km"] <= max_distance
    ].copy()


    # =====================================================
    # RECOMMENDATION SCORE
    # =====================================================

    data["distance_score"] = (
        1 / (1 + data["customer_distance_km"])
    )

    data["recommendation_score"] = (
        data["suitability_score"] * 0.7
        + data["distance_score"] * 30
    )


    # =====================================================
    # SORT RECOMMENDATIONS
    # =====================================================

    recommendations = data.sort_values(
        "recommendation_score",
        ascending=False
    )


    # =====================================================
    # RESULTS HEADER
    # =====================================================

    st.markdown(
        '<div class="section-title">✨ Recommended Bank Branches</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="result-count">
            <b>{len(recommendations)}</b> branches found
            within <b>{max_distance} km</b>
        </div>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # NO RESULTS
    # =====================================================

    if len(recommendations) == 0:

        st.warning(
            "No bank branches found within the selected distance."
        )


    # =====================================================
    # RECOMMENDATION CARDS
    # =====================================================

    for index, (_, row) in enumerate(
        recommendations.head(10).iterrows(),
        start=1
    ):

        st.markdown(
            '<div class="bank-card">',
            unsafe_allow_html=True
        )

        # Bank header

        st.markdown(
            f"""
            <div class="bank-name">
                {index}. {row["bank"]}
            </div>

            <div class="branch-name">
                {row["branch"]}
            </div>

            <div class="bank-type">
                {row["bank_group"]}
            </div>
            """,
            unsafe_allow_html=True
        )


        # Main metrics

        col1, col2, col3 = st.columns(3)

        with col1:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">Distance</div>
                    <div class="metric-value">
                        {row["customer_distance_km"]:.2f} km
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            suitability = row["suitability"]

            if suitability == "High":
                suitability_class = "suitability-high"

            elif suitability == "Medium":
                suitability_class = "suitability-medium"

            else:
                suitability_class = "suitability-low"

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">Suitability</div>
                    <div class="metric-value {suitability_class}">
                        {suitability}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">Suitability Score</div>
                    <div class="metric-value">
                        {row["suitability_score"]:.2f}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        # Accessibility metrics

        st.markdown(
            "<br>",
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">🚌 Nearest Bus Stop</div>
                    <div class="metric-value">
                        {row["nearest_bus_km"]:.2f} km
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">🚆 Nearest Railway</div>
                    <div class="metric-value">
                        {row["nearest_railway_km"]:.2f} km
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">🚇 Nearest Metro</div>
                    <div class="metric-value">
                        {row["nearest_metro_km"]:.2f} km
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col4:

            st.markdown(
                f"""
                <div class="metric-box">
                    <div class="metric-label">🏦 Nearby Branches</div>
                    <div class="metric-value">
                        {int(row["nearby_branch_count"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


        # Road accessibility

        st.markdown(
            f"""
            <div class="metric-box">
                <div class="metric-label">🛣️ Nearest Major Road</div>
                <div class="metric-value">
                    {row["nearest_major_road_km"]:.2f} km
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )


    # =====================================================
    # BRANCH LOCATION MAP
    # =====================================================

    if len(recommendations) > 0:

        st.markdown(
            '<div class="section-title">🗺️ Branch Location Map</div>',
            unsafe_allow_html=True
        )

        branch_map = folium.Map(
            location=[
                latitude,
                longitude
            ],
            zoom_start=12
        )


        # =================================================
        # CUSTOMER MARKER
        # =================================================

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


        # =================================================
        # RECOMMENDED BRANCH MARKERS
        # =================================================

        for _, row in recommendations.head(10).iterrows():

            popup_text = f"""
            <b>{row['bank']}</b><br>
            Branch: {row['branch']}<br>
            Bank Type: {row['bank_group']}<br>
            Distance: {row['customer_distance_km']:.2f} km<br>
            Suitability: {row['suitability']}<br>
            Suitability Score: {row['suitability_score']:.2f}<br>
            Nearest Major Road: {row['nearest_major_road_km']:.2f} km
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


        # =================================================
        # DISPLAY MAP
        # =================================================

        st_folium(
            branch_map,
            width=900,
            height=600
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        Map data © OpenStreetMap contributors.
    </div>
    """,
    unsafe_allow_html=True
)
