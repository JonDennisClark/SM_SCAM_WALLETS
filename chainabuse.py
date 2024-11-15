from bs4 import BeautifulSoup
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime, timedelta
import sqlite3
import re
from dotenv import load_dotenv
import os

async def scrape_chainabuse(conn, cursor):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        load_dotenv()
        user = os.getenv("USER")
        password = os.getenv("PASSWORD")
        # Login to chainabuse first
        await page.goto('https://auth.chainabuse.com/u/login/identifier?state=hKFo2SBJaTUyV29ZWEVfVVNneW8xZnVVQkJLcWdSMUNXRmItN6Fur3VuaXZlcnNhbC1sb2dpbqN0aWTZIHdhN2ZPc1l3QXJWc0NETWZubktFS0FJY3RHdEdXa0dDo2NpZNkgTU5YdXZUUjVRYVZxMkVyM1ptSTV1OTNia3gxa29nYTg')
        await page.locator("[name='username']").fill(user)
        await page.locator('[name="action"]').click()
        await page.locator('[name="password"]').fill(password)
        await page.locator('[name="action"]').click()

        #await page.wait_for_timeout(2000)

        # Start at page 873
        for i in range(1667):
            print(f"Page {i}")
            # Check different sorting to try to find the most human entries 
            #await page.goto(f"https://www.chainabuse.com/category/phishing?page={i}&sort=up-votes")
            #await page.goto(f"https://www.chainabuse.com/category/phishing?page={i}&sort=most-comments")
            #await page.goto(f"https://www.chainabuse.com/category/phishing?page={i}&sort=newest&filter=ETH")
            await page.goto(f"https://www.chainabuse.com/category/phishing?page={i}&sort=oldest&filter=ETH")

            await page.wait_for_selector(".create-ScamReportCard__body")

            #await page.wait_for_timeout(5000)

            html = await page.content()
            soup = BeautifulSoup(html, "html.parser")

            reports = soup.select(".create-ScamReportCard")

            # Each page contains 15 reports
            for report in reports:
                platform = None
                paragraphs = report.select(".create-Editor__paragraph")
                report_txt = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs)

                platform_keywords = {
                        "youtube": "youtube",
                        "twitter": "twitter",
                        "tweet": "twitter",
                        "x.com": "twitter",
                        "discord": "discord",
                        "facebook": "facebook",
                        "instagram": "instagram",
                        "tiktok": "tiktok",
                        "snapchat": "snapchat",
                        "telegram": "telegram",
                        "reddit": "reddit"
                }
                # Search through each report text to find the social media platform 
                for keyword, platform_val in platform_keywords.items():
                    if keyword in report_txt.lower():
                        platform = platform_val
                        break
                
                if platform:
                    # A report must also contain a crypto wallet address
                    wallet_address = report.select_one(".create-ResponsiveAddress__text")
                    if wallet_address:
                        wallet_address = wallet_address.get_text(strip=True) 
                        date = report.select(".create-ScamReportCard__submitted-info .create-Text.type-h5")
                        date = date[1].get_text(strip=True)
                        date = date.replace("on ", "")

                        # Handle different timestamp formatting and convert it into a useable format for SQLite
                        if "hours ago" in date or "hour ago" in date or "minutes ago" in date or "minute ago" in date:
                            date = datetime.now().strftime("%Y-%m-%d")
                        elif "day ago" in date or "days ago" in date:
                            days_ago = int(re.search(r"(\d+) day", date).group(1))
                            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
                        else:
                            date = datetime.strptime(date, "%b %d, %Y")
                            date = date.strftime("%Y-%m-%d")

                        
                        print(f"{platform}\n{wallet_address}\n{date}\n\n")

                        # Store a valid entry into our database
                        cursor.execute('''
                            INSERT OR IGNORE INTO wallet_reports (platform, wallet, date, report)
                            VALUES (?, ?, ?, ?)
                        ''', (platform, wallet_address, date, report_txt))
                        conn.commit()


        await browser.close()


def create_walletDB():
    conn = sqlite3.connect('wallet_reports.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_reports (
                   
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   platform TEXT,
                   wallet TEXT NOT NULL,
                   date DATE,
                   report TEXT,
                   UNIQUE(wallet)
                   )
                   ''')
    conn.commit()
    return conn, cursor

conn, cursor = create_walletDB()
asyncio.run(scrape_chainabuse(conn, cursor))
conn.close()