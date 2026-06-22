class Music:
    def __init__(self):
        self.name = "music"
        self.description = "Подписка на музыку"
        self.price = 250

class Courses:
    def __init__(self):
        self.name = "courses"
        self.description = "Подписка на курсы"
        self.price = 500

class Movies:
    def __init__(self):
        self.name = "movies"
        self.description = "Подписка на фильмы"
        self.price = 750

SERVICES = {
    "music": Music(),
    "courses": Courses(),
    "movies": Movies(),
}

def get_service(service_name: str):
    return SERVICES.get(service_name)