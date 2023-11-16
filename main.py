from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from threading import Thread
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
import cv2
from typing import Generator

app = FastAPI()

class CameraAPI:
    def __init__(self, camera_id=0):
        self.camera = cv2.VideoCapture(camera_id)
        if not self.camera.isOpened():
            raise HTTPException(status_code=500, detail="Error: Unable to open camera.")

    def capture_frame(self):
        ret, frame = self.camera.read()
        if not ret:
            raise HTTPException(status_code=500, detail="Error: Unable to capture frame.")
        return frame

    def release_camera(self):
        self.camera.release()

camera_api = CameraAPI()

def generate_frames() -> Generator[bytes, None, None]:
    while True:
        frame = camera_api.capture_frame()
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(generate_frames(), media_type="multipart/x-mixed-replace;boundary=frame")

class CameraApp(App):
    def build(self):
        self.server_running = False
        self.server_thread = None

        layout = BoxLayout(orientation='vertical')

        self.start_button = Button(text='Start Server', on_press=self.start_server)
        self.stop_button = Button(text='Stop Server', on_press=self.stop_server)

        layout.add_widget(self.start_button)
        layout.add_widget(self.stop_button)

        return layout

    def start_server(self, instance):
        if not self.server_running:
            self.server_thread = Thread(target=self.run_server)
            self.server_thread.start()
            self.server_running = True

    def stop_server(self, instance):
        if self.server_running:
            self.server_running = False
            self.server_thread.join()
            camera_api.release_camera()

    def run_server(self):
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

if __name__ == '__main__':
    CameraApp().run()