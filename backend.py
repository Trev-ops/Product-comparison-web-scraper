from flask import Flask, request, jsonify
from flask_cors import CORS
from playwright.sync_api import sync_playwright
import time
#Files for cvs
import csv
import os


app = Flask(__name__)
CORS(app)

CSV_FILE_PATH = 'product_data.csv'

# Checks if csv exists, if not creates it
def create_csv_file():
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(["EAN Code", "Store", "Price", "Review Average", "Number of Reviews"])

def update_csv(ean_code, store, price, review_avg, review_count):
    rows = []
    product_updated = False

    with open(CSV_FILE_PATH, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)
        rows.append(header)

        for row in reader:
            if row[0] == ean_code and row[1] == store:
                rows.append([ean_code, store, price, review_avg, review_count])
                product_updated = True
            else:
                rows.append(row)

    if product_updated:
        with open(CSV_FILE_PATH, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    else:
        append_to_csv(ean_code, store, price, review_avg, review_count)

def append_to_csv(ean_code, store, price, review_avg, review_count):
    with open(CSV_FILE_PATH, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([ean_code, store, price, review_avg, review_count])

def accept_cookies(page, selector):
    try:
        page.wait_for_selector(selector, timeout=100000) #Long timeout to work with slow internet connection
        accept_button = page.query_selector(selector)
        if accept_button:
            accept_button.click()
            page.wait_for_timeout(5000)  # Waits a bit after clicking
        else:
            print("Accept cookies button not found.")
    except Exception as e:
        print(f"Could not find or click the cookie button: {e}")

def extract_price(page, selector, value):
    try:
        price = page.get_attribute(selector, value)
    except:
        price = ""
    return price

def extract_review(page, selector):
    try:
        review_avg = page.locator(selector).text_content().strip()
    except:
        review_avg = ""
    return review_avg

def extract_review_count(page, selector):
    try:
        review_count = page.locator(selector).text_content().strip()
    except:
        review_count = ""
    return review_count

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.get_json()
    ean_code = data.get('ean_code')

    try:

        create_csv_file()# Create the CSV file if it doesn't exist

        # Uses Playwright for browser automation
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=False)  # Uses firefox for the web scraper
            context = browser.new_context()
            page = context.new_page()

####################################Prisma###########################################
#Code has long timeouts due to testing with slow internet

            store = "Prisma"
            homepage_url = 'https://www.prisma.fi/'
            page.goto(homepage_url, wait_until="domcontentloaded", timeout=50000)

            accept_cookies(page, 'button[data-testid="uc-accept-all-button"]')

            search_input_selector = 'input[data-test-id="search-input"]'
            page.fill(search_input_selector, ean_code)
            page.press(search_input_selector, 'Enter')


            try:
                page.wait_for_selector('li[data-test-id^="products-list-item-"]', timeout=100000)

                product_link_selector = 'li[data-test-id^="products-list-item-"] a[data-test-id="product-card-link"]'
                page.wait_for_selector(product_link_selector, timeout=100000)

                product_link = page.query_selector(product_link_selector)

                if product_link:
                    product_link.click()
                    time.sleep(5)

                    try:
                        price = page.locator('section[data-test-id="product-price"] span.text-heading-medium-medium').text_content().strip()
                        price = price.replace('\xa0', '')
                    except:
                        price = "Price not found"

                    update_csv(ean_code, store, price, "No reviews", "No reviews")

                else:
                    update_csv(ean_code, store, "", "", "")

            except Exception as e:
                update_csv(ean_code, store, "", "", "")            

############################################################################################

####################################Gigantti###########################################
    
            store = "Gigantti"
            search_url = f'https://www.gigantti.fi/search?query={ean_code}'
            page.goto(search_url, wait_until="domcontentloaded", timeout=600000)
            time.sleep(5)

            accept_cookies(page, 'button.coi-banner__accept')

            try:
                # Uses review count to check if one correct
                product_name_selector = 'div.flex.flex-wrap.gap-2.items-end.md\\:items-center.justify-between.w-full a[href="#reviews"] > span.flex.items-center.rating span.text-discrete-600'
                page.wait_for_selector(product_name_selector, timeout=5000)

                price = extract_price(page, 'div[data-primary-price]', 'data-primary-price')

                review_avg = extract_review(page, 'div.flex.flex-wrap.gap-2.items-end.md\\:items-center.justify-between.w-full a[href="#reviews"] > span.flex.items-center.rating strong')

                review_count = extract_review_count(page, 'div.flex.flex-wrap.gap-2.items-end.md\\:items-center.justify-between.w-full a[href="#reviews"] > span.flex.items-center.rating span.text-discrete-600')

                try:
                    review_count_text = extract_review_count(page, 'div.flex.flex-wrap.gap-2.items-end.md\\:items-center.justify-between.w-full a[href="#reviews"] > span.flex.items-center.rating span.text-discrete-600')
                    review_count = ''.join(filter(str.isdigit, review_count_text))
                except:
                    review_count = ""

                update_csv(ean_code, store, price, review_avg, review_count)
            except:        
                update_csv(ean_code, store, "", "", "")

############################################################################################'

####################################Verkkokauppa###########################################

            store = "Verkkokauppa"
            search_url = f'https://www.verkkokauppa.com/fi/search?query={ean_code}'
            page.goto(search_url, wait_until="load", timeout=60000)

            accept_cookies(page, 'button[data-action="consent"][data-action-type="accept"].uc-accept-button')
            time.sleep(5)

            try:
                product_selector = 'a.sc-m8oi7n-1.bIAYpu'
                page.wait_for_selector(product_selector, timeout=10000)
                first_product = page.query_selector(product_selector)
                if first_product:
                    first_product.click()
                    time.sleep(3)

                    price = extract_price(page, 'data[data-price="current"]', 'value')

                    review_avg = extract_review(page, 'div.sc-hoLEA.jaCkdO.sc-awkpk3-0.jwnjWg span.sc-hknOHE.sc-gEkIjz.cJKJrq.bGZfUu')

                    review_count = extract_review_count(page, 'a[href*="/reviews"] span.sc-kAyceB.hfnJt')

                    update_csv(ean_code, store, price, review_avg, review_count)

                else:
                    update_csv(ean_code, store, "", "", "")
            except Exception as e:
                update_csv(ean_code, store, "", "", "")

############################################################################################

###################################POWER###############################################

            store = "Power"
            search_url = f'https://www.power.fi/search/?q={ean_code}'
            page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(5)

            accept_cookies(page, 'button.coi-banner__accept')

            try:
                product_selector = 'pwr-product-item-v2 a'
                page.wait_for_selector(product_selector, timeout=10000)
                first_product = page.query_selector(product_selector)
                if first_product:
                    first_product.click()
                    print("Clicked the first product successfully.")
                    time.sleep(3) # Helped prevent errors in testing
                    
                    # Need to use this code instead of extract_price function
                    try:
                        price_selector = 'pwr-price span'
                        price = page.evaluate('''(selector) => {
                            const element = document.querySelector(selector);
                            return element ? element.textContent.trim() : null;
                        }''', price_selector)
                        
                        if not price:
                            price = "Price not found"
                    except Exception as e:
                        price = "Error retrieving price"

                    review_avg = extract_review(page, 'div[itemprop="ratingValue"]')

                    # Need to use this code instead of extract_review_count function
                    try:
                        review_count_selector = 'meta[itemprop="reviewCount"]'
                        review_count = page.locator(review_count_selector).get_attribute("content").strip()
                    except:
                        review_count = "No reviews found"

                    update_csv(ean_code, store, price, review_avg, review_count)

                else:
                    update_csv(ean_code, store, "", "", "")
            except Exception as e:
                update_csv(ean_code, store, "", "", "")

############################################################################################

            browser.close()

    except Exception as e:
        print(f"Error occurred: {e}")
        return jsonify({"error": "An error occurred while opening the site."}), 500

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False) # Could change reloader to True though on some machines caused crashing issues