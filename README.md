# CondoFace — Controle de acesso com reconhecimento facial

O **CondoFace** é um projeto acadêmico de controle de acesso para condomínios. Ele reúne um painel administrativo web, cadastros de moradores e visitantes, captura de imagens faciais, treinamento de um reconhecedor LBPH e registro de tentativas de acesso no MySQL.

> **Estado atual:** protótipo em desenvolvimento. A captura de 30 imagens e o treinamento LBPH já foram testados; o registro automático de acesso negado também foi observado. A confirmação automática da biometria no banco e o fluxo completo de acesso permitido ainda precisam de validação. Não utilize o protótipo para controlar uma entrada real.

## 1. Funcionalidades

- Login de administrador com senha armazenada como hash.
- Cadastro, edição, listagem e ativação/desativação de moradores e visitantes.
- Captura facial pelo painel web, com até **30 imagens por pessoa**.
- Treinamento de reconhecimento facial com **OpenCV LBPH**.
- Detecção facial com modelo **DNN/Caffe** e reconhecimento pela webcam.
- Consulta de situação cadastral e regras de autorização no MySQL.
- Histórico de tentativas de acesso e indicadores no dashboard.

## 2. Tecnologias

| Camada | Tecnologias |
| --- | --- |
| Backend web | Python, Flask |
| Visão computacional | OpenCV, NumPy, LBPH, DNN/Caffe |
| Banco de dados | MySQL, `mysql-connector-python` |
| Interface | HTML, CSS, JavaScript |
| Segurança administrativa | Sessão Flask, hash de senha, validação CSRF |

## 3. Como o sistema funciona

```text
Administrador acessa o painel
             |
             v
Cadastra morador ou visitante no MySQL
             |
             v
Captura até 30 imagens do rosto
             |
             v
Executa treinar.py para gerar o modelo LBPH
             |
             v
Executa main.py e abre a webcam
             |
             v
Detecta rosto -> tenta identificar pessoa
             |
             v
Consulta cadastro, biometria e autorização
             |
             v
Registra resultado no histórico do MySQL
             |
             v
Dashboard apresenta os registros
```

**Importante:** salvar imagens, treinar o modelo e marcar a biometria como cadastrada no banco são etapas distintas. Na versão atual, a captura e o treinamento não garantem que `biometria_cadastrada` seja atualizado automaticamente.

## 4. Pré-requisitos

- Windows com PowerShell (ambiente utilizado no desenvolvimento).
- Python instalado e acessível pelo comando `python`.
- MySQL Server instalado e em execução.
- Webcam funcional e permissão de acesso à câmera.
- Arquivos do projeto e os modelos DNN/Caffe necessários.

## 5. Instalação passo a passo

### Passo 1 — Abrir a pasta do projeto

```powershell
cd "C:\caminho\para\CondoFace"
```

Substitua o caminho pelo local em que você salvou o projeto.

### Passo 2 — Criar um ambiente virtual

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Se a política de execução impedir a ativação, você pode executar diretamente `\.venv\Scripts\python.exe` nos comandos seguintes.

### Passo 3 — Instalar as dependências

```powershell
python -m pip install --upgrade pip
python -m pip install flask opencv-contrib-python numpy mysql-connector-python
```

Use `opencv-contrib-python`, pois o reconhecimento LBPH depende do módulo `cv2.face`. Se o projeto tiver um `requirements.txt` atualizado, prefira `python -m pip install -r requirements.txt`.

### Passo 4 — Preparar o banco de dados

1. Inicie o MySQL.
2. Crie o banco `condoface` caso ainda não exista:

