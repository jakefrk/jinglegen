# JingleGen

[**JingleGen.com**](https://jinglegen.com) generates ORTB bid request snippet from analyzed audio to simulate a supply-side contextual targeting engine in a programmatic advertising ecosystem. Conceptually, a DSP could receive the returned ORTB data and by using ML/AI, returns an audio creative that appropriately matches the audio content of the viewer/listener. 


## Features

*   API endpoint for audio analysis.
*   Audio feature extraction (tempo, energy, mood, instruments) from uploaded audio.
*   Generation of ORTB bid request snippet. 

## Application Screenshot

![JingleGen Application Screenshot](screenshot.png)

 
**Prerequisites:**
*   Python 3.10.x
*   Librosa, NumPy, SciPy
*   AWS Lambda
*   AWS API Gateway
*   Amazon ECR (Elastic Container Registry) 
*   Docker

 
**API Request (Example):**

*   **Method:** `POST`
*   **Endpoint:** `/analyze`
*   **Body (JSON):**
    ```json
    {
        "audio_data": "<base64_encoded_string_of_your_audio_file>",
        "filename": "myaudio.mp3" 
    }
    ```

 
## Future Considerations / Next Steps

*   Implement more error handling, input validation.
*   Add authentication/authorization to the API Gateway endpoint.
*   Add AWS Transcribe for transcription of audio lyrics