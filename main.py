#! /bin/env python
"""This module contains the main class to operate the app dispenser app"""

import docker
import os
import re
import logging

LOGGER = logging.getLogger()


class App(object):
    def __init__(self, name, client, workers=1):
        """Create an app

            Args:
                name (str): app name
                client (DockerClient): docker daemon client
                workers (int): Experiental number of app instance
        """
        self.name = name
        self.docker = docker


class AppDispenser(object):
    def __init__(self, app_limit=-1, domain="domain.com", docker_host=None):
        """main class of the app, control the creation of the app
        instances, route and monior them later

        Args:
            app_limit (int): Maximum number of app instance allowed
            domain (str): base domain name to serve the apps under
            docker_host (str): hostname and port of docker daemon
            if it is not local
        """
        self.app_limit = app_limit
        self.domain = domain
        self.docker_host = docker_host
        self.app_names = []
        # Regex for valid app name, mainly a valid subdomain
        self.app_name_validator = re.compile(r"^[a-zA-Z0-9][ A-Za-z0-9_-]*$")
        # exit if app_limit is set to 0
        if self.app_limit == 0:
            LOGGER.info("Cannot create apps due to app limit")
        # Exit if we cannot contact the docker daemon
        # Set DOCKER_HOST env variable if provided
        if self.docker_host:
            LOGGER.debug("Trying to contact remote docker client")
            os.environ["DOCKER_HOST"] = self.docker_host
        else:
            LOGGER.debug("Trying to contact local docker daemon")
        try:
            self.docker_client = docker.from_env()
        except Exception as ex:
            LOGGER.error(
                "Cannot contact docker daemon please check docker service")
            raise ex
        # Create the docker container app to route traffic to new apps
        # TODO: for this iteration the nginx is a special application because
        # we need to change its config to enable traffic to be routed to
        # the correct container, will need to see if there is another solution
        nginx_container = None
        if not nginx_container:
            raise Exception("Cannot run while nginx app is down")

    def create_app(self, name=None):
        """As stupid as it can be in this iteration, no need for information
        from the user to create the app just return an app URL
        after it is created

        Args:
            name (str): name of the docker container and eventually the app
        """
        # the name is used as a subdomain, check it is unique
        if name is None:
            # TODO: use custom exception
            raise Exception("Cannot create an app without name")
            if not self.validate_name(name):
                raise Exception("Name is not unique nor/or valid")
        app = App(client=self.client, name=name)
        app.start()
        if app.is_alive():
            LOGGER.debug("App %s started successfully", app.id)
        # if the app is alive then route the traffic to the app
        self.web_server.route(app)
        # everything is cool ? add app name to list
        self.app_names.append(name)
        return app.url

    def kill_app(self, app_id, reasons=None):
        """Kill running or stopped app

        Args:
            app_id (str): app identifier, use docker container id
            reasons (str): Optional register reasons to kill the app
        """
        app = App.get_app(id=app_id)
        if app:
            app.kill()
            if not app.is_alive():
                LOGGER.debug("app %s killed", app.id)
                return True
        return False

    def stop_app(self, app_id, reasons=None):
        """Stop the container running the app

        Args:
            app_id (str): app_id, same as docker id
            reasons (str): Optional reaosns to stop the app
        """
        app = App.get_app(id=app_id)
        if app:
            app.kill()
            if app.is_stopped():
                LOGGER.debug("App %s is stopped", app.id)
                return True
        return False

    def validate_name(self, name):
        """Validate the app name to be unique and valid

        Args:
            name (str): app name to validate
        """
        if not self.app_name_validator.match(name):
            LOGGER.error("App name %s is not valid against our regex", name)
            return False
        if name in self.app_names:
            LOGGER.error("App name %s exists already", name)
            return False
