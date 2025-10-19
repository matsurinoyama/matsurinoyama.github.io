import os
import time
import cv2
import mediapipe as mp
import numpy as np
from pathlib import Path
from flask import Flask, request, send_from_directory, jsonify, abort


ROOT_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT_DIR / "uploads"
FACES_DIR = ROOT_DIR / "faces"
UPLOAD_DIR.mkdir(exist_ok=True)
FACES_DIR.mkdir(exist_ok=True)

# Lazy initialize MediaPipe Face Mesh to avoid heavy initialization at import time
mp_face_mesh = mp.solutions.face_mesh
face_mesh = None

def get_face_mesh():
    """Create and return a singleton FaceMesh instance."""
    global face_mesh
    if face_mesh is None:
        face_mesh = mp_face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1)
    return face_mesh

def get_landmarks(img):
    """Extract face landmarks from image using MediaPipe"""
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    fm = get_face_mesh()
    results = fm.process(img_rgb)
    if not results.multi_face_landmarks:
        return None
    landmarks = results.multi_face_landmarks[0].landmark
    h, w, _ = img.shape
    # Convert normalized coordinates to pixel coordinates
    points = np.array([(int(lm.x * w), int(lm.y * h)) for lm in landmarks], dtype=np.float32)
    return points

def align_face_to_reference(input_img_path, reference_img_path, output_path):
    """Align input face to reference using similarity (no shear),
    fallback to full affine only if needed."""
    try:
        # Load images
        input_img = cv2.imread(str(input_img_path))
        reference_img = cv2.imread(str(reference_img_path))
        
        if input_img is None or reference_img is None:
            return False, "Could not load images"
        
        # Get landmarks
        input_landmarks = get_landmarks(input_img)
        ref_landmarks = get_landmarks(reference_img)
        
        if input_landmarks is None or ref_landmarks is None:
            return False, "Face not detected in one of the images"
        
        # Choose 3 key points: left eye, right eye, nose tip
        ref_pts = np.array([
            ref_landmarks[33],  # left eye corner
            ref_landmarks[263], # right eye corner
            ref_landmarks[1]    # nose tip
        ], dtype=np.float32)
        
        input_pts = np.array([
            input_landmarks[33],
            input_landmarks[263],
            input_landmarks[1]
        ], dtype=np.float32)
        
        # Prefer similarity transform (rotation + scale + translation, no shear)
        M, inliers = cv2.estimateAffinePartial2D(
            input_pts.reshape(-1, 1, 2),
            ref_pts.reshape(-1, 1, 2),
            method=cv2.RANSAC,
            ransacReprojThreshold=3.0,
            maxIters=2000,
            confidence=0.99,
            refineIters=10,
        )

        # Fallback to full affine only if partial estimation failed
        if M is None:
            M = cv2.getAffineTransform(input_pts, ref_pts)

        aligned_img = cv2.warpAffine(
            input_img,
            M,
            (reference_img.shape[1], reference_img.shape[0]),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT101,
        )
        
        # Save aligned image
        cv2.imwrite(str(output_path), aligned_img)
        return True, "Face aligned successfully"
        
    except Exception as e:
        return False, f"Alignment failed: {str(e)}"

app = Flask(
    __name__,
    static_folder=str(ROOT_DIR),
    static_url_path="",
)


@app.get("/")
def root():
    return send_from_directory(ROOT_DIR, "index.html")


@app.post("/upload")
def upload():
    try:
        # Expecting multipart/form-data with field name 'image'
        if "image" not in request.files:
            return jsonify({"status": "error", "message": "No image file part in the request"}), 400

        file = request.files["image"]
        if file.filename == "":
            return jsonify({"status": "error", "message": "Empty filename"}), 400

        # Basic filename sanitation and unique naming
        name, ext = os.path.splitext(file.filename)
        ext = ext.lower() if ext else ".jpg"
        ts = int(time.time() * 1000)
        safe_name = f"upload_{ts}{ext}"
        save_path = UPLOAD_DIR / safe_name
        file.save(save_path)
        
        print(f"Saved uploaded file to: {save_path}")
    except Exception as e:
        return jsonify({"status": "error", "message": f"Upload failed: {str(e)}"}), 500

    # Try to align face if reference image exists
    reference_path = ROOT_DIR / "reference.jpg"
    if reference_path.exists():
        print(f"Reference image found at: {reference_path}")
        aligned_name = f"aligned_{ts}{ext}"
        aligned_path = FACES_DIR / aligned_name
        success, message = align_face_to_reference(save_path, reference_path, aligned_path)
        
        if success:
            print(f"Face alignment successful: {aligned_path}")
            return jsonify({
                "status": "ok",
                "filename": safe_name,
                "path": f"/uploads/{safe_name}",
                "aligned_filename": aligned_name,
                "aligned_path": f"/faces/{aligned_name}",
                "message": "Image uploaded and face aligned"
            })
        else:
            print(f"Face alignment failed: {message}")
            return jsonify({
                "status": "warning",
                "filename": safe_name,
                "path": f"/uploads/{safe_name}",
                "message": f"Image uploaded but alignment failed: {message}"
            })
    else:
        print("No reference image found, skipping alignment")
        return jsonify({
            "status": "ok",
            "filename": safe_name,
            "path": f"/uploads/{safe_name}",
            "message": "Image uploaded (no reference for alignment)"
        })


@app.get("/uploads/<path:filename>")
def get_upload(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.get("/faces/<path:filename>")
def get_face(filename: str):
    return send_from_directory(FACES_DIR, filename)


if __name__ == "__main__":
    # For local dev you can enable debug by setting FLASK_DEBUG=1 in the env.
    port = int(os.environ.get("PORT", "8000"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)


