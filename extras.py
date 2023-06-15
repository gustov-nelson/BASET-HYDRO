from bs4 import BeautifulSoup
import requests
import time
import bom

headers = {
    'User-Agent': 'Mozilla/5.0 (X11; CrOS aarch64 13597.84.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.57 Safari/537.36', 
    'Accept-Language': 'en-US, en;q=0.5'
}

def grap_prices():
    products = bom.products
    append_list = bom.append_list
    while True:
        for product in products:
            page = requests.get(product[1], headers=headers)
            soup1 = BeautifulSoup(page.content, 'html.parser')
            soup2 = soup1.prettify()
            if 'homedepot.com' in product[1]:
                price = soup1.find('div', class_='price').get_text()
                price = price.replace(" ", "").replace("$", "").replace("\n", "")
                i = 0
                cents = price[len(price)-2] + price[len(price)-1]
                dollars = []
                while i < len(price) - 2:
                    dollars.append(price[i])
                    i = i + 1
                dollars = ''.join(dollars)
                final = float(dollars + "." + cents)
                product.append(final)
            elif 'amazon.com' in product[1]:
                price = soup1.find('span', class_='a-offscreen').get_text()
                price = float(price.replace('$', ''))
                product.append(price)
            elif 'vivosun.com' in product[1]:
                price = soup1.find('strong', class_=['shop-price', 'deal-price'])
                price = float(price.text.strip().replace('$','').replace("US",''))
                if price is None:
                    time.sleep(5)
                    break
                product.append(price)
        for item in append_list:
            products.append(item)
        total_cost = 0
        for item in products:
            cost = round(item[2]*item[3],2)
            total_cost = total_cost + cost
            item.append(cost)
        products.append(['Total Cost:','','','',total_cost])
        return products


#This code is used to test the web scrapper by itself. 
#It is very important to comment it out when done otherwise the main module will execute this on boot. 
#if __name__: "__main__"
#test = grap_prices()
#for item in test:
#    print(item)
#    print()
