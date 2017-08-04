# Copyright 2017 Donour Sizemore
#
# This file is part of RacePi
#
# RacePi is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2.
#
# RacePi is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RacePi.  If not, see <http://www.gnu.org/licenses/>.


from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/test.db'
db = SQLAlchemy(app)


class ConfigurationProfile(db.Model):
    """
    Basic Configuration Profile information
    """
    id = db.Column(db.Integer, primary_key=True, unique=True, nullable=False)
    name = db.Column(db.String(80), unique=True, nullable=False)
    session_db_path = db.Column(db.String(2048))

    captured_can_ids = db.relationship('CapturedCanIds', backref='configuration_profile', lazy='select')

    def __init__(self, name, session_db_path):
        self.name = name
        self.session_db_path = session_db_path

    def __repr__(self):
        return '<ConfigurationProfile %r>' % self.name


class CapturedCanIds(db.Model):
    """
    Collections of CAN IDs that are captured through direct bus listening
    """
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    configuration_profile_id = db.Column(db.Integer, db.ForeignKey("configuration_profile.id"))
    can_id = db.Column(db.Integer, nullable=False)

    def __init__(self, session_db_path):
        self.session_db_path = session_db_path

    def __repr__(self):
        return '<CapturedCanIds %r>' % self.id


