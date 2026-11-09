import re
import unicodedata


# ============================================================
# CATEGORIAS PERMITIDAS
# ============================================================

CATEGORIAS_TECNOLOGIA = {
    "placa_video",
    "processador",
    "placa_mae",
    "memoria_ram",
    "armazenamento",
    "fonte",
    "cooler",
    "gabinete",
    "monitor",
    "mouse",
    "teclado",
    "headset",
    "acessorios",
    "cadeira",
    "action_figure",
}


# ============================================================
# DOMÍNIOS DO MERCADO LIVRE
# ============================================================

DOMINIOS_TECNOLOGIA = {
    # Placas de vídeo
    "MLB-GRAPHICS_CARDS",

    # Processadores
    "MLB-PROCESSORS",

    # Placas-mãe
    "MLB-MOTHERBOARDS",

    # Memória RAM
    "MLB-RAM_MEMORY_MODULES",
    "MLB-RAM_MEMORY_KITS",

    # Armazenamento
    "MLB-SOLID_STATE_DRIVES",
    "MLB-HARD_DRIVES",
    "MLB-EXTERNAL_HARD_DRIVES",
    "MLB-MEMORY_CARDS",
    "MLB-USB_FLASH_DRIVES",

    # Fontes
    "MLB-POWER_SUPPLIES",
    "MLB-COMPUTER_POWER_SUPPLIES",

    # Gabinetes
    "MLB-COMPUTER_CASES",

    # Refrigeração
    "MLB-CPU_COOLERS",
    "MLB-COMPUTER_FANS",
    "MLB-WATER_COOLERS",
    "MLB-THERMAL_PASTES",

    # Monitores
    "MLB-COMPUTER_MONITORS",
    "MLB-MONITORS",

    # Mouse
    "MLB-MOUSES",
    "MLB-MOUSE_PADS",

    # Teclados
    "MLB-KEYBOARDS",

    # Áudio
    "MLB-HEADPHONES",
    "MLB-HEADSETS",
    "MLB-COMPUTER_SPEAKERS",
    "MLB-MICROPHONES",

    # Acessórios
    "MLB-MONITOR_STANDS",
    "MLB-USB_HUBS",
    "MLB-WEBCAMS",
    "MLB-NOTEBOOK_STANDS",
    "MLB-LAPTOP_COOLING_PADS",
    "MLB-COMPUTER_CABLES",
    "MLB-VIDEO_CABLES",
    "MLB-POWER_CABLES",

    # Cadeiras
    "MLB-GAMING_CHAIRS",
    "MLB-OFFICE_CHAIRS",

    # Colecionáveis permitidos no bot
    "MLB-ACTION_FIGURES",
    "MLB-COLLECTIBLE_FIGURES",
}


# ============================================================
# TERMOS POR CATEGORIA
# ============================================================

