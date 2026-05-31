"""Service layer package.

Houses the business-logic / data-access functions that sit between the API
routers and the ORM models. Routes call into these modules (e.g.
``game_service``, ``player_service``, ``prediction_service``) so query and
persistence logic stays out of the HTTP handlers and is independently testable.
"""
