class ValidateFormFields:
    def __init__(self, draft):
        self.ready_for_submission = True
        if draft.name is None:
            self.name = "Name cannot be blank"
            self.ready_for_submission = False
        if draft.usage is None:
            self.usage = "Usage cannot be blank"
            self.ready_for_submission = False
        if draft.activity is None:
            self.activity = "Activity cannot be blank"
            self.ready_for_submission = False
        if draft.destination is None:
            self.destination = "Destination cannot be blank"
            self.ready_for_submission = False