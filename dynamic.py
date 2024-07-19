from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from webdriver_manager.chrome import ChromeDriverManager
import time
import json
import re
import urllib.parse
import pandas as pd
import streamlit as st
chrome_options = webdriver.ChromeOptions()

# service = Service(
#   ChromeDriverManager().install()
# )

driver = webdriver.Chrome(
  options=chrome_options
)

def scrapper(input_data):  # corrected function name and parameter name
    try: 
        # query = input("Enter your search query: ")
        # encoded_query = urllib.parse.quote_plus(query)

        driver.get(f'https://www.google.com/maps/search/{input_data}/')

        try:
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, "form:nth-child(2)"))).click()
        except Exception:
            pass

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

        results = []
        for item in items:
            data = {}

            try:
                data['title'] = item.find_element(By.CSS_SELECTOR, ".fontHeadlineSmall").text
            except Exception:
                pass

            try:
                text_content = item.text
                address_element = r'(?:\d+\s)?[A-Za-z0-9\s.,-]+,\s[A-Za-z\s]+(?:,\s[A-Z]{2}\s\d{5})?'
                matches = re.findall(address_element, text_content)
                unique_address = list(set(matches))
                data['address'] = unique_address[0] if unique_address else None
            except Exception:
                pass

            try:
                text_content = item.text
                phone_pattern = r'((\+?\d{1,2}[ -]?)?(\(?\d{3}\)?[ -]?\d{3,4}[ -]?\d{4}|\(?\d{2,3}\)?[ -]?\d{2,3}[ -]?\d{2,3}[ -]?\d{2,3}))'
                matches = re.findall(phone_pattern, text_content)

                phone_numbers = [match[0] for match in matches]
                unique_phone_numbers = list(set(phone_numbers))

                data['phone'] = unique_phone_numbers[0] if unique_phone_numbers else None   
            except Exception:
                pass

            if data.get('title'):
                results.append(data)

        with open('results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        try:
            df = pd.DataFrame(data=results)
            df.to_csv("map.csv", index=False)
        except Exception as e:
            print(e)
    except:
        driver.quit()
    finally:
        driver.quit()



def main():
  st.title('Google Map Scrapper')
  query = st.text_input("Enter your search query: ")
  encoded_query = urllib.parse.quote_plus(query)
  html_temp=""
  if st.button('Search'):
      scrapper(encoded_query)
      st.success("Finally scrapped")
      
if __name__=='__main__':
    main()
    
     

