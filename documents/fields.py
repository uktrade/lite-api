from django.db.models import FileField


class S3FileField(FileField):
    def save(self, name, content, save=True):
        name = self.field.generate_filename(self.instance, name)
        self.name = name  # self.storage.save(name, content, max_length=self.field.max_length)
        setattr(self.instance, self.field.name, self.name)
        self._committed = True

        # Save the object because it has changed, unless save is False
        if save:
            self.instance.save()
    save.alters_data = True
