import csv
from pathlib import Path


ARQUIVO_DADOS = Path(__file__).resolve().parent.parent / "data" / "dados.csv"

BAIRROS = {
    "vila_horizonte": "Vila Horizonte",
    "jardim_do_ipe": "Jardim do Ipê",
}
CATEGORIAS = {
    "iluminacao": "Iluminação",
    "acessibilidade": "Acessibilidade",
    "limpeza": "Limpeza",
    "conservacao": "Conservação",
}
SITUACOES = {
    "aberta": "Aberta",
    "em_analise": "Em análise",
    "concluida": "Concluída",
}
CAMPOS_CSV = [
    "codigo", "bairro", "categoria", "descricao", "local", "dia_abertura",
    "situacao", "dia_analise", "dia_conclusao",
]

MENU = """
Menu principal

  1. Listar ocorrências
  2. Buscar por código
  3. Filtrar por categoria e situação

  4. Cadastrar ocorrência
  5. Examinar a próxima ocorrência da fila
  6. Alterar situação por código

  7. Consultar histórico
  8. Consultar por bairro e categoria
  9. Exibir indicadores

  0. Sair
"""


def inteiro_positivo(texto, campo):
    if texto.isascii() and texto.isdecimal():
        try:
            numero = int(texto)
        except ValueError:
            pass
        else:
            if numero > 0:
                return numero
    raise ValueError(f"{campo} deve ser um número inteiro positivo.")


def validar_ocorrencia(ocorrencia, por_codigo):
    if ocorrencia["codigo"] in por_codigo:
        raise ValueError("O código já está cadastrado.")
    if not ocorrencia["categoria"]:
        raise ValueError("A categoria é obrigatória.")
    if ocorrencia["categoria"] not in CATEGORIAS:
        raise ValueError("Categoria desconhecida.")
    if ocorrencia["bairro"] not in BAIRROS:
        raise ValueError("Selecione um dos bairros da simulação.")
    if not ocorrencia["descricao"]:
        raise ValueError("A descrição é obrigatória.")
    if not ocorrencia["local"]:
        raise ValueError("O local genérico é obrigatório.")

    situacao = ocorrencia["situacao"]
    abertura = ocorrencia["dia_abertura"]
    analise = ocorrencia["dia_analise"]
    conclusao = ocorrencia["dia_conclusao"]
    if situacao == "aberta":
        dias_coerentes = analise is None and conclusao is None
    elif situacao == "em_analise":
        dias_coerentes = analise is not None and conclusao is None
    elif situacao == "concluida":
        dias_coerentes = analise is not None and conclusao is not None
    else:
        raise ValueError("Situação desconhecida.")
    if not dias_coerentes:
        raise ValueError("Os dias de acompanhamento não correspondem à situação.")
    if analise is not None and analise < abertura:
        raise ValueError("O dia da análise é anterior à abertura.")
    if conclusao is not None and conclusao < analise:
        raise ValueError("O dia da conclusão é anterior à análise.")


def registrar_ocorrencia(estado, ocorrencia):
    validar_ocorrencia(ocorrencia, estado["por_codigo"])
    codigo = ocorrencia["codigo"]
    numero_codigo = int(codigo)

    # A lista e o índice apontam para o mesmo registro.
    estado["ocorrencias"].append(ocorrencia)
    estado["por_codigo"][codigo] = ocorrencia
    if ocorrencia["situacao"] == "aberta":
        estado["fila"].append(codigo)
    estado["ultimo_codigo"] = max(estado["ultimo_codigo"], numero_codigo)
    estado["dia"] = max(
        estado["dia"],
        ocorrencia["dia_abertura"],
        ocorrencia["dia_analise"] or 0,
        ocorrencia["dia_conclusao"] or 0,
    )


def registrar_evento(historico, codigo, anterior, nova, dia):
    historico.append({"codigo": codigo, "anterior": anterior, "nova": nova, "dia": dia})


