"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

words = ['acres','adult','advice','arrangement','attempt','August',
'Autumn','border','breeze','brick','calm','canal','Casey','cast','chose',
'claws','coach','constantly','contrast','cookies','customs','damage',
'Danny','deeply','depth','discussion','doll','donkey','Egypt','Ellen',
'essential','exchange','exist','explanation','facing','film','finest',
'fireplace','floating','folks','fort','garage','grabbed','grandmother','habit',
'happily','Harry','heading','hunter','Illinois','image','independent',
'instant','January','kids','label','Lee','lungs','manufacturing','Martin',
'mathematics','melted','memory','mill','mission','monkey','Mount','mysterious',
'neighborhood','Norway','nuts','occasionally','official','ourselves','palace',
'Pennsylvania','Philadelphia','plates','poetry','policeman','positive',
'possibly','practical','pride','promised','recall','relationship','remarkable',
'require','rhyme','rocky','rubbed','rush','sale','satellites','satisfied',
'scared','selection','shake','shaking','shallow','shout','silly','simplest',
'slight','slip','slope','soap','solar','species','spin','stiff','swung','tales',
'thumb','tobacco','toy','trap','treated','tune','University','vapor','vessels',
'wealth','wolf','zoo']

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    attempts_allowed = ndb.IntegerProperty(required=True)
    wrong_guesses_remaining = ndb.IntegerProperty(required=True)
    target_word = ndb.StringProperty(required=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')

    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user,
                    target_word=random.choice(words),
                    attempts_allowed=100,
                    wrong_guesses_remaining=5,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.wrong_guesses_remaining = self.wrong_guesses_remaining
        form.game_over = self.game_over
        form.message = message
        form.target_word= self.target_word
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts_allowed - self.attempts_remaining)
        score.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), guesses=self.guesses)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    wrong_guesses_remaining = messages.IntegerField(2, required=True, default=6)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    target_word = messages.StringField(6, required=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.IntegerField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)