import cv2
import numpy as np
import threading
from flask import Flask, jsonify
from flask_cors import CORS
import os

# --- CONFIGURACIÓN ---
# Si usas celular IP Webcam:
# URL_CAMARA = 'http://192.168.1.XX:8080/video' 
# Si usas USB/Webcam directa (DroidCam suele ser 0, 1 o 2):
URL_CAMARA = 2 

ancho_asiento, alto_asiento = 50, 50 
UMBRAL_BRILLO = 100 

# Variable GLOBAL que compartiremos entre la cámara y la API
estado_bus = {
    "ocupacion": 0,
    "total_asientos": 12,
    "alerta": False
}

asientos = []

# --- INICIALIZAR FLASK ---
app = Flask(__name__)
CORS(app) 

def click_asiento(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        asientos.append((x, y))

def procesar_video():
    # IMPORTANTE: Agregamos 'asientos' aquí para poder resetearla
    global estado_bus, asientos
    
    cap = cv2.VideoCapture(URL_CAMARA)
    
    cv2.namedWindow("Servidor Procesamiento")
    cv2.setMouseCallback("Servidor Procesamiento", click_asiento)

    print("--> Presiona 'r' para borrar los asientos.")
    print("--> Presiona 'ESC' para salir.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error leyendo cámara (Intentando reconectar...)")
            cv2.waitKey(1000)
            cap.open(URL_CAMARA)
            continue
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        ocupados = 0

        for (x, y) in asientos:
            x1, y1 = x - ancho_asiento // 2, y - alto_asiento // 2
            x2, y2 = x + ancho_asiento // 2, y + alto_asiento // 2
            
            if x1 < 0 or y1 < 0: continue
            
            roi = gray[y1:y2, x1:x2]
            if roi.size == 0: continue
            
            promedio = np.mean(roi)
            
            # Ajusta la lógica: 
            # > UMBRAL si el pasajero es CLARO y asiento OSCURO
            esta_ocupado = promedio > UMBRAL_BRILLO
            
            color = (0, 0, 255) # Rojo
            grosor = 2
            
            if esta_ocupado:
                ocupados += 1
                color = (0, 255, 0) # Verde
                grosor = -1 # Relleno
            
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, grosor)

        # ACTUALIZAMOS LA VARIABLE GLOBAL
        estado_bus["ocupacion"] = ocupados
        estado_bus["total_asientos"] = len(asientos) if len(asientos) > 0 else 12
        
        # UI en pantalla
        cv2.putText(frame, f'Ocupados: {ocupados}', (10, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        cv2.putText(frame, f'[R]eset  [ESC]Salir', (10, 60), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        cv2.imshow("Servidor Procesamiento", frame)
        
        # --- TECLAS ---
        key = cv2.waitKey(1) & 0xFF
        if key == 27: # ESC para cerrar
            break
        elif key == ord('r'): # R para resetear
            asientos = []
            print("!!! Asientos reiniciados localmente !!!")

    cap.release()
    cv2.destroyAllWindows()
    os._exit(0) # Mata todo el proceso (incluido Flask)

# --- ENDPOINTS DE LA API ---

@app.route('/api/status', methods=['GET'])
def get_status():
    return jsonify(estado_bus)

@app.route('/api/reset', methods=['POST'])
def reset_asientos_api():
    global asientos
    asientos = []
    return jsonify({"msg": "Asientos reiniciados"})

if __name__ == '__main__':
    # 1. Arrancar el hilo de visión artificial
    t = threading.Thread(target=procesar_video)
    t.daemon = True 
    t.start()
    
    # 2. Arrancar el servidor Flask
    print("--- SERVIDOR LISTO ---")
    print(f"Usando Cámara Índice: {URL_CAMARA}")
    print("API disponible en: http://0.0.0.0:5000/api/status")
    
    # host='0.0.0.0' para que se vea en la red
    app.run(host='0.0.0.0', port=5000, debug=False)