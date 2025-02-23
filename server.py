from fastapi import FastAPI, File, UploadFile
from fastapi.responses import PlainTextResponse
import boto3
import asyncio
import uvicorn

app = FastAPI()

my_id = "1232089042"
s3_bucket = f"{my_id}-in-bucket"
db_name = f"{my_id}-simpleDB"

s3 = boto3.client('s3', region_name='us-east-1')
db = boto3.client('sdb', region_name='us-east-1')

async def save_file_to_s3(uploaded_file):
    data = await uploaded_file.read()
    name = uploaded_file.filename.split('.')[0] 
    
    await asyncio.to_thread(s3.put_object, Bucket=s3_bucket, Key=name, Body=data)
    
    return name

async def check_db(name):
    query = f"SELECT recognition FROM `{db_name}` WHERE itemName() = '{name}'"
    response = await asyncio.to_thread(db.select, SelectExpression=query)
    
    items = response.get('Items', [])
    if items:
        return items[0]['Attributes'][0]['Value']
    return "Not found"

@app.post("/", response_class=PlainTextResponse)
async def process_image(image: UploadFile = File(...)):    
    file_name = await save_file_to_s3(image)
    result = await check_db(file_name)
    return f"{file_name}: {result}"

if __name__ == "__main__":
    print("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
