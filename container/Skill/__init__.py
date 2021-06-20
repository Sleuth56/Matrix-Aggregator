from opsdroid.connector.matrix import ConnectorMatrix
from opsdroid.events import Message, UserInvite, JoinRoom
from opsdroid.matchers import match_event, match_regex
from opsdroid.skill import Skill
import markdown
import logging
import re


_LOGGER = logging.getLogger(__name__)

class Aggregator_Skill(Skill):
  def __init__(self, opsdroid, config):
    super().__init__(opsdroid, config)
    self.join_when_invited = config.get("join_when_invited", True)
    self.logging = config.get("logging", False)
    self.deletion_message = config.get("delete_message", "I deleted your entire message.")
    self.sent_successfully_message = config.get("sent_ack" , "I sent your message!")
    self.nothing_to_send_message = config.get("nothing_to_send", "I don't have anything to send")
    self.nothing_to_preview = config.get("nothing_to_preview", "Their isn't anything to preview")
    self.header_format = config.get("header", "<h2>{user_name} said </h2>")
    self.help_message = ("## Matrix Aggregator Help\n"
                         "just type your messages as you would usually do. "
                         "As many as you would like in fact.\n"
                         "If you would like to preview what you've written type **!preview**\n"
                         "When your ready just type **!send**\n"
                         "Type help to show this again.\n"
                         "If you are totally discusted with what you wrote type **!delete** to errace it from the plannet.\n"
    )

  def MKToHTML(self, string):
    # This is redundant for now. There is a bug where element android doesn't show inline code rn. 
    return markdown.markdown(string)

  async def send_to_destination_rooms(self, string):
    for i in range(len(self.destination_rooms)):
      await self.opsdroid.send(Message(string, target='secondary'))

  @match_event(UserInvite)
  async def respond_to_invites(self, opsdroid, config, invite):
    if (self.logging == True):
      _LOGGER.info(f"Got room invite for {invite.target}.")
    if self.join_when_invited:
      _LOGGER.debug(f"Joining room from invite.")
      await invite.respond(JoinRoom())

  @match_regex(r'^!help|help|hi|hello', case_sensitive=False)
  async def help_menu(self, opsdroid, config, message):
    await message.respond(self.MKToHTML(self.help_message))

  @match_regex(r'(?P<string>^(?!help|!help)((.|\n)*))', case_sensitive=False)
  async def process_message(self, opsdroid, config, message):
    if (self.logging == True):
      _LOGGER.info("matched process_message regex!")
    string = message.regex.group('string')
    if (self.logging == True):
      _LOGGER.info("User Message:" + str(string))

    if ("!delete" in string):
      await opsdroid.memory.delete(message.target)
      await message.respond(self.deletion_message)

    elif ("!send" in string):
      output = self.header_format.format(user_name = message.user)
      messages = await opsdroid.memory.get(message.target)
      if (not isinstance(messages, dict)):
        await message.respond(self.nothing_to_send_message)
        return
      keys = list(messages.keys())
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await message.respond(self.sent_successfully_message)
      await self.send_to_destination_rooms(output)
      await opsdroid.memory.delete(message.target)

    elif ("!preview" in string):
      output = self.header_format.format(user_name = message.user)
      messages = await opsdroid.memory.get(message.target)
      if (not isinstance(messages, dict)):
        await message.respond(self.nothing_to_preview)
        return
      keys = list(messages.keys())
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await message.respond(output)

    elif (r'help|!help' in string):
      _LOGGER.info("Bad match help")

    else:
      if (self.logging == True):
        _LOGGER.info("Message.get = " + str(message.raw_event))
        _LOGGER.info("opsdroid.memory.get message.raw_event is currently: " + str(await opsdroid.memory.get(message.target)))

      # Attempts to get the current message state of the room
      content = await opsdroid.memory.get(message.target)

      # If this returns none create a new dictionary
      if (content == None or content == ""):
        content = {}

      # Extra logging for debuging
      if (self.logging == True):
        _LOGGER.info(message.raw_event)

      # Checks if this message was an edit
      if ("m.relates_to" in message.raw_event['content']):
        if (self.logging == True):
          _LOGGER.info("User Message:" + str(message.raw_event['content']['m.new_content']['body']))

        # Updates the original message with the edit 
        content[message.raw_event['content']['m.relates_to']['event_id']] = self.MKToHTML(message.raw_event['content']['m.new_content']['body'])
      else:
        # Creates new entry for the message
        content[message.raw_event["event_id"]] = self.MKToHTML(message.raw_event["content"]["body"])

      # Log check from the dictionary
      if (self.logging == True):
        _LOGGER.info(str(content))

      # Store the dictionary as the room id
      await opsdroid.memory.put(message.target, content)