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
from flask import jsonify, request
from racepi_config_webapp.config_model import \
    app, db, ConfigurationProfile, ActiveConfigurationProfile

db.create_all()


@app.route('/')
def root_index():
    return app.send_static_file('index.html')


def get_configuration_profile(configuration_profile_name):
    config = ConfigurationProfile.query.filter_by(name=configuration_profile_name).first_or_404()

    data = {
        'id': config.id,
        'name': config.name,
        'session_db_path': config.session_db_path
    }
    return jsonify(configuration_profile=data)


def set_configuration_profile(configuration_profile_name, request_data):
    config = ConfigurationProfile.query.filter_by(name=configuration_profile_name).first_or_404()
    if request_data and config:
        config.name = request_data['name']
        config.session_db_path = request_data['session_db_path']

    db.session.commit()
    return jsonify({})


@app.route('/active_setting_profile/<configuration_profile_name>')
def active_configuration_profile(configuration_profile_name):
    config = ConfigurationProfile.query.filter_by(name=configuration_profile_name).first_or_404()
    acp = ActiveConfigurationProfile(config.id)
    db.session.add(acp)
    db.session.commit()
    return get_configuration_profile(configuration_profile_name)


@app.route('/settings/<configuration_profile_name>', methods=['GET', 'POST'])
def readwrite_config_profile(configuration_profile_name):
    if 'POST' in request.method:
        data = request.json.get('configuration_profile')
        return set_configuration_profile(configuration_profile_name, data)
    else:
        return get_configuration_list(configuration_profile_name)


@app.route('/settings')
def get_configuration_list():
    data = [d.name for d in ConfigurationProfile.query.all()]
    return jsonify(configuration_profiles=data)

