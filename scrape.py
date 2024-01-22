from selenium import webdriver
import time
from bs4 import BeautifulSoup
import csv
import requests
import re
import certifi
import ssl 

URL = 'https://www.producthunt.com/'
OUTPUT_FILE = 'products.csv'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def fetch_webpage(url):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    driver.get(url)

    # Scroll down multiple times to load more products
    for _ in range(160):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    content = driver.page_source
    driver.close()
    return content

def fetch_emails_from_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # This will raise an HTTPError if the HTTP request returned an unsuccessful status code

        content = response.text
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,6}\b'
        emails = set(re.findall(email_pattern, content))
        return emails

    except requests.exceptions.SSLError:
        print(f"SSLError encountered while fetching {url}. Skipping...")
        return set()

    except requests.exceptions.ConnectionError:
        print(f"ConnectionError encountered while fetching {url}. Skipping...")
        return set()

    except requests.exceptions.RequestException as e:
        print(f"An error occurred while fetching {url}: {e}. Skipping...")
        return set()







def scrape_info(content):
    soup = BeautifulSoup(content, 'html.parser')
    products = []

    # Locate all divs with the specified class
    for div in soup.find_all('div', class_='styles_item__Dk_nz'):
        
        # Extract product name
        name_anchor = div.find('a', class_='styles_title__HzPeb')
        if name_anchor:
            product_name = name_anchor.text.strip()

            # Extract number of upvotes
            upvotes_div = div.find('div', class_='color-lighter-grey fontSize-12 fontWeight-600 noOfLines-undefined')
            upvotes = int(upvotes_div.text.replace(',', '').strip()) if upvotes_div else None

            # Extract product link and resolve to final destination
            link_anchor = div.find('a', class_='styles_externalLinkIcon__vjPDi', href=True)
            if link_anchor:
                intermediate_link = 'https://www.producthunt.com' + link_anchor['href']
                try:
                    response = requests.get(intermediate_link, headers=HEADERS, timeout=10)
                    product_link = response.url

                    if product_link.endswith('?ref=producthunt'):
                        product_link = product_link.rsplit('?ref=producthunt', 1)[0]
                except (requests.RequestException, ValueError):
                    product_link = intermediate_link
            else:
                product_link = None

           # Extract product description
            description_div = div.find('div', class_='color-lighter-grey fontSize-mobile-12 fontSize-desktop-16 fontSize-tablet-16 fontSize-widescreen-16 fontWeight-400 noOfLines-2')
            description = description_div.text.strip() if description_div else None


            # Extract producthunt link from the post
            producthunt_anchor = div.find('a', {'href': True, 'aria-label': product_name})
            if producthunt_anchor:
                producthunt_link = 'https://www.producthunt.com' + producthunt_anchor['href']
            else:
                producthunt_link = None

            # Extract tags
            tag_anchors = div.find_all('a', class_='styles_underlinedLink__pq3Kl')
            tags = [tag.text for tag in tag_anchors]

            # Extract emails from product's website
            emails = fetch_emails_from_url(product_link) if product_link else set()
            email_list = ", ".join(list(emails))

            products.append({
                'name': product_name,
                'upvotes': upvotes,
                'link': product_link,
                'producthunt_link': producthunt_link,
                'description': description,
                'tags': ', '.join(tags),  # Join tags with commas
                'emails': email_list
            })

    return products

def save_to_csv(data, filename):
    with open(filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['name', 'upvotes', 'link', 'producthunt_link', 'description', 'tags', 'emails'])
        writer.writeheader()
        writer.writerows(data)

def main():
    content = fetch_webpage(URL)
    if content:
        products = scrape_info(content)
        save_to_csv(products, OUTPUT_FILE)

if __name__ == "__main__":
    main()
