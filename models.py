"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb

#word list of common English words from http://www.manythings.org/vocabulary/lists/l/words.php?f=noll15
words = ['acres','adult','advice','arrangement','attempt',
'autumn','border','breeze','brick','calm','canal','cast','chose',
'claws','coach','constantly','contrast','cookies','customs','damage',
'deeply','depth','discussion','doll','donkey',
'essential','exchange','exist','explanation','facing','film','finest',
'fireplace','floating','folks','fort','garage','grabbed','grandmother','habit',
'happily', 'heading','hunter','image','independent',
'instant','kids','label','lungs','manufacturing',
'mathematics','melted','memory','mill','mission','monkey','mysterious',
'neighborhood','nuts','occasionally','official','ourselves','palace',
'plates','poetry','policeman','positive',
'possibly','practical','pride','promised','recall','relationship','remarkable',
'require','rhyme','rocky','rubbed','rush','sale','satellites','satisfied',
'scared','selection','shake','shaking','shallow','shout','silly','simplest',
'slight','slip','slope','soap','solar','species','spin','stiff','swung','tales',
'thumb','tobacco','toy','trap','treated','tune','university','vapor','vessels',
'wealth','wolf','zoo']

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
    wins = ndb.IntegerProperty(default = 0)
    guesses = ndb.IntegerProperty(default = 0)
    winning_percentage = ndb.FloatProperty(default = 0.0)

    def to_form(self, wins, guesses, winning_percentage):
        form = UserForm()
        form.user_name = self.name
        form.email = self.email
        form.wins = wins
        form.guesses = guesses
        form.winning_percentage = winning_percentage
        return form


class Game(ndb.Model):
    """Game object"""
    user = ndb.KeyProperty(required=True, kind='User')
    target_word = ndb.StringProperty(required=True)
    attempts = ndb.IntegerProperty(required=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    guessed_letters = ndb.StringProperty()
    history = ndb.StringProperty(repeated = True)
    word_so_far = ndb.StringProperty()



    @classmethod
    def new_game(cls, user):
        """Creates and returns a new game"""
        game = Game(user=user,
                    target_word=random.choice(words),
                    attempts=0,
                    game_over=False,
                    guessed_letters = "",
                    history = [])
        game.word_so_far = ("*" * len(game.target_word))
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.game_over = self.game_over
        form.message = message
        form.user_name = self.user.get().name
        form.word_so_far = self.word_so_far
        form.attempts = self.attempts
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      guesses=self.attempts)
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

class UserForm(messages.Message):
    """UserForm for outbound User information"""
    user_name = messages.StringField(1, required=True)
    wins = messages.IntegerField(2)
    guesses = messages.IntegerField(3)
    winning_percentage = messages.FloatField(4)
    email = messages.StringField(5)

class UserForms(messages.Message):
    """Return multiple UserForms"""
    items = messages.MessageField(UserForm, 1, repeated=True)

class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    game_over = messages.BooleanField(2, required=True)
    message = messages.StringField(3, required=True)
    user_name = messages.StringField(4, required=True)
    attempts = messages.IntegerField(5, required=True)
    word_so_far = messages.StringField(6)


class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    guesses = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class HistoryForm(messages.Message):
    """HistoryForm for outbound History information"""
    items = messages.StringField(1, repeated = True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
