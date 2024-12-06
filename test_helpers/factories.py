import factory


def get_model_for_factory(factory_class, apps):
    model_meta = factory_class._meta.model._meta

    return apps.get_model(model_meta.app_label, model_meta.object_name)


def fullname(cls):
    return f"{cls.__module__}.{cls.__name__}"


def generate_factory(apps, factory_class, **defaults):
    for field_name, field_value in factory_class._meta.declarations.items():
        if field_name in defaults:
            continue
        if not isinstance(field_value, factory.declarations.SubFactory):
            continue
        generated_factory = generate_factory(
            apps,
            field_value.get_factory(),
            **field_value.defaults,
        )
        defaults[field_name] = factory.declarations.SubFactory(generated_factory)

    updated_factory = factory.make_factory(
        get_model_for_factory(factory_class, apps),
        **defaults,
        FACTORY_CLASS=factory_class,
    )
    return updated_factory
