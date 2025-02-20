from fastapi import FastAPI, Request, Response
import requests
import os
import time
import uuid
from azure.cosmos import CosmosClient
from datetime import datetime

app = FastAPI()

# Azure TTS API configuration
TTS_ENDPOINT = os.environ.get("tts-endpoint")
AZURE_TTS_KEY = os.environ.get("tts-key")
TTS_FORMAT = os.environ.get("tts-format")
TTS_HEADER = os.environ.get("tts-header")

HEADERS = {
    "Ocp-Apim-Subscription-Key": AZURE_TTS_KEY,
    "Content-Type": TTS_HEADER,
    "X-Microsoft-OutputFormat": TTS_FORMAT
}

# Azure Cosmos DB configuration
COSMOS_ENDPOINT = os.environ.get("cosmos-endpoint")
COSMOS_KEY = os.environ.get("cosmos-key")
DATABASE_ID = os.environ.get("cosmos-db")
CONTAINER_ID = os.environ.get("cosmos-container")

# Initialize Cosmos Client
cosmos_client = CosmosClient(COSMOS_ENDPOINT, COSMOS_KEY)
database = cosmos_client.get_database_client(DATABASE_ID)
container = database.get_container_client(CONTAINER_ID)

@app.post("/")
async def synthesize_speech(request: Request):
    """Receives text from the user, calls Azure TTS, and returns the audio file."""
    try:
        data = await request.json()
        text = data.get("text", "").strip()

        if not text:
            return {"error": "No text provided"}
        
        text_length = len(text)
        request_id = str(uuid.uuid4())
        request_time = datetime.utcnow().isoformat()

        # Construct SSML body for Azure TTS
        ssml_body = f"""
        <speak version='1.0' xml:lang='pt-BR'>
            <voice xml:gender='Female' name='pt-BR-ThalitaMultilingualNeural'>
                {text}
            </voice>
        </speak>
        """

        # Measure request duration
        start_time = time.time()
        tts_response = requests.post(TTS_ENDPOINT, data=ssml_body, headers=HEADERS)
        end_time = time.time()
        tts_duration = end_time - start_time

        tts_result_code = tts_response.status_code
        tts_size = len(tts_response.content) if tts_response.status_code == 200 else 0

        # Store request details in Cosmos DB
        item = {
            "id": request_id,
            "request_time": request_time,
            "request_text": text,
            "request_text_length": text_length,
            "tts_result_code": tts_result_code,
            "tts_duration": tts_duration,
            "tts_size": tts_size
        }
        container.create_item(body=item)

        if tts_response.status_code != 200:
            return {"error": f"Azure TTS API failed with status {tts_response.status_code}"}

        # Return the audio response with correct Content-Type
        return Response(content=tts_response.content, media_type="audio/x-wav")

    except Exception as e:
        return {"error": str(e)}

# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
