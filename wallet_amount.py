from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright
import sqlite3

async def get_wallet_total(addresses):
  wallet_data = {}
  
  async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True)
    page = await browser.new_page()
    
    for address in addresses:
      print(address)
      
      try:
        await page.goto(f'https://www.blockchain.com/explorer/addresses/eth/{address}')
        await page.wait_for_selector('.sc-92d5245a-4.eacMWo', timeout=3000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        parent_div = soup.find_all('div', class_='sc-92d5245a-0 gJWFSC')
        
        received_div = parent_div[0].find('div', class_='sc-92d5245a-4 eacMWo')
        sent_div = parent_div[1].find('div', class_='sc-92d5245a-4 eacMWo')
        transactions_div = parent_div[5].find('div', class_='sc-92d5245a-2 cWXKHx')
        
        received = received_div.text.strip().replace('$', '').replace(',', '')
        sent = sent_div.text.strip().replace('$', '').replace(',', '')
        crypto = 'Ethereum'
        transactions = transactions_div.text.strip().replace(',', '')
        
        wallet_data[address] = {'received': received, 'sent': sent,'crypto': crypto, 'transactions': transactions}
        continue
        
      except Exception as e:
        print('Not an Ethereum address, trying Bitcoin...')
        
      try:
        await page.goto(f'https://www.blockchain.com/explorer/addresses/btc/{address}')
        await page.wait_for_selector('.sc-92d5245a-4.eacMWo', timeout=3000)
        
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        parent_div = soup.find_all('div', class_='sc-92d5245a-0 gJWFSC')
        
        received_div = parent_div[0].find('div', class_='sc-92d5245a-4 eacMWo')
        sent_div = parent_div[1].find('div', class_='sc-92d5245a-4 eacMWo')
        transactions_div = parent_div[3].find('div', class_='sc-92d5245a-2 cWXKHx')
        
        received = received_div.text.strip().replace('$', '').replace(',', '')
        sent = sent_div.text.strip().replace('$', '').replace(',', '')        
        crypto = 'Bitcoin'
        transactions = transactions_div.text.strip().replace(',', '')
        
        wallet_data[address] = {'received': received, 'sent': sent, 'crypto': crypto, 'transactions': transactions}

      except Exception as e:
        print("-- Invalid address")
        wallet_data[address] = {'received': None, 'sent': None, 'crypto': None, 'transactions': None}
        continue
        
    await browser.close()
      
  return wallet_data

async def get_wallets():
  conn = sqlite3.connect('wallet_reports.db')
  cursor = conn.cursor()
  
  cursor.execute('SELECT wallet FROM wallet_reports;')
  rows = cursor.fetchall()
  
  addresses = [row[0] for row in rows]

  wallet_data = await get_wallet_total(addresses)
  
  columns_to_add = [
    ("received", "NUMERIC"),
    ("sent", "NUMERIC"),
    ("crypto", "TEXT"),
    ("transactions", "INTEGER")
  ]

  for column_name, column_type in columns_to_add:
    try:
      cursor.execute(f"ALTER TABLE wallet_reports ADD COLUMN {column_name} {column_type};")
      print(f"Added column '{column_name}'")
    except sqlite3.OperationalError:
      print(f"Column '{column_name}' already exists")
  
  for address, data in wallet_data.items():
    received = data['received']
    sent = data['sent']
    crypto = data['crypto']
    transactions = data['transactions']

    cursor.execute('''
      UPDATE wallet_reports
      SET received = ?, sent = ?, crypto = ?, transactions = ?
      WHERE wallet = ?;
    ''', (received, sent, crypto, transactions, address))
        
  conn.commit()
  conn.close()
      
asyncio.run(get_wallets())
