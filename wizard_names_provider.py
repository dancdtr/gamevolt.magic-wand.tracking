import random

_NAMES = [
    "Harry Potter",
    "Hermione Granger",
    "Ron Weasley",
    "Albus Dumbledore",
    "Minerva McGonagall",
    "Severus Snape",
    "Sirius Black",
    "Remus Lupin",
    "Rubeus Hagrid",
    "Bellatrix Lestrange",
    "Lord Voldemort",
    "Draco Malfoy",
    "Lucius Malfoy",
    "Narcissa Malfoy",
    "Ginny Weasley",
    "Luna Lovegood",
    "Neville Longbottom",
    "Dolores Umbridge",
    "Gellert Grindelwald",
    "Kingsley Shacklebolt",
    "Gilderoy Lockhart",
]


class WizardNameProvider:
    def get_name(self) -> str:
        return random.choice(_NAMES)
