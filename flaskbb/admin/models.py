from wtforms import (TextField, IntegerField, FloatField, BooleanField,
                     SelectField, SelectMultipleField, validators)
from flask.ext.wtf import Form
from flaskbb.extensions import db


class SettingsGroup(db.Model):
    __tablename__ = "settingsgroup"

    key = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=False)
    settings = db.relationship("Setting", lazy="dynamic", backref="group",
                               cascade="all, delete-orphan")

    def save(self):
        """Saves a settingsgroup."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Deletes a settingsgroup."""
        db.session.delete(self)
        db.session.commit()


class Setting(db.Model):
    __tablename__ = "settings"

    key = db.Column(db.String, primary_key=True)
    value = db.Column(db.PickleType, nullable=False)
    settingsgroup = db.Column(db.String,
                              db.ForeignKey('settingsgroup.key',
                                            use_alter=True,
                                            name="fk_settingsgroup"),
                              nullable=False)

    # The name (displayed in the form)
    name = db.Column(db.String, nullable=False)

    # The description (displayed in the form)
    description = db.Column(db.String, nullable=False)

    # Available types: string, integer, float, boolean, select, selectmultiple
    value_type = db.Column(db.String, nullable=False)

    # Extra attributes like, validation things (min, max length...)
    # For Select*Fields required: choices
    extra = db.Column(db.PickleType)

    @classmethod
    def get_form(cls, group):
        """Returns a Form for all settings found in :class:`SettingsGroup`.

        :param group: The settingsgroup name. It is used to get the settings
                      which are in the specified group.
        """

        class SettingsForm(Form):
            pass

        # now parse the settings in this group
        for setting in group.settings:
            field_validators = []

            # generate the validators
            if "min" in setting.extra:
                # Min number validator
                if setting.value_type in ("integer", "float"):
                    field_validators.append(
                        validators.NumberRange(min=setting.extra["min"])
                    )

                # Min text length validator
                elif setting.value_type in ("string"):
                    field_validators.append(
                        validators.Length(min=setting.extra["min"])
                    )

            if "max" in setting.extra:
                # Max number validator
                if setting.value_type in ("integer", "float"):
                    field_validators.append(
                        validators.NumberRange(max=setting.extra["max"])
                    )

                # Max text length validator
                elif setting.value_type in ("string"):
                    field_validators.append(
                        validators.Length(max=setting.extra["max"])
                    )

            # Generate the fields based on value_type
            # IntegerField
            if setting.value_type == "integer":
                setattr(
                    SettingsForm, setting.key,
                    IntegerField(setting.name, validators=field_validators,
                                 description=setting.description)
                )
            # FloatField
            elif setting.value_type == "float":
                setattr(
                    SettingsForm, setting.key,
                    FloatField(setting.name, validators=field_validators,
                               description=setting.description)
                )

            # TextField
            if setting.value_type == "string":
                setattr(
                    SettingsForm, setting.key,
                    TextField(setting.name, validators=field_validators,
                              description=setting.description)
                )

            # SelectMultipleField
            if setting.value_type == "selectmultiple":
                # if no coerce is found, it will fallback to unicode
                if "coerce" in setting.extra:
                    coerce_to = setting.extra['coerce']
                else:
                    coerce_to = unicode

                setattr(
                    SettingsForm, setting.key,
                    SelectMultipleField(
                        setting.name,
                        choices=setting.extra['choices'](),
                        coerce=coerce_to,
                        description=setting.description
                    )
                )

            # SelectField
            if setting.value_type == "select":
                # if no coerce is found, it will fallback to unicode
                if "coerce" in setting.extra:
                    coerce_to = setting.extra['coerce']
                else:
                    coerce_to = unicode

                setattr(
                    SettingsForm, setting.key,
                    SelectField(
                        setting.name,
                        coerce=coerce_to,
                        choices=setting.extra['choices'](),
                        description=setting.description)
                )

            # BooleanField
            if setting.value_type == "boolean":
                setattr(
                    SettingsForm, setting.key,
                    BooleanField(setting.name, description=setting.description)
                )

        return SettingsForm

    @classmethod
    def get_all(cls):
        return cls.query.all()

    @classmethod
    def update(cls, settings, app=None):
        """Updates the current_app's config and stores the changes in the
        database.

        :param config: A dictionary with configuration items.
        """
        updated_settings = {}
        for key, value in settings.iteritems():
            setting = cls.query.filter(Setting.key == key.lower()).first()

            setting.value = value

            updated_settings[setting.key.upper()] = setting.value

            db.session.add(setting)
            db.session.commit()

        if app is not None:
            app.config.update(updated_settings)

    @classmethod
    def as_dict(cls, from_group=None, upper=False):
        """Returns the settings key and value as a dict.

        :param from_group: Returns only the settings from the group as a dict.
        :param upper: If upper is ``True``, the key will use upper-case
                      letters. Defaults to ``False``.
        """
        settings = {}
        result = None
        if from_group is not None:
            result = SettingsGroup.query.filter_by(key=from_group).\
                first_or_404()
            result = result.settings
        else:
            result = cls.query.all()

        for setting in result:
            if upper:
                settings[setting.key.upper()] = setting.value
            else:
                settings[setting.key] = setting.value

        return settings

    def save(self):
        """Saves a setting"""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Deletes a setting"""
        db.session.delete(self)
        db.session.commit()