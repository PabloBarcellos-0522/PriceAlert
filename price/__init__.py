from importlib import import_module

create_app = import_module("app").create_app