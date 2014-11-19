import logging
import json
import requests
import os
import boto.sqs
from boto.sqs.message import RawMessage


import flask
from flask import request, Response, Flask, jsonify, abort, make_response


application = flask.Flask(__name__)
application.config.from_object('default_config')
application.debug = application.config['FLASK_DEBUG'] in ['true', 'True']

@application.route('/add-to-que', methods=['POST'])
def add_to_que():
    if not request.json or 'to' not in request.json \
            or 'marketplace_id' not in request.json:
        abort(400)
    account = {
        'to': request.json['to'],
        'marketplace_id': request.json['marketplace_id'],
        }
    try:
        add_to_que(account)
    except Exception, e:
        return jsonify({"error": str(e)}), 500
    return jsonify({"account": account}), 201


def add_to_que(data):
    conn = boto.sqs.connect_to_region("us-east-1")
    # if que exisits it returns exisiting que
    queue = conn.create_queue('chompy')

    # Put the message in the queue
    m = RawMessage()
    m.set_body(json.dumps(data))
    status = queue.write(m)


@application.route('/send', methods=['POST'])
def send():
    """Send an e-mail using Mailgun"""

    response = None
    if request.json is None:
        # Expect application/json request
        response = Response("", status=415)
    else:
        message = dict()
        try:
            message = request.json

            send_simple_message(message['to'], message['marketplace_id'])
            response = Response("", status=200)
        except Exception as ex:
            logging.exception('Error processing message: %s' % request.json)
            response = Response(ex.message, status=500)

    return response

def send_simple_message(to, url_to_file):
    return requests.post(
        os.environ['MAILGUN_DOMAIN'],
        auth=("api", os.environ['MAILGUN_API_KEY']),
        data={"from": 'support@balancedpayments.com',
              "to": [to],
              "subject": 'Balanced CSV Download Ready',
              "text": 'Your CSV is ready to download. ' + marketplace_id +
                      ' This file will be available for you to download for '
                      'the next two days.'
        })

if __name__ == '__main__':
    application.run(host='0.0.0.0')