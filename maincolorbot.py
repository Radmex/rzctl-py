import threading
import win32api
import numpy as np
import dxcam
import time
import hashlib
import logging
import comtypes
from rzctl import RZCONTROL, MOUSE_CLICK, KEYBOARD_INPUT_TYPE







# logs config
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


# frame process
def analyze_frame(frame, target_type, color_filters):
    red, green, blue = frame[:, :, 0], frame[:, :, 1], frame[:, :, 2]
    return color_filters[target_type](red, green, blue)

# aimbot class
def perform_aimbot(cam, rzctl, region, midpoint, filters, color, x_offset, y_offset, smoothing, thread_lock):
    try:
        with thread_lock:
            current_frame = cam.grab(region=region)
            if current_frame is None:
                logging.warning("Captured empty frame.")
                return
            mask = analyze_frame(current_frame, color, filters)
            points_of_interest = np.transpose(np.nonzero(mask))
            if points_of_interest.size > 0:
                distances = np.linalg.norm(points_of_interest - midpoint, axis=1)
                priority_scores = points_of_interest[:, 0] + distances
                closest_target = points_of_interest[np.argmin(priority_scores)]
                x_delta = closest_target[1] - midpoint[1]
                y_delta = closest_target[0] - midpoint[0]
                rzctl.mouse_move(
                    int(x_delta + x_offset),
                    int(y_delta + y_offset),
                    True  # pass the smoothing factor
                )
    except Exception as error:
        logging.error(f"Aimbot error: {error}")

def run():
    try:
        # Initial configuration
        fov_width, fov_height = 70, 40
        target_color = "purple"
        x_offset, y_offset = 0, 1
        movement_smoothness = 10  # You can adjust the smoothing factor here (higher value = slower, smoother movement)
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        capture_region = (
            (screen_width - fov_width) // 2,
            (screen_height - fov_height) // 2,
            (screen_width - fov_width) // 2 + fov_width,
            (screen_height - fov_height) // 2 + fov_height
        )
        frame_center = np.array([fov_height // 2, fov_width // 2])
        lock = threading.Lock()

        logging.info("Starting dxcam")
        cam_instance = dxcam.create(output_idx=0)
        
        if cam_instance is None:
            pause_exit("Camera error (dxcam returned None). Check dxcam.")
        
        try:
            cam_instance.start(target_fps=165)
            logging.info("Dxcam started successfully.")
        except Exception as e:
            logging.error(f"Error starting dxcam: {e}")
            return
        
        logging.info("Configuring MouseKernelDriver")
        rzctl = RZCONTROL()
        
        #controller = MouseController()
        logging.info("MouseKernelDriver configured successfully.")

        # Color filter setup
        color_filters = {
            "yellow": lambda r, g, b: np.logical_and.reduce((r >= 250, r <= 255, g >= 250, g <= 255, b >= 27, b <= 104)),
            "red": lambda r, g, b: np.logical_and(g < 81, np.logical_or(
                np.logical_and.reduce((r >= 180, r <= 255, b >= 30, b <= 120)),
                np.logical_and.reduce((r >= 180, r <= 255, b >= 30, b <= 150))
            )),
            "purple": lambda r, g, b: np.logical_and.reduce((np.abs(r - b) <= 30, r - g >= 60, b - g >= 60, r >= 140, b >= 170, g < b))
        }

        def aimbot_loop():
            while True:
                if win32api.GetAsyncKeyState(18):  # ALT hold
                    perform_aimbot(
                        cam_instance, rzctl, capture_region, frame_center,
                        color_filters, target_color, x_offset, y_offset,
                        movement_smoothness, lock
                    )
                time.sleep(0.001)

        logging.info("Starting colorbot")
        threading.Thread(target=aimbot_loop, daemon=True).start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        logging.info("Ending program.")
    except Exception as error:
        logging.error(f"Fatal error: {error}")
    finally:
        if 'cam_instance' in locals():
            try:
                cam_instance.stop()
            except Exception as e:
                logging.error(f"Error stopping dxcam: {e}")
        logging.info("Cleaning up.")
        input("Press enter to exit.")



def main():

    rzctl = RZCONTROL()
    
    if not rzctl.init():
        print("Failed to initialize rzctl")


    rzctl.mouse_move(30, 200, True)
    time.sleep(1)
    print("Left click")

    time.sleep(1 / 1000)










if __name__ == "__main__":
    #main()
    run()
