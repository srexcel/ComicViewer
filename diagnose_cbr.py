# -*- coding: utf-8 -*-
"""
Created on Mon Jul  8 14:12:32 2024

@author: Usuario
"""

import rarfile
import os

# Ruta al archivo CBR
rar_path = 'D:/Descargas/Quetzalcoatl06.cbr'
extract_dir = 'D:/Descargas/Quetzalcoatl06_extracted'

def diagnose_cbr(rar_path, extract_dir):
    try:
        with rarfile.RarFile(rar_path) as rf:
            files = rf.namelist()
            print("Archivos contenidos en el CBR:")
            for file in files:
                print(file)
                
            # Intentar extraer cada archivo
            for file in files:
                try:
                    rf.extract(file, path=extract_dir)
                    print(f"Archivo extraído correctamente: {file}")
                except rarfile.Error as e:
                    print(f"Error al extraer el archivo {file}: {e}")
                    
    except rarfile.Error as e:
        print(f"Error al abrir el archivo RAR: {e}")

# Ejecutar diagnóstico
diagnose_cbr(rar_path, extract_dir)
