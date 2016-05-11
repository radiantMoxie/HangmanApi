#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import HangmanApi

from models import User, Game

class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with at least 1 incomplete game.
        Called every 24 hours using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        for user in users:
            games = Game.query(Game.user == user.key)
            games = games.filter(Game.game_over == False)
            if games.count() > 0:
                subject = 'This is a reminder to prevent an execution!'
                body = 'Hello {}, please complete your Hangman game!'.format(user.name)

                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)

app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)