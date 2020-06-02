from enum import Enum


class TemplateType(Enum):
    ECJU_CREATED = "ecju_created"
    APPLICATION_STATUS = "application_status"

    @property
    def template_id(self):
        return {
            self.ECJU_CREATED: "bcf052e0-54d9-4ed2-b77e-2f5a77589466",
            self.APPLICATION_STATUS: "b9c3403a-8d09-416e-acd3-99baabf5b043",
        }[self]
