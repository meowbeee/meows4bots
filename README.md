# Meows For'bots Project
Primary purpose of this project is both to add some fun functionality to Twitch streaming, but also incorporating information from the Twitch API into a Discord bot. In essence, this would be two different bots, one for Twitch chat and one for Discord.

# Implementation
## Discord
- Nothing yet

## Twitch
- Commands
    - gup
        - Replies in chat with another gup!
    - !discord, !gupcord
        - Provides a link to the discord
    - !nowplaying, !np
        - Reads the current song playing on my Spotify
        - Includes name, artists, and current time progress
    - !counting, !count
        - Reports the current chat counting high-score
    - !pts, !points, !audit
        - Gets the points for a given user or self
- Redeems / Channel Points
    - Skip Song
        - Calls Spotify API to skip the current song playing
    - Request / Add to Queue
        - Given a Spotify URL, adds song to queue
- Channel States
    - Ad Roll Announcement
        - Posts in chat when an ad break occurs
- Games / Easter Eggs / Chat Reading
    - Counting Game
        - Counts highest sequence of 1,2,3... unbroken!
        - Has some easter eggs
    - Chat Auditing
        - +1 your faves
        - or your fave emotes
        - anything really
    - Six Seven
        - 67

# Functionality Goals
## Discord
- Linking fun stats from Twitch chat to Discord
- Announcing Go Live notifications
- Minigames (may start as simple as high-low, but can program more complex games)
- Full configuration (server specific mentions, multiple channels, toggling functions)

## Twitch
- Track extra gimmick for subscribers/followers (i.e. collecting "items" for each month of subbing)
- Prediction / Poll Announcement
- Timeout redeem handler
- OBS hook in for redeems?
- ... and maybe more? We will see!

# Necessary Integrations for Plans
- Bungie API for Destiny for pulling Destiny items / FFXIV third party API for pulling XIV items
- Spotify API for song requesting directly
- Twitch API for reading channel states, chat, and other information
- OBS Connectivity for changing stream elements based on chat
- Discord API for sending messages and relaying user information
