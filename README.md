# Protean

Hello, this is my project to tie an LLM and a MUD together and see what happens.  

Built on the Evennia MU* framework: https://www.evennia.com/

## Installation
Will make this smoother at some point. Best way to install to:
1. Clone this repo
2. Set up virtual environment, for ex. `python -m venv venv`
3. Install dependencies `pip install -r requirements.txt`
4. Use `evennia --initmissing` and then `evennia migrate` to create a new db and `secret_settings.py`.
   * Windows users will want to run `py -m evennia` beforehand to create an executable.
5. Add your OpenAI api key to either 
   1. The environmental variable `OPENAI_API_KEY` 
   2. `\server\conf\settings.py` or `\server\conf\secret_settings.py` with `OPENAI_KEY = "<your OpenAI key>"`
6. Use `evennia start` to start up the MUD server.  
You should be able to access the MUD from _localhost_, port 4000 via telnet or favorite MUD client. 
You can also play via browser at http://localhost:4001. 

Check out https://www.evennia.com/docs/latest/index.html for more info on the mechanics of running the MUD

## My changes
Where you want to look and see what I done did

commands/command.py  
commands/default_cmdsets.py  

typeclasses/exits.py  
typeclasses/objects.py  
typeclasses/rooms.py  

world/ai.py
