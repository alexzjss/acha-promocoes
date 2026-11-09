import re
import unicodedata

from services.filtro_tecnologia import encontrar_termo_bloqueado


def normalizar_texto(texto):
    texto = str(texto).lower().strip()

    # Remove acentos
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )

    # Normaliza separadores e espaços
    texto = texto.replace("-", " ")
    texto = re.sub(r"\s+", " ", texto)

    return texto


def contem_termo(texto, termo):
    termo = normalizar_texto(termo)

    padrao = rf"(?<!\w){re.escape(termo)}(?!\w)"

    return re.search(padrao, texto) is not None


def contem_algum(texto, termos):
    return any(contem_termo(texto, termo) for termo in termos)


# PCs completos (desktops, mini PCs, kits de upgrade). A regra é ancorada
# no início do nome: "Fonte ... para Computador" não é um PC.
PREFIXOS_PC = [
    "pc ",
    "computador",
    "desktop",
    "mini pc",
    "all in one",
    "workstation",
    "kit upgrade",
    "kit montado",
    "kit processador",
]


def eh_pc(nome_normalizado):
    return any(nome_normalizado.startswith(p) for p in PREFIXOS_PC)


def identificar_categoria(nome_produto):
    nome = normalizar_texto(nome_produto)

    # =========================================================
    # PC COMPLETO (antes dos componentes: o nome de um PC cita
    # placa de vídeo, processador, memória...)
    # =========================================================

    if eh_pc(nome):
        return "pc"

    # =========================================================
    # PLACA DE VIDEO
    # =========================================================

    termos_gpu = [
        "rtx",
        "geforce",
        "placa de video",
        "gpu",
        "rx 6600",
        "rx 6650",
        "rx 6700",
        "rx 6750",
        "rx 6800",
        "rx 6900",
        "rx 7600",
        "rx 7700",
        "rx 7800",
        "rx 7900",
        "rx 9070"
    ]

    if contem_algum(nome, termos_gpu):
        return "placa_video"

    # =========================================================
    # PROCESSADOR
    # =========================================================

    termos_cpu = [
        "processador",
        "ryzen 3",
        "ryzen 5",
        "ryzen 7",
        "ryzen 9",
        "core i3",
        "core i5",
        "core i7",
        "core i9",
        "intel core",
        "cpu"
    ]

    if contem_algum(nome, termos_cpu):
        return "processador"

    # =========================================================
    # PLACA MAE
    # =========================================================

    termos_placa_mae = [
        "placa mae",
        "motherboard",
        "a320",
        "a520",
        "a620",
        "b350",
        "b450",
        "b550",
        "b650",
        "b850",
        "x370",
        "x470",
        "x570",
        "x670",
        "x870",
        "h510",
        "h610",
        "h670",
        "h770",
        "h810",
        "b560",
        "b660",
        "b760",
        "b860",
        "z590",
        "z690",
        "z790",
        "z890"
    ]

    if contem_algum(nome, termos_placa_mae):
        return "placa_mae"

    # =========================================================
    # MEMORIA RAM
    # =========================================================

    termos_ram_fortes = [
        "memoria ram",
        "memoria gamer",
        "kit memoria",
        "sodimm",
        "so dimm"
    ]

    if contem_algum(nome, termos_ram_fortes):
        return "ram"

    possui_capacidade_ram = re.search(
        r"\b(4|8|16|24|32|48|64|96|128)\s*gb\b",
        nome
    )

    possui_ddr = contem_algum(
        nome,
        [
            "ddr3",
            "ddr4",
            "ddr5"
        ]
    )

    if possui_capacidade_ram and possui_ddr:
        return "ram"

    # =========================================================
    # SSD / HD
    # =========================================================

    termos_armazenamento = [
        "ssd",
        "nvme",
        "m.2",
        "hard disk",
        "disco rigido",
        "hd externo"
    ]

    if contem_algum(nome, termos_armazenamento):
        return "ssd_hd"

    # =========================================================
    # FONTE
    # =========================================================

    termos_fonte = [
        "fonte",
        "fonte gamer",
        "fonte atx",
        "power supply",
        "psu"
    ]

    if contem_algum(nome, termos_fonte):
        return "fonte"

    # =========================================================
    # COOLER / WATER COOLER / FAN
    # =========================================================

    termos_cooler = [
        "water cooler",
        "watercooler",
        "air cooler",
        "cpu cooler",
        "cooler para processador",
        "cooler cpu",
        "cooler gamer",
        "cooler",
        "ventoinha",
        "ventoinhas",
        "kit ventoinha",
        "kit ventoinhas",
        "kit fan",
        "controladora fan",
        "fan para gabinete",
        "fan gabinete",
        "case fan",
        "argb fan",
        "rgb fan"
    ]

    if contem_algum(nome, termos_cooler):
        return "cooler"

    # =========================================================
    # GABINETE
    # =========================================================

    termos_gabinete = [
        "gabinete",
        "gabinete gamer",
        "gabinete atx",
        "gabinete matx",
        "gabinete micro atx",
        "pc case",
        "computer case"
    ]

    if contem_algum(nome, termos_gabinete):
        return "gabinete"


        # =========================================================
    # SUPORTES DE MONITOR -> ACESSORIOS
    # Precisa vir ANTES da categoria MONITOR
    # =========================================================

    termos_suporte_monitor = [
        "suporte para monitor",
        "suporte de monitor",
        "suporte monitor",
        "suporte de mesa para monitor",
        "suporte de mesa articulado para monitor",
        "braco para monitor",
        "braco articulado para monitor",
        "base para monitor"
    ]

    if contem_algum(nome, termos_suporte_monitor):
        return "acessorios"
    
    # =========================================================
    # MONITOR
    # =========================================================

    termos_monitor = [
        "monitor",
        "ultragear",
        "odyssey",
        "ultrawide"
    ]

    if contem_algum(nome, termos_monitor):
        return "monitor"

    # =========================================================
    # ACTION FIGURES
    # =========================================================

    termos_action_figures = [
        "action figure",
        "funko",
        "funko pop",
        "estatua colecionavel",
        "figura colecionavel"
    ]

    if contem_algum(nome, termos_action_figures):
        return "action_figures"

    # =========================================================
    # ACESSORIOS
    # =========================================================

    termos_acessorios = [
        "mouse",
        "teclado",
        "headset",
        "mousepad",
        "microfone",
        "webcam",
        "controle gamer",
        "gamepad"
    ]

    if contem_algum(nome, termos_acessorios):
        return "acessorios"

    # =========================================================
    # CADEIRAS -> OUTROS
    # =========================================================

    termos_cadeira = [
        "cadeira",
        "cadeira gamer",
        "cadeira escritorio",
        "cadeira de escritorio",
        "gaming chair"
    ]

    if contem_algum(nome, termos_cadeira):
        return "outros"

    # =========================================================
    # FALLBACK
    # =========================================================

    return "outros"