TERMOS_CATEGORIAS = {
    "placa_video": {
        "placa de video",
        "placa grafica",
        "graphics card",
        "geforce",
        "radeon",
        "nvidia",
        "rtx 3050",
        "rtx 3060",
        "rtx 3070",
        "rtx 3080",
        "rtx 3090",
        "rtx 4060",
        "rtx 4060 ti",
        "rtx 4070",
        "rtx 4070 ti",
        "rtx 4080",
        "rtx 4090",
        "rtx 5060",
        "rtx 5070",
        "rtx 5080",
        "rtx 5090",
        "gtx 1050",
        "gtx 1060",
        "gtx 1070",
        "gtx 1080",
        "gtx 1650",
        "gtx 1660",
        "rx 550",
        "rx 560",
        "rx 570",
        "rx 580",
        "rx 6600",
        "rx 6650",
        "rx 6700",
        "rx 6750",
        "rx 7600",
        "rx 7700",
        "rx 7800",
        "rx 7900",
    },

    "processador": {
        "processador",
        "cpu",
        "amd ryzen",
        "ryzen 3",
        "ryzen 5",
        "ryzen 7",
        "ryzen 9",
        "intel core",
        "core i3",
        "core i5",
        "core i7",
        "core i9",
        "intel pentium",
        "intel celeron",
        "threadripper",
    },

    "placa_mae": {
        "placa mae",
        "motherboard",
        "mainboard",
        "socket am4",
        "socket am5",
        "socket lga",
        "chipset a320",
        "chipset a520",
        "chipset b450",
        "chipset b550",
        "chipset b650",
        "chipset x570",
        "chipset x670",
        "chipset h610",
        "chipset b660",
        "chipset b760",
        "chipset z690",
        "chipset z790",
    },

    "memoria_ram": {
        "memoria ram",
        "memory ram",
        "memoria ddr",
        "ddr3",
        "ddr4",
        "ddr5",
        "sodimm",
        "so-dimm",
        "memoria notebook",
        "memoria para notebook",
        "memoria gamer",
    },

    "armazenamento": {
        "ssd",
        "nvme",
        "m.2",
        "m2 nvme",
        "disco rigido",
        "hard disk",
        "hd interno",
        "hd externo",
        "pendrive",
        "pen drive",
        "cartao de memoria",
        "micro sd",
        "microsd",
    },

    "fonte": {
        "fonte atx",
        "fonte gamer",
        "fonte modular",
        "fonte semi modular",
        "power supply",
        "psu",
        "80 plus",
        "500w",
        "550w",
        "600w",
        "650w",
        "700w",
        "750w",
        "800w",
        "850w",
        "1000w",
    },

    "cooler": {
        "water cooler",
        "air cooler",
        "cpu cooler",
        "cooler processador",
        "cooler para processador",
        "kit fan",
        "fan rgb",
        "fan argb",
        "ventoinha",
        "pasta termica",
    },

    "gabinete": {
        "gabinete gamer",
        "gabinete atx",
        "gabinete matx",
        "gabinete micro atx",
        "gabinete mid tower",
        "gabinete full tower",
        "computer case",
        "mini tower",
        "mid tower",
        "full tower",
    },

    "monitor": {
        "monitor gamer",
        "monitor led",
        "monitor ips",
        "monitor oled",
        "monitor ultrawide",
        "monitor curvo",
        "monitor 144hz",
        "monitor 165hz",
        "monitor 180hz",
        "monitor 240hz",
        "monitor 360hz",
        "monitor 4k",
        "monitor qhd",
        "monitor full hd",
    },

    "mouse": {
        "mouse gamer",
        "mouse sem fio",
        "mouse wireless",
        "mouse bluetooth",
        "mousepad",
        "mouse pad",
    },

    "teclado": {
        "teclado gamer",
        "teclado mecanico",
        "teclado magnetico",
        "teclado optico",
        "teclado sem fio",
        "teclado wireless",
        "teclado bluetooth",
        "keycap",
        "switch teclado",
    },

    "headset": {
        "headset gamer",
        "headset sem fio",
        "headset wireless",
        "fone gamer",
        "fone bluetooth",
        "headphone",
        "microfone gamer",
        "microfone usb",
    },

    "acessorios": {
        "suporte monitor",
        "braco articulado",
        "suporte notebook",
        "base notebook",
        "base refrigerada",
        "hub usb",
        "webcam",
        "cabo displayport",
        "cabo hdmi",
        "adaptador displayport",
        "adaptador hdmi",
        "controle pc",
        "controle gamer",
        "gamepad",
    },

    "cadeira": {
        "cadeira gamer",
        "cadeira escritorio",
        "cadeira ergonomica",
    },

    "action_figure": {
        "action figure",
        "funko pop",
        "estatua colecionavel",
        "figura colecionavel",
        "boneco colecionavel",
    },
}


# ============================================================
# TERMOS BLOQUEADOS
# ============================================================

