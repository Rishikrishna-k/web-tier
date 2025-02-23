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
    print("[DEBUG] Starting image upload to S3...")
    image_data = await file.read()
    file_name = file.filename
    print(f"[DEBUG] Original file name: {file_name}")
    
    file_name = file_name.rsplit('.', 1)[0]  # Remove extension
    print(f"[DEBUG] Processed file name: {file_name}")

    try:
        await asyncio.to_thread(
            s3_client.put_object,
            Bucket=S3_BUCKET_NAME,
            Key=file_name,
            Body=image_data,
            ContentType=file.content_type
        )
        print(f"[DEBUG] Successfully uploaded {file_name} to S3 bucket {S3_BUCKET_NAME}")
    except Exception as e:
        print(f"[ERROR] Failed to upload {file_name} to S3: {e}")

    return file_name

async def query_simpledb(image_id):
    print(f"[DEBUG] Querying SimpleDB for image ID: {image_id}")
    query = f"SELECT recognition FROM `{DOMAIN_NAME}` WHERE itemName() = '{image_id}'"
    
    try:
        response = await asyncio.to_thread(
            sdb_client.select,
            SelectExpression=query
        )
        print(f"[DEBUG] SimpleDB response: {response}")

        items = response.get('Items', [])
        if items:
            recognition_value = items[0]['Attributes'][0]['Value']
            print(f"[DEBUG] Recognition result found: {recognition_value}")
            return recognition_value

        print("[DEBUG] No recognition result found in SimpleDB")
        return "No recognition result found"
    except Exception as e:
        print(f"[ERROR] Failed to query SimpleDB: {e}")
        return "Error querying database"

@app.post("/", response_class=PlainTextResponse)
async def handle_image(inputFile: UploadFile = File(...)):
    print("[DEBUG] Received file upload request")
    
    image_id = await upload_image_to_s3(inputFile)
    print(f"[DEBUG] Image ID after upload: {image_id}")

    recognition_result = await query_simpledb(image_id)
    print(f"[DEBUG] Final recognition result: {recognition_result}")

    return f"{image_id}:{recognition_result}"

if __name__ == "__main__":
    print("[DEBUG] Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
