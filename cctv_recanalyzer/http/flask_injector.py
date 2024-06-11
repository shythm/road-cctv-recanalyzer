from flask import Flask
from abc import ABC, abstractmethod

class FlaskInjector(ABC):
    @abstractmethod
    def inject(self, app: Flask, endpoint: str):
        pass