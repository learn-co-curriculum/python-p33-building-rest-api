# Lesson : Code-Along

## Learning Goals

- Build and test a RESTful API.

---

## Key Vocab

- **Representational State Transfer (REST)**: a convention for developing
  applications that use HTTP in a consistent, human-readable, machine-readable
  way.
- **Application Programming Interface (API)**: a software application that
  allows two or more software applications to communicate with one another. Can
  be standalone or incorporated into a larger product.
- **HTTP Request Method**: assets of HTTP requests that tell the server which
  actions the client is attempting to perform on the located resource.
- **`GET`**: the most common HTTP request method. Signifies that the client is
  attempting to view the located resource.
- **`POST`**: the second most common HTTP request method. Signifies that the
  client is attempting to submit a form to create a new resource.
- **`PATCH`**: an HTTP request method that signifies that the client is
  attempting to update a resource with new information.
- **`PUT`**: an HTTP request method that signifies that the client is attempting
  to update a resource with new information contained in a complete record.
- **`DELETE`**: an HTTP request method that signifies that the client is
  attempting to delete a resource.

---

## Introduction

In the previous lesson we learned how to use the Flask-Smorest library to
implement the following API:

| Method | Endpoint                  | Description                             |
| ------ | ------------------------- | --------------------------------------- |
| GET    | `/api/v1/teams`           | Get a list of all teams.                |
| GET    | `/api/v1/teams/{team_id}` | Get a single team, given its unique id. |

In this lesson, we'll extend the API to create, update, and delete a team:

| Method | Endpoint                  | Description                                                                                              |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------- |
| POST   | `/api/v1/teams`           | Create a team.                                                                                           |
| PATCH  | `/api/v1/teams/{team_id}` | Update a team given its unique id. The team wins and losses can be specified in the body of the request. |
| DELETE | `/api/v1/teams/{team_id}` | Delete a team given its unique id                                                                        |

## Setup

> This lesson is a code-along, so fork and clone the repo.

Run `pipenv install && pipenv shell` to generate and enter your virtual
environment.

```console
$ pipenv install && pipenv shell
```

Change into the `server` directory:

```console
$ cd server
```

You can run the application as a script within the `server/` directory:

```console
$ python app.py
```

If you prefer working in a Flask environment, remember to configure it with the
following commands within the `server/` directory:

```console
$ export FLASK_APP=app.py
$ export FLASK_RUN_PORT=5555
$ flask run
```

When you complete this lesson, commit and push your work using `git` to submit.

---

## POST request

The starter code in the repo contains the solution to the previous lesson. The
file `server/resources.py` creates a `Blueprint` object and defines `MethodView`
classes to handle GET requests for a team resource. Let's update the API to
support POST requests that will add new teams to the data store.

| Method | Endpoint        | Description    |
| ------ | --------------- | -------------- |
| POST   | `/api/v1/teams` | Create a team. |

Consider the `Team` model class in `server/models.py`:

```py
# server/models.py

from enum import StrEnum, auto

class Division(StrEnum):
    Pacific = auto()    # "pacific"
    Central = auto()    # "central"
    Atlantic = auto()   # "atlantic"

class Team:
    all = {}  # dictionary with id as key

    def __init__(self, name, wins, losses, division):
        self.id = len(type(self).all.keys())+1
        self.name = name
        self.wins = wins
        self.losses = losses
        self.division = division
        type(self).all[self.id] = self

    @classmethod
    def seed(cls):
        """Initialize the dictionary with sample data"""
        Team(name="San Jose Swifts", wins=10, losses=2, division=Division.Pacific)
        Team(name="Chicago Chickadees", wins=7, losses=1, division=Division.Central)
        Team(name="Boston Buffleheads", wins=8, losses=3, division=Division.Atlantic)
```

The `Team` initializer method takes parameters for `name`, `wins`, `losses`, and
`division`. Note the `id` is generated based on the dictionary contents. Since
`id` is generated, the user should not provide an id when attempting to make a
POST request to create a new team. Thus, we need to update `server/schemas.py`
to adapt the schema `TeamSchema` such that `id` is not required for
deserialization. This is achieved by making the field `dump_only`, meaning it is
used during serialization but not deserialization. We'll also update the schema
with the following validation rules:

- all input fields are required
- name is not an empty string and is unique
- wins and losses have a minimum value of `0`
- division is one of the defined enum values

```py
from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)
from models import Team, Division

class TeamSchema(Schema):
    __model__ = Team
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    wins = fields.Int(required=True, validate=validate.Range(min=0))
    losses = fields.Int(required=True, validate=validate.Range(min=0))
    division = fields.Str(
        required=True,
        validate=validate.OneOf(
            [division for division in Division.__members__.values()]
        ),
    )  # ["Pacific", "Central", "Atlantic"]

    @validates("name")
    def validate_name( self, value ):
        if any(team.name == value for team in Team.all.values()):
            raise ValidationError("Name must be unique.")
```

Now we can update the `Teams` class in `server/resources.py` to add a new
function to handle the POST request:

