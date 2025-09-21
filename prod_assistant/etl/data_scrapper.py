import csv                     
import time                    
import re                      
import os                      
from bs4 import BeautifulSoup   
import undetected_chromedriver as uc  
from selenium.webdriver.common.by import By          
from selenium.webdriver.common.keys import Keys       
from selenium.webdriver.common.action_chains import ActionChains  

class FlipkartScraper:
    def __init__(self, output_dir="data"):
        """
        Initialise the scraper with an output directory.
        Creates the folder if it does not exist.
        """
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)  # Create output folder if needed

    def get_top_reviews(self, product_url, count=2):
        """
        Visit a product page and scrape up to `count` customer reviews.
        """
        # Launch Chrome in undetected mode with options to reduce detection
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-blink-features=AutomationControlled")
        driver = uc.Chrome(options=options, use_subprocess=True)

        # Validate the product URL
        if not product_url.startswith("http"):
            driver.quit()                    # Close browser if URL invalid
            return "No reviews found"

        try:
            driver.get(product_url)           # Open the product page
            time.sleep(4)                     # Wait for page to load fully

            # Try to close the login/sign-up popup if it appears
            try:
                driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
                time.sleep(1)
            except Exception as e:
                print(f"Error occurred while closing popup: {e}")

            # Scroll down multiple times to ensure reviews are loaded
            for _ in range(4):
                ActionChains(driver).send_keys(Keys.END).perform()
                time.sleep(1.5)

            # Parse the page source with BeautifulSoup
            soup = BeautifulSoup(driver.page_source, "html.parser")

            # Review containers – Flipkart uses any of these classes for review text
            review_blocks = soup.select("div._27M-vq, div.col.EPCmJX, div._6K-7Co")

            seen = set()      # To avoid duplicate reviews
            reviews = []      # Collected reviews

            # Loop through each review block and extract clean text
            for block in review_blocks:
                text = block.get_text(separator=" ", strip=True)
                if text and text not in seen:
                    reviews.append(text)
                    seen.add(text)
                if len(reviews) >= count:     # Stop if we already have required number
                    break
        except Exception:
            reviews = []      # In case of any error, return empty list

        driver.quit()         # Close the browser session
        # Return reviews joined by ' || ' or message if none found
        return " || ".join(reviews) if reviews else "No reviews found"
    
    def scrape_flipkart_products(self, query, max_products=1, review_count=2):
        """
        Search Flipkart for the given `query`,
        scrape up to `max_products` items and their top `review_count` reviews.
        """
        options = uc.ChromeOptions()                       # Setup Chrome options
        driver = uc.Chrome(options=options, use_subprocess=True)
        # Construct search URL by replacing spaces with '+'
        search_url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
        driver.get(search_url)                             # Open the search results page
        time.sleep(4)                                      # Let results load

        # Close the login popup if present
        try:
            driver.find_element(By.XPATH, "//button[contains(text(), '✕')]").click()
        except Exception as e:
            print(f"Error occurred while closing popup: {e}")

        time.sleep(2)                                      # Extra wait to stabilize page
        products = []                                      # Will hold scraped product data

        # Find product cards (each has data-id attribute)
        items = driver.find_elements(By.CSS_SELECTOR, "div[data-id]")[:max_products]

        # Loop through each product card
        for item in items:
            try:
                # Extract key product details
                title = item.find_element(By.CSS_SELECTOR, "div.KzDlHZ").text.strip()
                price = item.find_element(By.CSS_SELECTOR, "div.Nx9bqj").text.strip()
                rating = item.find_element(By.CSS_SELECTOR, "div.XQDdHH").text.strip()
                reviews_text = item.find_element(By.CSS_SELECTOR, "span.Wphh3N").text.strip()

                # Use regex to extract total number of reviews (digits before the word 'Reviews')
                match = re.search(r"\d+(,\d+)?(?=\s+Reviews)", reviews_text)
                total_reviews = match.group(0) if match else "N/A"
                
                # Extract product page link and product ID
                link_el = item.find_element(By.CSS_SELECTOR, "a[href*='/p/']")
                href = link_el.get_attribute("href")
                product_link = href if href.startswith("http") else "https://www.flipkart.com" + href
                match = re.findall(r"/p/(itm[0-9A-Za-z]+)", href)
                product_id = match[0] if match else "N/A"
            except Exception as e:
                # If any detail is missing, skip this product
                print(f"Error occurred while processing item: {e}")
                continue

            # Fetch the top reviews for the product page
            top_reviews = self.get_top_reviews(product_link, count=review_count) \
                        if "flipkart.com" in product_link else "Invalid product URL"

            # Add all scraped details to the list
            products.append([product_id, title, rating, total_reviews, price, top_reviews])

        driver.quit()    # Close the search results browser session
        return products  # Return list of product info + reviews
    
    def save_to_csv(self, data, filename="product_reviews.csv"):
        """
        Save the scraped product data to a CSV file.
        Handles absolute paths, subfolders, or plain filenames.
        """
        if os.path.isabs(filename):
            path = filename                                 # Absolute path given
        elif os.path.dirname(filename):                     # e.g. 'data/products.csv'
            path = filename
            os.makedirs(os.path.dirname(path), exist_ok=True)
        else:                                               # Plain filename -> put inside output_dir
            path = os.path.join(self.output_dir, filename)

        # Write CSV with UTF-8 encoding
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            # Header row
            writer.writerow(["product_id", "product_title", "rating","total_reviews", "price", "top_reviews"])
            # Product data rows
            writer.writerows(data)

# ------------------------- Example usage -------------------------
if __name__ == "__main__":
    scraper = FlipkartScraper(output_dir="data")            # Create scraper with output folder

    # Scrape first product for query 'iphone 15' and get top 2 reviews
    products = scraper.scrape_flipkart_products(query="iphone 14", max_products=1, review_count=2)

    # Print each product's scraped information to console
    for p in products:
        print(p)

    # Save the scraped results to CSV file inside 'data' folder
    scraper.save_to_csv(products, filename="data/product_reviews.csv")
