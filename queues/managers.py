from django.db import models


class QueueManager(models.Manager):
    def team(self, team_id):
        return self.filter(team_id=team_id)
