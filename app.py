import streamlit as st
import pandas as pd
import requests
import zipfile
import io

# Set the title of the web page
st.title("PHMSA DOT Annual Report Fetcher")

# Add a welcoming description
st.write("Welcome! This tool helps you find your client's specific data from the public PHMSA annual reports.")

# Create a text box for the user to type the OPID
opid_input = st.text_input("Enter the Operator Identification Number (OPID):")

# Create a text box for the ZIP file URL 
st.write("Because the PHMSA website updates its files, please paste the direct link to the ZIP folder below.")
zip_url = st.text_input(
    "Enter the URL for the PHMSA ZIP file:",
    value="https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/data_statistics/pipeline/PHMSA_Pipeline_Safety_Flagged_Incidents.zip"
)

# Create a button to start the download and search
if st.button("Fetch and Search"):
    # Check if the user filled in the boxes
    if not opid_input:
        st.warning("Please enter an OPID to search for.")
    elif not zip_url:
        st.warning("Please enter the ZIP file URL.")
    else:
        # Let the user know the digital courier is working
        st.info("Downloading data... this might take a moment depending on the size of the folder.")
        
        try:
            # 1. Download the ZIP file from the internet (Added a User-Agent header to bypass security)
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(zip_url, headers=headers)
            response.raise_for_status() # Check if the download was successful
            
            # 2. Open the downloaded ZIP folder in memory
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # 3. Look for a spreadsheet or text file inside the folder
                data_filename = None
                for filename in z.namelist():
                    if filename.endswith('.csv') or filename.endswith('.txt'):
                        data_filename = filename
                        break
                
                if data_filename:
                    st.success(f"Successfully opened the folder and found the data file: {data_filename}")
                    
                    # 4. Read the data into a digital table
                    with z.open(data_filename) as f:
                        # Try to read it, automatically guessing the formatting
                        try:
                            df = pd.read_csv(f, sep=None, engine='python', dtype=str)
                        except Exception:
                            # If the first try fails, try a different common format
                            f.seek(0)
                            df = pd.read_csv(f, sep='\t', dtype=str)
                    
                    # 5. Look for the column that contains the Operator ID
                    opid_col = None
                    for col in df.columns:
                        # Government data columns vary, so we look for common names
                        if 'OPID' in col.upper() or 'OPERATOR_ID' in col.upper() or 'OPERATOR' in col.upper():
                            opid_col = col
                            break
                    
                    if opid_col:
                        # 6. Filter the table to only show rows matching the client's OPID
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
                    st.error("Could not find a usable data file (.csv or .txt) inside the downloaded ZIP folder.")
                    
        except Exception as e:
            # If anything goes wrong (like a bad link), tell the user safely
            st.error(f"An error occurred while fetching or processing the data: {e}")