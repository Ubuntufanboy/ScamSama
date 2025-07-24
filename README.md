# ScamSama
``"Fighting crime, one meme at a time"``

Created by Ubuntufanboy 

Discord:@apolloiscool for any questions

Check out Vedal987's streams ![Here](https://www.twitch.tv/vedal987)
## What is ScamSama?
ScamSama is a NeuroSama implementation for telephone calling specifically in the domain of scambaiting. This code grants Neuro the ability to call lists of scammers and promptly waste their time. 

## Why ScamSama
Scambaiting is an effective technique to protect the elderly from scams because it both disrupts scam operations and raises public awareness of fraud tactics (especially when paired with entertainment), equipping at-risk groups, especially older adults, with the practical knowledge and confidence needed to spot and avoid scams.

## Usage
You first need to set up some free accounts (Although for practical usage paid accounts are **strongly** reccomended)

0. Clone repo

    - run ``git clone https://github.com/Ubuntufanboy/ScamSama``
    - run ``cd ScamSama`` (``.env`` file is here but hidden)

1. ngrok (Tunneling Service. No Portforwarding required)
    
    - Create a free ngrok account ![Here](https://dashboard.ngrok.com/signup)
    - Download ngrok. Instructions vary depending on OS varient
    - Run ``ngrok http 5000`` to create tunnel

2. Twilio (Calling service. Phone number required)

    - Create a free/paid account (free accounts are only for testing purposes)
    - Buy a phone number (Usually only around ~1 USD a month)
    - (Depending on type of phone number you may need to configure emergancy services)
    - Copy your twilio account SID (Should start with AC) into the ``.env`` file
    - Copy your twilio account auth token into the ``.env`` file
    - Copy your twilio phone number into the ``.env`` file. (This isn't the scammers number)
    - Put the scammer phone number as ``YOUR_PERSONAL_PHONE_NUMBER`` (Naming could be better admittably)

3. Discord

    - Create discord bot with voice channel permissions
    - Invite them into a ***PRIVATE*** discord server (Bot sometimes leaks info)
    - Run the bot with ``cd src/`` then ``python3 main.py``
    - Join Vc then type in a channel ``!callme`` after Neuro is already in VC (All other users should be muted)
    - All should be working correctly (Make sure the code is set to your countries correct audio transcoding! Code is set to Mu-law for USA and Japan but Europians need to switch this to A-law. See comment in ``discord_bot.py``)

## Contributing

I would love it if others improved this program as well! Feel free to create a pull request!

- Made with care @Ubuntufanboy
