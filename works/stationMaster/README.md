# Local dev

## Prereqs

- Python 3.9+

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python server.py
```

Then open `http://localhost:8000` in your browser.

Uploads are saved to the `uploads/` directory.

## Face API.js models

This app can use face-api.js for better guidance.

1. Download models (TinyFaceDetector + Landmark68) from the face-api.js repo releases.
   - Files typically include:
     - `tiny_face_detector_model-weights_manifest.json`
     - `tiny_face_detector_model-shard1`
     - `face_landmark_68_model-weights_manifest.json`
     - `face_landmark_68_model-shard1`
2. Create a `models/` directory next to `index.html` and place the files there.
3. Reload the page. The app will load models from `./models` automatically on camera start.

Note: Native FaceDetector is not used. The app requires face-api.js models to enable Capture.
