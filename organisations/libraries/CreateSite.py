from organisations.models import Site


class CreateSite:
    def __init__(self, name, address):
        new_site = Site(name=name,
                        address=address)
        new_site.save()