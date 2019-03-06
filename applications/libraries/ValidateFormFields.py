class ValidateFormFields:
    def __init__(self, draft):
        self.ready_for_submission = True
        if draft.user_id is None:
            self.user_id = "User id cannot be blank"
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
        if draft.control_code is None:
            self.control_code = "Control code cannot be blank"
            self.ready_for_submission = False
