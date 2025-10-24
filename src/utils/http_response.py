from typing import Optional
import json


def create_http_response(status_code: int, message: str, data: Optional[dict] = None):
    if data is None:
        return {
            'statusCode': status_code,
            'body': json.dumps(
                {
                    'code': status_code,
                    'message': message
                }
            ),
        }
    return {
        'statusCode': status_code,
        'body': json.dumps(
            {
                'code': status_code,
                'message': message,
                'data': data
            }
        ),
    }
