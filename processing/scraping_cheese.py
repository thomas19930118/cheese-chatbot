import requests
from bs4 import BeautifulSoup
import time  # Add this for delays between requests

CAT_URL = "https://shop.kimelo.com/department/cheese/3365"
PRODUCTS = []
i = 0

def get_details(url):
    print(url)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    r_details = requests.get(url, headers=headers)
    r_details.raise_for_status()

    soup_details = BeautifulSoup(r_details.text, "html.parser")
    
    cheese_data = {
        'brand': '',
        'category': '',
        'SKU': '',
        'UPC': '',
        'Warning': '',
        'CASE': {
            'count': '',
            'dimension': '',
            'weight': '',
            'price': '',
            'price_per_lb': ''
        },
        'EACH': {
            'count': '',
            'dimension': '',
            'weight': '',
            'price': '',
            'price_per_lb': ''
        },
        'related_items': []
    }
    
    # Get brand
    brand = soup_details.find('p', class_='css-drbcjm')
    if brand:
        cheese_data['brand'] = brand.text.strip()
    
    # Get category and subcategory
    breadcrumbs = soup_details.find_all('a', class_='chakra-breadcrumb__link')
    if len(breadcrumbs) >= 2:
        cheese_data['category'] = f"{breadcrumbs[0].text.strip()} > {breadcrumbs[1].text.strip()}"
    
    # Get SKU and UPC
    sku_upc_elements = soup_details.find_all('p', class_='chakra-text')
    for element in sku_upc_elements:
        if 'SKU:' in element.text:
            cheese_data['SKU'] = element.find('b').text.strip()
        elif 'UPC:' in element.text:
            cheese_data['UPC'] = element.find('b').text.strip()
    
    # Get Warning (Proposition 65)
    warning_text = soup_details.findAll('p', class_='chakra-text css-dw5ttn')
    if warning_text:
        cheese_data['Warning'] = warning_text[1].text.strip()
    # Get Case and Each information from table
    table = soup_details.find_all('table', class_='chakra-table css-5605sr')
    if table:
        if len(table) >= 2:
            rows = table[1].find('tbody').find_all('tr')
        else:
            rows = table[0].find('tbody').find_all('tr')
        print(rows)
        for row in rows:
            cells = row.find_all('td')
            
            if len(cells) >= 2:
                case_text = cells[0].text.strip()
                each_text = cells[1].text.strip()
                
                if "Eaches" in case_text or "Item" in each_text:
                    cheese_data['CASE']['count'] = case_text
                    cheese_data['EACH']['count'] = each_text
                elif any(x in case_text for x in ['L', 'W', 'H']):  # Dimensions row
                    cheese_data['CASE']['dimension'] = case_text
                    cheese_data['EACH']['dimension'] = each_text
                elif "lbs" in case_text:  # Weight row
                    cheese_data['CASE']['weight'] = case_text
                    cheese_data['EACH']['weight'] = each_text
            else:
                each_text = cells[0].text.strip()
                
                if "Item" in each_text:
                    cheese_data['CASE']['count'] = "1 Eaches"
                    cheese_data['EACH']['count'] = each_text
                elif any(x in each_text for x in ['L', 'W', 'H']):  # Dimensions row
                    cheese_data['CASE']['dimension'] = each_text
                    cheese_data['EACH']['dimension'] = each_text
                elif "lbs" in each_text:  # Weight row
                    cheese_data['CASE']['weight'] = each_text
                    cheese_data['EACH']['weight'] = each_text
        
    # Get prices and price per lb
    price = soup_details.find_all('b', class_='chakra-text css-0', string=lambda x: x and '$' in x)

    if len(price) >= 2:
        cheese_data['CASE']['price'] = price[0].text.strip()
        cheese_data['EACH']['price'] = price[1].text.strip()
    else:
        cheese_data['CASE']['price'] = price[0].text.strip()
        cheese_data['EACH']['price'] = price[0].text.strip()
    
    price_per_lb = soup_details.find_all('span', class_='chakra-badge css-1mwp5d1')

    if len(price_per_lb) >= 2:
        cheese_data['CASE']['price_per_lb'] = price_per_lb[0].text.strip()
        cheese_data['EACH']['price_per_lb'] = price_per_lb[1].text.strip()
    elif len(price_per_lb) == 1:
        cheese_data['CASE']['price_per_lb'] = price_per_lb[0].text.strip()
        cheese_data['EACH']['price_per_lb'] = price_per_lb[0].text.strip()
    else:
        cheese_data['CASE']['price_per_lb'] = "None"
        cheese_data['EACH']['price_per_lb'] = "None"
    # Get related items
    related_items = soup_details.find_all('a', class_='chakra-card group css-5pmr4x')

    if related_items:
        for item in related_items:
            item_data = {}
            # Get product name
            product_name = item.find('p', class_='chakra-text css-pbtft')
            if product_name:
                item_data['name'] = product_name.text.strip()
            
            # Get brand
            brand = item.find('p', class_='chakra-text css-w6ttxb')
            if brand:
                item_data['brand'] = brand.text.strip()
            
            # Get price
            price = item.find('b', class_='chakra-text css-1vhzs63')
            if price:
                item_data['price'] = price.text.strip()
            
            # Get price per lb
            price_per_lb = item.find('span', class_='chakra-badge css-ff7g47')
            if price_per_lb:
                item_data['price_per_lb'] = price_per_lb.text.strip()
            
            if item_data:  # Only append if we found some data
                cheese_data['related_items'].append(item_data)
    else:
        cheese_data['related_items'] = 'None'
        
    return cheese_data

