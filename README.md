# A Mesa

Um lugar só para guardar as fichas dos personagens, PDFs de regras,
mapas e aventuras do seu grupo de RPG. Funciona no computador de
alguém do grupo, e todo mundo acessa pelo próprio celular ou notebook,
sem precisar de internet.

---

## O que você precisa

Só o **Python** instalado no computador que vai guardar os arquivos.
Não precisa instalar mais nada.

- Windows: baixe em python.org/downloads (marque a opção "Add Python
  to PATH" na instalação).
- Mac e Linux: já vem pronto.

---

## Como ligar

1. Coloque os arquivos `server.py`, `index.html` e este `README.md`
   numa mesma pasta.
2. Abra o terminal dentro dessa pasta.
3. Digite:

   ```
   python3 server.py
   ```

   (no Windows, se não funcionar, tente `python server.py`)

4. Vai aparecer uma mensagem parecida com esta:

   ```
   Neste computador:   http://localhost:8000
   Na rede local:      http://192.168.0.15:8000
   ```

5. **Você** abre o primeiro endereço no navegador.
   **O resto do grupo** abre o segundo endereço (o do IP) — funciona
   em qualquer celular ou notebook conectado no mesmo Wi-Fi.

Para desligar, volte ao terminal e aperte `Ctrl + C`.

---

## Como usar

- **Fichas** — veja, busque e organize os personagens do grupo.
- **PDFs e arquivos** — envie livros de regras, mapas e aventuras.
- **Nova ficha** — cadastre um personagem: atributos, PV, itens,
  história. Serve para qualquer sistema de RPG.
- **Ficha em branco** — gera um modelo pronto para imprimir ou salvar
  como PDF.

---

## Onde ficam os dados

Tudo é salvo dentro de uma pasta chamada `data`, criada
automaticamente ao lado do `server.py`. Quer fazer backup? É só copiar
essa pasta para outro lugar.

---

## Dúvidas comuns

**Preciso de internet?**
Não. Só é preciso que todos estejam no mesmo Wi-Fi.

**O link parou de funcionar de um dia para o outro.**
O IP pode ter mudado. Reinicie o `server.py` e veja o novo endereço no
terminal.

**Dá para acessar de fora de casa?**
Não é recomendado — o sistema foi feito para uso simples dentro da
mesma rede, sem login ou senha.
