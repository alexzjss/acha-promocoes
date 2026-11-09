import os
from pathlib import Path

from dotenv import load_dotenv

# Carrega o .env antes de ler CANAL_PC (este módulo pode ser importado
# antes do load_dotenv() do bot).
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

CANAL_TESTE = 1565001094759714988


def _canal_env(nome):
    valor = os.getenv(nome, "").strip()

    return int(valor) if valor.isdigit() else None


CANAIS = {
    "monitor": 1565061780512964798,
    "acessorios": 1565061941175525507,
    "action_figures": 1565061993919021176,
    "processador": 1568785275931594852,
    "placa_mae": 1568784917473656944,
    "ram": 1568784983139680306,
    "placa_video": 1568785181492641833,
    "fonte": 1568785436787085332,
    "ssd_hd": 1568785742103183500,

    # Novas categorias
    "cooler": 1569121306069303317,
    "gabinete": 1569121326034321519,
    "outros": 1565001094759714988,

    # PCs completos: informe o ID em CANAL_PC no .env (ou aqui).
    # Enquanto estiver vazio, os PCs não são publicados.
    "pc": _canal_env("CANAL_PC"),
}


def escolher_canal(categoria):
    categoria = categoria.lower().strip()

    mapa_categorias = {
        # Categorias internas
        "monitor": "monitor",
        "acessorios": "acessorios",
        "action_figures": "action_figures",
        "processador": "processador",
        "placa_mae": "placa_mae",
        "ram": "ram",
        "placa_video": "placa_video",
        "fonte": "fonte",
        "ssd_hd": "ssd_hd",
        "cooler": "cooler",
        "gabinete": "gabinete",
        "outros": "outros",

        # Monitores
        "monitores": "monitor",

        # Acessórios
        "mouse": "acessorios",
        "teclado": "acessorios",
        "headset": "acessorios",
        "fone": "acessorios",
        "microfone": "acessorios",
        "webcam": "acessorios",
        "mousepad": "acessorios",

        # Action Figures
        "action figure": "action_figures",
        "action figures": "action_figures",

        # Processadores
        "processadores": "processador",
        "cpu": "processador",

        # Placas-mãe
        "placa mae": "placa_mae",
        "placa mãe": "placa_mae",
        "placa-mãe": "placa_mae",
        "motherboard": "placa_mae",

        # Memória
        "memoria ram": "ram",
        "memória ram": "ram",

        # Placas de vídeo
        "placa de video": "placa_video",
        "placa de vídeo": "placa_video",
        "gpu": "placa_video",
        "rtx": "placa_video",

        # Fontes
        "psu": "fonte",
        "power supply": "fonte",

        # Armazenamento
        "ssd": "ssd_hd",
        "hd": "ssd_hd",
        "nvme": "ssd_hd",

        # Refrigeração
        "water cooler": "cooler",
        "watercooler": "cooler",
        "air cooler": "cooler",
        "fan": "cooler",
        "fans": "cooler",
        "ventoinha": "cooler",

        # PCs completos
        "pc": "pc",
        "pcs": "pc",
        "computador": "pc",

        # Gabinetes
        "case": "gabinete",
        "gabinete gamer": "gabinete",

        # Cadeiras ficam em outros
        "cadeira": "outros",
        "cadeira gamer": "outros",
        "cadeira escritorio": "outros"
    }

    categoria_interna = mapa_categorias.get(categoria)

    if categoria_interna is None:
        print(
            f"⚠️ Categoria desconhecida: {categoria}. "
            "Enviando para #outros."
        )

        categoria_interna = "outros"

    canal_id = CANAIS[categoria_interna]

    print(
        f"🧭 Roteamento: "
        f"{categoria} -> {categoria_interna} -> {canal_id}"
    )

    return canal_id