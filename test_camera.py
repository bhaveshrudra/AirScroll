import cv2
import re
from pathlib import Path

print("AirScroll Camera Selector")
print("N = Next camera | S = Select camera | Q = Quit")

for index in range(10):
    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        cap.release()
        continue

    frame = None

    for _ in range(20):
        ret, frame = cap.read()
        if ret:
            break

    if not ret:
        cap.release()
        continue

    print(f"Camera {index} detected")

    while True:
        display = frame.copy()

        cv2.putText(
            display,
            f"CAMERA INDEX: {index} | N: Next | S: Select | Q: Quit",
            (15, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

        cv2.imshow("AirScroll Camera Selector", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('n'):
            break

        elif key == ord('s'):
            config = Path("airscroll/config.py")
            text = config.read_text(encoding="utf-8")

            text = re.sub(
                r"(?m)^CAMERA_INDEX\s*=\s*\d+",
                f"CAMERA_INDEX = {index}",
                text
            )

            config.write_text(text, encoding="utf-8")

            print(f"Successfully selected Camera {index}!")
            cap.release()
            cv2.destroyAllWindows()
            raise SystemExit

        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            raise SystemExit

        ret, frame = cap.read()

        if not ret:
            break

    cap.release()

cv2.destroyAllWindows()
print("No more cameras found.")