```sql
CREATE DATABASE IF NOT EXISTS condoface
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

3. **Importe o script SQL do projeto** com as tabelas e relacionamentos. Criar apenas o banco vazio não é suficiente. O projeto utiliza, entre outras, as tabelas `administradores`, `moradores`, `visitantes` e `historico_acessos`, além das tabelas de autorização.
4. Confira as configurações de conexão em `conexao.py` (`host`, `user`, `password`, `database`). **Não publique senhas reais no GitHub.** Antes de disponibilizar o projeto, adapte essas configurações para variáveis de ambiente.

> O script SQL completo ainda precisa ser incluído no repositório. Sem ele, uma instalação nova não terá a estrutura de tabelas necessária.

### Passo 5 — Configurar a chave secreta do Flask

No mesmo terminal PowerShell em que iniciará o painel:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

Copie o valor gerado e configure-o na sessão atual:

```powershell
$env:CONDOFACE_SECRET_KEY="COLE_AQUI_A_CHAVE_GERADA"
```

Não compartilhe essa chave nem a inclua no código-fonte.

### Passo 6 — Criar o administrador

```powershell
python criar_admin.py
```

Informe nome, e-mail e uma senha com pelo menos 12 caracteres. Esse comando exige que a tabela `administradores` já exista.

### Passo 7 — Iniciar o painel administrativo

```powershell
python app.py
```

Abra no navegador:

**http://127.0.0.1:5000**

Entre com o e-mail e a senha do administrador.

## 6. Como usar o CondoFace

### 6.1. Cadastrar uma pessoa

1. Entre no painel administrativo.
2. Abra a seção de **moradores** ou **visitantes**.
3. Preencha os dados solicitados e salve.
4. Confira se a pessoa aparece na listagem.

### 6.2. Cadastrar imagens faciais

1. Escolha a pessoa cadastrada.
2. Abra a opção de **cadastro facial**.
3. Autorize o uso da câmera e inicie a captura.
4. Aguarde a indicação **30/30 imagens salvas**.
5. Feche a janela de captura.

As imagens são organizadas em pastas semelhantes a:

```text
banco_faces/
├── moradores/
│   └── 4/
│       ├── rosto_001.jpg
│       └── ...
└── visitantes/
    └── 2/
        ├── rosto_001.jpg
        └── ...
