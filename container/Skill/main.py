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
    self.deletion_message = "I deleted your entire message."
    self.sent_successfully_message = "I sent your message!"
    self.nothing_to_send_message = "I don't have anything to send"
    self.nothing_to_preview = "Their isn't anything to preview"
    # self.header_format = f'<h2>{message.user} said </h2>'
    self.help_message = ("<h2>Matrix Aggregator help</h2>"
                         "just type your messages as you would usually do. "
                         "As many as you would like in fact.<br>"
                         "If you would like to preview what you've written type `!preview`<br>"
                         "When your ready just type `!send`<br>"
                         "Type help to show this again.<br>"
                         "If you are totally discusted with what you wrote type `!delete` to errace it from the plannet.<br>"
    )

  def MKToHTML(self, content):
    if ("```" in content):
      if (self.logging == True):
        _LOGGER.info(str(content.split("```")[1]))


      code_block = content.split("```")[1].split("```")[0].strip('\n')
      content = f'{content.split("```")[0]} <pre><code>{code_block}</code></pre> {content.split("```")[2]}'

    return content.replace("\n", "<br>")


  @match_event(UserInvite)
  async def respond_to_invites(self, opsdroid, config, invite):
    if (self.logging == True):
      _LOGGER.info(f"Got room invite for {invite.target}.")
    if self.join_when_invited:
      _LOGGER.debug(f"Joining room from invite.")
      await invite.respond(JoinRoom())

  @match_regex(r'^!help|help', case_sensitive=False)
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
      await opsdroid.memory.delete(message.raw_event["room_id"])
      await message.respond(self.deletion_message)

    elif ("!send" in string):
      output = f'<h2>{message.user} said </h2>'
      messages = await opsdroid.memory.get(message.raw_event["room_id"])
      if (not isinstance(messages, dict)):
        await message.respond(self.nothing_to_send_message)
        return
      keys = list(messages.keys())
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await message.respond(self.sent_successfully_message)
      await self.opsdroid.send(Message(output))
      await opsdroid.memory.delete(message.raw_event["room_id"])

    elif ("!preview" in string):
      output = f'<h2>{message.user} said </h2>'
      messages = await opsdroid.memory.get(message.raw_event["room_id"])
      if (not isinstance(messages, dict)):
        await message.respond(self.nothing_to_preview)
        return
      keys = list(messages.keys())
      for i in range(len(keys)):
        output += f'{messages[keys[i]]}<br>'
      await message.respond(output)

    elif (r'help' in string):
      _LOGGER.info("Bad match help")

    else:
      if (self.logging == True):
        _LOGGER.info("Message.get = " + str(message.raw_event))
        _LOGGER.info("opsdroid.memory.get message.raw_event is currently: " + str(await opsdroid.memory.get(message.raw_event["room_id"])))

      # Attempts to get the current message state of the room
      content = await opsdroid.memory.get(message.raw_event["room_id"])

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
      await opsdroid.memory.put(message.raw_event["room_id"], content)