import cv2
import numpy as np
from PIL import Image



def recalcular_paneles(image_path):
    # Cargar la imagen
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Aplicar umbral adaptativo
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Aplicar operaciones morfológicas para cerrar pequeños huecos
    kernel = np.ones((3,3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filtrar y ordenar los contornos
    min_area = image.shape[0] * image.shape[1] * 0.005  # 0.5% del área de la imagen
    valid_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
    valid_contours.sort(key=lambda c: (cv2.boundingRect(c)[1], cv2.boundingRect(c)[0]))
    
    panels = []
    for contour in valid_contours:
        x, y, w, h = cv2.boundingRect(contour)
        panels.append((x, y, x+w, y+h))
    
    return panels

# ... (resto del código)

def visualize_panels(image_path, panels):
    # Esta función es para visualizar los paneles detectados
    image = cv2.imread(image_path)
    for i, (x1, y1, x2, y2) in enumerate(panels):
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(image, str(i+1), (x1+10, y1+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
    
    cv2.imshow('Detected Panels', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    