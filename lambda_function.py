import json
import base64
import os
import librosa
import numpy as np
from datetime import datetime
import time
import uuid # Can be used for unique filenames if needed
from pydub import AudioSegment
import io
# import boto3 # Commented out for now, not used in this simplified version
# import requests # Was in old file, not used here
# import botocore # Was in old file, not used here

# --- Core Audio Analysis Logic (from app.py) ---
def analyze_audio(file_path):
    """Extract detailed audio features using librosa"""
    print(f"[{time.strftime('%H:%M:%S')}] Starting analysis for: {file_path}")
    start_time = time.time()

    try:
        print(f"[{time.strftime('%H:%M:%S')}] Loading audio with pydub/ffmpeg...")
        load_start = time.time()
        
        # Use pydub to open the file, which is more robust with ffmpeg
        # The file extension is important for pydub to know the format
        file_extension = os.path.splitext(file_path)[1].lstrip('.')
        audio_segment = AudioSegment.from_file(file_path, format=file_extension)

        # Convert to mono if it's stereo
        if audio_segment.channels > 1:
            audio_segment = audio_segment.set_channels(1)

        # Export to a format librosa understands well (WAV) in-memory
        wav_buffer = io.BytesIO()
        audio_segment.export(wav_buffer, format="wav")
        wav_buffer.seek(0)

        # Load the WAV data from the in-memory buffer using librosa
        # We limit the duration here
        y, sr = librosa.load(wav_buffer, duration=15.0, sr=None) # sr=None to preserve original sample rate from pydub
        
        print(f"[{time.strftime('%H:%M:%S')}] Audio loaded via pydub in {time.time() - load_start:.2f}s. Sample rate: {sr}, Duration of y: {len(y)/sr:.2f}s")

        # Mood/Energy Analysis
        print(f"[{time.strftime('%H:%M:%S')}] Calculating spectral rolloff...")
        rolloff_start = time.time()
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr))
        print(f"[{time.strftime('%H:%M:%S')}] Spectral rolloff calculated in {time.time() - rolloff_start:.2f}s.")

        print(f"[{time.strftime('%H:%M:%S')}] Calculating spectral bandwidth...")
        bandwidth_start = time.time()
        spectral_bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))
        print(f"[{time.strftime('%H:%M:%S')}] Spectral bandwidth calculated in {time.time() - bandwidth_start:.2f}s.")

        # Instrument Analysis
        print(f"[{time.strftime('%H:%M:%S')}] Performing HPSS...")
        hpss_start = time.time()
        harmonic, percussive = librosa.effects.hpss(y)
        print(f"[{time.strftime('%H:%M:%S')}] HPSS completed in {time.time() - hpss_start:.2f}s.")
        
        harmonic_sum = np.mean(harmonic)
        percussive_sum = np.mean(percussive)
        if harmonic_sum + percussive_sum == 0:
            harmonic_ratio = 0.5
        else:
            harmonic_ratio = harmonic_sum / (harmonic_sum + percussive_sum)
        print(f"[{time.strftime('%H:%M:%S')}] Harmonic ratio calculated.")

        # Musical Characteristics
        print(f"[{time.strftime('%H:%M:%S')}] Calculating onset strength...")
        onset_env_start = time.time()
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        print(f"[{time.strftime('%H:%M:%S')}] Onset strength calculated in {time.time() - onset_env_start:.2f}s.")

        print(f"[{time.strftime('%H:%M:%S')}] Tracking beat...")
        beat_track_start = time.time()
        tempo, _ = librosa.beat.beat_track(onset_envelope=onset_env, sr=sr)
        print(f"[{time.strftime('%H:%M:%S')}] Beat tracked in {time.time() - beat_track_start:.2f}s. Tempo: {tempo}")

        # Rhythm Analysis
        print(f"[{time.strftime('%H:%M:%S')}] Detecting onsets...")
        onset_detect_start = time.time()
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        print(f"[{time.strftime('%H:%M:%S')}] Onsets detected in {time.time() - onset_detect_start:.2f}s. Count: {len(onset_frames)}")
        
        audio_duration_seconds = len(y) / sr
        if audio_duration_seconds == 0:
            rhythm_density = 0
        else:
            rhythm_density = len(onset_frames) / audio_duration_seconds
        print(f"[{time.strftime('%H:%M:%S')}] Rhythm density calculated.")

        raw_analysis_results = {
            'mood_energy': {
                'spectral_rolloff': float(spectral_rolloff),
                'spectral_bandwidth': float(spectral_bandwidth),
                'interpreted_energy': 'High' if spectral_rolloff > 3000 else 'Medium' if spectral_rolloff > 1500 else 'Low',
                'interpreted_brightness': 'Bright' if spectral_bandwidth > 2000 else 'Muted'
            },
            'instrument_analysis': {
                'harmonic_ratio': float(harmonic_ratio),
                'harmonic_energy_mean': float(harmonic_sum),
                'percussive_energy_mean': float(percussive_sum),
                'interpreted_instrument_type': 'Melodic' if harmonic_ratio > 0.6 else 'Percussive' if harmonic_ratio < 0.4 else 'Mixed'
            },
            'musical_characteristics': {
                'tempo_bpm': int(tempo) if tempo else 0,
                'onset_strength_mean': float(np.mean(onset_env)),
                'interpreted_style': 'Fast-paced' if tempo and tempo > 120 else 'Medium-paced' if tempo and tempo > 90 else 'Slow-paced'
            },
            'rhythm_analysis': {
                'onset_count': len(onset_frames),
                'rhythm_density_onsets_per_sec': float(rhythm_density),
                'interpreted_beat_density': 'High' if rhythm_density > 2 else 'Medium' if rhythm_density > 1 else 'Low'
            }
        }
        print(f"[{time.strftime('%H:%M:%S')}] Analysis dictionary populated.")
        total_time = time.time() - start_time
        print(f"[{time.strftime('%H:%M:%S')}] Total analysis time: {total_time:.2f}s")
        return raw_analysis_results

    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error during audio analysis: {e}")
        import traceback
        traceback.print_exc() 
        return {"error": str(e), "trace": traceback.format_exc()}

