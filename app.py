import streamlit as st
import pandas as pd
import zipfile
import io

# Set the title of the web page
st.title("PHMSA DOT Annual Report Fetcher")

# Add a welcoming description
st.write("Welcome! This tool helps you find your client's specific data from the public PHMSA annual reports.")

# Create a text box for the user to type the OPID
opid_input = st.text_input("Enter the Operator Identification Number (OPID):")

# Provide instructions and a direct download link for the user
st.write("Because the government firewall blocks automated downloads, please click the link below to download the ZIP folder to your computer, then upload it here.")
st.markdown("[Click here to manually download the PHMSA ZIP file](https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/data_statistics/pipeline/PHMSA_Pipeline_Safety_Flagged_Incidents.zip)")

# Create a drag-and-drop file upload box
uploaded_file = st.file_uploader("Upload the downloaded ZIP folder here:", type=["zip"])

# Create a button to start the search
if st.button("Search Data"):
    # Check if the user filled in the box and uploaded the file
    if not opid_input:
        st.warning("Please enter an OPID to search for.")
    elif not uploaded_file:
        st.warning("Please upload the ZIP file.")
    else:
        st.info("Reading the uploaded folder...")
        
        try:
            # 1. Open the uploaded ZIP folder directly from the app
            with zipfile.ZipFile(uploaded_file) as z:
                # 2. Look for a spreadsheet or text file inside the folder
                data_filename = None
                for filename in z.namelist():
                    if filename.endswith('.csv') or filename.endswith('.txt'):
                        data_filename = filename
                        break
                
                if data_filename:
                    st.success(f"Successfully opened the folder and found the data file: {data_filename}")
                    
                    # 3. Read the data into a digital table
                    with z.open(data_filename) as f:
                        # Try to read it, automatically guessing the formatting
                        try:
                            df = pd.read_csv(f, sep=None, engine='python', dtype=str)
                        except Exception:
                            # If the first try fails, try a different common format
                            f.seek(0)
                            df = pd.read_csv(f, sep='\t', dtype=str)
                    
                    # 4. Look for the column that contains the Operator ID
                    opid_col = None
                    for col in df.columns:
                        # Government data columns vary, so we look for common names
                        if 'OPID' in col.upper() or 'OPERATOR_ID' in col.upper() or 'OPERATOR' in col.upper():
                            opid_col = col
                            break
                    
                    if opid_col:
                        # 5. Filter the table to only show rows matching the client's OPID
                        client_data = df[df[opid_col] == opid_input]
                        
                        if client_data.empty:
                            st.warning(f"No records were found for OPID: {opid_input}")
                        else:
                            st.success("Client data found!")
                            # Display the filtered data on the screen
                            st.dataframe(client_data)
                    else:
                        st.error("Could not find an OPID column in the data to filter by.")
                        st.write("Here is a preview of the raw data instead:")
                        st.dataframe(df.head())
                        
                else:
                    st.error("Could not find a usable data file (.csv or .txt) inside the uploaded ZIP folder.")
                    
        except Exception as e:
            # If anything goes wrong with the file, tell the user safely
            st.error(f"An error occurred while processing the file: {e}")