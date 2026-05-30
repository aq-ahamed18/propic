import os
import streamlit as st
import folium
from streamlit_folium import st_folium
from img_prop_handler import save_uploaded_image, PropertyImage
from ai_locationAPI import LocationAPI

class ValuationForm:
    def render(self) -> dict:
        fields = {}

        st.markdown(
            "<p style='color:#6b7280; font-size: 15px; margin-top: -10px; margin-bottom: 20px;'>"
            "Complete the four tabs below to compile your professional property valuation report."
            "</p>",
            unsafe_allow_html=True
        )

        # Reorganizing form inputs into neat tabs for a premium, compact user experience
        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Step 1: General & Client Info",
            "🏗️ Step 2: Property & Site Profile",
            "💰 Step 3: Financials & Methodology",
            "📷 Step 4: Property Images"
        ])

        with tab1:
            st.markdown("#### 📋 General Administration Details")
            col1, col2 = st.columns(2)
            with col1:
                fields["a) Identification and status of the valuer"] = st.text_input(
                    "Valuer Name & Status",
                    placeholder="e.g., John Doe, B.Sc. (EMV) Hons, AIV (SL)",
                    help="Enter the valuer's full name, academic/professional credentials, and licensing status."
                )
                fields["c) Purpose of the valuation"] = st.text_area(
                    "Purpose of Valuation",
                    placeholder="e.g., Mortgage securing, insurance assessment, transfer of ownership, or court proceedings.",
                    help="Define clearly why this valuation report is being prepared."
                )
                fields["e) Basis of value adopted"] = st.text_input(
                    "Basis of Value Adopted",
                    value="Market Value (IVS 104)",
                    placeholder="e.g., Market Value, Forced Sale Value, or Replacement Cost.",
                    help="Specify the standard definition of value being used (usually IVS 104 Market Value)."
                )
            with col2:
                fields["b) Client details"] = st.text_input(
                    "Client Identification & Intended Users",
                    placeholder="e.g., People's Bank, Head Office / Mr. K. Silva",
                    help="Identify the client who commissioned the report and any other intended users."
                )
                fields["d) Identification of the property"] = st.text_area(
                    "Property Description & Title Details",
                    placeholder="e.g., Lot A, Plan No. 1024, Assessment No. 45, Galle Road, Colombo 03. Deed No: 9876.",
                    help="State the legal identification of the asset, including title deed registration, assessment numbers, and land registrar details."
                )
                fields["f) Valuation date"] = st.date_input(
                    "Valuation Reference Date",
                    help="The effective date on which the property's value is assessed."
                )

        with tab2:
            st.markdown("#### 🏗️ Property Site Profile & Location Details")
            col3, col4 = st.columns(2)
            with col3:
                fields["g) Nature of the property"] = st.text_area(
                    "Nature & Tenure of Property",
                    placeholder="e.g., Freehold interest in a 2-story residential dwelling with a landscaped garden.",
                    help="Describe whether the property is freehold/leasehold and its general occupancy state."
                )
            with col4:
                fields["h) Site profile"] = st.text_area(
                    "Site & Ground Profile (Land/Building)",
                    placeholder="e.g., Rectangular, flat terrain, solid red soil, boundaries demarcated by brick walls. Floor area: 2,500 sq.ft.",
                    help="Describe the physical characteristics of the land, shape, size, topography, and structural components of any buildings."
                )

            st.markdown("---")
            # Select property structural parts
            selected_parts = self._render_property_parts()
            fields["q) Selected Property Parts"] = selected_parts

            st.markdown("---")
            # Render GIS mapping
            location_data = self._render_location()
            if location_data and "lat" in location_data:
                fields["Location Address"] = location_data.get("address", "")
                fields["Latitude"]         = location_data.get("lat", "")
                fields["Longitude"]        = location_data.get("lon", "")

        with tab3:
            st.markdown("#### 💰 Financial Details & Valuation Approach")
            col5, col6 = st.columns(2)
            with col5:
                fields["i) Market value evidence"] = st.text_area(
                    "Evidence of Market Values",
                    placeholder="e.g., Comparable sale of Lot B (50m away) at LKR 2.5M per perch in Dec 2024.",
                    help="List recent comparable transactions, local listings, or cost index details supporting your valuation."
                )
                fields["k) Valuation approach"] = st.text_area(
                    "Valuation Approach & Survey Reasoning",
                    placeholder="e.g., Market Comparison Approach adopted due to active sales registry. Land valued at LKR 2.5M/perch. Building valued using depreciated cost.",
                    help="Explain the surveyor's logic and the chosen valuation method (Cost, Income, or Market comparison)."
                )
                fields["l) Amount of valuation"] = st.text_input(
                    "Final Valuation Amount (LKR)",
                    placeholder="e.g., 42,500,000",
                    help="Enter the final assessed value of the property in Sri Lankan Rupees."
                )
            with col6:
                fields["j) Assumptions and reservations"] = st.text_area(
                    "Assumptions & Special Reservations",
                    placeholder="e.g., Assumed that the title is clear and marketable, and no structural defects exist in load-bearing walls.",
                    help="State any general assumptions or special reservations governing the valuation."
                )
                date_report = st.date_input(
                    "Date of Report Sign-off",
                    help="The date on which the valuation report is officially compiled and signed."
                )
                fields["m) Date of report"] = date_report
                fields["m) Date of the valuation report"] = date_report

        with tab4:
            st.markdown("#### 📷 Property Photographic Documentation")
            property_images = self._render_image_uploads(selected_parts)
            fields["r) Property Images"] = property_images

        # Progress indicator (visual layout improvement)
        st.markdown("---")
        self._render_progress(fields)
        return fields

    def _render_location(self) -> dict:
        st.markdown("#### 📍 Property Geolocation & GIS Map Pinning")
        st.markdown(
            "<span style='color:#6b7280; font-size:13.5px;'>Search and pin the property location on the live OpenStreetMap below to embed coordinates in the report.</span>",
            unsafe_allow_html=True
        )

        if "location_data" not in st.session_state:
            st.session_state.location_data = {}

        col_in1, col_in2 = st.columns([3, 1])
        with col_in1:
            search_input = st.text_input(
                "Search Location (Address, City, or Coordinates):",
                placeholder="e.g., University of Sri Jayewardenepura, Nugegoda",
                key="location_search_input",
                label_visibility="collapsed"
            )
        with col_in2:
            search_button = st.button("🔍 Pin Location", key="search_location", use_container_width=True)

        if search_button and search_input:
            with st.spinner("Locating..."):
                loc_result = LocationAPI.get_location(search_input)
                if loc_result:
                    if "error" in loc_result:
                        st.error(f"Error: {loc_result['error']}")
                        st.session_state.location_data = {}
                    else:
                        st.session_state.location_data = loc_result
                        st.success("Location pinpointed!")
                else:
                    st.error("Location not found. Please try a different query.")
                    st.session_state.location_data = {}

        if st.session_state.location_data and "lat" in st.session_state.location_data:
            lat = st.session_state.location_data["lat"]
            lon = st.session_state.location_data["lon"]
            
            # Print feedback
            st.success(f"📍 **Pin Location**: {st.session_state.location_data.get('address', '')}")
            
            # Map preview
            map_preview = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker(
                [lat, lon],
                popup=f"<a href='https://www.openstreetmap.org/?mlat={lat}&mlon={lon}&zoom=18' target='_blank'>Open Full Map</a>",
                tooltip="Click to open full map",
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(map_preview)
            
            st_folium(map_preview, width=700, height=350)
            st.caption(f"Coordinates pinned: Lat: {lat:.6f}, Lon: {lon:.6f}")
            st.info("✅ This geolocation map will be automatically rendered as a visual graphic in your generated PDF report.")

        return st.session_state.location_data

    def _render_property_parts(self) -> list[str]:
        st.markdown("#### 🏠 Inspected Structural Property Sections")
        st.markdown(
            "<span style='color:#6b7280; font-size:13.5px;'>Select all sections of the asset that were physically inspected. You will be able to upload photos for each section below.</span>",
            unsafe_allow_html=True
        )
        part_options = ["Living Room", "Bedroom", "Dining Room", "Open Veranda", "Other"]
        
        cols = st.columns(len(part_options))
        checked = {}
        for i, p in enumerate(part_options):
            with cols[i]:
                checked[p] = st.checkbox(p, key=f"part_check_{p}")
                
        other_text = st.text_input(
            "If 'Other' selected, please specify:", 
            placeholder="e.g., Kitchen, Garage, Garden",
            key="other_part_text"
        ) if checked.get("Other") else None

        selected = [p for p, v in checked.items() if v and p != "Other"]
        if other_text:
            selected.append(other_text)
        return selected

    def _render_image_uploads(self, selected_parts: list[str]) -> list[PropertyImage]:
        images: list[PropertyImage] = []
        os.makedirs("images", exist_ok=True)

        st.markdown("##### 📸 Upload Subject Cover Photo")
        main_img = st.file_uploader(
            "Upload primary property photograph (to be shown on cover page)",
            type=["jpg", "jpeg", "png"],
            key="main_img"
        )
        if main_img:
            path = "images/cover_property.jpg"
            save_uploaded_image(main_img, path)
            images.append(PropertyImage(part="Subject Property", path=path))
            st.image(path, caption="Primary Property Photograph (Cover Page preview)", width=350)

        if selected_parts:
            st.markdown("---")
            st.markdown("##### 📸 Upload Photos of Inspected Sections")
            for i, part in enumerate(selected_parts, start=1):
                img = st.file_uploader(
                    f"Upload photograph for section: {part}",
                    type=["jpg", "jpeg", "png"],
                    key=f"img_{part}_{i}"
                )
                if img:
                    path = f"images/property_image_{i}.jpg"
                    save_uploaded_image(img, path)
                    images.append(PropertyImage(part=part, path=path))
                    st.image(path, caption=f"Inspected section photo: {part}", width=350)
        else:
            st.info("💡 **Tip**: Select one or more inspected property sections in Step 2 to enable sub-section photo uploads here.")

        return images

    def _render_progress(self, fields: dict):
        # Calculate completion percent (excluding temporary list structures or helper keys)
        important_keys = [
            "a) Identification and status of the valuer",
            "b) Client details",
            "c) Purpose of the valuation",
            "d) Identification of the property",
            "e) Basis of value adopted",
            "f) Valuation date",
            "g) Nature of the property",
            "h) Site profile",
            "i) Market value evidence",
            "j) Assumptions and reservations",
            "k) Valuation approach",
            "l) Amount of valuation",
            "m) Date of report"
        ]
        
        filled = sum(1 for k in important_keys if fields.get(k))
        total  = len(important_keys)
        pct    = int((filled / total) * 100) if total > 0 else 0
        
        col_pr1, col_pr2 = st.columns([5, 1])
        with col_pr1:
            st.progress(pct / 100)
        with col_pr2:
            st.markdown(f"**{pct}% Complete**")
        st.caption("Draft Completion Progress (calculating essential fields)")