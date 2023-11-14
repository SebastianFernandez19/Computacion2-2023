# -*- coding: utf-8 -*-
import os
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("-f", help="Archivo de texto a leer")
args = parser.parse_args()

# Función para poner en reversa el texto
def reverse(s):
    return s[::-1]

# Abrir el archivo, leer las líneas. En caso de no encontrar el archivo, da error.
try:
    with open(args.f, "r") as file:
        lines = file.readlines()
except IOError:
    print("Error: El archivo no se encuentra")
    exit(1)  # Salir del programa con código de error 1

pipes_r = [] #Lista donde cada hijo pondra la linea de texto que lee
for line in lines:
    r, w = os.pipe()
    pid = os.fork()
    if pid == 0: # Proceso hijo
        os.close(r)
        w = os.fdopen(w, "w")  # Convertir el descriptor de archivo en objeto de archivo
        w.write(reverse(line))
        w.close()
        exit(0)  # Salir del proceso hijo con éxito
    elif pid > 0:
        # Proceso padre
        os.close(w)
        pipes_r.append(os.fdopen(r, "r"))  # Convertir el descriptor de archivo en objeto de archivo

for pipe in pipes_r:
    print(pipe.read().strip())

# Esperar a que todos los procesos hijos terminen
while True:
    try:
        pid, status = os.waitpid(-1, 0) #El parametro -1 hace que el wait espere a cualquier hijo
        if pid == 0:
            break  # No hay más procesos hijos que esperar,termina el bucle
        elif status != 0: #El hijo termina con un error
            print("Error en el proceso hijo con PID", pid)
    except ChildProcessError:
        break  # No hay más procesos hijos que esperar

