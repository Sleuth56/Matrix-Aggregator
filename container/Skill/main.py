from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.events import Message, OpsdroidStarted, UserInvite, JoinRoom
from opsdroid.matchers import match_event, match_regex, match_always
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
  async def on_invite_to_room(self, invite):
    _LOGGER.info(f"Got room invite for {invite.target}.")
    if self.join_when_invited:
      _LOGGER.debug(f"Joining room from invite.")
      await invite.respond(JoinRoom())

  @match_regex(r'(?P<string>.*)')
  async def last_seen(self, opsdroid, config, message):
    # Grabs the regex string. In this case it's the whole message.
    string = message.regex.group('string')

    # Attempts to get the current message state of the room
    content = await opsdroid.memory.get(message.raw_event["room_id"])

    # If this returns none create a new dictionary
    if (content == None):
      content = {}

    # Extra logging for debuging
    if (self.logging == True):
      _LOGGER.info(message.raw_event)
      _LOGGER.info(type(content))

    # Checks if this message was an edit
    if ("m.relates_to" in message.raw_event['content']):
      if (self.logging == True):
        _LOGGER.info(str(message.raw_event['content']['m.new_content']['body']))

      # Updates the original message with the edit 
      content[message.raw_event['content']['m.relates_to']['event_id']] = message.raw_event['content']['m.new_content']['body']
    else:
      if (self.logging == True):
        _LOGGER.info(await opsdroid.memory.get(message.raw_event["room_id"]))

      # Creates new entry for the message
      content[message.raw_event["event_id"]] = message.raw_event["content"]["body"]

    # Log check from the edited dictionary
    if (self.logging == True):
      _LOGGER.info(str(content))

    # Store the dictionary as the room id
    await opsdroid.memory.put(message.raw_event["room_id"], content)