def carregar_dados(caminho=ARQUIVO_DADOS):
    estado = {
        "ocorrencias": [],
        "por_codigo": {},
        "fila": [],
        "historico": [],
        "ultimo_codigo": 0,
        "dia": 0,
    }
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo, strict=True)
        if leitor.fieldnames != CAMPOS_CSV:
            raise ValueError("O cabeçalho de dados.csv precisa seguir o formato do README.")

        for linha in leitor:
            try:
                if None in linha or None in linha.values():
                    raise ValueError("Quantidade de campos diferente do cabeçalho.")
                ocorrencia = {}
                for campo in CAMPOS_CSV:
                    ocorrencia[campo] = linha[campo].strip()

                numero = inteiro_positivo(ocorrencia["codigo"], "Código")
                ocorrencia["codigo"] = f"{numero:03d}"
                ocorrencia["dia_abertura"] = inteiro_positivo(
                    ocorrencia["dia_abertura"], "Dia de abertura"
                )
                for campo in ("dia_analise", "dia_conclusao"):
                    if ocorrencia[campo]:
                        ocorrencia[campo] = inteiro_positivo(ocorrencia[campo], campo)
                    else:
                        ocorrencia[campo] = None
                registrar_ocorrencia(estado, ocorrencia)
            except ValueError as erro:
                print(f"Linha {leitor.line_num} de dados.csv ignorada. {erro}")

    # As datas do CSV reconstroem os eventos que antecedem esta sessão.
    historico = estado["historico"]
    for ocorrencia in estado["ocorrencias"]:
        codigo = ocorrencia["codigo"]
        if ocorrencia["dia_analise"] is not None:
            registrar_evento(historico, codigo, "aberta", "em_analise", ocorrencia["dia_analise"])
        if ocorrencia["dia_conclusao"] is not None:
            registrar_evento(historico, codigo, "em_analise", "concluida", ocorrencia["dia_conclusao"])
    historico.sort(key=lambda evento: evento["dia"])
    return estado


def buscar_por_codigo(estado, texto):
    numero = inteiro_positivo(texto, "Código")
    ocorrencia = estado["por_codigo"].get(f"{numero:03d}")
    if ocorrencia is None:
        raise ValueError("Ocorrência não encontrada para esse código.")
    return ocorrencia


def filtrar_ocorrencias(ocorrencias, categoria, situacao):
    resultado = []
    for ocorrencia in ocorrencias:
        categoria_confere = categoria == "" or ocorrencia["categoria"] == categoria
        situacao_confere = situacao == "" or ocorrencia["situacao"] == situacao
        if categoria_confere and situacao_confere:
            resultado.append(ocorrencia)
    return resultado


def alterar_situacao(estado, ocorrencia, nova):
    atual = ocorrencia["situacao"]
    if nova not in SITUACOES:
        raise ValueError("Situação desconhecida.")
    if atual == "aberta" and nova == "em_analise":
        campo_dia = "dia_analise"
    elif atual == "em_analise" and nova == "concluida":
        campo_dia = "dia_conclusao"
    else:
        raise ValueError("Transição inválida. O fluxo é Aberta → Em análise → Concluída.")

    codigo = ocorrencia["codigo"]
    dia = estado["dia"] + 1
    if atual == "aberta":
        estado["fila"].remove(codigo)
    ocorrencia["situacao"] = nova
    ocorrencia[campo_dia] = dia
    estado["dia"] = dia
    registrar_evento(estado["historico"], codigo, atual, nova, dia)
    print(f"Ocorrência {codigo} alterada para {SITUACOES[nova]} no dia {dia}.")


def montar_hierarquia(ocorrencias):
    hierarquia = {}
    for ocorrencia in ocorrencias:
        categorias = hierarquia.setdefault(ocorrencia["bairro"], {})
        codigos = categorias.setdefault(ocorrencia["categoria"], [])
        codigos.append(ocorrencia["codigo"])
    return hierarquia


