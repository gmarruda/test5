from fastapi import FastAPI, Request, Response
import requests
import os

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

@app.post("/")
async def synthesize_speech(request: Request):
    """Receives text from the user, calls Azure TTS, and returns the audio file."""
    try:
        data = await request.json()
        text = data.get("text", "").strip()

        if not text:
            return {"error": "No text provided"}

        # Construct SSML body for Azure TTS
        ssml_body = f"""
        <speak version='1.0' xml:lang='pt-BR'>
            <voice xml:lang='pt-BR' xml:gender='Female' name='pt-BR-LeilaNeural'>
                {text}
            </voice>
        </speak>
        """

        # Send request to Azure TTS API
        tts_response = requests.post(TTS_ENDPOINT, data=ssml_body, headers=HEADERS)

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