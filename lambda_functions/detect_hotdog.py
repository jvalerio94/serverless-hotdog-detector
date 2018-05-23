import os
import urllib
import boto3
import json

BOT_EMAIL = os.environ['BOT_EMAIL']  # Webex Teams Bot ID from environment variables
BOT_TOKEN = os.environ['BOT_TOKEN']  # Webex Teams Bot Bearer Auth token from environment variables

rekognition = boto3.client('rekognition')


def lambda_handler(message, context):
    print('Validating message...')
    msg_details = message['data']

    msg_id = msg_details['id']
    room_id = msg_details['roomId']

    print(msg_details)

    if 'files' in msg_details:
        file_details = msg_details['files']
        if len(file_details) > 1:
            print("More than one files found in message id: " + msg_id)
            message = "Sorry, I can only handle one image at a time!"
        else:
            file_url = file_details[0]
            print('Downloading image...')
            image_bytes = download_image(file_url)

            print('Checking for hotdogs...')
            is_hotdog = detect_hotdog(image_bytes)

            if is_hotdog:
                print('Hotdog detected...')
                message = 'Hotdog ✅'
            else:
                print('Hotdog not detected...')
                message = 'Not hotdog ❌'

        post_message(room_id, message)
    else:
        print("No files found in message id: " + msg_id)
        post_message(room_id, "Hey there, your text is not a hotdog.. I need an image to analyze.")


def download_image(url):
    """ Download image from Teams URL using bearer token authorization.

    Args:
        url (string): Teams URL for uploaded image.

    Returns:
        (bytes)
        Blob of bytes for downloaded image.


    """
    request = urllib.request.Request(url, headers={'Authorization': 'Bearer %s' % BOT_TOKEN})
    return urllib.request.urlopen(request).read()


def detect_hotdog(image_bytes):
    """ Checks image for hotdog label using Amazon Rekoginition's object and scene detection deep learning feature.

    Args:
        image_bytes (bytes): Blob of image bytes.

    Returns:
        (boolean)
        True if object and scene detection finds hotdog in blob of image bytes.
        False otherwise.

    """
    try:
        response = rekognition.detect_labels(
            Image={
                'Bytes': image_bytes,
            },
            MinConfidence=80.0
        )
    except Exception as e:
        print(e)
        print('Unable to detect labels for image.')
        raise (e)
    labels = response['Labels']
    if any(label['Name'] == 'Hot Dog' for label in labels):
        return True
    return False


def post_message(room_id, message):
    """ Posts message to Webex Teams Space via Teams API.

    Args:
        room_id (string): Room ID of the space to send message to.
        message (string): Message to post to channel

    Returns:
        (None)
    """
    url = 'https://api.ciscospark.com/v1/messages'
    msg_data = {'roomId': room_id, 'text': message}
    data = json.dumps(msg_data).encode('utf8')
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer %s' % BOT_TOKEN}

    request = urllib.request.Request(url, data, headers)
    urllib.request.urlopen(request)