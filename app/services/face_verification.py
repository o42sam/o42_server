import face_recognition
import cv2
import numpy as np

async def create_face_mapping_from_video(video_file) -> list:
    """
    Processes a video file to find a face and create a face encoding (mapping).
    This is a simplified example. A real implementation would need more robust error handling
    and might average encodings from multiple frames.
    """
    print("--- CREATING FACE MAPPING FROM VIDEO ---")

    contents = await video_file.read()
    nparr = np.frombuffer(contents, np.uint8)
    

    cap = cv2.VideoCapture()
    cap.open(video_file.filename, cv2.CAP_FFMPEG)
    
    face_encoding = None
    

    for _ in range(30):
        ret, frame = cap.read()
        if not ret:
            break


        rgb_frame = frame[:, :, ::-1]
        

        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        if face_encodings:

            face_encoding = face_encodings[0]
            print("--- FACE FOUND AND ENCODING CREATED ---")
            break

    cap.release()
    
    if face_encoding is not None:
        return face_encoding.tolist()
    else:
        print("--- NO FACE FOUND IN VIDEO ---")
        return None

async def verify_face(known_face_mapping: list, image_file) -> bool:
    """

    Compares a face in a new image with the known face mapping.
    """
    print("--- VERIFYING FACE ---")
    known_encoding = np.array(known_face_mapping)
    
    image_contents = await image_file.read()
    image = face_recognition.load_image_file(image_contents)
    
    unknown_encodings = face_recognition.face_encodings(image)
    
    if not unknown_encodings:
        print("--- NO FACE FOUND IN VERIFICATION IMAGE ---")
        return False
        

    results = face_recognition.compare_faces([known_encoding], unknown_encodings[0])
    
    if results[0]:
        print("--- FACE VERIFIED SUCCESSFULLY ---")
    else:
        print("--- FACE VERIFICATION FAILED ---")
        
    return results[0]