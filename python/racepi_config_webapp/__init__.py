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
from flask import jsonify

from racepi_config_webapp.config_model import app, db, ConfigurationProfile

@app.route('/')
def root_index():
    return app.send_static_file('index.html')


@app.route('/settings/<configuration_profile_id>')
def get_configuration_profile(configuration_profile_id):
    return jsonify(data="")


@app.route('/settings')
def get_configuration_list():
    data = [d.name for d in ConfigurationProfile.query.all()]
    return jsonify(configuration_profiles=data)

