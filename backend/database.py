import os
import bcrypt
from pymongo import MongoClient


class Database:
    def __init__(self):
        mongo_host = os.environ.get("MONGO_HOST", "mongodb://db:27017")
        self._client = MongoClient(mongo_host)
        self._db = self._client.BankAPI
        self._users = self._db["Users"]
        self._ensure_bank_account()

    def _ensure_bank_account(self):
        if not self.user_exists("BANK"):
            self._users.insert_one({
                "Username": "BANK",
                "Password": b"",
                "Own": 0,
                "Debt": 0
            })

    def user_exists(self, username):
        return self._users.find_one({"Username": username}) is not None

    def register(self, username, password):
        hashed = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
        self._users.insert_one({
            "Username": username,
            "Password": hashed,
            "Own": 0,
            "Debt": 0
        })

    def verify_password(self, username, password):
        stored = self._users.find_one({"Username": username})["Password"]
        return bcrypt.hashpw(password.encode("utf8"), stored) == stored

    def get_balance(self, username):
        return self._users.find_one(
            {"Username": username},
            {"Password": 0, "_id": 0}
        )

    def get_cash(self, username):
        return self._users.find_one({"Username": username})["Own"]

    def get_debt(self, username):
        return self._users.find_one({"Username": username})["Debt"]

    def update_cash(self, username, amount):
        self._users.update_one(
            {"Username": username},
            {"$set": {"Own": amount}}
        )

    def update_debt(self, username, amount):
        self._users.update_one(
            {"Username": username},
            {"$set": {"Debt": amount}}
        )