from opsdroid.connector.matrix import ConnectorMatrix
# from opsdroid.connector.matrix.events import MatrixStateEvent
from opsdroid.events import Message, OpsdroidStarted, UserInvite, JoinRoom
from opsdroid.matchers import match_event, match_regex, match_always
from opsdroid.skill import Skill
from time import sleep
import logging

_LOGGER = logging.getLogger(__name__)

class ANSSkill(Skill):
  def __init__(self, opsdroid, config):
    super().__init__(opsdroid, config)
    self.join_when_invited = config.get("join_when_invited", True)

  @match_event(UserInvite)
  async def on_invite_to_room(self, invite):
    """
    Join all rooms on invite.
    """
    _LOGGER.info(f"Got room invite for {invite.target}.")
    if self.join_when_invited:
      _LOGGER.debug(f"Joining room from invite.")
      await invite.respond(JoinRoom())

  @match_regex(r'(?P<string>.*)')
  async def last_seen(self, opsdroid, config, message):
    string = message.regex.group('string')
    #  {0: "test"}
    # await opsdroid.memory.put(str(message.target), string)
    previousKey = None

    try:
      previousKey = str(message.raw_event)
    except KeyError:
      pass

    if (previousKey != None):
      await message.respond(previousKey)
    else:
      await message.respond("Nothing.")
    # await message.respond(str(await opsdroid.memory.get(str(message.target))))