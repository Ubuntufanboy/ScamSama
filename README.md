# ScamSama
"Fighting crime, one meme at a time"

Created by Ubuntufanboy

Discord: @apolloiscool for any questions

Check out Vedal987's streams here: https://www.twitch.tv/vedal987

**DISCLAIMER**: I don't know what I'm doing... I am new to Neurosama... The code is really bad (Feel free to send PRs fixing it!). Hopefully as the community gets more involved the code will drastically improve.

## What is ScamSama?
ScamSama is a NeuroSama implementation for telephone calling specifically in the domain of scambaiting. This code grants Neuro the ability to call lists of scammers and promptly waste their time.

## Why ScamSama
Scambaiting is an effective technique to protect the elderly from scams because it both disrupts scam operations and raises public awareness of fraud tactics (especially when paired with entertainment), equipping at-risk groups, especially older adults, with the practical knowledge and confidence needed to spot and avoid scams.

## Usage
You first need to set up some free accounts (Although for practical usage paid accounts are **strongly** reccomended)

0. Clone repo

    - run `git clone https://github.com/Ubuntufanboy/ScamSama`
    - run `cd ScamSama`

1. ngrok (Tunneling Service. No Portforwarding required)

    - Create a free ngrok account here: https://dashboard.ngrok.com/signup
    - Download ngrok. Instructions vary depending on OS varient
    - Run `ngrok http 5000` to create tunnel

2. Twilio (Calling service. Phone number required)

    - Create a free/paid account (free accounts are only for testing purposes)
    - Buy a phone number (Usually only around 1 USD a month)
    - (Depending on type of phone number you may need to configure emergancy services)

3. Discord

    - Create discord bot with voice channel permissions
    - Invite them into a **PRIVATE** discord server (Bot sometimes leaks info)

4. Running the bot
    - Run `python3 launcher.py` and follow the on-screen instructions.
    - The launcher will guide you through the setup process, including creating the `.env` file.
    - To run the bot without the verbose output, use the `-v` flag: `python3 launcher.py -v`
    - Join a voice channel and type `!callme` in a text channel. (All other users should be muted)
    - The bot will automatically select the correct audio codec based on your country code (set in the `.env` file).

## Contributing

I would love it if others improved this program as well! Feel free to create a pull request!

- Made with care @Ubuntufanboy
