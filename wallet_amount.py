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
        
        received = received_div.text.strip().replace('$', '').replace(',', '')
        sent = sent_div.text.strip().replace('$', '').replace(',', '')
        crypto = 'Ethereum'
        
        wallet_data[address] = {'received': received, 'sent': sent, 'crypto': crypto}
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
        
        received = received_div.text.strip().replace('$', '').replace(',', '')
        sent = sent_div.text.strip().replace('$', '').replace(',', '')
        crypto = 'Bitcoin'
        
        wallet_data[address] = {'received': received, 'sent': sent, 'crypto': crypto}

      except Exception as e:
        print("-- Invalid address")
        wallet_data[address] = {'received': None, 'sent': None, 'crypto': None}
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
  
  cursor.execute('ALTER TABLE wallet_reports ADD COLUMN received NUMERIC;')
  cursor.execute('ALTER TABLE wallet_reports ADD COLUMN sent NUMERIC;')
  cursor.execute('ALTER TABLE wallet_reports ADD COLUMN crypto TEXT;')
  
  for address, data in wallet_data.items():
    received = data['received']
    sent = data['sent']
    crypto = data['crypto']

    cursor.execute('''
      UPDATE wallet_reports
      SET received = ?, sent = ?, crypto = ?
      WHERE wallet = ?;
    ''', (received, sent, crypto, address))
        
  conn.commit()
  conn.close()
      
asyncio.run(get_wallets())
