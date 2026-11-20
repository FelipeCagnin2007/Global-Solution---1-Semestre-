# Neighborhood Action Dashboard

Global Solution 2026.2 · Ciência da Computação Online · FIAP

- **Entrega individual** de Felipe Cagnin de Lima, RM 575251.
- **Participação na competição** — Não.

## Comunidade simulada

Vila Horizonte e Jardim do Ipê são bairros fictícios. Problemas como postes apagados, desníveis em travessias, resíduos e bancos danificados podem ficar dispersos em relatos informais. O painel reúne as ocorrências e permite que moradores e representantes comunitários consultem a situação de cada relato e vejam quais categorias têm mais pendências.

## Como executar

Baixe ou clone o repositório, abra o terminal na raiz do projeto e execute com Python 3.

```bash
python src/sistema.py
```

Se o seu sistema usa o comando `python3`, execute `python3 src/sistema.py`. A aplicação usa a biblioteca padrão do Python e funciona localmente. Cada execução começa com a base fictícia. Cadastros e atualizações ficam disponíveis até o fim da sessão.

## Dados de demonstração

A base [data/dados.csv](data/dados.csv) usa UTF-8 e vírgulas. O cabeçalho abaixo indica a ordem dos campos.

```text
codigo,bairro,categoria,descricao,local,dia_abertura,situacao,dia_analise,dia_conclusao
```

| Campos | Regras |
| --- | --- |
| `codigo` | Obrigatório e único. A aplicação usa pelo menos três dígitos e aceita a busca com ou sem zeros à esquerda. |
| `bairro`, `categoria` | Obrigatórios e padronizados. Os bairros usam `vila_horizonte` e `jardim_do_ipe`. As categorias usam `iluminacao`, `acessibilidade`, `limpeza` e `conservacao`. |
| `descricao`, `local` | Obrigatórios. Registram um relato breve e um ponto de referência genérico. |
| `dia_abertura`, `situacao` | Obrigatórios. A abertura usa um dia inteiro positivo. A situação usa `aberta`, `em_analise` ou `concluida`. |
| `dia_analise`, `dia_conclusao` | Preenchidos apenas quando o registro alcançou a etapa correspondente. Os dias seguem a ordem de abertura, análise e conclusão. |

A carga inicial aceita 12 ocorrências e recompõe 10 eventos de histórico a partir dos dias de análise e conclusão. A linha 13, de código `012`, tem a categoria vazia de propósito. O programa informa o motivo da rejeição e segue com as linhas válidas.

## Estruturas de dados

| Estrutura | Uso |
| --- | --- |
| Lista | Guarda os registros válidos na ordem de cadastro. O programa percorre a lista para listar, filtrar e contar. |
| Dicionário | Associa cada código ao mesmo registro guardado na lista. A busca chega diretamente à ocorrência, e a atualização aparece nas duas consultas. |
| Fila FIFO | Guarda os códigos das ocorrências abertas por ordem de cadastro. A triagem examina a primeira. Uma triagem por código retira apenas o item escolhido e preserva a ordem dos demais. |
| Pilha | Recebe as mudanças de situação no topo. A consulta começa pelo último evento e preserva o histórico. |
| Hierarquia | Agrupa os códigos por bairro e depois por categoria, facilitando a consulta de demandas do mesmo tipo em cada localidade. |
| Matriz | Usa uma linha por categoria e uma coluna por situação. Cada célula conta a combinação da sua linha com a sua coluna. |

## Regras de cadastro, consulta e atualização

| Situação | Significado |
| --- | --- |
| Aberta | Ocorrência cadastrada e ainda à espera de triagem. |
| Em análise | Ocorrência examinada e em acompanhamento. |
| Concluída | Acompanhamento encerrado na simulação. |

O cadastro cria um código sequencial e começa em **Aberta**. O calendário simulado começa no último dia válido da base e avança um dia por cadastro ou mudança aceita. O fluxo é **Aberta → Em análise → Concluída**. A primeira mudança retira o código da fila. Cada alteração registra o código, o dia e as situações anterior e nova. Se um código não existir ou a mudança for inválida, o menu informa o motivo e preserva a sessão.