def calcular_indicadores(ocorrencias):
    categorias = list(CATEGORIAS)
    situacoes = list(SITUACOES)
    matriz = []
    for _ in categorias:
        matriz.append([0] * len(situacoes))

    totais_situacao = [0] * len(situacoes)
    soma_dias = 0
    for ocorrencia in ocorrencias:
        linha = categorias.index(ocorrencia["categoria"])
        coluna = situacoes.index(ocorrencia["situacao"])
        matriz[linha][coluna] += 1
        totais_situacao[coluna] += 1
        if ocorrencia["situacao"] == "concluida":
            soma_dias += ocorrencia["dia_conclusao"] - ocorrencia["dia_abertura"]

    concluidas = totais_situacao[situacoes.index("concluida")]
    total = len(ocorrencias)
    media_dias = None
    if concluidas:
        media_dias = soma_dias / concluidas
    return matriz, totais_situacao, total - concluidas, media_dias


def percentual(quantidade, total):
    proporcao = 0
    if total:
        proporcao = 100 * quantidade / total
    return f"{proporcao:.1f}%".replace(".", ",")


def exibir_indicadores(ocorrencias):
    matriz, totais_situacao, pendencias, media_dias = calcular_indicadores(ocorrencias)
    total = len(ocorrencias)
    print(f"Total de ocorrências válidas na sessão: {total}")
    print("Origem dos dados: registros válidos de dados.csv e operações desta sessão.")
    print()
    print("Categoria       | Aberta | Em análise | Concluída | Total | % do total")
    pendencias_por_categoria = []
    for indice, categoria in enumerate(CATEGORIAS):
        abertas, em_analise, concluidas = matriz[indice]
        subtotal = sum(matriz[indice])
        pendencias_por_categoria.append(abertas + em_analise)
        print(
            f"{CATEGORIAS[categoria]:15} | {abertas:6} | {em_analise:10} |"
            f" {concluidas:9} | {subtotal:5} | {percentual(subtotal, total)}"
        )
    print()
    for indice, situacao in enumerate(SITUACOES):
        quantidade = totais_situacao[indice]
        print(f"{SITUACOES[situacao]}: {quantidade} ({percentual(quantidade, total)})")

    print(f"Pendências (abertas + em análise): {pendencias}")
    if media_dias is None:
        print("Ainda não há conclusões para calcular o tempo médio.")
    else:
        media_formatada = f"{media_dias:.1f}".replace(".", ",")
        print(f"Tempo médio simulado até a conclusão: {media_formatada} dias")
    print()
    print("Percentual = quantidade ÷ total válido × 100.")
    print("Tempo médio = soma de (dia de conclusão − dia de abertura) ÷ total de concluídas.")
    if pendencias:
        maior = max(pendencias_por_categoria)
        destaques = []
        for indice, categoria in enumerate(CATEGORIAS):
            if pendencias_por_categoria[indice] == maior:
                destaques.append(CATEGORIAS[categoria])
        print(f"Na amostra, o maior total por categoria é de {maior} pendências ({', '.join(destaques)}).")
    else:
        print("Nenhuma demanda pendente na amostra atual.")


def exibir_listagem(ocorrencias):
    if not ocorrencias:
        print("Nenhuma ocorrência para exibir.")
        return
    print("Código | Categoria | Bairro e local | Situação")
    for ocorrencia in ocorrencias:
        bairro = BAIRROS[ocorrencia["bairro"]]
        categoria = CATEGORIAS[ocorrencia["categoria"]]
        situacao = SITUACOES[ocorrencia["situacao"]]
        print(f"{ocorrencia['codigo']} | {categoria} | {bairro}, {ocorrencia['local']} | {situacao}")


def exibir_historico(historico):
    if not historico:
        print("Nenhum evento no histórico.")
        return
    print("Histórico com os eventos mais recentes primeiro")
    for evento in reversed(historico):
        anterior = SITUACOES[evento["anterior"]]
        nova = SITUACOES[evento["nova"]]
        print(f"Dia {evento['dia']} | {evento['codigo']} | {anterior} → {nova}")


def exibir_hierarquia(ocorrencias):
    if not ocorrencias:
        print("Nenhuma ocorrência para agrupar.")
        return
    for bairro, categorias in montar_hierarquia(ocorrencias).items():
        print(BAIRROS[bairro])
        for categoria, codigos in categorias.items():
            print(f"  {CATEGORIAS[categoria]}: {', '.join(codigos)}")


