from fastapi import FastAPI, File, UploadFile
from fastapi.responses import PlainTextResponse
import boto3
import asyncio
import uvicorn

app = FastAPI()

ASU_ID = "1232089042"
S3_BUCKET_NAME = f"{ASU_ID}-in-bucket"
DOMAIN_NAME = f"{ASU_ID}-simpleDB"

s3_client = boto3.client('s3', region_name='us-east-1')
sdb_client = boto3.client('sdb', region_name='us-east-1')

async def upload_image_to_s3(file):
    image_data = await file.read()
    file_name = file.filename
    file_name = file_name.rsplit('.', 1)[0]
    await asyncio.to_thread(s3_client.put_object, Bucket=S3_BUCKET_NAME, Key=file_name, Body=image_data, ContentType=file.content_type)
    return file_name

async def query_simpledb(image_id):
    query = f"SELECT recognition FROM `{DOMAIN_NAME}` WHERE itemName() = '{image_id}'"
    response = await asyncio.to_thread(sdb_client.select, SelectExpression=query)
    items = response.get('Items', [])
    if items:
        return items[0]['Attributes'][0]['Value']
    return "No recognition result found"

@app.post("/", response_class=PlainTextResponse)
async def handle_image(inputFile: UploadFile = File(...)):
    image_id = await upload_image_to_s3(inputFile)
    recognition_result = await query_simpledb(image_id)
    return f"{image_id}:{recognition_result}"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)