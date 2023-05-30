from bs4 import BeautifulSoup
import requests
import time
#import RPi.GPIO as GPIO

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36', 
    'Accept-Language': 'en-US, en;q=0.5'
}



#def setup_gpio():
  #  GPIO.setmode(GPIO.BCM)
  #  GPIO.setup(VDC, GPIO.OUT)
  #  GPIO.setup(Lights, GPIO.OUT)
  #  GPIO.setup(Pump, GPIO.OUT)
  #  GPIO.setup(Water_Heater, GPIO.OUT)
  #  GPIO.setup(Heater, GPIO.OUT)
  #  GPIO.setup(acid, GPIO.OUT)
  #  GPIO.setup(base, GPIO.OUT)
  #  GPIO.setup(nutrients, GPIO.OUT)
  #  GPIO.setup(Fan, GPIO.OUT) 






def grap_prices():
    
    products = [
       # ["1in. x 10ft. PVC pipe", 'https://www.homedepot.com/p/Charlotte-Pipe-1-in-x-10-ft-Plastic-Plain-End-Pipe-PVC200100600/100348483', 14],
        ["#8 x 1 in. Wood Screws (50 per Pack)", 'https://www.homedepot.com/p/Everbilt-8-x-1-in-Coarse-Zinc-Plated-Phillips-Bugle-Head-Wood-Screws-50-per-Pack-802672/204283331', 1],
        ['106 Qt. Latching Storage Box', 'https://www.homedepot.com/p/Sterilite-106-Qt-Latching-Storage-Box-14998004/206721484', 1],
        ['Raspberry Pi 4', 'https://www.amazon.com/Raspberry-Pi-Computer-Suitable-Workstation/dp/B0899VXM8F/?_encoding=UTF8&content-id=amzn1.sym.bc5f3394-3b4c-4031-8ac0-18107ac75816&ref_=pd_gw_ci_mcx_mr_hp_atf_m', 1],
        ['Ratchet Pulley', 'https://www.amazon.com/Pairs-inch-Adjustable-Heavy-Hanger/dp/B07XKLLVL7/ref=sr_1_5?keywords=ratchet+pulley&sr=8-5', 1],
        ['Panda','https://www.vivosun.com/vivosun-5-gallon-grow-bags-5-pack-black-thickened-nonwoven-fabric-pots-with-handles-p68320123310965170-v58820960379602944?_lf=buyWith',1],
        ['1kg Black PLA filament','https://www.amazon.com/OVERTURE-Filament-Consumables-Dimensional-Accuracy/dp/B07PGY2JP1/ref=sr_1_1_sspa?keywords=PLA%2Bfilament&sr=8-1-spons&spLa=ZW5jcnlwdGVkUXVhbGlmaWVyPUExQUFQTU1YSk5MNzZJJmVuY3J5cHRlZElkPUEwNzYzODU1M1JINjVRWFREVDQyMCZlbmNyeXB0ZWRBZElkPUEwMTE2NjI0MVpOR0o1RjFWMThLNyZ3aWRnZXROYW1lPXNwX2F0ZiZhY3Rpb249Y2xpY2tSZWRpcmVjdCZkb05vdExvZ0NsaWNrPXRydWU&th=1',1]
    ]

    append_list = [
        ["1in. x 10ft. PVC pipe", 'https://www.homedepot.com/p/Charlotte-Pipe-1-in-x-10-ft-Plastic-Plain-End-Pipe-PVC200100600/100348483', 14, float(4.41)],
    ]
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
        return products



#bom = grap_prices()

#for item in bom:
#    print(item)
#    print()
