from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.events import Message, UserInvite, JoinRoom
from opsdroid.constraints import constrain_connectors
from opsdroid.matchers import match_event, match_regex
from opsdroid.skill import Skill
import logging

_LOGGER = logging.getLogger(__name__)

class ANSSkill(Skill):
  def __init__(self, opsdroid, config):
    super().__init__(opsdroid, config)
    self.join_when_invited = config.get("join_when_invited", True)
    self.logging = True

  # Join all rooms on invite.
  @match_event(UserInvite)
  async def on_invite_to_room(self, config, invite):
    _LOGGER.info(f"Got room invite for {invite.target}.")
    if self.join_when_invited:
      _LOGGER.debug(f"Joining room from invite.")
      await invite.respond(JoinRoom())
      if not config.get('room_notify') in invite.target:
        await invite.respond("hi")
        
      

  # @match_event(JoinRoom)
  # async def on_join(self, join):
  #   opsdroid.send(Message(text="Hi, I'm new", target=self.config.get('room_notify')))
    

  @match_regex(r'(?P<string>.*)')
  @constrain_connectors(['matrix'])
  async def process_message(self, opsdroid, config, Message):
    string = Message.regex.group('string')

    if ("!send" in string):
      output = f'{Message.user}<br>'
      messages = await opsdroid.memory.get(Message.raw_event["room_id"])
      keys = list(messages.keys())
      _LOGGER.info(keys)
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await Message.respond(output)
      await self.opsdroid.send(Message(text=output, target=self.config.get('room_notify')))

    else:
      # Attempts to get the current message state of the room
      content = await opsdroid.memory.get(Message.raw_event["room_id"])

      # If this returns none create a new dictionary
      if (content == None):
        content = {}

      # Extra logging for debuging
      if (self.logging == True):
        _LOGGER.info(Message.raw_event)
        _LOGGER.info(type(content))

      # Checks if this message was an edit
      if ("m.relates_to" in Message.raw_event['content']):
        if (self.logging == True):
          _LOGGER.info(str(Message.raw_event['content']['m.new_content']['body']))

        # Updates the original message with the edit 
        content[Message.raw_event['content']['m.relates_to']['event_id']] = Message.raw_event['content']['m.new_content']['body']
      else:
        if (self.logging == True):
          _LOGGER.info(await opsdroid.memory.get(Message.raw_event["room_id"]))

        # Creates new entry for the message
        content[Message.raw_event["event_id"]] = Message.raw_event["content"]["body"]

      # Log check from the edited dictionary
      if (self.logging == True):
        _LOGGER.info(str(content))

      # Store the dictionary as the room id
      await opsdroid.memory.put(Message.raw_event["room_id"], content)