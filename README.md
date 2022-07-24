# Welcome to Evennia!

An Evennia-based port of the original Dragon Ball Advent Truth

An overview of this directory is found [here](https://github.com/evennia/evennia/wiki/Directory-Overview#the-game-directory)

## Directory structure
`./` is your main game directory where you can set the game up and start with your new game right away. The directory structure is highly customizable and can be re-arranged to suit your sense of organisation except for the `server/` directory, as Evennia expects. If you change the directory structure, you must edit/add to your settings file to tell Evennia where to look for things.

## Instruction
Your game's main configuration file is found in
`server/conf/settings.py` (but you don't need to change it to get
started). If you just created this directory (which means you'll already
have a `virtualenv` running if you followed the default instructions),
`cd` to this directory then initialize a new database using

    evennia migrate

To start the server, stand in this directory and run

    evennia start

This will start the server, logging output to the console. Make
sure to create a superuser when asked. By default you can now connect
to your new game using a MUD client on `localhost`, port `4000`.  You can
also log into the web client by pointing a browser to
`http://localhost:4001`.

## Getting started

From here on you might want to look at one of the beginner tutorials:
http://github.com/evennia/evennia/wiki/Tutorials.

Evennia's documentation is here:
https://github.com/evennia/evennia/wiki.

Enjoy!
