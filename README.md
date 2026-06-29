# cortex

CLI com **skills** plugáveis para apoiar o fluxo de desenvolvimento de ponta a ponta — tanto upstream (planejamento, board) quanto downstream (PR, testes).

Cada skill é uma pasta independente em `skills/`, com um `manifest.yaml` (nome + descrição) e um `skill.py` (função `run`). O core descobre e registra as skills automaticamente como comandos do CLI — adicionar uma automação nova não exige tocar no core.

## Instalação

Requer Python 3.10+.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/Mac

pip install -e .
```

Isso instala o comando `cortex` no seu ambiente (editável — mudanças no código refletem sem reinstalar).

## Configuração

Copie `.env.example` para `.env` e preencha as variáveis necessárias para as skills que for usar:

```bash
cp .env.example .env
```

| Variável | Usada por | Onde obter |
|---|---|---|
| `AZURE_DEVOPS_ORG` | `azure-create-card` | Nome da organização na URL do Azure DevOps (`dev.azure.com/<org>`) |
| `AZURE_DEVOPS_PROJECT` | `azure-create-card` | Nome do projeto no Azure DevOps |
| `AZURE_DEVOPS_PAT` | `azure-create-card` | Azure DevOps → ícone de usuário → *Personal access tokens* → escopo **Work Items: Read & write** |
| `ANTHROPIC_API_KEY` | `test-generator` | [console.anthropic.com](https://console.anthropic.com/settings/keys) |

Em pipelines (dev/tst/prd) essas variáveis devem ser injetadas diretamente pelo pipeline (ex: script PowerShell) — o `.env` é usado só localmente e nunca sobrescreve uma variável já definida no ambiente.

## Skills disponíveis

### `pr-description`

Gera a descrição de um PR a partir dos commits e arquivos alterados em relação a uma branch base.

```bash
cortex pr-description --base main
cortex pr-description --base main --output pr.md
```

| Opção | Descrição | Default |
|---|---|---|
| `--base`, `-b` | Branch base para comparar | `main` |
| `--output`, `-o` | Arquivo para salvar a descrição (senão imprime no terminal) | — |

### `azure-create-card`

Cria um work item (Task, User Story, Bug, etc.) em um board do Azure DevOps.

```bash
cortex azure-create-card --title "Ajustar validação de CPF" --type Task --description "Detalhes do que precisa ser feito"
```

| Opção | Descrição | Default |
|---|---|---|
| `--title`, `-t` | Título do card (obrigatório) | — |
| `--type` | Tipo do work item (`Task`, `User Story`, `Bug`, ...) | `Task` |
| `--description`, `-d` | Descrição do card | — |
| `--area-path` | Area Path do projeto | — |
| `--iteration-path` | Iteration Path (sprint) | — |
| `--assigned-to` | E-mail da pessoa responsável | — |

### `test-generator`

Gera testes automatizados (pytest) para um arquivo Python, usando a API da Claude.

```bash
cortex test-generator --file caminho/do/arquivo.py --output caminho/do/test_arquivo.py
```

| Opção | Descrição | Default |
|---|---|---|
| `--file`, `-f` | Arquivo Python para gerar testes (obrigatório) | — |
| `--output`, `-o` | Arquivo para salvar os testes (senão imprime no terminal) | — |

> Testes gerados por IA devem ser revisados antes de aceitos — nem sempre cobrem corretamente o comportamento real do código (ex: tipos de exceção, side effects).

## Criando uma nova skill

1. Crie uma pasta em `skills/`, ex: `skills/minha-skill/`.
2. Adicione um `manifest.yaml`:
   ```yaml
   name: minha-skill
   description: O que essa skill faz.
   ```
3. Adicione um `skill.py` com uma função `run(...)`, usando `typer.Option`/`typer.Argument` nos parâmetros — o Typer gera as flags da CLI a partir da assinatura da função.
4. Reinstale (`pip install -e .`) se for a primeira skill nova desde a instalação — o comando `cortex minha-skill` passa a existir.
