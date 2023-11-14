import http.server
import socketserver
import threading
import os
import argparse
from http import HTTPStatus
from multiprocessing import Process, Pipe
from PIL import Image

# Función para procesar imágenes en escala de grises
def convert_to_grayscale(input_path, output_path):
    image = Image.open(input_path).convert("L")
    image.save(output_path)

# Función para el servidor HTTP concurrente
def run_http_server(ip, port, child_conn):
    class ImageRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_POST(self):
            content_length = int(self.headers['Content-Length'])
            image_data = self.rfile.read(content_length)

            # Crear un archivo temporal para la imagen
            image_path = "image.jpg"
            with open(image_path, "wb") as image:
                image_path.write(image_data)

            # Notificar al servidor padre que la imagen está lista para ser procesada
            child_conn.send(image_path)

            # Esperar la respuesta del servidor padre
            response = child_conn.recv()

            self.send_response(HTTPStatus.OK)
            self.end_headers()
            self.wfile.write(response)

    with socketserver.ThreadingTCPServer((ip, port), ImageRequestHandler) as httpd:
        print(f"Servidor HTTP en http://{ip}:{port}")
        httpd.serve_forever()

# Función para el servidor de escalado
def run_scaling_server(ip, port, parent_conn):
    class ScalingRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            try:
                # Obtener la última parte de la URL
                scale_str = self.path.split('/')[-1]

                # Verificar si hay un valor numérico
                if scale_str:
                    # Convertir a float si hay un valor
                    scale_factor = float(scale_str)

                    # Notificar al servidor padre sobre el factor de escala
                    parent_conn.send(scale_factor)

                    # Esperar la respuesta del servidor padre
                    response = parent_conn.recv()

                    self.send_response(HTTPStatus.OK)
                    self.end_headers()
                    self.wfile.write(str(response).encode())  # Modificación aquí

                else:
                    # Enviar una respuesta de error si no hay un valor numérico
                    error_message = "Error: No se proporcionó un valor numérico en la URL"
                    self.send_response(HTTPStatus.BAD_REQUEST)
                    self.end_headers()
                    self.wfile.write(error_message.encode())

            except ValueError as e:
                # Enviar una respuesta de error si la conversión a float falla
                error_message = f"Error: {e}"
                self.send_response(HTTPStatus.BAD_REQUEST)
                self.end_headers()
                self.wfile.write(error_message.encode())

    with socketserver.ThreadingTCPServer((ip, port), ScalingRequestHandler) as httpd:
        print(f"Servidor de Escalado en http://{ip}:{port}")
        httpd.serve_forever()

# Función principal
def main():
    parser = argparse.ArgumentParser(description="Procesador de imágenes")
    parser.add_argument("-i", "--ip", required=True, help="Dirección de escucha")
    parser.add_argument("-p", "--port", required=True, type=int, help="Puerto de escucha")
    args = parser.parse_args()

    # Crear una conexión entre el servidor HTTP y el servidor de escalado
    parent_conn, child_conn = Pipe()

    # Iniciar el servidor de escalado en un proceso separado
    scaling_server_process = Process(target=run_scaling_server, args=(args.ip, args.port + 1, parent_conn))
    scaling_server_process.start()

    # Iniciar el servidor HTTP en un hilo
    http_server_thread = threading.Thread(target=run_http_server, args=(args.ip, args.port, child_conn))
    http_server_thread.start()

    try:
        scaling_server_process.join()
        http_server_thread.join()
    except KeyboardInterrupt:
        print("Servidores detenidos.")

if __name__ == "__main__":
    main()
