import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import json
import re
import urllib.parse

# Setup Chrome options for headless operation
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-gpu')

# Initialize the Chrome WebDriver with webdriver_manager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrapper(input_data):
    results = []
    try:
        driver.get(f'https://www.google.com/maps/search/{input_data}/')

        try:
            WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception as e:
            print(f"Error clicking on form: {e}")

        # Wait for page to load and find the scrollable div
        scrollable_div = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        driver.execute_script("""
            var scrollableDiv = arguments[0];
            function scrollWithinElement(scrollableDiv) {
                return new Promise((resolve, reject) => {
                    var totalHeight = 0;
                    var distance = 1000;
                    var scrollDelay = 3000;

                    var timer = setInterval(() => {
                        var scrollHeightBefore = scrollableDiv.scrollHeight;
                        scrollableDiv.scrollBy(0, distance);
                        totalHeight += distance;

                        if (totalHeight >= scrollHeightBefore) {
                            totalHeight = 0;
                            setTimeout(() => {
                                var scrollHeightAfter = scrollableDiv.scrollHeight;
                                if (scrollHeightAfter > scrollHeightBefore) {
                                    return;
                                } else {
                                    clearInterval(timer);
                                    resolve();
                                }
                            }, scrollDelay);
                        }
                    }, 200);
                });
            }
            return scrollWithinElement(scrollableDiv);
        """, scrollable_div)

        items = driver.find_elements(By.CSS_SELECTOR, 'div[role="feed"] > div > div[jsaction]')

        for item in items:
            data = {}
            try:
                data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
            except Exception as e:
                print(f"Title extraction error: {e}")

            try:
                text_content = item.text
                address_element = r'(?:\d+\s)?[A-Za-z0-9\s.,-]+,\s[A-Za-z\s]+(?:,\s[A-Z]{2}\s\d{5})?'
                matches = re.findall(address_element, text_content)
                unique_address = list(set(matches))
                data['address'] = unique_address[0] if unique_address else None
            except Exception as e:
                print(f"Address extraction error: {e}")

            try:
                phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
                matches = re.findall(phone_pattern, text_content)
                phone_numbers = [match[0] for match in matches]
                unique_phone_numbers = list(set(phone_numbers))
                data['phone'] = unique_phone_numbers[0] if unique_phone_numbers else None
            except Exception as e:
                print(f"Phone extraction error: {e}")

            if data.get('title'):
                results.append(data)

        # Convert results to JSON and CSV formats
        results_json = json.dumps(results, ensure_ascii=False, indent=2)
        df = pd.DataFrame(data=results)
        csv_data = df.to_csv(index=False)

        # Save to files
        with open('results.json', 'w', encoding='utf-8') as f:
            f.write(results_json)

        with open('map.csv', 'w', encoding='utf-8') as f:
            f.write(csv_data)

        return results_json, csv_data

    except Exception as e:
        print(f"Scraper error: {e}")
    finally:
        driver.quit()

def main():
    st.title('Google Map Scraper')
    query = st.text_input("Enter your search query: ")

    if st.button('Search'):
        results_json, csv_data = scrapper(query)

        if results_json and csv_data:
            st.success("Scraped data is available for download")

            # Provide download buttons for JSON and CSV files
            st.download_button(
                label="Download JSON",
                data=results_json,
                file_name="results.json",
                mime="application/json"
            )

            st.download_button(
                label="Download CSV",
                data=csv_data,
                file_name="map.csv",
                mime="text/csv"
            )
        else:
            st.error("No data found or an error occurred.")

if __name__ == '__main__':
    main()
