# Protean

Hello, this is my project to tie an LLM and a MUD together and see what happens.  

Built on the Evennia MU* framework: https://www.evennia.com/

## Installation
Will make this smoother at some point. Best way to install to:
1. Create a virtualenv. There is a requirements.txt to recreate the virtualenv that I currently use. Download it and use `pip install -r requirements.txt`
2. Clone this repo
3. Use `evennia migrate` to create a new db and other set up stuff.  Should only have to do this once.
4. Either update `\server\conf\settings.py` or create `\server\conf\secret_settings.py` with `OPENAI_KEY = "<your OpenAI key>"`
5. Use `evennia start` to start up the MUD server.  If you did everything right, you should be able to access your MUD from _localhost_. localhost, port 4000 via telnet, or http://localhost:4001 to play via the Django 

Check out https://www.evennia.com/docs/latest/index.html for more info on the mechanics of running the MUD

## My changes
Where you want to look and see what I done did

commands/command.py  
commands/default_cmdsets.py  

typeclasses/exits.py  
typeclasses/objects.py  
typeclasses/rooms.py  

world/ai.py
