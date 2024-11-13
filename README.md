# SM_Scam_Wallets

### Overview
In this study we scrape data from chainabuse.com in order to find crypto wallets that are associated with social media phishing attacks.
We then run the wallets through Blockchain.com to determine how much the wallet address has received and sent to infer profitability.
This gives us an idea of which social media sites might host the most phishing attacks, and which sites are the most profitable.

Currently looking into Discord, Facebook, Telegram, Twitter (X), YouTube.

### Running the Code
- First run chainabuse.py in order to populate or update the database file with wallet adddresses and information related to the attacks
  - We interacted with the database file using SQLite
- Second run wallet_amount.py to find transaction information related to each wallet address stored in the database.