```py
from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Team, Division
from schemas import TeamSchema, TeamUpdateSchema

blp = Blueprint("Team API", __name__)

@blp.route("/api/v1.0/teams")
class Games(MethodView):

    @blp.response(200, TeamSchema(many=True))
    def get(self):
        """List teams"""
        return Team.all.values()

    @blp.arguments(TeamSchema)
    @blp.response(201, TeamSchema)
    def post(self, fields):
        """Create a new team"""
        return Team(**fields)

# other MethodView classes
```

- The `post()` method is decorated with `@blp.arguments(TeamSchema)` to indicate
  the request data contains fields as defined in `TeamSchema`.
- The `post()` method is decorated with `@blp.response(201, TeamSchema)` to
  indicate the response returns a successful update status code `201` along with
  the serialized team data based on schema `TeamSchema`.
- The `post()` method returns a new instance of `Team`, instantiated with the
  data passed to the request.

  Running the application, we see the OpenAPI document now includes an endpoint
  for the POST request:

  ![https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/post_request.png
](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/post_request.png)

Click on the "POST" endpoint, then click "Try it out".

The request body contains example request data based on the fields defined in
the schema `TeamSchema`. The fields are generated from the decorator
`@blp.arguments(TeamSchema)` attached to the POST function.

```text
{
  "name": "string",
  "wins": 0,
  "losses": 0,
  "division": "pacific"
}
```

You can assign values to the name, wins, losses and division fields, then press
"Execute" to submit the POST request.

![post request data](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/post_data.png)

If your data passes the validation, you'll see a `201` status code along with
the serialized data of the newly created `Team` object:

![post response](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/post_response.png)

You can use one of the GET endpoints to confirm the team was added to the
dictionary.

Let's also try issuing a POST request with invalid data. For example, we can try
to add a team with a name that already exists, or negative values for wins and
losses, or a non-existent division:

![post invalid request data](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/post_invalid_data.png)

The response includes a 422 status code, along with the various validation
errors:

![post invalid request response](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/post_invalid_response.png)

An error would also occur if the request data includes fields that are not
defined in `TeamSchema`. The server would respond with a 422 status code for the
unknown field.

## PATCH request

The PUT request is normally used to replace all attributes of a resource, while
the PATCH request replaces some of the attributes. We will implement a PATCH
request to update the wins and losses for a team specified by their unique id,
implying modifications to name and division are not supported by the API.

| Method | Endpoint                  | Description                                                                                                  |
| ------ | ------------------------- | ------------------------------------------------------------------------------------------------------------ |
| PATCH  | `/api/v1/teams/{team_id}` | Update a team given its unique id. The team `wins` and `losses` can be specified in the body of the request. |

A PATCH request requires the team `id`, which will be specified in the endpoint
parameter, along with the new values for `wins` and/or `losses` that are
provided in the request header.

Edit `server/schemas.py` to add a new schema named `TeamUpdateSchema` with
fields `wins` and `losses` as shown. Note the fields are not required, meaning a
PATCH request may include data for just one of the fields:

```py
from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)
from models import Team, Division

class TeamSchema(Schema):
    __model__ = Team
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    wins = fields.Int(required=True, validate=validate.Range(min=0))
    losses = fields.Int(required=True, validate=validate.Range(min=0))
    division = fields.Str(
        required=True,
        validate=validate.OneOf(
            [division for division in Division.__members__.values()]
        ),
    )  # ["Pacific", "Central", "Atlantic"]

    @validates("name")
    def validate_name( self, value ):
        if any(team.name == value for team in Team.all.values()):
            raise ValidationError("Name must be unique.")


class TeamUpdateSchema(Schema):
    __model__ = Team
    wins = fields.Int(validate=validate.Range(min=0))
    losses = fields.Int(validate=validate.Range(min=0))
```

Now we can add a new `patch` method to the `TeamsById` class to implement the
PATCH request. Note the request uses `TeamUpdateSchema` to deserialize the
request data, and `TeamSchema` to produce a response containing the serialized
data from the updated `Team` object.

```py
# server/resources.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Team
from schemas import TeamSchema, TeamUpdateSchema

blp = Blueprint("teams", __name__, url_prefix="/api/v1", description="Operations on teams")

@blp.route("/teams")
class Teams(MethodView):

    @blp.response(200, TeamSchema(many=True))
    def get(self):
        """List teams"""
        return Team.all.values()

    @blp.arguments(TeamSchema)
    @blp.response(201, TeamSchema)
    def post(self, fields):
        """Create a new team"""
        return Team(**fields)

@blp.route("/teams/<int:team_id>")
class TeamsById(MethodView):

    @blp.response(200, TeamSchema)
    def get(self, team_id):
        """Get team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        return team

    @blp.arguments(TeamUpdateSchema)
    @blp.response(200, TeamSchema)
    def patch(self, fields, team_id):
        """Update team by id."""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Game {team_id} not found.")
        for key,value in fields.items():
            setattr(team,key,value)

        return team
```

Let's use the OpenAPI doc to test the new PATCH endpoint. We'll update the wins
and losses for team with id 1:

![patch request wins and losses](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/patch_request_all.png)