TERMOS_BLOQUEADOS = {
    # Moda
    "vestido",
    "camiseta",
    "camisa social",
    "calca jeans",
    "bermuda",
    "cueca",
    "calcinha",
    "sutia",
    "tenis feminino",
    "tenis masculino",
    "sandalia",
    "chinelo",
    "bolsa feminina",

    # Beleza
    "perfume",
    "desodorante",
    "maquiagem",
    "batom",
    "shampoo",
    "condicionador",
    "hidratante",
    "protetor solar",

    # Casa e cozinha
    "panela",
    "frigideira",
    "jogo de panelas",
    "talheres",
    "prato porcelana",
    "copo vidro",
    "toalha",
    "lencol",
    "travesseiro",
    "colchao",
    "sofa",

    # Mercado
    "chocolate",
    "biscoito",
    "refrigerante",
    "cafe em po",
    "cerveja",
    "whisky",
    "vinho",
    "suplemento alimentar",

    # Automotivo sem relação com PC
    "pneu",
    "capacete motocicleta",
    "oleo motor",
    "pastilha de freio",
    "amortecedor",
    "retrovisor",

    # Ferramentas
    "furadeira",
    "parafusadeira",
    "serra circular",
    "martelete",
    "jogo de chave",

    # Produtos incompatíveis
    "usado",
    "recondicionado",
    "para retirada de pecas",
    "com defeito",
    "nao funciona",
    "sem garantia",
}


# ============================================================
# TERMOS AMBÍGUOS
# ============================================================

TERMOS_AMBIGUOS = {
    "fonte",
    "memoria",
    "monitor",
    "cooler",
    "fan",
    "controle",
    "gabinete",
    "processador",
    "placa",
}


# ============================================================
# NORMALIZAÇÃO
# ============================================================

def normalizar_texto(texto):
    """
    Remove acentos, símbolos repetidos e converte
    o texto para letras minúsculas.
    """

    if texto is None:
        return ""

    texto = str(texto).strip().lower()

    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )

    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(
            caractere
        )
    )

    texto = re.sub(
        r"[^a-z0-9\s\.\-\+]",
        " ",
        texto,
    )

    texto = re.sub(
        r"\s+",
        " ",
        texto,
    )

    return texto.strip()


# ============================================================
# VERIFICAR TERMO
# ============================================================

def contem_termo(
    texto,
    termo,
):
    texto = normalizar_texto(texto)
    termo = normalizar_texto(termo)

    if not texto or not termo:
        return False

    return termo in texto


# ============================================================
# VERIFICAR BLOQUEIO
# ============================================================

def encontrar_termo_bloqueado(
    nome,
):
    nome_normalizado = normalizar_texto(
        nome
    )

    for termo in TERMOS_BLOQUEADOS:
        if contem_termo(
            nome_normalizado,
            termo,
        ):
            return termo

    return None


# ============================================================
# CLASSIFICAR POR DOMÍNIO
# ============================================================

def classificar_por_dominio(
    domain_id,
):
    dominio = str(
        domain_id or ""
    ).strip().upper()

    mapa = {
        "MLB-GRAPHICS_CARDS": "placa_video",

        "MLB-PROCESSORS": "processador",

        "MLB-MOTHERBOARDS": "placa_mae",

        "MLB-RAM_MEMORY_MODULES": "memoria_ram",
        "MLB-RAM_MEMORY_KITS": "memoria_ram",

        "MLB-SOLID_STATE_DRIVES": "armazenamento",
        "MLB-HARD_DRIVES": "armazenamento",
        "MLB-EXTERNAL_HARD_DRIVES": "armazenamento",
        "MLB-MEMORY_CARDS": "armazenamento",
        "MLB-USB_FLASH_DRIVES": "armazenamento",

        "MLB-POWER_SUPPLIES": "fonte",
        "MLB-COMPUTER_POWER_SUPPLIES": "fonte",

        "MLB-CPU_COOLERS": "cooler",
        "MLB-COMPUTER_FANS": "cooler",
        "MLB-WATER_COOLERS": "cooler",
        "MLB-THERMAL_PASTES": "cooler",

        "MLB-COMPUTER_CASES": "gabinete",

        "MLB-COMPUTER_MONITORS": "monitor",
        "MLB-MONITORS": "monitor",

        "MLB-MOUSES": "mouse",
        "MLB-MOUSE_PADS": "mouse",

        "MLB-KEYBOARDS": "teclado",

        "MLB-HEADPHONES": "headset",
        "MLB-HEADSETS": "headset",
        "MLB-MICROPHONES": "headset",
        "MLB-COMPUTER_SPEAKERS": "headset",

        "MLB-MONITOR_STANDS": "acessorios",
        "MLB-USB_HUBS": "acessorios",
        "MLB-WEBCAMS": "acessorios",
        "MLB-NOTEBOOK_STANDS": "acessorios",
        "MLB-LAPTOP_COOLING_PADS": "acessorios",
        "MLB-COMPUTER_CABLES": "acessorios",
        "MLB-VIDEO_CABLES": "acessorios",
        "MLB-POWER_CABLES": "acessorios",

        "MLB-GAMING_CHAIRS": "cadeira",
        "MLB-OFFICE_CHAIRS": "cadeira",

        "MLB-ACTION_FIGURES": "action_figure",
        "MLB-COLLECTIBLE_FIGURES": "action_figure",
    }

    return mapa.get(dominio)


