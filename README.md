 # JingleGen

A web application that analyzes short audio clips and generates mock ORTB bid requests with audio signals.

## Features
- Audio file analysis (≤2 seconds)
- Audio feature extraction (tempo, energy, mood, instruments)
- Mock ORTB bid request generation
- GitHub Pages hosted frontend


## Technologies
- Python (librosa, numpy, scipy)
- AWS Lambda (compute audio analysis)
- AWS API Gateway (exposes Lambda as REST API)
- AWS S3 (for storing audio files)
- AWS IAM (permissions and roles for Lambda/API)
- GitHub Pages (static frontend hosting)



## Project Structure

```
jinglegen/
├── index.html
├── .nojekyll
├── README.md
├── lambda/
│   └── audio-analyzer/
│       ├── lambda_function.py
│       ├── requirements.txt
│       └── ... (other Lambda files)
├── iam_policies/
│   ├── transcribe_policy.json
│   └── ... (other policy files)
```

