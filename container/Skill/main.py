from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.events import Message, UserInvite, JoinRoom
from opsdroid.matchers import match_event, match_regex
from opsdroid.skill import Skill
import logging

_LOGGER = logging.getLogger(__name__)

class Aggregator_Skill(Skill):
  def __init__(self, opsdroid, config):
    super().__init__(opsdroid, config)
    self.join_when_invited = config.get("join_when_invited", True)
    self.logging = False

  @match_event(UserInvite)
  async def respond_to_invites(self, opsdroid, config, invite):
    if (self.logging == True):
      _LOGGER.info(f"Got room invite for {invite.target}.")
    if self.join_when_invited:
      _LOGGER.debug(f"Joining room from invite.")
      await invite.respond(JoinRoom())

  @match_regex(r'^!help|help', case_sensitive=False)
  async def help_message(self, opsdroid, config, message):
    await message.respond("My help message isn't ready yet.")

  @match_regex(r'(?P<string>^(?!help|!help)((.|\n)*))', case_sensitive=False)
  async def process_message(self, opsdroid, config, message):
    _LOGGER.info("match!")
    string = message.regex.group('string')
    if (self.logging == True):
      _LOGGER.info(str(string))
    if ("!send" in string):
      output = f'<h2>{message.user} said</h2>'
      messages = await opsdroid.memory.get(message.raw_event["room_id"])
      if (not isinstance(messages, dict)):
        await message.respond("I don't have anything to send")
        return
      keys = list(messages.keys())
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await message.respond(output)
      await self.opsdroid.send(Message("I sent your message!"))
      await opsdroid.memory.delete(message.raw_event["room_id"])

    elif ("!preview" in string):
      output = f'<h2>{message.user} said</h2>'
      messages = await opsdroid.memory.get(message.raw_event["room_id"])
      if (not isinstance(messages, dict)):
        await message.respond("Their isn't anything to preview")
        return
      keys = list(messages.keys())
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await message.respond(output)

    elif (r'help' in string):
      _LOGGER.info("Bad match help")

    else:
      # Attempts to get the current message state of the room
      content = await opsdroid.memory.get(message.raw_event["room_id"])

      # If this returns none create a new dictionary
      if (content == None or content == ""):
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

      # Log check from the dictionary
      if (self.logging == True):
        _LOGGER.info(str(content))

      content[message.raw_event["event_id"]] = content[message.raw_event["event_id"]].replace("\n", "<br>")

      # Store the dictionary as the room id
      await opsdroid.memory.put(message.raw_event["room_id"], content)