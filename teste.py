def parse_page(html):
    soup = BeautifulSoup(html, 'html.parser')
    
    product_name = soup.find('h1', class_='ui-pdp-title').get_text()
    prices = soup.find_all('span', class_='andes-money-amount__fraction')

    old_price = int(prices[0].get_text().replace('.', '')) if len(prices) > 0 else None
    new_price = int(prices[1].get_text().replace('.', '')) if len(prices) > 1 else None
    installment_price = int(prices[2].get_text().replace('.', '')) if len(prices) > 2 else None

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

    return {
        'product_name': product_name,
        'old_price': old_price,
        'new_price': new_price,
        'installment_price': installment_price,
        'timestamp': timestamp
    }