# ============================================================
# CLASSIFICAR POR NOME
# ============================================================

def classificar_por_nome(
    nome,
):
    nome_normalizado = normalizar_texto(
        nome
    )

    if not nome_normalizado:
        return None

    categorias_encontradas = []

    for categoria, termos in (
        TERMOS_CATEGORIAS.items()
    ):
        quantidade_acertos = 0
        termos_encontrados = []

        for termo in termos:
            if contem_termo(
                nome_normalizado,
                termo,
            ):
                quantidade_acertos += 1

                termos_encontrados.append(
                    termo
                )

        if quantidade_acertos > 0:
            categorias_encontradas.append(
                {
                    "categoria": categoria,
                    "pontuacao": quantidade_acertos,
                    "termos": termos_encontrados,
                }
            )

    if not categorias_encontradas:
        return None

    categorias_encontradas.sort(
        key=lambda resultado: (
            resultado["pontuacao"]
        ),
        reverse=True,
    )

    return categorias_encontradas[0]


# ============================================================
# VALIDAR PRODUTO
# ============================================================

def validar_produto_tecnologia(
    produto,
):
    """
    Valida um produto retornado pelo Mercado Livre.

    Retorno:

    {
        "aprovado": True ou False,
        "categoria": "...",
        "motivo": "...",
        "pontuacao": 0,
        "termos": []
    }
    """

    if not isinstance(produto, dict):
        return {
            "aprovado": False,
            "categoria": None,
            "motivo": "produto_invalido",
            "pontuacao": 0,
            "termos": [],
        }

    nome = (
        produto.get("name")
        or produto.get("title")
        or produto.get("nome")
        or ""
    )

    domain_id = (
        produto.get("domain_id")
        or produto.get("dominio")
        or ""
    )

    nome_normalizado = normalizar_texto(
        nome
    )

    if not nome_normalizado:
        return {
            "aprovado": False,
            "categoria": None,
            "motivo": "produto_sem_nome",
            "pontuacao": 0,
            "termos": [],
        }

    termo_bloqueado = (
        encontrar_termo_bloqueado(
            nome_normalizado
        )
    )

    if termo_bloqueado:
        return {
            "aprovado": False,
            "categoria": None,
            "motivo": (
                "termo_bloqueado:"
                f"{termo_bloqueado}"
            ),
            "pontuacao": 0,
            "termos": [
                termo_bloqueado
            ],
        }

    categoria_dominio = (
        classificar_por_dominio(
            domain_id
        )
    )

    resultado_nome = (
        classificar_por_nome(
            nome_normalizado
        )
    )

    # Caso ideal:
    # nome e domínio confirmam tecnologia.
    if categoria_dominio and resultado_nome:
        return {
            "aprovado": True,
            "categoria": (
                resultado_nome["categoria"]
            ),
            "motivo": (
                "dominio_e_nome_confirmados"
            ),
            "pontuacao": (
                resultado_nome["pontuacao"]
                + 2
            ),
            "termos": (
                resultado_nome["termos"]
            ),
        }

    # Domínio conhecido é uma evidência forte.
    if categoria_dominio:
        return {
            "aprovado": True,
            "categoria": categoria_dominio,
            "motivo": "dominio_permitido",
            "pontuacao": 2,
            "termos": [],
        }

    # Domínio desconhecido, mas nome possui
    # termos específicos de tecnologia.
    if resultado_nome:
        categoria = (
            resultado_nome["categoria"]
        )

        pontuacao = (
            resultado_nome["pontuacao"]
        )

        termos = (
            resultado_nome["termos"]
        )

        # Termos únicos e ambíguos não são
        # suficientes para aprovar um produto.
        if pontuacao == 1:
            termo_encontrado = (
                termos[0]
                if termos
                else ""
            )

            if (
                termo_encontrado
                in TERMOS_AMBIGUOS
            ):
                return {
                    "aprovado": False,
                    "categoria": categoria,
                    "motivo": (
                        "termo_ambiguo_sem_"
                        "dominio_confirmado"
                    ),
                    "pontuacao": pontuacao,
                    "termos": termos,
                }

        return {
            "aprovado": True,
            "categoria": categoria,
            "motivo": (
                "nome_confirmou_tecnologia"
            ),
            "pontuacao": pontuacao,
            "termos": termos,
        }

    return {
        "aprovado": False,
        "categoria": None,
        "motivo": (
            "categoria_nao_reconhecida"
        ),
        "pontuacao": 0,
        "termos": [],
    }


