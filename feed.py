import cv2
import numpy as np
import requests

class VideoFeedClient:
    def __init__(self, url):
        self.url = url

    def start_stream(self):
        # Start a streaming request to the FastAPI server
        with requests.get(self.url, stream=True) as response:
            # Check if the request was successful
            if response.status_code != 200:
                print("Error: Unable to connect to video feed.")
                return

            # Iterate over the frame segments in the response
            bytes_data = b''
            for chunk in response.iter_content(chunk_size=1024):
                bytes_data += chunk
                a = bytes_data.find(b'\xff\xd8')
                b = bytes_data.find(b'\xff\xd9')
                if a != -1 and b != -1:
                    jpg = bytes_data[a:b+2]
                    bytes_data = bytes_data[b+2:]
                    frame = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                    # Display the frame
                    cv2.imshow('Video Feed', frame)
                    if cv2.waitKey(1) == ord('q'):
                        break

        cv2.destroyAllWindows()

# Replace 'http://localhost:8000/video_feed' with the actual URL of your FastAPI server
video_feed_url = 'http://localhost:8000/video_feed'
video_feed_client = VideoFeedClient(video_feed_url)
video_feed_client.start_stream()