def ler_entrada(pergunta):
    resposta = input(f"{pergunta} > ").strip()
    print()
    return resposta


def escolher(rotulo, opcoes, permitir_todas=False):
    por_numero = {}
    print(rotulo)
    if permitir_todas:
        print("  0. Todas")
        por_numero["0"] = ""
    for numero, (chave, nome) in enumerate(opcoes.items(), 1):
        print(f"  {numero}. {nome}")
        por_numero[str(numero)] = chave
    entrada = ler_entrada("Informe o número")
    if entrada not in por_numero:
        raise ValueError(f"Opção inválida para {rotulo.lower()}. Escolha um número da lista.")
    return por_numero[entrada]


def cadastrar(estado):
    print("Use apenas descrições fictícias e locais genéricos.")
    bairro = escolher("Bairro", BAIRROS)
    categoria = escolher("Categoria", CATEGORIAS)
    descricao = ler_entrada("Descrição breve")
    local = ler_entrada("Local genérico")
    numero = estado["ultimo_codigo"] + 1
    ocorrencia = {
        "codigo": f"{numero:03d}",
        "bairro": bairro,
        "categoria": categoria,
        "descricao": descricao,
        "local": local,
        "dia_abertura": estado["dia"] + 1,
        "situacao": "aberta",
        "dia_analise": None,
        "dia_conclusao": None,
    }
    registrar_ocorrencia(estado, ocorrencia)
    print(f"Ocorrência {ocorrencia['codigo']} cadastrada no dia {ocorrencia['dia_abertura']}.")
    print("Situação inicial: Aberta.")


def executar_menu(estado):
    while True:
        print(MENU)
        opcao = ler_entrada("Escolha uma opção")
        ocorrencias = estado["ocorrencias"]
        try:
            if opcao == "1":
                exibir_listagem(ocorrencias)
            elif opcao == "2":
                ocorrencia = buscar_por_codigo(estado, ler_entrada("Código"))
                exibir_listagem([ocorrencia])
                print(f"Descrição: {ocorrencia['descricao']}")
                print(f"Dia de abertura: {ocorrencia['dia_abertura']}")
            elif opcao == "3":
                categoria = escolher("Categoria", CATEGORIAS, permitir_todas=True)
                situacao = escolher("Situação", SITUACOES, permitir_todas=True)
                exibir_listagem(filtrar_ocorrencias(ocorrencias, categoria, situacao))
            elif opcao == "4":
                cadastrar(estado)
            elif opcao == "5":
                if estado["fila"]:
                    # Examinar pela fila sempre começa pelo registro mais antigo.
                    codigo = estado["fila"][0]
                    alterar_situacao(estado, estado["por_codigo"][codigo], "em_analise")
                else:
                    print("A fila de ocorrências abertas está vazia.")
            elif opcao == "6":
                ocorrencia = buscar_por_codigo(estado, ler_entrada("Código"))
                situacao = escolher("Situação", SITUACOES)
                alterar_situacao(estado, ocorrencia, situacao)
            elif opcao == "7":
                exibir_historico(estado["historico"])
            elif opcao == "8":
                exibir_hierarquia(ocorrencias)
            elif opcao == "9":
                exibir_indicadores(ocorrencias)
            elif opcao == "0":
                return
            else:
                print("Opção inválida. Escolha um número do menu.")
        except ValueError as erro:
            print(erro)


def main():
    print("Neighborhood Action Dashboard")
    print("Global Solution 2026.2 | Painel comunitário simulado")
    print()
    try:
        estado = carregar_dados()
    except (OSError, UnicodeError, csv.Error, ValueError) as erro:
        print(f"Não foi possível carregar a base de dados. {erro}")
        return 1
    print("A base é recarregada a cada execução. As alterações ficam nesta sessão.")
    try:
        executar_menu(estado)
    except (EOFError, KeyboardInterrupt):
        print()
    print("Sessão encerrada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
