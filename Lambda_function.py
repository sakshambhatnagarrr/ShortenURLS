import json, os, random, string
import boto3

table = boto3.resource("dynamodb").Table(os.environ.get("TABLE", "urls"))
BASE = os.environ.get("BASE_URL", "")

def code_gen(n=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))

def resp(status, body=None, headers=None):
    h = {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"}
    if headers:
        h.update(headers)
    return {"statusCode": status, "headers": h, "body": json.dumps(body) if body else ""}

def lambda_handler(event, context):
    method = event["requestContext"]["http"]["method"]

    if method == "POST":
        data = json.loads(event.get("body") or "{}")
        url = data.get("url", "")
        if not url.startswith(("http://", "https://")):
            return resp(400, {"error": "Provide a valid http(s) URL"})
        code = code_gen()
        table.put_item(Item={"code": code, "url": url, "clicks": 0})
        return resp(200, {"code": code, "short_url": f"{BASE}/{code}"})

    if method == "GET":
        code = event["pathParameters"]["code"]
        item = table.get_item(Key={"code": code}).get("Item")
        if not item:
            return resp(404, {"error": "Not found"})
        table.update_item(
            Key={"code": code},
            UpdateExpression="ADD clicks :one",
            ExpressionAttributeValues={":one": 1},
        )
        return {"statusCode": 302, "headers": {"Location": item["url"]}, "body": ""}

    return resp(405, {"error": "Method not allowed"})