```

**Atenção:** fechar a janela não equivale a concluir a validação biométrica. No estado atual do projeto, pode ser necessário corrigir a integração que atualiza o campo `biometria_cadastrada` após o treinamento.

### 6.3. Treinar o reconhecimento facial

Pare o processo de reconhecimento, caso esteja aberto, e execute na pasta do projeto:

```powershell
python treinar.py
```

O programa procura imagens nas pastas `banco_faces/moradores/<id>` e `banco_faces/visitantes/<id>`, usando no mínimo 30 imagens por identidade, e gera:

```text
lbph_classifier.yml
face_names.pickle
```

Verifique no terminal a quantidade de pessoas e imagens processadas. **Não reutilize o mesmo rosto em cadastros de identidades diferentes**, pois isso confunde o modelo.

### 6.4. Iniciar o reconhecimento pela webcam

Em outro terminal, com o ambiente virtual ativo:

```powershell
python main.py
```

O script carrega os arquivos de detecção e reconhecimento facial, abre a webcam, tenta identificar o rosto e consulta as condições de acesso. O resultado pode ser exibido como reconhecido, desconhecido ou acesso negado conforme as verificações realizadas.

Os seguintes arquivos devem estar nos caminhos esperados pelo `main.py`:

```text
deploy.prototxt.txt
res10_300x300_ssd_iter_140000.caffemodel
lbph_classifier.yml
face_names.pickle
```

**Observação sobre o limite:** `THRESHOLD` no `main.py` representa uma **distância LBPH**, e não uma porcentagem. Aumentar de 70 para 80 torna a aceitação mais permissiva e pode aumentar identificações incorretas.

### 6.5. Consultar o histórico

No dashboard, acesse a tabela de histórico de acessos e use o botão de atualização quando necessário. A API protegida por login é:

```http
GET /api/historico
```

O histórico apresenta informações como pessoa, tipo, data/hora, resultado e motivo, conforme os registros existentes.

## 7. Principais arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Servidor Flask, login, rotas do painel e recebimento de imagens faciais |
| `main.py` | Detecção, reconhecimento pela webcam e avaliação de acesso |
| `cadastrar.py` | Processamento de imagens enviadas pelo cadastro web |
| `treinar.py` | Treinamento LBPH e geração dos arquivos do modelo |
| `identidade.py` | Identificadores que distinguem moradores de visitantes |
| `conexao.py` | Conexão com o MySQL |
| `criar_admin.py` | Cadastro inicial do administrador |
| `morador_repository.py` | Consultas de moradores |
| `visitante_repository.py` | Consultas de visitantes |
| `autorizacao_repository.py` | Consulta de autorizações de moradores |
| `autorizacao_visitante_repository.py` | Consulta de autorizações de visitantes |
| `historico_repository.py` | Registro e consulta do histórico de acessos |
| `templates/dashboard.html` | Interface do painel |
| `static/js/dashboard.js` | Interações do painel com a API |

## 8. Problemas comuns

**`Desconhecido` na webcam:** verifique se a pessoa possui fotos no diretório correto, se `treinar.py` foi executado após a captura e se o `main.py` está carregando o modelo atualizado. Evite duplicar o mesmo rosto entre pessoas diferentes.

**`BIOMETRIA NAO CADASTRADA`:** verifique o campo `biometria_cadastrada` no MySQL. A existência das 30 fotos e do modelo treinado não implica, por si só, que o campo tenha sido atualizado.

**Pessoa não aparece na lista:** consulte o registro diretamente no MySQL e confira a resposta de `GET /api/moradores` ou `GET /api/visitantes`. Se o registro existir na API, investigue a atualização da interface JavaScript.

**`No module named cv2.face` ou ausência de `cv2.face`:** instale `opencv-contrib-python` no ambiente Python correto e evite instalações conflitantes do OpenCV.

**Erro ao conectar no MySQL:** confirme se o servidor está ativo, se o banco `condoface` existe e se as credenciais configuradas são válidas.

**Erro `CONDOFACE_SECRET_KEY`:** defina a variável de ambiente antes de executar `python app.py`.

## 9. Testes e limitações atuais

- [x] Cadastro de moradores e visitantes pelo backend.
- [x] Captura de 30 imagens de uma identidade.
- [x] Treinamento LBPH com geração do modelo.
- [x] Consulta do histórico no painel.
- [x] Registro automático observado de tentativa negada.
- [ ] Confirmar atualização automática de `biometria_cadastrada` após treinamento bem-sucedido.
- [ ] Validar integralmente o fluxo de acesso permitido.
- [ ] Revisar comportamento da lista após fechar a janela de captura.
- [ ] Adicionar script SQL completo para instalação reproduzível.
- [ ] Remover credenciais fixas antes da publicação.

## 10. Privacidade e segurança

Imagens faciais são dados biométricos sensíveis. Utilize somente imagens de pessoas que autorizaram o teste. Não publique fotos reais, arquivos de treinamento pessoais, credenciais, dumps de banco com dados pessoais ou chaves secretas em repositórios públicos. Para uma aplicação real, seriam necessários controles adicionais de proteção de dados, prevenção de fraude por foto/vídeo, auditoria, retenção e exclusão de dados, além de validação de desempenho e adequação à LGPD.

## 11. Publicação no GitHub

Antes de publicar:

1. Crie um `.gitignore` para `.venv/`, `__pycache__/`, `.env`, arquivos de dados e imagens biométricas.
2. Remova senhas e chaves fixas do código e do histórico de commits.
3. Inclua um `requirements.txt` gerado e revisado no ambiente que funciona.
4. Inclua o script SQL de criação das tabelas, sem dados pessoais.
5. Adicione capturas de tela do dashboard **sem informações pessoais**.
6. Descreva as limitações e os testes realmente executados.

## 12. Objetivo acadêmico

Demonstrar a integração entre visão computacional, persistência de dados, regras de autorização e interface administrativa, aplicando Python, OpenCV, Flask e MySQL em um protótipo de controle de acesso.

---

**CondoFace — projeto acadêmico e de portfólio, em desenvolvimento.**
