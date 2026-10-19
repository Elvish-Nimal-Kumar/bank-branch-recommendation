import streamlit as st
import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import haversine_distances
from streamlit_js_eval import get_geolocation

import folium
from streamlit_folium import st_folium


# -----------------------------------
# PAGE CONFIGURATION
# -----------------------------------

st.set_page_config(
    page_title="Bank Branch Recommendation System",
    page_icon="🏦",
    layout="wide"
)


# -----------------------------------
# LOAD DATASET
# -----------------------------------

data = pd.read_csv("final_bank_recommendation_data.csv")


# -----------------------------------
# PAGE STYLING
# -----------------------------------

st.markdown("""
<style>
    .stApp {
        background-color: #F5F8FC;
    }

    h1 {
        color: #173B67;
        letter-spacing: -0.5px;
    }

    h2, h3 {
        color: #244A73;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border: 1px solid #DCE7F3;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(28, 67, 110, 0.05);
    }

    div.stButton > button {
        background-color: #246BCE;
        color: white;
        border: 1px solid #246BCE;
        border-radius: 9px;
        font-weight: 600;
        padding: 0.55rem 1rem;
    }

    div.stButton > button:hover {
        background-color: #174F9E;
        border-color: #174F9E;
        color: white;
    }

    div[data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #DCE7F3;
        padding: 16px;
        border-radius: 12px;
    }

    div[data-testid="stExpander"] {
        border: 1px solid #DCE7F3;
        border-radius: 10px;
        background-color: #FFFFFF;
    }

    div[data-testid="stAlert"] {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------
# SESSION STATE
# -----------------------------------

if "show_results" not in st.session_state:
    st.session_state.show_results = False

if "current_latitude" not in st.session_state:
    st.session_state.current_latitude = None

if "current_longitude" not in st.session_state:
    st.session_state.current_longitude = None


# -----------------------------------
# PAGE TITLE
# -----------------------------------

st.title("🏦 Bank Branch Recommendation System")

st.write(
    "Find suitable bank branches based on your location and preferences."
)

st.divider()


# -----------------------------------
# CUSTOMER LOCATION
# -----------------------------------

st.subheader("📍 Customer Location")

location_option = st.radio(
    "Choose your location method",
    [
        "Use My Current Location",
        "Enter Coordinates"
    ],
    horizontal=True
)

latitude_input = ""
longitude_input = ""


# -----------------------------------
# CURRENT LOCATION
# -----------------------------------

if location_option == "Use My Current Location":

    st.info(
        "Allow location access in your browser to find nearby bank branches."
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

            st.success("Your current location was detected.")

else:

    location_col1, location_col2 = st.columns(2)

    with location_col1:
        latitude_input = st.text_input(
            "Latitude",
            placeholder="Example: 13.0827"
        )

    with location_col2:
        longitude_input = st.text_input(
            "Longitude",
            placeholder="Example: 80.2707"
        )


st.divider()


# -----------------------------------
# BANK PREFERENCES
# -----------------------------------

st.subheader("⚙️ Bank Preferences")

preference_col1, preference_col2 = st.columns(2)

with preference_col1:

    bank_preference = st.selectbox(
        "Bank Preference",
        ["Any", "Public", "Private"]
    )

with preference_col2:

    max_distance = st.number_input(
        "Maximum Distance (km)",
        min_value=1.0,
        max_value=500.0,
        value=10.0,
        step=1.0
    )


# -----------------------------------
# FIND BANKS BUTTON
# -----------------------------------

if st.button(
    "🔍 Find Recommended Banks",
    use_container_width=True
):
    st.session_state.show_results = True


# -----------------------------------
# RECOMMENDATION PROCESS
# -----------------------------------

if st.session_state.show_results:

    latitude = None
    longitude = None

    # -----------------------------------
    # GET CUSTOMER LOCATION
    # -----------------------------------

    if location_option == "Use My Current Location":

        latitude = st.session_state.current_latitude
        longitude = st.session_state.current_longitude

        if latitude is None or longitude is None:

            st.error(
                "Please allow location access first."
            )

            st.stop()

    else:

        if not latitude_input.strip():

            st.error("Please enter your latitude.")
            st.stop()

        if not longitude_input.strip():

            st.error("Please enter your longitude.")
            st.stop()

        try:

            latitude = float(latitude_input)
            longitude = float(longitude_input)

        except ValueError:

            st.error(
                "Please enter valid latitude and longitude values."
            )

            st.stop()

        if not -90 <= latitude <= 90:

            st.error(
                "Latitude must be between -90 and 90."
            )

            st.stop()

        if not -180 <= longitude <= 180:

            st.error(
                "Longitude must be between -180 and 180."
            )

            st.stop()

    # -----------------------------------
    # CALCULATE DISTANCES
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

    # Keep the original dataset unchanged
    filtered_data = data.copy()

    filtered_data["customer_distance_km"] = distances[0]

    # -----------------------------------
    # APPLY BANK PREFERENCE
    # -----------------------------------

    if bank_preference == "Public":

        filtered_data = filtered_data[
            filtered_data["bank_group"] == "Public Sector Banks"
        ]

    elif bank_preference == "Private":

        filtered_data = filtered_data[
            filtered_data["bank_group"] == "Private Sector Banks"
        ]

    # -----------------------------------
    # APPLY DISTANCE FILTER
    # -----------------------------------

    filtered_data = filtered_data[
        filtered_data["customer_distance_km"] <= max_distance
    ].copy()

    # -----------------------------------
    # CALCULATE RECOMMENDATION SCORE
    # Used internally for ranking
    # -----------------------------------

    filtered_data["distance_score"] = (
        1 / (1 + filtered_data["customer_distance_km"])
    )

    filtered_data["recommendation_score"] = (
        filtered_data["suitability_score"] * 0.7
        + filtered_data["distance_score"] * 30
    )

    # -----------------------------------
    # SORT RECOMMENDATIONS
    # -----------------------------------

    recommendations = filtered_data.sort_values(
        "recommendation_score",
        ascending=False
    )

    # -----------------------------------
    # RESULTS HEADING
    # -----------------------------------

    st.divider()
    st.subheader("🏦 Recommended Bank Branches")

    st.caption(
        f"{len(recommendations)} branches found within "
        f"{max_distance:.1f} km"
    )

    # -----------------------------------
    # NO RESULTS
    # -----------------------------------

    if recommendations.empty:

        st.warning(
            "No bank branches found within the selected distance. "
            "Try increasing the distance or changing your bank preference."
        )

        st.stop()

    # -----------------------------------
    # SUMMARY METRICS
    # -----------------------------------

    nearest_branch = recommendations.loc[
        recommendations["customer_distance_km"].idxmin()
    ]

    best_branch = recommendations.iloc[0]

    metric_col1, metric_col2, metric_col3 = st.columns(3)

    with metric_col1:
        st.metric(
            "Branches Found",
            len(recommendations)
        )

    with metric_col2:
        st.metric(
            "Nearest Branch",
            f"{nearest_branch['customer_distance_km']:.2f} km"
        )

    with metric_col3:
        st.metric(
            "Best Suitability",
            f"{best_branch['suitability_score']:.2f}"
        )

    st.divider()

    # -----------------------------------
    # BANK RECOMMENDATION CARDS
    # -----------------------------------

    for rank, (_, row) in enumerate(
        recommendations.head(10).iterrows(),
        start=1
    ):

        with st.container(border=True):

            st.markdown(
                f"""
<div style="color:#246BCE;font-size:12px;font-weight:700;
letter-spacing:0.8px;margin-bottom:8px;">
RECOMMENDATION #{rank}
</div>
""",
                unsafe_allow_html=True
            )

            st.subheader(f"🏦 {row['bank']}")

            st.caption(
                f"{row['branch']} · {row['bank_group']}"
            )

            # -----------------------------------
            # DISTANCE AND SUITABILITY CARDS
            # Important: HTML begins at column 1,
            # preventing Markdown from treating it as code.
            # -----------------------------------

            metric_col1, metric_col2 = st.columns(2)

            with metric_col1:

                st.markdown(
                    f"""
<div style="background-color:#EAF3FF;padding:14px;
border-radius:10px;border-left:4px solid #246BCE;">
<div style="color:#52677F;font-size:12px;">DISTANCE</div>
<div style="color:#173B67;font-size:22px;font-weight:700;">
{row['customer_distance_km']:.2f} km
</div>
</div>
""",
                    unsafe_allow_html=True
                )

            with metric_col2:

                st.markdown(
                    f"""
<div style="background-color:#EAF8F0;padding:14px;
border-radius:10px;border-left:4px solid #27A56B;">
<div style="color:#52677F;font-size:12px;">SUITABILITY SCORE</div>
<div style="color:#176B45;font-size:22px;font-weight:700;">
{row['suitability_score']:.2f}
</div>
</div>
""",
                    unsafe_allow_html=True
                )

            # -----------------------------------
            # BRANCH DETAILS
            # -----------------------------------

            with st.expander("View branch details"):

                st.write(
                    f"**Suitability:** {row['suitability']}"
                )

                st.write(
                    f"**Nearest Bus Stop:** "
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
    # BRANCH LOCATION MAP
    # -----------------------------------

    st.divider()
    st.subheader("📍 Branch Location Map")

    # OpenStreetMap does not require a Carto API key.
    branch_map = folium.Map(
        location=[latitude, longitude],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    # -----------------------------------
    # CUSTOMER MARKER
    # -----------------------------------

    folium.Marker(
        location=[latitude, longitude],
        popup="Your Current Location",
        tooltip="Your Location",
        icon=folium.Icon(
            color="red",
            icon="user"
        )
    ).add_to(branch_map)

    # -----------------------------------
    # BANK BRANCH MARKERS
    # -----------------------------------

    for _, row in recommendations.head(10).iterrows():

        popup_text = f"""
        <div style="width:220px;font-family:Arial,sans-serif;">
            <h4 style="color:#246BCE;">{row['bank']}</h4>
            <b>Branch:</b> {row['branch']}<br>
            <b>Bank Type:</b> {row['bank_group']}<br>
            <b>Distance:</b> {row['customer_distance_km']:.2f} km<br>
            <b>Suitability:</b> {row['suitability']}<br>
            <b>Suitability Score:</b> {row['suitability_score']:.2f}<br>
            <b>Nearest Major Road:</b> {row['nearest_major_road_km']:.2f} km
        </div>
        """

        folium.Marker(
            location=[
                row["lattitude"],
                row["longitude"]
            ],
            popup=folium.Popup(
                popup_text,
                max_width=300
            ),
            tooltip=f"{row['bank']} - {row['branch']}",
            icon=folium.Icon(
                color="blue",
                icon="home"
            )
        ).add_to(branch_map)

    # -----------------------------------
    # DISPLAY MAP
    # -----------------------------------

    st_folium(
        branch_map,
        width=None,
        height=550,
        use_container_width=True,
        key="bank_branch_map"
    )


# -----------------------------------
# FOOTER
# -----------------------------------

st.divider()

st.caption(
    "Map data © OpenStreetMap contributors."
)
