import streamlit as st
from prod_assistant.etl.data_scrapper import FlipkartScraper   # Import scraper class
from prod_assistant.etl.data_injection import DataIngestion #impoRT INGESTION class
import os

# Initialize the Flipkart scraper
flipkart_scraper = FlipkartScraper()

# Define path to save scraped data CSV
output_path = "data/product_reviews.csv"

# Set the title of the Streamlit app
st.title("📦 Product Review Scraper")

# Initialize session state for product inputs if not already present
if "product_inputs" not in st.session_state:
    st.session_state.product_inputs = [""]   # Start with one empty input field

# Function to add a new empty product input field
def add_product_input():
    st.session_state.product_inputs.append("")

# Subheader and text area for optional product description
st.subheader("📝 Optional Product Description")
product_description = st.text_area("Enter product description (used as an extra search keyword):")

# Subheader for product name inputs
st.subheader("🛒 Product Names")
updated_inputs = []
# Loop through all current product input fields and display them
for i, val in enumerate(st.session_state.product_inputs):
    input_val = st.text_input(f"Product {i+1}", value=val, key=f"product_{i}")
    updated_inputs.append(input_val)
st.session_state.product_inputs = updated_inputs  # Save updated inputs back to session

# Button to add another product input field dynamically
st.button("➕ Add Another Product", on_click=add_product_input)

# Number inputs to control how many products and reviews to scrape
max_products = st.number_input("How many products per search?", min_value=1, max_value=10, value=1)
review_count = st.number_input("How many reviews per product?", min_value=1, max_value=10, value=2)

# Button to start scraping
if st.button("🚀 Start Scraping"):
    # Clean and combine product inputs and optional description
    product_inputs = [p.strip() for p in st.session_state.product_inputs if p.strip()]
    if product_description.strip():
        product_inputs.append(product_description.strip())

    # Warn user if no input provided
    if not product_inputs:
        st.warning("⚠️ Please enter at least one product name or a product description.")
    else:
        final_data = []
        # Loop through each search query and scrape products
        for query in product_inputs:
            st.write(f"🔍 Searching for: {query}")   # Show which query is being processed
            results = flipkart_scraper.scrape_flipkart_products(
                query, max_products=max_products, review_count=review_count
            )
            final_data.extend(results)   # Add scraped results to final list

        # Remove duplicate products based on product title
        unique_products = {}
        for row in final_data:
            if row[1] not in unique_products:
                unique_products[row[1]] = row
        final_data = list(unique_products.values())

        # Save scraped data in session state for later use
        st.session_state["scraped_data"] = final_data
        # Save the scraped data to CSV
        flipkart_scraper.save_to_csv(final_data, output_path)
        st.success("✅ Data saved to `data/product_reviews.csv`")
        # Provide download button for the CSV file
        st.download_button(
            "📥 Download CSV",
            data=open(output_path, "rb"),
            file_name="product_reviews.csv"
        )

# Button to store data in AstraDB vector database (only available after scraping)
if "scraped_data" in st.session_state and st.button("🧠 Store in Vector DB (AstraDB)"):
    with st.spinner("📡 Initializing ingestion pipeline..."):  # Show spinner while processing
        try:
            ingestion = DataIngestion()         # Initialize data ingestion pipeline
            st.info("🚀 Running ingestion pipeline...")
            ingestion.run_pipeline()            # Transform CSV to documents and store in vector DB
            st.success("✅ Data successfully ingested to AstraDB!")
        except Exception as e:
            st.error("❌ Ingestion failed!")   # Show error if ingestion fails
            st.exception(e)                     # Display full exception traceback
