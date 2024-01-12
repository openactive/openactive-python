import openactive as oa
from flask import Flask, request
from openactive.openactive import set_message

# ----------------------------------------------------------------------------------------------------

application = Flask(__name__)

# ----------------------------------------------------------------------------------------------------

@application.route('/catalogue-urls')
def app_get_catalogue_urls():
    return oa.get_catalogue_urls(
        flatten = str(request.args.get('flatten')).lower() == 'true',
        verbose = str(request.args.get('verbose')).lower() == 'true',
    )

@application.route('/dataset-urls')
def app_get_dataset_urls():
    return oa.get_dataset_urls(
        flatten = str(request.args.get('flatten')).lower() == 'true',
        verbose = str(request.args.get('verbose')).lower() == 'true',
    )

@application.route('/feeds')
def app_get_feeds():
    return oa.get_feeds(
        flatten = str(request.args.get('flatten')).lower() == 'true',
        verbose = str(request.args.get('verbose')).lower() == 'true',
    )

@application.route('/opportunities')
def app_get_opportunities():
    if (   type(request.args.get('url')) != str
        or len(request.args.get('url')) == 0
    ):
        message = 'Invalid input, feed URL must be given as a parameter via "/opportunities?url=your-feed-url"'
        set_message(message, 'warning')
        return message
    return oa.get_opportunities(
        arg = request.args.get('url'),
        verbose = str(request.args.get('verbose')).lower() == 'true',
    )

# ----------------------------------------------------------------------------------------------------

if (__name__ == '__main__'):
    application.run()