# =============================================================
# NICHO: o que conta como "tecnologia" dentro de 'outros'
# =============================================================

TERMOS_TECNOLOGIA = [
    # computadores e telas
    "notebook", "laptop", "computador", "pc gamer", "mini pc", "all in one",
    "tablet", "ipad", "monitor", "projetor", "tv", "smart tv", "televisao",
    "tela secundaria", "mesa digitalizadora",
    # celulares e wearables
    "celular", "smartphone", "iphone", "galaxy", "xiaomi", "motorola",
    "smartwatch", "relogio inteligente", "pulseira inteligente",
    "carregador", "power bank", "powerbank", "cabo usb", "cabo type c",
    "fone de ouvido", "fone bluetooth", "earbuds", "airpods",
    # games
    "playstation", "ps5", "ps4", "xbox", "nintendo", "switch", "dualsense",
    "joystick", "controle sem fio", "gamepad", "console",
    # periféricos e áudio
    "teclado", "mouse", "mousepad", "headset", "webcam", "microfone",
    "caixa de som", "soundbar", "gamer",
    # rede e conectividade
    "roteador", "repetidor", "wi fi", "wifi", "mesh", "access point",
    "switch de rede", "hub usb", "adaptador", "cabo hdmi",
    "cabo displayport", "pci express", "riser", "placa de rede",
    # armazenamento
    "pendrive", "cartao de memoria", "micro sd", "hd externo", "ssd", "nvme",
    # periféricos de escritório e energia
    "impressora", "scanner", "nobreak", "estabilizador",
    # casa inteligente
    "tomada inteligente", "lampada inteligente", "camera ip",
    "camera de seguranca", "alexa", "echo dot", "fire tv", "chromecast",
    "robo aspirador", "kindle", "fechadura digital", "controladora",
    # software
    "antivirus", "kaspersky", "windows", "licenca", "office 365",
    # fãs/colecionáveis geek (já são categoria própria, mas ficam no nicho)
    "funko", "action figure",
]

# Termos que, mesmo com palavra de tecnologia, indicam outro tipo de item.
TERMOS_EXCLUIDOS = [
    "cadeira de escritorio", "cadeira escritorio", "ventilador",
    "protetor solar", "shampoo", "creme", "sabonete", "desodorante",
    "parafusadeira", "furadeira", "ferramentas", "mesa para computador",
]


def eh_tecnologia(nome_produto):
    """
    True se o produto pertence ao nicho de tecnologia: ou tem categoria
    específica, ou contém algum termo de tecnologia.
    """

    nome = normalizar_texto(nome_produto)

    # Lista de bloqueio completa (moda, beleza, casa...) mantida em
    # services/filtro_tecnologia.py, compartilhada com o coletor do ML.
    if encontrar_termo_bloqueado(nome_produto):
        return False

    if identificar_categoria(nome_produto) != "outros":
        return True

    if contem_algum(nome, TERMOS_EXCLUIDOS):
        return False

    return contem_algum(nome, TERMOS_TECNOLOGIA)


if __name__ == "__main__":
    produtos_teste = [
        "Corsair RM850e Fonte 850W",
        "Fonte MSI MAG A650BN 650W",
        "Water Cooler Rise Mode 240mm ARGB",
        "Cooler Master Hyper 212",
        "Kit 3 Fans Cooler Master ARGB",
        "Kit Ventoinha Rise Mode RGB",
        "Gabinete Gamer Montech Air 100",
        "Gabinete Corsair 4000D Airflow",
        "Cadeira Gamer ThunderX3",
        "Cadeira de Escritorio Ergonômica",
        "ASUS Prime B760M-A DDR5",
        "Kingston Fury 32GB DDR5 6000MHz"
    ]

    print("\n🔎 TESTE DO CLASSIFICADOR")
    print("=" * 70)

    for produto in produtos_teste:
        categoria = identificar_categoria(produto)

        print(produto)
        print(f"→ {categoria}")
        print("-" * 70)