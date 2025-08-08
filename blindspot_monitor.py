import cv2
import serial
import time
import tkinter as tk
from tkinter import ttk
from ultralytics import YOLO
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from collections import deque
import threading
import csv
from datetime import datetime

# === Serial Setup ===
SERIAL_PORT = 'COM4'  # Change to your actual COM port
BAUD_RATE = 9600
arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# === YOLO Setup ===
model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)  # or replace with your IP cam

ROI_X1, ROI_Y1, ROI_X2, ROI_Y2 = 100, 100, 500, 400

# === GUI Setup ===
root = tk.Tk()
root.title("Blind Spot Monitor")
root.geometry("600x200")

risk_label = ttk.Label(root, text="Risk: ", font=("Arial", 18))
risk_label.pack(pady=10)

status_label = ttk.Label(root, text="System Status: ", font=("Arial", 14))
status_label.pack(pady=5)

distance_label = ttk.Label(root, text="Distance: ", font=("Arial", 14))
distance_label.pack(pady=5)

# === Graph Setup ===
# fig, ax = plt.subplots(figsize=(6, 3))
# distance_data = deque(maxlen=50)
# time_data = deque(maxlen=50)
# line, = ax.plot([], [], color='blue')
# ax.set_ylim(0, 150)
# ax.set_xlim(0, 50)
# ax.set_ylabel("Distance (cm)")
# ax.set_xlabel("Time (s)")
# canvas = FigureCanvasTkAgg(fig, master=root)
# canvas.get_tk_widget().pack()

# === CSV Logging ===
log_file = open("qrisk_log.csv", mode="w", newline="")
csv_writer = csv.writer(log_file)
csv_writer.writerow(["Timestamp", "Risk", "Distance", "Status"])

# === Read Arduino Serial and Update GUI ===
def read_from_arduino():
    while True:
        try:
            line = arduino.readline().decode().strip()
            if line.startswith("RISK:"):
                parts = line.split(",")
                risk = parts[0].split(":")[1]
                dist = int(parts[1].split(":")[1])
                status = parts[2].split(":")[1]

                # Update GUI
                distance_label.config(text=f"Distance: {dist} cm")
                status_label.config(text=f"System Status: {status}")

                if risk == "HIGH":
                    risk_label.config(text="Risk Level: HIGH", foreground="red")
                elif risk == "LOW":
                    risk_label.config(text="Risk Level: LOW", foreground="orange")
                else:
                    risk_label.config(text="Risk Level: NONE", foreground="green")

                # Log data
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                csv_writer.writerow([timestamp, risk, dist, status])

                # # Plot graph
                # current_time = time.time()
                # base_time = time_data[0] if time_data else current_time
                # time_data.append(current_time - base_time)
                # distance_data.append(dist)

                # ax.clear()
                # ax.set_ylim(0, 150)
                # ax.set_xlim(0, max(10, len(time_data)))
                # ax.set_ylabel("Distance (cm)")
                # ax.set_xlabel("Time (s)")
                # ax.plot(list(time_data), list(distance_data), color='blue')
                # canvas.draw()
        except Exception as e:
            print("Error in read_from_arduino():", e)
            continue

# === Run YOLO Detection ===
def run_yolo():
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        risk_sent = "NONE"
        results = model(frame, stream=True)

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls = int(box.cls[0])
                label = model.names[cls]
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                if x1 < ROI_X2 and x2 > ROI_X1 and y1 < ROI_Y2 and y2 > ROI_Y1:
                    if label == "person":
                        risk_sent = "HIGH"
                    elif label in ["car", "motorbike", "bus"]:
                        risk_sent = "LOW"

        print(f"risk_sent: {risk_sent}")
        arduino.write((risk_sent + '\n').encode())

        # Draw ROI box
        cv2.rectangle(frame, (ROI_X1, ROI_Y1), (ROI_X2, ROI_Y2), (255, 0, 0), 2)
        cv2.imshow("Camera View", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_system()
            break

# === Stop System Gracefully ===
def stop_system():
    try:
        print("System stopped.")
        arduino.write(b'NONE\n')
        time.sleep(0.5)
        cap.release()
        arduino.close()
        log_file.close()
        cv2.destroyAllWindows()
        root.destroy()
    except Exception as e:
        print("Shutdown error:", e)
        root.destroy()

# === Stop Button ===
stop_button = ttk.Button(root, text="🛑 Stop System", command=stop_system)
stop_button.pack(pady=15)

# === Launch Threads ===
threading.Thread(target=run_yolo, daemon=True).start()
threading.Thread(target=read_from_arduino, daemon=True).start()

# === Run GUI ===
root.mainloop()