# --- ORTB Request Generation (Adapted from app.py) ---
def generate_ortb_request(raw_audio_analysis_data, transcribed_text=""):
    """Generate a mock ORTB bid request with selected audio signals for cloud context"""
    
    ortb_signals = {
        "energy_level": raw_audio_analysis_data.get('mood_energy', {}).get('interpreted_energy', 'N/A'),
        "brightness": raw_audio_analysis_data.get('mood_energy', {}).get('interpreted_brightness', 'N/A'),
        "instrument_type": raw_audio_analysis_data.get('instrument_analysis', {}).get('interpreted_instrument_type', 'N/A'),
        "tempo_bpm": raw_audio_analysis_data.get('musical_characteristics', {}).get('tempo_bpm', 0),
        "style": raw_audio_analysis_data.get('musical_characteristics', {}).get('interpreted_style', 'N/A'),
        "beat_density": raw_audio_analysis_data.get('rhythm_analysis', {}).get('interpreted_beat_density', 'N/A'),
        "onset_count": raw_audio_analysis_data.get('rhythm_analysis', {}).get('onset_count', 0)
    }
    # Transcription is not part of the core analysis for now
    # if transcribed_text:
    #     ortb_signals["transcribed_text_snippet"] = transcribed_text[:256]

    # Generate a unique bid ID, suitable for cloud context
    bid_id = f"bid-cloud-{uuid.uuid4()}"

    return {
        "id": bid_id,
        "imp": [{
            "id": "1", # Impression ID
            "audio": {
                "mimes": ["audio/mpeg", "audio/wav"], 
                "minduration": 1, # Minimum ad duration in seconds
                "maxduration": 15, # Maximum ad duration in seconds (can be adjusted)
            },
            "ext": {
                "custom_audio_signals": ortb_signals 
            }
        }],
        "app": { 
            "id": "jinglegen-cloud-app-v2",
            "name": "JingleGen Audio Analyzer (Cloud V2)",
            "bundle": "com.example.jinglegen.cloud", # Example bundle ID
            "publisher": {
                "id": "pub-cloud-jinglegen", # Example publisher ID
                "name": "JingleGen Cloud Services"
            }
        },
        "device": { # These would ideally be populated from the actual request if available via API Gateway
            "ua": "Unknown", 
            "ip": "0.0.0.0",   
            "devicetype": 2, # Example: Mobile (can be refined based on actual client info)
            "os": "Unknown" 
        },
        "user": { 
            "id": f"cloud-user-{uuid.uuid4()}" # Example unique user ID
        },
        "at": 1, # Auction type (1 = First Price, 2 = Second Price Plus)
        "tmax": 200, # Timeout for submitting the bid in milliseconds
        "regs": { 
            "coppa": 0, 
            "ext": { "gdpr": 0 } # Placeholder, real values depend on user context
        }
    }

