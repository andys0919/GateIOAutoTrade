# Configuration Guide for Trading Script

## Overview
This document provides instructions for setting up and using the `config.json` file required for the automated trading script. The script utilizes this file to manage multiple trading accounts on the Gate.io platform.

## Creating Your `config.json` File
To use the script, you need to create a `config.json` file containing the API keys, secrets, and account names for each of your Gate.io accounts.

### Steps:
1. **Generate API Keys:**
   - Log in to your Gate.io account.
   - Navigate to the API Management section.
   - Create a new API key and secret, ensuring to grant necessary permissions for trading.

2. **Create `config.json` File:**
   - Create a new file named `config.json` in the same directory as your trading script.
   - Use the following format to add your account details:

```json
[
    {
        "API_KEY": "your_api_key_for_account_1",
        "API_SECRET": "your_api_secret_for_account_1",
        "ACCOUNT_NAME": "account_1_name"
    },
    {
        "API_KEY": "your_api_key_for_account_2",
        "API_SECRET": "your_api_secret_for_account_2",
        "ACCOUNT_NAME": "account_2_name"
    }
    // Add more accounts as needed
]
```

3. **Fill in Your Account Details:**
   - Replace `your_api_key_for_account_X` and `your_api_secret_for_account_X` with the API key and secret you generated.
   - Replace `account_X_name` with a name for your account (this is used for identification in the script's logs and outputs).

## Using Your `config.json` File
Once your `config.json` file is set up with your account details:
- Run the trading script.
- The script will automatically read the `config.json` file and manage trading activities for each account specified in the file.

## Note
- Keep your `config.json` file secure as it contains sensitive API keys and secrets.
- Ensure that the API keys have the correct permissions set for the script to function properly.
- The script's efficiency and performance depend on the correct configuration in this file.
