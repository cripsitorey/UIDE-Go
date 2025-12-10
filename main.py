import cv2
import numpy as np

# --- CONFIGURACIÓN ---
# Si usas DroidCam, generalmente es el indice 0 o 1.
# Si no abre, prueba cambiando a 1, 2, etc.
cap = cv2.VideoCapture(2) 

# Ancho y alto de cada cajita de asiento (ajústalo según tu cámara)
ancho_asiento, alto_asiento = 50, 50 

# Umbral de detección (Juega con esto: menor número = más sensible a oscuros)
# Si tus pasajeros son CLAROS y asientos OSCUROS: detectamos brillo alto
# Si tus pasajeros son OSCUROS y asientos CLAROS: detectamos brillo bajo
# Aquí asumiremos: Asientos oscuros, Pasajeros claros (monedas/papel)
UMBRAL_BRILLO = 100 

asientos = []

def click_asiento(event, x, y, flags, params):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Guardamos la coordenada del clic central
        asientos.append((x, y))

cv2.namedWindow("Demo Vision Artificial")
cv2.setMouseCallback("Demo Vision Artificial", click_asiento)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Convertimos a escala de grises para facilitar el cálculo
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    pasajeros_detectados = 0

    for i, (x, y) in enumerate(asientos):
        # 1. Definir la zona del asiento (ROI)
        x1 = x - ancho_asiento // 2
        y1 = y - alto_asiento // 2
        x2 = x + ancho_asiento // 2
        y2 = y + alto_asiento // 2
        
        # Evitar salirnos de la imagen
        if x1 < 0 or y1 < 0: continue

        # 2. Recortar ese pedacito de la imagen
        roi = gray[y1:y2, x1:x2]
        
        # 3. Calcular el promedio de brillo en esa zona
        # Si el ROI está vacío o error, saltar
        if roi.size == 0: continue
        promedio_brillo = np.mean(roi)

        # 4. Lógica de Detección (Ajustar según tu maqueta)
        # CASO A: Pasajero CLARO sobre asiento OSCURO
        ocupado = promedio_brillo > UMBRAL_BRILLO
        
        # CASO B: Pasajero OSCURO sobre asiento CLARO (Descomenta si es tu caso)
        # ocupado = promedio_brillo < UMBRAL_BRILLO

        # 5. Dibujar cajitas
        color = (0, 0, 255) # Rojo (Vacío) por defecto
        grosor = 2
        
        if ocupado:
            color = (0, 255, 0) # Verde (Ocupado)
            grosor = -1 # Relleno
            pasajeros_detectados += 1
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, grosor)
        cv2.putText(frame, str(i+1), (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    # Mostrar info en pantalla
    cv2.rectangle(frame, (0,0), (250, 80), (0,0,0), -1)
    cv2.putText(frame, f'Ocupacion: {pasajeros_detectados}/12', (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    cv2.putText(frame, f'[R] Reset  [Esc] Salir', (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    cv2.imshow("Demo Vision Artificial", frame)

    key = cv2.waitKey(1)
    if key == 27: # Esc para salir
        break
    elif key == ord('r'): # R para borrar los asientos y empezar de nuevo
        asientos = []

cap.release()
cv2.destroyAllWindows()