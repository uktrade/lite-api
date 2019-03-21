class ValidateOrganisationCreateRequest:
    def __init__(self, request):
        self.is_valid = True

        if request.POST.get('name') == "None":
            self.is_valid = False

        if request.POST.get('eori_number') == "None":
            self.is_valid = False

        if request.POST.get('sic_number') == "None":
            self.is_valid = False

        if request.POST.get('address') == "None":
            self.is_valid = False

        if request.POST.get('admin_user_email') == "None":
            self.is_valid = False
