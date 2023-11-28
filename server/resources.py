# server/resources.py

from flask.views import MethodView
from flask_smorest import Blueprint, abort

from models import Team
from schemas import TeamSchema

blp = Blueprint("teams", __name__, url_prefix="/api/v1", description="Operations on teams")

@blp.route("/teams")
class Teams(MethodView):

    @blp.response(200, TeamSchema(many=True))
    def get(self):
        """List teams"""
        return Team.all.values()

@blp.route("/teams/<int:team_id>")
class TeamsById(MethodView):

    @blp.response(200, TeamSchema)
    def get(self, team_id):
        """Get team by id"""
        team = Team.all.get(team_id)
        if team is None:
            abort(404, message=f"Team {team_id} not found.")
        return team