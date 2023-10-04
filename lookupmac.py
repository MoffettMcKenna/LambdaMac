import json


def lambda_handler(event, context):
    print(event)
    decoded = json.loads(event['body'])
    print(decoded)

    return {
        'headers': {"Content-Type": "image/png"},
        'isBase64Encoded': True,
        "result": "Success",
        "orgs": [{
            decoded['macs'][0]: "test1",
            decoded['macs'][1]: "Test2"
        }],
        'images':
            [{
                'test1': 'base64 encoded data, decoded to utf-8',
                'Test2': 'base64 encoded data, decoded to utf-8'
            }]
    }