# --- Lambda Handler ---
def lambda_handler(event, context):
    print(f"Received event: {json.dumps(event)}")

    try:
        # Check if the body is base64 encoded (common for binary data via API Gateway)
        is_base64_encoded = event.get('isBase64Encoded', False)
        raw_body = event.get('body', '{}')

        if is_base64_encoded:
            # This assumes the entire body is the base64 encoded file data from a direct binary upload
            # or a specific field if structured differently.
            # For multipart/form-data, API Gateway needs specific configuration
            # and parsing logic here would be different.
            # Assuming the 'body' is the base64 string of the audio file itself
            # and 'filename' might be passed in headers or as a query parameter.
            
            # For simplicity, let's assume a JSON payload with 'audio_data' (base64) and 'filename'
            # If event['body'] is ALREADY a JSON string:
            try:
                payload = json.loads(raw_body)
            except json.JSONDecodeError:
                 # If raw_body is not JSON, and isBase64Encoded is true,
                 # it might be that the body *is* the base64 audio directly.
                 # This part needs careful testing with how API Gateway sends binary.
                 # For now, we will assume JSON payload for clarity.
                if is_base64_encoded and isinstance(raw_body, str): # If body is direct base64
                     payload = {'audio_data': raw_body, 'filename': event.get('queryStringParameters', {}).get('filename', 'audio.mp3')}
                else:
                    print("Error: Body is not valid JSON and not directly decodable as base64 audio.")
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': 'Invalid request body format. Expected JSON or direct base64.'})
                    }


            audio_data_base64 = payload.get('audio_data')
            # Try to get filename from payload, then query string, then default
            filename_from_payload = payload.get('filename')
            filename_from_query = event.get('queryStringParameters', {}).get('filename') if event.get('queryStringParameters') else None
            
            filename = filename_from_payload or filename_from_query or f"audio-{uuid.uuid4().hex[:8]}.mp3" # Ensure a default if not provided

            if not audio_data_base64:
                print("Error: 'audio_data' not found in request payload.")
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': "'audio_data' not found in request payload."})
                }
            
            audio_bytes = base64.b64decode(audio_data_base64)
        
        else: # Handling non-base64 encoded body, assuming it's JSON with a key for audio_data
            print("Warning: Request body is not base64 encoded. Assuming JSON payload with 'audio_data'.")
            try:
                payload = json.loads(raw_body)
                audio_data_base64 = payload.get('audio_data')
                filename_from_payload = payload.get('filename')
                filename_from_query = event.get('queryStringParameters', {}).get('filename') if event.get('queryStringParameters') else None
                filename = filename_from_payload or filename_from_query or f"audio-{uuid.uuid4().hex[:8]}.mp3"


                if not audio_data_base64:
                    print("Error: 'audio_data' not found in JSON request payload.")
                    return {
                        'statusCode': 400,
                        'headers': {'Content-Type': 'application/json'},
                        'body': json.dumps({'error': "'audio_data' not found in JSON request payload (non-base64)."})
                    }
                audio_bytes = base64.b64decode(audio_data_base64) # Assuming audio_data is still base64 within the JSON

            except json.JSONDecodeError:
                print(f"Error: Could not parse non-base64 body as JSON: {raw_body}")
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid JSON in request body when not base64 encoded.'})
                }
            except base64.BinasciiError:
                 print("Error: Could not decode base64 audio_data from JSON payload.")
                 return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Invalid base64 data in audio_data field.'})
                 }


        # Ensure /tmp directory exists (it always does in Lambda)
        temp_file_path = os.path.join('/tmp', filename)
        
        print(f"Saving decoded audio to: {temp_file_path}")
        with open(temp_file_path, 'wb') as f:
            f.write(audio_bytes)
        
        # Perform analysis
        raw_analysis_results = analyze_audio(temp_file_path)
        if 'error' in raw_analysis_results: # Handle analysis errors
             print(f"Error during analysis: {raw_analysis_results}")
             # Ensure the error response from analyze_audio is properly formatted
             error_detail = raw_analysis_results.get("error", "Unknown analysis error")
             # trace_detail = raw_analysis_results.get("trace", "") # Can be too verbose for client
             return {
                'statusCode': 500,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Analysis failed', 'detail': error_detail})
            }

        # Generate ORTB request
        ortb_bid_request = generate_ortb_request(raw_analysis_results)

        combined_results = {
            "audio_analysis": raw_analysis_results,
            "ortb_request": ortb_bid_request
        }

        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                print(f"Successfully removed temporary file: {temp_file_path}")
            except Exception as e_remove:
                print(f"Error removing temporary file {temp_file_path}: {e_remove}")

        # Conditionally format the response based on the client
        headers = event.get('headers', {})
        # API Gateway headers are case-insensitive and typically lowercased
        user_agent = headers.get('user-agent', '').lower()

        if 'curl' in user_agent:
            # For curl users, return only the ORTB bid request
            response_body = json.dumps(ortb_bid_request, indent=2) # Add indent for readability
        else:
            # For other clients (like the web app), return the full analysis
            response_body = json.dumps(combined_results, indent=2) # Add indent for readability

        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*' # Add CORS header if needed by API Gateway
            },
            'body': response_body
        }

    except base64.BinasciiError as e:
        print(f"Error decoding base64 audio data: {e}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid base64 encoded audio data', 'detail': str(e)})
        }
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from event body: {e}")
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Invalid JSON in request body', 'detail': str(e)})
        }
    except Exception as e:
        print(f"Unhandled error in lambda_handler: {e}")
        import traceback
        traceback.print_exc()
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error', 'detail': str(e)})
        }

# To test locally (example structure, won't run MediaConvert/Transcribe)
if __name__ == '__main__':
    # This __main__ block is for local testing of the functions if needed,
    # but the lambda_handler itself is typically invoked by the Lambda runtime.
    # You would need to mock an 'event' object.
    
    # Example of creating a dummy base64 audio file for testing:
    # Create a dummy wav file (e.g., using scipy.io.wavfile.write)
    # then base64 encode it.
    # For now, this is just a conceptual placeholder for local tests.

    print("Lambda function module loaded. Define a mock event and context to test lambda_handler locally.")
    
    # mock_event_body_json = {
    #     "audio_data": "BASE64_ENCODED_STRING_OF_A_SHORT_AUDIO_CLIP_HERE",
    #     "filename": "test.mp3" 
    # }
    # mock_event = {
    #     "body": json.dumps(mock_event_body_json),
    #     "isBase64Encoded": False # If body is JSON string, this is False. If body is direct base64, this is True.
    #                            # If body is JSON and audio_data is base64 within it, still False for event.isBase64Encoded
    # }
    # mock_context = {}
    # response = lambda_handler(mock_event, mock_context)
    # print("\nLAMBDA HANDLER RESPONSE:\n", json.dumps(response, indent=2))
