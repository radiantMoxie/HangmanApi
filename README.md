#Hangman Api

## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
3. You'll need to open Chrome using a special command-line flag since this API 
 is hosted over HTTP: --unsafely-treat-origin-as-secure
 
 
##Game Description:
Hangman is a simple word guessing game. Each game begins with a random 'target_word'
whose length is specified to the user and noted by the number of asterisks in the 
'word_so_far'. 'Guesses' are sent to the `make_move` endpoint which will reply 
with information about whether that guess is valid and/or present in the word. Entire
words can also be guessed.

Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

Scores are determined by number of wins, winning percentage, and number of guesses.
It is in the user's score interest to attempt to guess the word in as few guesses
as possible.


##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist or if that user has 
    no scores yet.
    
 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: None
    - Returns: GameForms
    - Description: Get an individual user's current games. Will raise a NotFoundException 
    if there are no active games for the requested user.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel_game'
    - Method: POST
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: Cancel a game in progress and penalize player 3 points. Will raise a 
    NotFoundException if the game can't be found.

 - **get_low_scores**
    - Path: 'game/{urlsafe_game_key}/cancel_game'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms
    - Description: Generate a list of low scores of won games in ascending order.

 - **get_user_rankings**
    - Path: 'users/rankings'
    - Method: GET
    - Parameters: None
    - Returns: UserForms
    - Description: Get the rankings of each player. First ordered by number of wins, 
    then winning percentage, then number of guesses.

 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: HistoryForm
    - Description: Retrieves an individual game history.

##Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.
    
##Forms Included:
 - **UserForm**
    - Representation of a User's state (user_name, wins, guesses, winning_percentage,
    email).
 - **UserForms**
    - Multiple UserForm container.
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name).
 - **GameForms**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (user_name)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **HistoryForm**
    - Representation of a game's History presented in a list.
 - **StringMessage**
    - General purpose String container.