O filtro usa `0` para aceitar todas as categorias ou todas as situações. A expressão abaixo exige que o registro satisfaça as duas escolhas.

```python
categoria_confere = categoria == "" or ocorrencia["categoria"] == categoria
situacao_confere = situacao == "" or ocorrencia["situacao"] == situacao
if categoria_confere and situacao_confere:
    resultado.append(ocorrencia)
```

`or` permite selecionar todas ou exigir uma correspondência. `and` exige a combinação dos dois critérios. Na validação, `if not ocorrencia["categoria"]` rejeita a categoria ausente. Na atualização, `if` aceita iniciar a análise, `elif` aceita concluí-la, e `else` sinaliza a transição inválida.

## Indicadores da base inicial

| Categoria | Aberta | Em análise | Concluída | Total | % do total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Iluminação | 2 | 1 | 1 | 4 | 33,3% |
| Acessibilidade | 1 | 1 | 1 | 3 | 25,0% |
| Limpeza | 1 | 1 | 1 | 3 | 25,0% |
| Conservação | 1 | 1 | 0 | 2 | 16,7% |
| **Total** | **5** | **4** | **3** | **12** | **100,0%** |

- **Percentual** = quantidade da categoria ou situação ÷ total de ocorrências válidas × 100. As situações correspondem a 41,7% abertas, 33,3% em análise e 25,0% concluídas.
- **Pendências** = abertas + em análise. Na base inicial, são 5 + 4 = **9**.
- **Tempo médio até a conclusão** = soma das diferenças entre o dia de conclusão e o de abertura ÷ total de concluídas. As três durações iniciais são 4, 6 e 8 dias, com média de **6,0 dias simulados**. Se a base estiver sem conclusões, o painel explica por que a média ainda não pode ser calculada.

Iluminação concentra três das nove pendências simuladas. Essa frequência dá um ponto de partida para examinar os relatos da amostra. A análise se limita aos dados fictícios e ao período simulado.

## Exemplo de uso

1. Escolha `4` e depois Vila Horizonte (`1`) e Iluminação (`1`). Digite “Poste apagado perto do acesso à praça” e “Praça Central”.
2. Escolha `2` e busque por `014`. Em seguida, use `3` com categoria `1` e situação `1` para listar as ocorrências abertas de iluminação.
3. Use `5` para examinar a primeira ocorrência da fila, de código `001`. Use `6`, informe `001` e escolha `3` para concluí-la.
4. Use `7` para consultar os novos eventos e `9` para ver os indicadores atualizados.

Trechos da execução desse roteiro no terminal.

```text
Ocorrência 014 cadastrada no dia 19.
014 | Iluminação | Vila Horizonte, Praça Central | Aberta
Ocorrência 001 alterada para Em análise no dia 20.
Ocorrência 001 alterada para Concluída no dia 21.
Dia 21 | 001 | Em análise → Concluída
Dia 20 | 001 | Aberta → Em análise
Total de ocorrências válidas na sessão: 13
Tempo médio simulado até a conclusão: 9,5 dias
```

## Acessibilidade, privacidade e limites

O menu tem opções numeradas, rótulos em português e mensagens que indicam qual entrada precisa ser corrigida. As situações e os avisos são expressos em texto para leitura por teclado e terminal. Os relatos da demonstração são fictícios e usam locais genéricos. Ao testar, use descrições genéricas e preserve os dados pessoais dos moradores.

O painel mostra como organizar relatos e acompanhar mudanças de situação em uma comunidade. A situação “Concluída” descreve o encerramento do acompanhamento simulado. O programa atende uma sessão local e os números descrevem apenas a base utilizada.

## Documentação e vídeo

- Escolhas técnicas, testes e impacto social. [Relatório em PDF](docs/relatorio.pdf)
- Demonstração publicada no YouTube como **Não Listado**. [Vídeo de apresentação](https://youtu.be/XDPSd0apnoI)
- Apoio recebido e verificações realizadas. [Registro de uso de IA](docs/uso_ia.md)
