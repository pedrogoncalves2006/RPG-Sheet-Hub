#!/usr/bin/env python3
"""
Organizador de Fichas de RPG - servidor local
- Não precisa instalar nada (só Python 3, que já vem em quase todo PC/Linux/Mac).
- Roda na rede local: qualquer pessoa conectada no mesmo Wi-Fi/rede pode acessar
  pelo endereço IP da máquina que está rodando o servidor.
- Guarda tudo em arquivos simples dentro da pasta "data" (nada de banco de dados
  complicado), então dá pra copiar/fazer backup só copiando a pasta.
"""

import json
import mimetypes
import os
import re
import socket
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOADS_DIR = os.path.join(DATA_DIR, "uploads")
DB_FILE = os.path.join(DATA_DIR, "fichas.json")
FRONT_FILE = os.path.join(BASE_DIR, "index.html")
PORT = 8000

os.makedirs(UPLOADS_DIR, exist_ok=True)


def load_db():
    if not os.path.exists(DB_FILE):
        return {"fichas": [], "arquivos": []}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"fichas": [], "arquivos": []}


def save_db(db):
    tmp = DB_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    os.replace(tmp, DB_FILE)


def safe_filename(name):
    name = os.path.basename(name)
    name = re.sub(r"[^A-Za-z0-9_.\-áéíóúãõâêôçÁÉÍÓÚÃÕÂÊÔÇ ]", "_", name)
    return name.strip() or "arquivo"


def parse_multipart(body, boundary):
    """Parser simples de multipart/form-data (sem depender do módulo cgi, removido no 3.13)."""
    parts = body.split(b"--" + boundary)
    files = []
    fields = {}
    for part in parts:
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        if b"\r\n\r\n" not in part:
            continue
        header_blob, content = part.split(b"\r\n\r\n", 1)
        content = content.rstrip(b"\r\n")
        headers = header_blob.decode("utf-8", errors="replace")
        disp_match = re.search(r'name="([^"]+)"', headers)
        filename_match = re.search(r'filename="([^"]*)"', headers)
        if not disp_match:
            continue
        field_name = disp_match.group(1)
        if filename_match and filename_match.group(1):
            files.append({
                "field": field_name,
                "filename": filename_match.group(1),
                "content": content,
            })
        else:
            fields[field_name] = content.decode("utf-8", errors="replace")
    return fields, files


class Handler(BaseHTTPRequestHandler):
    server_version = "FichasRPG/1.0"

    def log_message(self, fmt, *args):
        pass  # deixa o terminal mais limpo

    # ---------- helpers ----------
    def send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def send_file(self, path, download_name=None):
        if not os.path.exists(path) or not os.path.isfile(path):
            self.send_json(404, {"erro": "arquivo não encontrado"})
            return
        ctype, _ = mimetypes.guess_type(path)
        ctype = ctype or "application/octet-stream"
        with open(path, "rb") as f:
            data = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        if download_name:
            self.send_header("Content-Disposition", f'inline; filename="{download_name}"')
        self.end_headers()
        self.wfile.write(data)

    def read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length) if length else b""

    # ---------- rotas ----------
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/" or path == "/index.html":
            self.send_file(FRONT_FILE)
            return

        if path == "/api/fichas":
            db = load_db()
            self.send_json(200, db["fichas"])
            return

        if path == "/api/arquivos":
            db = load_db()
            self.send_json(200, db["arquivos"])
            return

        if path.startswith("/uploads/"):
            fname = path[len("/uploads/"):]
            self.send_file(os.path.join(UPLOADS_DIR, fname), download_name=fname)
            return

        self.send_json(404, {"erro": "rota não encontrada"})

    def do_POST(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        if path == "/api/fichas":
            body = self.read_body()
            try:
                nova = json.loads(body.decode("utf-8"))
            except Exception:
                self.send_json(400, {"erro": "JSON inválido"})
                return
            db = load_db()
            nova["id"] = str(uuid.uuid4())
            db["fichas"].append(nova)
            save_db(db)
            self.send_json(201, nova)
            return

        if path == "/api/upload":
            ctype = self.headers.get("Content-Type", "")
            m = re.search(r'boundary=(.+)', ctype)
            if "multipart/form-data" not in ctype or not m:
                self.send_json(400, {"erro": "envie como multipart/form-data"})
                return
            boundary = m.group(1).strip('"').encode("utf-8")
            body = self.read_body()
            fields, files = parse_multipart(body, boundary)
            if not files:
                self.send_json(400, {"erro": "nenhum arquivo enviado"})
                return
            db = load_db()
            salvos = []
            for f in files:
                fname = safe_filename(f["filename"])
                unique = f"{uuid.uuid4().hex[:8]}_{fname}"
                with open(os.path.join(UPLOADS_DIR, unique), "wb") as out:
                    out.write(f["content"])
                registro = {
                    "id": str(uuid.uuid4()),
                    "nome_original": fname,
                    "arquivo": unique,
                    "sistema": fields.get("sistema", ""),
                    "categoria": fields.get("categoria", "outro"),
                    "descricao": fields.get("descricao", ""),
                    "ficha_id": fields.get("ficha_id", ""),
                }
                db["arquivos"].append(registro)
                salvos.append(registro)
            save_db(db)
            self.send_json(201, salvos)
            return

        self.send_json(404, {"erro": "rota não encontrada"})

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        m = re.match(r"^/api/fichas/([a-zA-Z0-9\-]+)$", path)
        if m:
            fid = m.group(1)
            body = self.read_body()
            try:
                dados = json.loads(body.decode("utf-8"))
            except Exception:
                self.send_json(400, {"erro": "JSON inválido"})
                return
            db = load_db()
            for i, f in enumerate(db["fichas"]):
                if f["id"] == fid:
                    dados["id"] = fid
                    db["fichas"][i] = dados
                    save_db(db)
                    self.send_json(200, dados)
                    return
            self.send_json(404, {"erro": "ficha não encontrada"})
            return
        self.send_json(404, {"erro": "rota não encontrada"})

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)

        m = re.match(r"^/api/fichas/([a-zA-Z0-9\-]+)$", path)
        if m:
            fid = m.group(1)
            db = load_db()
            antes = len(db["fichas"])
            db["fichas"] = [f for f in db["fichas"] if f["id"] != fid]
            db["arquivos"] = [a for a in db["arquivos"] if a.get("ficha_id") != fid]
            save_db(db)
            if len(db["fichas"]) < antes:
                self.send_json(200, {"ok": True})
            else:
                self.send_json(404, {"erro": "ficha não encontrada"})
            return

        m = re.match(r"^/api/arquivos/([a-zA-Z0-9\-]+)$", path)
        if m:
            aid = m.group(1)
            db = load_db()
            alvo = next((a for a in db["arquivos"] if a["id"] == aid), None)
            if alvo:
                try:
                    os.remove(os.path.join(UPLOADS_DIR, alvo["arquivo"]))
                except OSError:
                    pass
                db["arquivos"] = [a for a in db["arquivos"] if a["id"] != aid]
                save_db(db)
                self.send_json(200, {"ok": True})
            else:
                self.send_json(404, {"erro": "arquivo não encontrado"})
            return

        self.send_json(404, {"erro": "rota não encontrada"})


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    ip = get_local_ip()
    print("=" * 56)
    print(" Organizador de Fichas de RPG")
    print("=" * 56)
    print(f" Neste computador:   http://localhost:{PORT}")
    print(f" Na rede local:      http://{ip}:{PORT}")
    print(" (compartilhe o segundo endereço com o resto do grupo)")
    print(" Pressione CTRL+C para desligar o servidor.")
    print("=" * 56)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
