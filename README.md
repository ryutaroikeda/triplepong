Triple pong


A pong game for three players. And flappy birds!

[![Build Status](https://travis-ci.org/ryutaroikeda/triplepong.svg?branch=master)](https://travis-ci.org/ryutaroikeda/triplepong)

To do:

Engine:
* Event rewind.
* Eliminate dependency on renderer (to get rid of pygame import)

Testing:
* Make unittests pass. (Rewind with key is broken.)
* Make travis pass. (Travis can't find pygame.)

Networking:
* Test performance after engine is completed.

User Interface:
* Command line for setting up server / client.
* Render the score.
* Render the time (until next rotation, end of game).
* End of game message.
* Menu for choosing game server.
* Sound effects.
* Music.

Extensions:
* Support UPnP.
* AI player.
* Official website. 
* Smart-phone app.
* Port to browser.
