from dataclasses import dataclass

from gamevolt.configuration.appsettings_base import AppSettingsBase
from gamevolt.configuration.settings_base import SettingsBase


@dataclass
class Person(SettingsBase):
    name: str
    age: int
    gender: bool


@dataclass
class DummySettings(AppSettingsBase):
    name: str
    person: Person


settings = DummySettings.from_yaml("./dummy_settings.yml")

# print(settings)
print(settings.name)
print("----------")
print(settings.person)
print("----------")
print(settings.person.name)
print(settings.person.age)
print(settings.person.gender)