def parse_products(soup):
    global i
    i += 1
    cards = soup.find_all('a', class_="chakra-card")
    print(f"Found {len(cards)} products on page {i}")
    
    for card in cards:
        cheese_data = {
            'image': '',
            'url': '',
            'name': '',
            'brand': '',
            'category': '',
            'SKU': '',
            'UPC': '',
            'Warning': '',
            'CASE': {
                'count': '',
                'dimension': '',
                'weight': '',
                'price': '',
                'price_per_lb': ''
            },
            'EACH': {
                'count': '',
                'dimension': '',
                'weight': '',
                'price': '',
                'price_per_lb': ''
            },
            'related_items': []
        }
        # Link
        cheese_data["url"] = "https://shop.kimelo.com" + card['href'] if card.has_attr('href') else 'not sure'
        # Name/Description
        desc = card.select_one("p.chakra-text.css-pbtft")
        cheese_data["name"] = desc.text.strip() if desc else 'not sure'

        # Image
        img = card.select_one("img")
        cheese_data["image"] = "https://shop.kimelo.com" + img['src'] if img and img.has_attr('src') else 'None'

        details = get_details(cheese_data["url"])
        cheese_data.update(details)
        print(cheese_data)
        PRODUCTS.append(cheese_data)
    # print(f"Processed page {i}")

def scrape_page(page_num):
    try:
        if page_num == 1:
            url = CAT_URL
        else:
            url = f"{CAT_URL}?page={page_num}"
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching page {page_num}: {url}")
        r = requests.get(url, headers=headers)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")
        parse_products(soup)
        
        return True
    except Exception as e:
        print(f"Error on page {page_num}: {str(e)}")
        return False

def main():
    # We know there are 5 pages
    total_pages = 5
    for page_num in range(1, total_pages + 1):
        success = scrape_page(page_num)
        if success:
            print(f"Successfully scraped page {page_num}")
        else:
            print(f"Failed to scrape page {page_num}")
        
        # Add a delay between requests to be polite to the server
        if page_num < total_pages:
            time.sleep(2)  # 2 second delay between requests
    
    print(f"\nScraped {len(PRODUCTS)} cheese products in total!")
    
    # Save results to a file
    import json
    with open('cheese_products.json', 'w', encoding='utf-8') as f:
        json.dump(PRODUCTS, f, ensure_ascii=False, indent=2)
    print("Results saved to cheese_products.json")
    
    # Print first few products as sample
    print("\nSample of products scraped:")
    for prod in PRODUCTS[:5]:
        print(json.dumps(prod, indent=2))

if __name__ == "__main__":
    main()