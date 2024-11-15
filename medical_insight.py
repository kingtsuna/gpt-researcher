import streamlit as st
from gpt_researcher import GPTResearcher
import asyncio
import requests
from bs4 import BeautifulSoup
from PIL import Image
import time

# Set a white background color and ensure all text and elements are visible
st.markdown(
    """
    <style>
    .stApp {
        background-color: white;
        color: black;
    }
    .stApp h1 {
        color: black;  /* Title color */
    }
    .stTextInput > div > input {
        background-color: white;
        color: black;
        border: 1px solid #333;  /* Dark border for input box */
    }
    .chatbox {
        background-color: rgba(245, 245, 245, 0.9);  /* Light gray for chat bubbles */
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
        color: black;  /* Ensure text is black within chatbox */
    }
    .header {
        color: black;
        font-size: 24px;
        font-weight: bold;
    }
    .stButton > button {
        color: black; /* Set button text color to black */
        background-color: white; /* Set button background to white */
        border: 1px solid black; /* Add a border for better visibility */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display a logo at the top of the app
# logo = Image.open("ernst-young-ey-logo.png")  # replace with your logo path
# st.image(logo, width=100)  # Adjust width as needed

# App title and input components
st.title("Medical Insights from Trusted Sources")

import urllib3

# Disable insecure request warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Function to extract URLs based on query from multiple sources
def get_sources(query="random", max_pages=5):
    # Define base URLs for PubMed and Google Patents
    pubmed_base_url = 'https://pubmed.ncbi.nlm.nih.gov'
    patents_base_url = 'https://patents.google.com'

    # Format query for URL encoding
    query = query.replace(" ", "+")
    sources = []

    # Fetch sources from PubMed
    for page_num in range(1, max_pages + 1):
        search_url = f'{pubmed_base_url}/?term={query}&page={page_num}'
        page = requests.get(search_url, verify=False)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        if "No results found" in soup.get_text():
            break

        query_words = set(query.split("+"))

        for link in soup.find_all('a', href=True):
            href = link['href']
            if (href.startswith(pubmed_base_url) or href.startswith('/')) and (
                any(word.lower() in href.lower() for word in query_words) or
                any(word.lower() in link.get_text().lower() for word in query_words)
            ):
                full_url = pubmed_base_url + href if href.startswith('/') else href
                sources.append(full_url)

        time.sleep(0.5)
    return sources

    # Fetch sources from Google Patents
    for page_num in range(1, max_pages + 1):
        search_url = f'{patents_base_url}/?q=({query})&page={page_num}'
        page = requests.get(search_url, verify=False)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        if "No results found" in soup.get_text():
            break

        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/patent/') or href.startswith(patents_base_url):
                full_url = patents_base_url + href if href.startswith('/') else href
                sources.append(full_url)

        time.sleep(0.5)

    # Remove duplicate URLs and return the combined list of sources
    return list(set(sources))
 


async def gpt_res(query, q_type=1):
    report_type = "research_report"
    report_source = "static"
    pdf_source = "local"
    sources = get_sources(query)
    # return sources
    
    if q_type == 0:
        researcher = GPTResearcher(query=query, report_type=report_type, config_path=None)
    if q_type == 1:
        researcher = GPTResearcher(query=query, report_source=report_source, source_urls=sources, report_type=report_type)
    if q_type == 2:
        researcher = GPTResearcher(query=query, report_source=pdf_source, report_type=report_type)
    
    await researcher.conduct_research()
    report = await researcher.write_report()
    
    return report

# Input box for user query
query = st.text_input("Ask Your Question", placeholder="Enter your medical query here...")
report = ''

# Options for query types
if st.button("Search on Untrusted Sources"):
    with st.spinner("Searching..."):
        report = asyncio.run(gpt_res(query, q_type=0))
if st.button("Search on Trusted Sources"):
    with st.spinner("Searching..."):
        report = asyncio.run(gpt_res(query, q_type=1))
if st.button("Scan Local (still working...)"):
    with st.spinner("Scanning..."):
        report = asyncio.run(gpt_res(query, q_type=2))

# Display the response in a styled box
if report:
    st.markdown(f"<div class='chatbox'>{report}</div>", unsafe_allow_html=True)
