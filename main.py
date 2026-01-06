import sys
import time
import serial
import ascon
import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore, QtWidgets
from collections import deque
from sklearn.ensemble import IsolationForest

# --- Configuration ---
PORT = '/dev/ttyACM0' 
BAUD = 115200
KEY = bytes([0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15])
NONCE = bytes([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16])

class SecureAIStream(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Isolation Forest - Secure Stream")
        
        # Timing & State
        self.start_time = time.time()
        self.state = "WAITING" # WAITING -> RECORDING -> MONITORING
        self.training_buffer = []
        self.data_points = deque(maxlen=100)
        
        # AI Model
        self.model = IsolationForest(contamination=0.05, random_state=42)
        
        # Setup Serial & UI (same as previous)
        self.init_ui()
        try:
            self.ser = serial.Serial(PORT, BAUD, timeout=0.1)
        except Exception as e:
            print(f"Serial Error: {e}"); sys.exit()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(30)

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout()
        self.status_label = QtWidgets.QLabel("Status: Initializing...")
        self.plot_widget = pg.PlotWidget()
        self.curve = self.plot_widget.plot(pen=pg.mkPen('c', width=1.5))
        self.anomaly_scatter = pg.ScatterPlotItem(size=10, brush=pg.mkBrush(255, 0, 0))
        self.plot_widget.addItem(self.anomaly_scatter)
        layout.addWidget(self.status_label)
        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

    def update_loop(self):
        elapsed = time.time() - self.start_time
        
        # --- State Management Logic ---
        if self.state == "WAITING":
            self.status_label.setText(f"Status: WAITING (Starting in {int(20 - elapsed)}s)")
            if elapsed >= 20:
                self.state = "RECORDING"
                self.record_start = time.time()
                
        elif self.state == "RECORDING":
            rec_elapsed = time.time() - self.record_start
            self.status_label.setText(f"Status: RECORDING NORMAL DATA ({int(30 - rec_elapsed)}s left)")
            if rec_elapsed >= 30:
                self.train_model()
        
        # --- Data Acquisition ---
        if self.ser.in_waiting > 0:
            try:
                line = self.ser.readline().decode('utf-8', errors='ignore').strip()
                if "Encrypted Hex:" in line:
                    hex_str = line.split("Encrypted Hex: ")[1].strip()
                    val = self.decrypt_and_parse(hex_str)
                    if val is not None:
                        self.process_value(val)
            except Exception as e:
                print(f"Loop Error: {e}")

    def decrypt_and_parse(self, hex_str):
        try:
            data = bytes.fromhex(hex_str)
            decrypted = ascon.decrypt(KEY, NONCE, b"", data, "Ascon-128")
            return float(decrypted.decode('utf-8').replace("HR:", ""))
        except: return None

    def process_value(self, val):
        self.data_points.append(val)
        self.curve.setData(list(self.data_points))
        
        if self.state == "RECORDING":
            self.training_buffer.append(val)
            
        elif self.state == "MONITORING":
            # AI Inference
            prediction = self.model.predict([[val]])[0] 
            if prediction == -1:
                print(f"AI Alert: Outlier Detected ({val})")
                idx = len(self.data_points) - 1
                self.anomaly_scatter.addPoints([{'pos': (idx, val)}])
                if len(self.data_points) >= 100:
                    self.anomaly_scatter.clear()

    def train_model(self):
        self.status_label.setText("Status: TRAINING AI MODEL...")
        QtWidgets.QApplication.processEvents()
        
        if len(self.training_buffer) > 10:
            X = np.array(self.training_buffer).reshape(-1, 1)
            self.model.fit(X)
            self.state = "MONITORING"
            self.status_label.setText("Status: LIVE MONITORING (AI ACTIVE)")
            print("Model Trained Successfully.")
        else:
            self.status_label.setText("Status: ERROR (No data recorded)")
            self.state = "WAITING"

    def closeEvent(self, event):
        self.ser.close()
        event.accept()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    win = SecureAIStream()
    win.show()
    sys.exit(app.exec_())