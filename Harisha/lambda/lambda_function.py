import urllib.request
import time


def lambda_handler(event, context):
    
    url = "http://www.westernsydney.edu.au/"

    start_time = time.time()

    try:
        response = urllib.request.urlopen(url)

        end_time = time.time()

        return{
            "website":url,
            "status_code": response.status,
            "response_time": round(end_time - start_time, 3),
            "status": "UP"
        }

    except Exception as e:
      return {
        "website": url,
        "status": "DOWN",
        "error": str(e)
      }