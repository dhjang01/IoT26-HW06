import json
import os
from pathlib import Path

from ultralytics import YOLO


IMAGE_PATH = Path("/home/aiot/Pictures/photo1.jpg")
PROJECT_DIR = Path("/home/aiot/IoT26-HW06")
RESULT_PATH = Path("/home/aiot/IoT26-HW06/yolo_result.json")
MODEL_NAME = "yolov8n.pt"
VEHICLE_CLASSES = {"car", "truck", "bus", "motorcycle"}


def write_and_print(data):
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(data))


def main():
    try:
        if not IMAGE_PATH.exists():
            write_and_print(
                {
                    "success": False,
                    "error": f"Image file not found: {IMAGE_PATH}",
                }
            )
            return

        os.chdir(PROJECT_DIR)
        model = YOLO(MODEL_NAME)
        results = model(str(IMAGE_PATH), verbose=False)

        detections = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                if class_name in VEHICLE_CLASSES:
                    detections.append(
                        {
                            "class": class_name,
                            "confidence": round(float(box.conf[0]), 3),
                        }
                    )

        output = {
            "success": True,
            "image": str(IMAGE_PATH),
            "vehicle_detected": len(detections) > 0,
            "count": len(detections),
            "detections": detections,
        }
        write_and_print(output)
    except Exception as exc:
        write_and_print(
            {
                "success": False,
                "error": str(exc),
            }
        )


if __name__ == "__main__":
    main()