Since the data is valid, the server responds with a successful 200 status code,
along with the updated team data:

![patch request response](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/patch_response.png)

The `TeamUpdateSchema` does not require either field, so we can make a PATCH
request to update just the `wins` as shown:

![patch request partial data](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/patch_partial.png)

What happens if we try to update a field that is not defined in
`TeamUpdateSchema`? For example, let's try to update the name by passing the
following as the request data:

```text
{
  "wins": 0,
  "losses" : 0,
  "name" : "new name"
}
```

The server response includes the 422 status code along with a descriptive error
message:

![patch unknown field](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/patch_unknown_field.png)

## DELETE request

Let's update our RESTful API to handle DELETE requests.

| Method | Endpoint                  | Description                       |
| ------ | ------------------------- | --------------------------------- |
| DELETE | `/api/v1/teams/{team_id}` | Delete a team given its unique id |

Since the endpoint requires the team id, we need to add the delete method to the
`TeamsById` class:

```py
@blp.route("/teams/<int:team_id>")
class TeamsById(MethodView):

    @blp.response(200, TeamSchema)
    def get(self, team_id):
        """Get team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        return team

    @blp.arguments(TeamUpdateSchema)
    @blp.response(200, TeamSchema)
    def patch(self, fields, team_id):
        """Update team by id."""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Game {team_id} not found.")
        for key,value in fields.items():
            setattr(team,key,value)

        return team

    @blp.response(204)
    def delete(self, team_id):
        """Delete team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        # Delete the team from the dictionary
        del Team.all[team_id]
```

Use the OpenAPI doc to test the DELETE endpoint. Try deleting a team that exists
in the data store:

![delete team with id 1](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/delete_request.png)

The response returns a `204` status code indicating the deletion was successful:

![delete successful 204 response](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/delete_response.png)

However, if we try to delete a team using an id that is not in the datastore,
the server gives an error response.

![delete team with id 100](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/delete_error_request.png)

![delete error response](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/delete_error_response.png)

## Conclusion

Flask-smorest simplifies the process of implementing a RESTful API. We define a
Blueprint with MethodView classes to neatly organize the routes for GET, POST,
PATCH, DELETE, and more.

| Method | Endpoint                  | Description                                                                                              |
| ------ | ------------------------- | -------------------------------------------------------------------------------------------------------- |
| GET    | `/api/v1/teams`           | Get a list of all teams.                                                                                 |
| GET    | `/api/v1/teams/{team_id}` | Get a single team, given its unique id.                                                                  |
| POST   | `/api/v1/teams`           | Create a team.                                                                                           |
| PATCH  | `/api/v1/teams/{team_id}` | Update a team given its unique id. The team wins and losses can be specified in the body of the request. |
| DELETE | `/api/v1/teams/{team_id}` | Delete a team given its unique id.                                                                       |

The OpenAPI doc generated by Flask-Smorest makes it easy to test our RESTful
API:

![openapi restful documentation](https://curriculum-content.s3.amazonaws.com/7139/flask-smorest-intro/restful_api.png)

## Solution Code

```py
from marshmallow import (
    Schema,
    fields,
    validate,
    validates,
    ValidationError
)
from models import Team, Division

class TeamSchema(Schema):
    __model__ = Team
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    wins = fields.Int(required=True, validate=validate.Range(min=0))
    losses = fields.Int(required=True, validate=validate.Range(min=0))
    division = fields.Str(
        required=True,
        validate=validate.OneOf(
            [division for division in Division.__members__.values()]
        ),
    )  # ["Pacific", "Central", "Atlantic"]

    @validates("name")
    def validate_name( self, value ):
        if any(team.name == value for team in Team.all.values()):
            raise ValidationError("Name must be unique.")


class TeamUpdateSchema(Schema):
    __model__ = Team
    wins = fields.Int(validate=validate.Range(min=0))
    losses = fields.Int(validate=validate.Range(min=0))

```

```py
# server/resources.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Team
from schemas import TeamSchema, TeamUpdateSchema

blp = Blueprint("teams", __name__, url_prefix="/api/v1", description="Operations on teams")

@blp.route("/teams")
class Teams(MethodView):

    @blp.response(200, TeamSchema(many=True))
    def get(self):
        """List teams"""
        return Team.all.values()

    @blp.arguments(TeamSchema)
    @blp.response(201, TeamSchema)
    def post(self, fields):
        """Create a new team"""
        return Team(**fields)

@blp.route("/teams/<int:team_id>")
class TeamsById(MethodView):

    @blp.response(200, TeamSchema)
    def get(self, team_id):
        """Get team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        return team

    @blp.arguments(TeamUpdateSchema)
    @blp.response(200, TeamSchema)
    def patch(self, fields, team_id):
        """Update team by id."""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Game {team_id} not found.")
        for key,value in fields.items():
            setattr(team,key,value)

        return team

    @blp.response(204)
    def delete(self, team_id):
        """Delete team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        # Delete the team from the dictionary
        del Team.all[team_id]
```

---

## Resources

- [Flask Smorest](https://flask-smorest.readthedocs.io/en/latest/)
