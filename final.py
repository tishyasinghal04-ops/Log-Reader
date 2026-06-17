import streamlit as st     
import json
import os
from datetime import datetime
import pandas as pd

# Testing

#========== STYLING THE PAGE ==========
st.set_page_config(
    page_title="Log Reader",
    layout="wide"
)


#========== CONFIG A FILE ==========
with open("config.json", "r") as file:
    config = json.load(file)

folder_path = config["default_folder"]
ROWS_PER_PAGE = config["ROWS_PER_PAGE"]


#========== DATE FROM & DATE TO ==========
st.markdown("""
<style>
div[data-testid="stDateInput"] {
    width: 150px !important;
}
</style>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    date_from = st.date_input("DATE FROM")
with col2:
    date_to = st.date_input("DATE TO")


#========== SELECT A FOLDER ==========
st.markdown("""
<style>
div[data-testid="stMultiSelect"] {
    width: 150px !important;
}
</style>
""", unsafe_allow_html=True)

def get_folders(folder_path):
    folders =[]
    
    for item in os.listdir(folder_path):
        if os.path.isdir(os.path.join(folder_path,item)):
            folders.append(item)
    return folders
# folder_path = r"D:\NavigaLog"
folders = get_folders(folder_path)


#========== STYLING TYPE ==========
st.markdown("""
<style>
div[data-testid="stMultiSelect"] {
    width: 150px !important;
}
</style>
""", unsafe_allow_html=True)


#========== TYPE FILTER ==========
type_options = ["Error", "Info", "Warn"]


#========== ADDING OPTION "ALL"  ==========
col1, col2 = st.columns(2)
with col1:
    selected_folder = st.multiselect(
        "Select Folder",
        options=["All"] + folders,
        default=["All"]
    )
with col2:
    selected_types = st.multiselect(
        "Type",
        options=["All"] + type_options,
        default=["All"]
    )


#========== HANDLE "ALL" SELECTION ==========
if "All" in selected_folder:
    folders_to_search = folders
else:
    folders_to_search = selected_folder
if "All" in selected_types:
    types_to_search = []  # empty list means no type filtering
else:
    types_to_search = selected_types


#========== SEARCH SECTION ==========
if st.button("🔍 Search"):

    if not selected_folder:
        st.warning("Please select at least one folder.")

    else:

        results = []

        for folder in folders_to_search:        #ALL SECTION (selcted_folders=> Folders_to_search)=

            folder_full_path = os.path.join(folder_path, folder)

            for root, dirs, files in os.walk(folder_full_path):

                for file in files:

                    if ".log" in file.lower():

                        file_path = os.path.join(root, file)

                        try:

                            with open(
                                file_path,
                                "r",
                                encoding="utf-8",
                                errors="ignore"
                            ) as f:

                                for line in f:

                                    # TYPE FILTER
                                    if types_to_search:  #ALL SECTION (selected_types=>types_to_search)

                                        match_found = False

                                        for log_type in types_to_search:  #ALL SECTION (selected_types=>types_to_search)

                                            if f"| {log_type.upper()} |" in line.upper():
                                                match_found = True
                                                break

                                        if not match_found:
                                            continue

                                    parts = [x.strip() for x in line.split("|")]

                                    if len(parts) >= 6:

                                        try:
                                            log_date = datetime.strptime(
                                                parts[0][:8],
                                                "%Y%m%d"
                                            ).date()
                                            if date_from > date_to:
                                                st.error("Invalid date range!")
                                                st.stop()

                                            # DATE FILTER
                                            if (
                                                log_date < date_from
                                                or
                                                log_date > date_to
                                            ):
                                                continue

                                        except:
                                            continue

                                        results.append([
                                            parts[0],  # Timestamp
                                            parts[1],  # Log Type
                                            os.path.basename(root),  # Source
                                            parts[3],  # Session
                                            parts[4],  # Method
                                            parts[5][:100]  # Details (shortened)
                                        ])

                        except Exception as e:
                            st.error(f"Error reading {file}: {e}")

        if results:

            df = pd.DataFrame(
                results,
                columns=[
                    "DATE",
                    "Log Type",
                    "Source",
                    "Session",
                    "Method",
                    "Details"
                ]
            )

           # Save DataFrame
            st.session_state["result_df"] = df

            # Reset page when new search is performed
            st.session_state.page = 1

        else:
            st.warning("No matching logs found.")  


# ================= DASHBOARD =================

if "result_df" in st.session_state:

    df = st.session_state["result_df"]

    total_logs = len(df)
    total_error = len(df[df["Log Type"].str.upper() == "ERROR"])
    total_warn = len(df[df["Log Type"].str.upper() == "WARN"])
    total_info = len(df[df["Log Type"].str.upper() == "INFO"])

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("📄 Total Logs", total_logs)
    col2.metric("ℹ️ Info", total_info)
    col3.metric("⚠️ Warnings", total_warn)
    col4.metric("❌ Errors", total_error)

   #==== PAGINATION ====
    # ROWS_PER_PAGE = 20
    total_pages = max(
        1,
        (len(df) + ROWS_PER_PAGE - 1) // ROWS_PER_PAGE
    )

    if "page" not in st.session_state:
        st.session_state.page = 1

    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        if st.button("⬅ Previous"):
            if st.session_state.page > 1:
                st.session_state.page -= 1

    with col3:
        if st.button("Next ➡"):
            if st.session_state.page < total_pages:
                st.session_state.page += 1

    with col2:
        st.markdown(
            f"<center><h4>Page {st.session_state.page} of {total_pages}</h4></center>",
            unsafe_allow_html=True
        )

    start_idx = (st.session_state.page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE

    page_df = df.iloc[start_idx:end_idx]

    st.dataframe(
        page_df,
        use_container_width=True,
        hide_index=True
    )

    st.success(f"{len(df)} records found")


            