# ============================================================
# FILTRAR LISTA
# ============================================================

def filtrar_produtos_tecnologia(
    produtos,
    exibir_ignorados=True,
):
    produtos_aprovados = []

    if not isinstance(produtos, list):
        return produtos_aprovados

    for produto in produtos:
        resultado = (
            validar_produto_tecnologia(
                produto
            )
        )

        nome = (
            produto.get("name")
            or produto.get("title")
            or produto.get("nome")
            or "Produto sem nome"
        )

        if not resultado["aprovado"]:
            if exibir_ignorados:
                print(
                    f"⛔ Ignorado: {nome}"
                )

                print(
                    "   Motivo: "
                    f"{resultado['motivo']}"
                )

            continue

        produto_filtrado = dict(
            produto
        )

        produto_filtrado[
            "categoria_tecnologia"
        ] = resultado["categoria"]

        produto_filtrado[
            "filtro_tecnologia"
        ] = resultado

        produtos_aprovados.append(
            produto_filtrado
        )

        print(
            f"✅ Tecnologia: {nome}"
        )

        print(
            "   Categoria: "
            f"{resultado['categoria']}"
        )

    return produtos_aprovados


# ============================================================
# TESTE ISOLADO
# ============================================================

if __name__ == "__main__":
    produtos_teste = [
        {
            "name": (
                "Placa de Vídeo RTX 4060 "
                "8GB GDDR6"
            ),
            "domain_id": (
                "MLB-GRAPHICS_CARDS"
            ),
        },
        {
            "name": (
                "SSD Kingston NVMe 1TB"
            ),
            "domain_id": (
                "MLB-SOLID_STATE_DRIVES"
            ),
        },
        {
            "name": (
                "Perfume Importado 100ml"
            ),
            "domain_id": (
                "MLB-PERFUMES"
            ),
        },
        {
            "name": (
                "Jogo de Panelas Antiaderente"
            ),
            "domain_id": (
                "MLB-COOKWARE_SETS"
            ),
        },
        {
            "name": (
                "Memória RAM DDR5 16GB"
            ),
            "domain_id": "",
        },
        {
            "name": (
                "Cadeira Gamer Ergonômica"
            ),
            "domain_id": (
                "MLB-GAMING_CHAIRS"
            ),
        },
    ]

    aprovados = filtrar_produtos_tecnologia(
        produtos_teste
    )

    print("\n" + "=" * 70)

    print(
        f"Produtos analisados: "
        f"{len(produtos_teste)}"
    )

    print(
        f"Produtos aprovados: "
        f"{len(aprovados)}"
    )

    print("=" * 70)