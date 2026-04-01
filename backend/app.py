import os
import socket
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from database import Database

app = Flask(__name__)
api = Api(app)
db = Database()


def generate_response(status, msg):
    return {"status": status, "msg": msg}


def verify_credentials(username, password):
    if not db.user_exists(username):
        return generate_response(301, "Invalid username"), True
    if not db.verify_password(username, password):
        return generate_response(302, "Invalid password"), True
    return None, False


class Register(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]

        if db.user_exists(username):
            return jsonify(generate_response(301, "Invalid username"))

        db.register(username, password)
        return jsonify(generate_response(200, "You successfully signed up for the API"))


class Add(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        amount = data["amount"]

        ret, error = verify_credentials(username, password)
        if error:
            return jsonify(ret)

        if amount <= 0:
            return jsonify(generate_response(304, "The money amount entered must be positive!"))

        cash = db.get_cash(username)
        bank_cash = db.get_cash("BANK")
        db.update_cash("BANK", bank_cash + 1)
        db.update_cash(username, cash + amount - 1)

        return jsonify(generate_response(200, "Amount added successfully to account"))


class Transfer(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        to = data["to"]
        amount = data["amount"]

        ret, error = verify_credentials(username, password)
        if error:
            return jsonify(ret)

        cash = db.get_cash(username)
        if cash <= 0:
            return jsonify(generate_response(304, "You're out of money, please add or take a loan"))

        if not db.user_exists(to):
            return jsonify(generate_response(301, "Receiver username is invalid"))

        cash_to = db.get_cash(to)
        bank_cash = db.get_cash("BANK")
        db.update_cash("BANK", bank_cash + 1)
        db.update_cash(to, cash_to + amount - 1)
        db.update_cash(username, cash - amount)

        return jsonify(generate_response(200, "Amount transferred successfully"))


class Balance(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]

        ret, error = verify_credentials(username, password)
        if error:
            return jsonify(ret)

        balance = db.get_balance(username)
        return jsonify(balance)


class TakeLoan(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        amount = data["amount"]

        ret, error = verify_credentials(username, password)
        if error:
            return jsonify(ret)

        cash = db.get_cash(username)
        debt = db.get_debt(username)
        db.update_cash(username, cash + amount)
        db.update_debt(username, debt + amount)

        return jsonify(generate_response(200, "Loan added successfully!"))


class PayLoan(Resource):
    def post(self):
        data = request.get_json()
        username = data["username"]
        password = data["password"]
        amount = data["amount"]

        ret, error = verify_credentials(username, password)
        if error:
            return jsonify(ret)

        cash = db.get_cash(username)
        if cash < amount:
            return jsonify(generate_response(303, "You don't have enough money to pay the loan!"))

        debt = db.get_debt(username)
        db.update_cash(username, cash - amount)
        db.update_debt(username, debt - amount)

        return jsonify(generate_response(200, "Loan paid successfully!"))


class Info(Resource):
    def get(self):
        return jsonify({
            "hostname": socket.gethostname(),
            "pod_ip": os.environ.get("POD_IP", "unknown"),
        })


api.add_resource(Register, "/api/register")
api.add_resource(Add, "/api/add")
api.add_resource(Transfer, "/api/transfer")
api.add_resource(Balance, "/api/balance")
api.add_resource(TakeLoan, "/api/take_loan")
api.add_resource(PayLoan, "/api/pay_loan")
api.add_resource(Info, "/api/info")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)