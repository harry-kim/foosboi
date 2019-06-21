from errbot import BotPlugin, botcmd, arg_botcmd, re_botcmd
import re
from random import randint


class Lightning(BotPlugin):
    """
    Example for lightning talk
    """

    # Passing split_args_with=None will cause arguments to be split on any kind
    # of whitespace, just like Python's split() does
    @botcmd(split_args_with=None)
    def hello(self, message, args):
        """Obligtary first program."""
        return "Hello World"
    
    @re_botcmd(pattern=r"^(([Cc]an|[Mm]ay) I have a )?cookie please\?$")
    def hand_out_cookies(self, msg, match):
        """
        Gives cookies to people who ask me nicely.

        This command works especially nice if you have the following in
        your `config.py`:

        BOT_ALT_PREFIXES = ('Err',)
        BOT_ALT_PREFIX_SEPARATORS = (':', ',', ';')

        People are then able to say one of the following:

        Err, can I have a cookie please?
        Err: May I have a cookie please?
        Err; cookie please?
        """
        yield "Here's a cookie for you, {}".format(msg.frm)
        yield "*hands you a cookie.*"

    
    @re_botcmd(pattern=r"(^| )secret location?( |$)", prefixed=False, flags=re.IGNORECASE)
    def secret_location(self, msg, match):
        """ Find out the secret lunch location!"""
        self.send(msg.frm, "Shh... the secret lunch location is outside Sobeys!")
        self.send(msg.frm, "Don't tell Janice!:smiling_face_with_smiling_eyes_and_hand_covering_mouth:")

    @botcmd
    def egypt(self, msg, args):
        """Find out who was the coolest Egyptian of all time!?"""

        images = {
            'akram':  "https://avatars2.githubusercontent.com/u/33161840?s=460&v=4",
            'aser': 'https://www.listify.ca/listify-uploads/afe08ba9.jpg',
            'ramses': 'https://www.egypttoursportal.com/wp-content/uploads/2017/11/King-Ramses-II-Egypt-Tours-Portal-1-e1511900083998.jpg'
        }

        egyptian_list = ['akram', 'aser', 'ramses']
        egyptian = egyptian_list[randint(0, 2)]

        self.send_card(title='The coolest Egyptian of all time',
                       body='It was {}!!'.format(egyptian.upper()),
                       thumbnail='',
                       image=images[egyptian],
                       #link='http://www.google.com',
                       #fields=(('First Key','Value1'), ('Second Key','Value2')),
                       color='red',
                       in_reply_to=msg)
