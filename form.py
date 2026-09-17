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
            "<p style='color:#475569; font-size: 14.5px; margin-top: -10px; margin-bottom: 22px; font-weight: 500;'>"
            "Complete the four survey appraisal steps below. All details will be compiled into your standardized valuation report."
            "</p>",
            unsafe_allow_html=True
        )

        tab1, tab2, tab3, tab4 = st.tabs([
            "📋 Step 1: General & Client Info",
            "🏗️ Step 2: Property & Site Profile",
            "💰 Step 3: Financials & Methodology",
            "📷 Step 4: Property Photographs"
        ])

        with tab1:
            st.markdown("#### 📋 General Administration Details")
            st.markdown("<p style='color:#64748B; font-size:13px;'>Enter valuer credentials, client particulars, and appraisal reference dates.</p>", unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                fields["a) Identification and status of the valuer"] = st.text_input(
                    "Valuer Name & Professional Status *",
                    placeholder="e.g., K.A. Perera, B.Sc. (EMV) Hons, AIV (SL)",
                    help="Full name, academic degrees, professional membership (AIV/FIV SL), and licensing status."
                )
                fields["c) Purpose of the valuation"] = st.text_area(
                    "Purpose of Valuation *",
                    placeholder="e.g., Mortgage security assessment for Bank loan facility, financial reporting, or asset transfer.",
                    help="Clearly state why this valuation report is being prepared."
                )
                fields["e) Basis of value adopted"] = st.text_input(
                    "Basis of Value Adopted *",
                    value="Market Value (IVS 104)",
                    placeholder="e.g., Market Value (IVS 104), Forced Sale Value, or Depreciated Replacement Cost.",
                    help="Specify the standard definition of value being adopted (usually IVS 104 Market Value)."
                )
            with col2:
                fields["b) Client details"] = st.text_input(
                    "Client Identification & Intended Users *",
                    placeholder="e.g., Commercial Bank of Ceylon PLC / Mr. S. Wickramasinghe",
                    help="Identify the client who commissioned the appraisal and any intended secondary users."
                )
                fields["d) Identification of the property"] = st.text_area(
                    "Property Description & Title Details *",
                    placeholder="e.g., Lot 1, Plan No. 4092, Assessment No. 128, High Level Road, Nugegoda. Title Deed No: 14520.",
                    help="State the complete legal description of the property, deed particulars, and assessment numbers."
                )
                fields["f) Valuation date"] = st.date_input(
                    "Effective Valuation Reference Date *",
                    help="The effective date on which the property's physical state and value are assessed."
                )

        with tab2:
            st.markdown("#### 🏗️ Property Site Profile & Location Details")
            st.markdown("<p style='color:#64748B; font-size:13px;'>Describe site terrain, building configuration, inspected structural sections, and pin location coordinates.</p>", unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            with col3:
                fields["g) Nature of the property"] = st.text_area(
                    "Nature & Tenure of Property",
                    placeholder="e.g., Unencumbered Freehold interest in a 2-story residential building with private access road.",
                    help="Describe whether the asset is freehold/leasehold and its operational occupancy status."
                )
            with col4:
                fields["h) Site profile"] = st.text_area(
                    "Site Terrain & Ground Profile",
                    placeholder="e.g., Rectangular shape, flat terrain, firm soil. Demarcated by brick boundary walls. Total floor area: 2,400 sq.ft.",
                    help="Describe physical site characteristics, topography, boundaries, and structural size."
                )

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            selected_parts = self._render_property_parts()
            fields["q) Selected Property Parts"] = selected_parts

            st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
            location_data = self._render_location()
            if location_data and "lat" in location_data:
                fields["Location Address"] = location_data.get("address", "")
                fields["Latitude"]         = location_data.get("lat", "")
                fields["Longitude"]        = location_data.get("lon", "")

        with tab3:
            st.markdown("#### 💰 Financial Details & Valuation Approach")
            st.markdown("<p style='color:#64748B; font-size:13px;'>Provide market transaction evidence, appraisal methodology, final valuation figure, and special reservations.</p>", unsafe_allow_html=True)
            
            col5, col6 = st.columns(2)
            with col5:
                fields["i) Market value evidence"] = st.text_area(
                    "Evidence of Market Values",
                    placeholder="e.g., Comparable sale of Lot 4 (100m distance) at LKR 3.2M per perch in Jan 2026. Building rate: LKR 8,500/sq.ft.",
                    help="Detail recent neighborhood transactions, registry records, or broker rate evidence."
                )
                fields["k) Valuation approach"] = st.text_area(
                    "Valuation Approach & Survey Logic",
                    placeholder="e.g., Direct Market Comparison Approach adopted for land value combined with Depreciated Replacement Cost method for main dwelling.",
                    help="Explain the surveyor's appraisal methodology and calculation reasoning."
                )
                fields["l) Amount of valuation"] = st.text_input(
                    "Final Assessed Market Value (LKR) *",
                    placeholder="e.g., 45,000,000",
                    help="Enter the final valuation amount in Sri Lankan Rupees."
                )
            with col6:
                fields["j) Assumptions and reservations"] = st.text_area(
                    "Assumptions & Special Reservations",
                    placeholder="e.g., Title assumed clear and marketable; valuation assumes no hidden structural or environmental defects exist.",
                    help="State any special assumptions or reservations governing the report."
                )
                date_report = st.date_input(
                    "Date of Report Sign-off *",
                    help="Official date on which the valuation report is signed and issued."
                )
                fields["m) Date of report"] = date_report
                fields["m) Date of the valuation report"] = date_report

        with tab4:
            st.markdown("#### 📷 Property Photographic Documentation")
            st.markdown("<p style='color:#64748B; font-size:13px;'>Upload property photographs. The system automatically detects image orientation and standardizes the layout in the generated PDF.</p>", unsafe_allow_html=True)
            
            property_images = self._render_image_uploads(selected_parts)
            fields["r) Property Images"] = property_images

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        self._render_progress(fields)
        return fields

    def _render_location(self) -> dict:
        st.markdown("##### 📍 Property Geolocation & Map Pinning")
        st.markdown(
            "<span style='color:#64748B; font-size:13px;'>Search address or pin location coordinates to automatically embed a OpenStreetMap map graphic in the PDF report.</span>",
            unsafe_allow_html=True
        )

        if "location_data" not in st.session_state:
            st.session_state.location_data = {}

        col_in1, col_in2 = st.columns([3.5, 1])
        with col_in1:
            search_input = st.text_input(
                "Search Location:",
                placeholder="e.g., University of Sri Jayewardenepura, Nugegoda",
                key="location_search_input",
                label_visibility="collapsed"
            )
        with col_in2:
            search_button = st.button("🔍 Search Pin", key="search_location", use_container_width=True)

        if search_button and search_input:
            with st.spinner("Locating map coordinates..."):
                loc_result = LocationAPI.get_location(search_input)
                if loc_result:
                    if "error" in loc_result:
                        st.error(f"Geocoding Error: {loc_result['error']}")
                        st.session_state.location_data = {}
                    else:
                        st.session_state.location_data = loc_result
                        st.success("Location coordinates successfully pinned!")
                else:
                    st.error("Location not found. Please refine search terms.")
                    st.session_state.location_data = {}

        if st.session_state.location_data and "lat" in st.session_state.location_data:
            lat = st.session_state.location_data["lat"]
            lon = st.session_state.location_data["lon"]
            address = st.session_state.location_data.get("address", "")
            
            st.markdown(
                f"<div style='background-color:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; padding:10px 14px; margin-bottom:12px; font-size:13.5px; color:#1E293B;'>"
                f"📍 <strong>Pinned Address</strong>: {address}<br>"
                f"🌐 <strong>Coordinates</strong>: Lat <code>{lat:.6f}</code> | Lon <code>{lon:.6f}</code>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            map_preview = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker(
                [lat, lon],
                popup=f"Subject Property: {address}",
                tooltip="Subject Property Location",
                icon=folium.Icon(color="red", icon="home"),
            ).add_to(map_preview)
            
            st_folium(map_preview, width=720, height=320)

        return st.session_state.location_data

    def _render_property_parts(self) -> list[str]:
        st.markdown("##### 🏠 Inspected Structural Property Sections")
        st.markdown(
            "<span style='color:#64748B; font-size:13px;'>Select all property sections that were physically audited. Photo upload slots will automatically unlock for selected sections.</span>",
            unsafe_allow_html=True
        )
        part_options = ["Living Room", "Bedroom", "Dining Room", "Open Veranda", "Other"]
        
        cols = st.columns(len(part_options))
        checked = {}
        for i, p in enumerate(part_options):
            with cols[i]:
                checked[p] = st.checkbox(p, key=f"part_check_{p}")
                
        other_text = st.text_input(
            "Specify 'Other' Section Name:", 
            placeholder="e.g., Kitchen, Master Bedroom, Balcony",
            key="other_part_text"
        ) if checked.get("Other") else None

        selected = [p for p, v in checked.items() if v and p != "Other"]
        if other_text and other_text.strip():
            selected.append(other_text.strip())
        return selected

    def _render_image_uploads(self, selected_parts: list[str]) -> list[PropertyImage]:
        images: list[PropertyImage] = []
        os.makedirs("images", exist_ok=True)

        st.markdown("##### 📸 Primary Cover Photograph")
        main_img = st.file_uploader(
            "Upload Primary Subject Property Photo (Cover Page Container)",
            type=["jpg", "jpeg", "png"],
            key="main_img"
        )
        if main_img:
            path = "images/cover_property.jpg"
            save_uploaded_image(main_img, path)
            prop_img = PropertyImage(part="Subject Property (Cover)", path=path)
            images.append(prop_img)
            
            info = prop_img.get_info()
            orient_badge = f"📐 Detected: {info['orientation'].upper()} ({info['width']}×{info['height']}px, Ratio: {info['aspect_ratio']})"
            st.info(f"✅ **Cover Photo Uploaded** | {orient_badge} -> Auto-fitted to standard cover container in PDF report.")
            st.image(path, width=380)

        if selected_parts:
            st.markdown("<hr style='margin:18px 0;'>", unsafe_allow_html=True)
            st.markdown("##### 📸 Audited Property Sections Photographs")
            for i, part in enumerate(selected_parts, start=1):
                img = st.file_uploader(
                    f"Upload Photograph for Section: {part}",
                    type=["jpg", "jpeg", "png"],
                    key=f"img_{part}_{i}"
                )
                if img:
                    path = f"images/property_image_{i}.jpg"
                    save_uploaded_image(img, path)
                    prop_img = PropertyImage(part=part, path=path)
                    images.append(prop_img)
                    
                    info = prop_img.get_info()
                    orient_badge = f"📐 Orientation: {info['orientation'].upper()} ({info['width']}×{info['height']}px)"
                    st.info(f"✅ **{part} Photo Uploaded** | {orient_badge} -> Auto-fitted to standard {info['orientation']} PDF container.")
                    st.image(path, width=350)
        else:
            st.info("💡 **Tip**: Check one or more inspected structural sections in Step 2 to enable photo uploads for each section here.")

        return images

    def _render_progress(self, fields: dict):
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
        
        st.markdown(
            f"<div style='background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 18px; margin-top: 10px;'>"
            f"<div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;'>"
            f"<span style='font-weight: 700; color: #1E293B; font-size: 13.5px;'>📊 Report Completion Progress ({filled}/{total} Parameters)</span>"
            f"<span style='background: linear-gradient(135deg, #7A0016 0%, #9B111E 100%); color: white; font-weight: 800; font-size: 12.5px; padding: 3px 12px; border-radius: 20px; box-shadow: 0 2px 6px rgba(122,0,22,0.2);'>{pct}% Completed</span>"
            f"</div>",
            unsafe_allow_html=True
        )
        st.progress(pct / 100)
        st.markdown(
            "<span style='color: #64748B; font-size: 12px;'>Standardized survey fields required for PDF compiling</span>"
            "</div>",
            unsafe_allow_html=True
        )