# -*- coding: utf-8 -*-`
"""api.py - Exposes API resources and contains game logic."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue

from models import User, Game, Score
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm, UserForm
from models import GameForms, ScoreForms, UserForms, HistoryForm
from utils import get_by_urlsafe

NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_LOW_SCORES_REQUEST = endpoints.ResourceContainer(
        number_of_results = messages.IntegerField(1),)

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        game = Game.new_game(user.key)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        #taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman! Your word has ' + str(len(game.target_word)) + ' letters.')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game.game_over:
            return game.to_form('Game already over! The word was ' + game.target_word)

        #Ensures guess is lowercase since all target_words are lowercase
        request.guess = request.guess.lower()

        #Allows guessing of entire word but only counts as one attempt
        #Doesn't provide feedback about individual correct letters to dissuade cheating
        if request.guess == game.target_word:
            game.attempts += 1
            game.end_game(True)
            msg = 'You win!'
            game.history.append("(Guess: " + request.guess + ", Message: " + msg + ")")
            game.put()
            return game.to_form(msg)
        elif len(request.guess) == len(game.target_word):
            game.attempts += 1
            msg = "That's not the correct word!"
            game.history.append(("(Guess: " + request.guess + ", Message: " + msg + ")").encode('utf-8'))
            game.put()
            return game.to_form(msg)

        #Handles illegal moves, doesn't add to attempt count
        if len(request.guess) != 1:
            return game.to_form('Please only enter a single letter.')
        elif request.guess in game.guessed_letters:
            return game.to_form('You have already guessed ' + request.guess + '! Please guess a new letter.')
        elif request.guess not in "abcdefghijklmnopqrstuvwxyz":
            return game.to_form('Only letters are allowed as guesses!')

        game.attempts += 1
        game.guessed_letters += request.guess

        if request.guess in game.target_word:
            # Replace asterisks in word_so_far with correctly guessed letters
            for i in range(len(game.target_word)):
                if game.target_word[i] in game.guessed_letters:
                    game.word_so_far = game.word_so_far[:i] + game.target_word[i] + game.word_so_far[i+1:]
            msg = ('You guessed correctly!')
            game.history.append(("(Guess: " + request.guess + ", Message: " + msg + ")").encode('utf-8'))
            game.put()
            return game.to_form(msg)
        else:
            #Calculate number of incorrect guesses
            incorrect_guesses = 0
            for i in range(len(game.guessed_letters)):
                if game.guessed_letters[i] not in game.target_word:
                    incorrect_guesses += 1
            if incorrect_guesses > 5:
                game.end_game(False)
                msg = "You lose!The word was " + game.target_word
                game.history.append(("(Guess: " + request.guess + ", Message: " + msg + ")").encode('utf-8'))
                game.put()
                return game.to_form(msg)
            else:
                msg = ('Incorrect guess! Letter ' + request.guess + ' is not in the word. You are ' + str(6 - incorrect_guesses) + ' incorrect guess(es) from HANGMAN.')
                game.history.append(("(Guess: " + request.guess + ", Message: " + msg + ")").encode('utf-8'))
                game.put()
                return game.to_form(msg)


    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameForms,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Get an individual user's current games"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        games = Game.query(Game.user == user.key)
        games = games.filter(Game.game_over == False)
        return GameForms(
          items=[game.to_form(
            "User {}'s active games.".format(request.user_name)) for game in games])

    @endpoints.method(request_message= GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='games/user/cancel_game',
                      name='cancel_game',
                      http_method='POST')
    def cancel_game(self, request):
        """Cancel a game in progress and penalize player"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game and not game.game_over:
            game.attempts+=3
            game.end_game(False)
            game.key.delete()
            return StringMessage(
              message='Game with key{} has been cancelled and player penalized 3 points'.format(request.urlsafe_game_key))
        elif game and game.game_over:
            return StringMessage(
              message='Game with key{} is already over!'.format(request.urlsafe_game_key))
        else:
          raise endpoints.NotFoundException('A game with this key was not found. It may have been cancelled.')

    @endpoints.method(request_message=GET_LOW_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='scores/low_scores',
                      name='get_low_scores',
                      http_method='GET')
    def get_low_scores(self, request):
        """Generate a list of low scores of won games in ascending order"""
        scores = Score.query(Score.won == True).order(Score.guesses)
        scores = scores.fetch(limit=request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])


    @endpoints.method(response_message=UserForms,
                      path='users/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
        """Get the rankings of each player"""
        items = []
        users = User.query()
        for user in users:
          wins = 0
          guesses = 0
          #Use .fetch() to turn query into an iterable list you can take the len() of
          scores = Score.query(Score.user == user.key).fetch()
          for score in scores:
            guesses += score.guesses
            if score.won:
              wins += 1
          winning_percentage = 100 * wins/float(len(scores))
          items.append(user.to_form(wins, guesses, winning_percentage))
        #Lambda defines nameless inline function
        #items.sort(key=lambda u: u.winning_percentage, reverse = True)
        #http://stackoverflow.com/questions/12749398/using-a-comparator-function-to-sort\
        def _compare_user_games(a, b):
          """Sort user rankings by winning_percentage, then # wins, then # guesses"""
          if a.winning_percentage != b.winning_percentage:
            return int(a.winning_percentage - b.winning_percentage)
          elif a.wins != b.wins:
            return int(a.wins - b.wins)
          else:
            return b.guesses - a.guesses
        items = sorted(items, cmp = _compare_user_games, reverse = True)
        return UserForms(items=items)

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HistoryForm,
                      path='game/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Retrieves an individual game history"""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
          return HistoryForm(items=game.history)
        else:
          raise endpoints.NotFoundException('Game not found!')



api = endpoints.api_server([HangmanApi])