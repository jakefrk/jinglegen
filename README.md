# JingleGen

A web application that analyzes short audio clips and generates mock ORTB bid requests with audio signals.

## Features
- Audio file analysis (≤15 seconds for the local version)
- Audio feature extraction (tempo, energy, mood, instruments)
- Mock ORTB bid request generation
- Local Flask web interface for uploads and results

## Application Screenshot

![JingleGen Application Screenshot](screenshot.png)

## JingleJen: Local Audio Analysis Web App

**Note on Project Evolution:** This application was initially envisioned for cloud deployment on AWS Lambda. However, the substantial size of Python's scientific audio libraries (Librosa, SciPy, NumPy, etc., often exceeding 300-400MB when packaged for Linux) presented challenges with AWS Lambda's deployment package size limits (250MB unzipped for code + all layers). 

To address this, several measures were explored during the cloud deployment attempt:
*   **Leveraging AWS Lambda Layers:** The strategy was to use public layers (e.g., Klayers for NumPy/SciPy) and build a custom layer for remaining dependencies like Librosa, Numba, and scikit-learn.
*   **Docker for Custom Layer Builds:** A `Dockerfile` using an AWS Lambda Python base image was employed to compile and package these libraries in a Lambda-compatible Linux environment. The goal was to produce a zip file for the custom layer.
*   **Manual Size Optimization:** After creating the custom layer content, attempts were made to reduce its footprint by removing non-essential files such as `__pycache__` directories, `*.pyc` files, and embedded `tests` folders within the libraries.

Despite these efforts, the resulting custom layer for the core audio processing libraries remained significantly large, making it difficult to stay within the overall 250MB limit. This highlighted the complexities of managing large scientific Python stacks in a serverless environment and influenced the pivot to the current local Flask application. The "Cloud Deployment Journey" section below details further learnings.

This local version was developed to fully realize the core audio analysis functionality while also serving as a case study in managing large dependencies.

## How to set it up and run it locally

Follow these steps to get JingleGen running on your local machine:

**Prerequisites:**
*   Python 3.10.x (This project is specifically tested and set up for Python 3.10 to ensure compatibility with the scientific audio libraries.)
*   pip (Python package installer)
*   Git

**Setup:**

1.  **Clone the repository (or download files if you've just cleared it):**
    ```bash
    git clone https://github.com/jakefrk/jinglegen.git
    cd jinglegen
    ```

2.  **Create and activate a virtual environment:**
    (Recommended to keep dependencies isolated. Ensure you are using Python 3.10.x for this venv.)
    ```bash
    # If python3 points to 3.10, or you only have 3.10:
    python3 -m venv venv
    # If you need to specify python3.10:
    # python3.10 -m venv venv 
    
    source venv/bin/activate
    ```
    On Windows, use: `venv\Scripts\activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

**Running the Application:**

To start the Flask web server, run from the project root:
```bash
python app.py
```
Then, open your web browser and navigate to `http://127.0.0.1:5000`.

You can upload an audio file through the web interface or use a tool like `curl`:
```bash
curl -X POST -F "audioFile=@/path/to/your/audiofile.mp3" http://127.0.0.1:5000/analyze
```
*Note: Only the first 15 seconds of audio will be processed.*

## Technologies Used (Local Version)

*   **Python:** The core programming language.
*   **Flask:** A micro web framework used to build the web application, serve the HTML interface, and handle API requests.
*   **Librosa:** For audio analysis and feature extraction.
*   **NumPy:** For efficient numerical operations.
*   **SciPy:** Provides many user-friendly and efficient numerical routines.
*   **HTML/CSS/JavaScript:** For the frontend user interface.

## Cloud Deployment Journey (Learnings & Future Work)

This project initially aimed for deployment as an AWS Lambda function to create a serverless audio analysis service. This journey provided significant learning experiences regarding cloud-native application development with Python.

**Challenges Encountered:** (Covered in the "Note on Project Evolution" above)

**Explored Solutions & Tools (During Layer-Based Attempt):**
*   **AWS Lambda Layers:** (Covered above)
*   **Docker:** (Covered above, specifically for building layer contents, not direct container deployment)
*   **Size Optimization:** (Covered above)

**Key Learnings:**
*   Managing Python dependencies in a serverless environment requires careful planning and optimization, especially with scientific computing stacks.
*   Docker is an invaluable tool for creating consistent and compatible build artifacts for Lambda Layers.
*   Understanding the Lambda execution environment and its limitations (like the 250MB unzipped code+layer limit for zip deployments) is crucial.

**Future Considerations for Cloud Deployment (JingleJen V2):**
*   **AWS Lambda Container Image Support:** Instead of zip-based deployments and layers, AWS Lambda supports deploying functions as container images (up to 10GB). This approach offers more flexibility in packaging dependencies (like Librosa and its ecosystem) and managing the runtime environment. This would be the primary alternative to investigate further for a cloud version, as it directly addresses the package size limitations encountered with the layer-based method.
*   The `Dockerfile` present in previous versions of this repository was for building a *custom layer*, not for direct Lambda container image deployment. A new `Dockerfile` would be needed for a container image deployment approach. 