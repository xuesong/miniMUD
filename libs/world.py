""" world.py
    --------
    This is where the meat of the game-code resides.
"""

from libs import player
from libs.log import log
import time

class world:
    """ This is where the action happens! """
    PLAYERS = {}      # A dict of connected players, with addrport() as key.
    ALIVE = True      # Is the server alive?
    UPDATES = []      # A list of updates to execute in the world.
    TICK_LENGTH = 1.0 # How many seconds per tick?
    
    
    """ Public commands available to characters. """
    
    def quit(self, key, modifiers):
        # The user wishes to depart from our fine world.
        self.PLAYERS[key].quit()
    
    
    def reboot(self, key, modifiers):
        # The user wants to reboot the server.
        self.ALIVE = 'reboot'
        self._cleanup()
        log('%s issued the command to reboot.' % key)
    
    
    def shutdown(self, key, modifiers):
        # The user hopes to shut down the server.
        self._cleanup()
        log('%s issued the command to shutdown.' % key)
    
    
    """ Private functions for use by the server. """
    
    def _add_player(self, client):
        # Add a player to the list of connected players.
        self.PLAYERS[client.addrport()] = player.player(client)
    
    
    def _auto_complete(self, word, word_list):
        # Take the given (partial) word and find its equal in the word_list.
        word_length = len(word) # Get the length of the word.
        word = word.lower()     # Put the word in lowercase.
        if(word in word_list):
            # The word is already in the list.
            return word
        else:
            # We need to find out which word closest matches the word provided.
            word_list.sort()
            for item in word_list:
                # Check to see if the word provided could match.
                if(word == item.lower()[0:len(word)]):
                    # This word is a match.
                    return item # Return the item.
            return None # The item wasn't found.
    
    
    def _cleanup(self):
        # Clean up the server, then shut down.
        log('Saving characters...')     # Log about it.
        doing = 'shutting down temporarily'
        if(self.ALIVE == 'reboot'):
            doing = 'rebooting'
        else:
            self.ALIVE = False
        for key in self.PLAYERS.keys(): # Then tell each user, then clean them up.
            self.PLAYERS[key].send('The server is %s. Please come back soon!' % doing)
            self.PLAYERS[key].cleanup()
    
    
    def _drop_player(self, client):
        # Remove a player from our list of connected clients.
        del self.PLAYERS[client.addrport()]
    
    
    def _kick_idle(self):
        # Check for idle clients, then drop them.
        for key in self.PLAYERS.keys():
            # For each player,
            if(self.PLAYERS[key].CLIENT.idle() > 300):
                # If it's been idle for more than 5 minutes,
                self.PLAYERS[key].CLIENT.active = False  # Set it as inactive,
                log('%s timed out.' % client.addrport()) # then log about it.
    
    
    def _process_update(self, key, command, modifiers):
        # Take a piece of input, then act upon it.
        cmd = self._auto_complete(command, self.COMMANDS)
        if(cmd):
            # The command was found in the auto_complete.
            getattr(self, cmd)(key, modifiers) # Execute the command.
        else:
            # The command was not found in the auto_complete.
            self.PLAYERS[key].send("I'm sorry, I don't understand the command '%s'." % (command))
    
    
    def _tick(self):
        # This happens repeatedly, at an increment designated by self.TICK_LENGTH.
        self._kick_idle() # First, get rid of idle players.
        for key in self.PLAYERS.keys():
            # Now, update every player and get their latest action, if applicable.
            update = self.PLAYERS[key].tick()
            if(update != ''):
                # If they returned a legitimate action, append it to the list of updates for processing.
                self.UPDATES.append((key, update))
        
        # Next we need to process all updates from all ticks executed thus far.
        self._update() # Get 'er dunn.
        
        # Finally, we need to pause until the next tick.
        now = time.time()                     # Get the time.
        difference = now - self.LAST_TICK     # Get the time since our last tick.
        pause = self.TICK_LENGTH - difference # Get the remaining time in our tick.
        time.sleep(pause)                     # Sleep for that amount of time.
        self.LAST_TICK = time.time()          # Update the time.
    
    
    def _update(self):
        # Process all the updates returned by the tick.
        updates = self.UPDATES      # We need to clear the list of updates without losing them. So make a copy!
        self.UPDATES = []           # Then clear the current list of updates.
        for update in updates:
            # Process each update individually.
            (key, cmd) = update          # First let's get the raw command and the key of who sent it.
            cmd = cmd.strip().split(' ') # Remove extra whitespace.
            command = cmd[0]             # The command is the first word they issue.
            modifiers = cmd[1:]          # The modifiers are the remaining words they sent.
            self._process_update(key, command, modifiers) # Now parse and handle the input.
    
    
    def __init__(self):
        # Create the world.
        self.LAST_TICK = time.time() # Set our initial tick time.
        self.COMMANDS = []           # This will become the list of commands.
        for item in dir(self):
            # Scan every item in the world class.
            if((item[0] != '_') and hasattr(getattr(self, item), '__call__')):
                # Find all the public commands, then add them to a list.
                self.COMMANDS.append(item)