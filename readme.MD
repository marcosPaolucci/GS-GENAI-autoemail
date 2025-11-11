# Smart Inbox Triage and Response

Este projeto é um assistente de caixa de entrada inteligente que usa IA para automatizar a triagem, análise e resposta de e-mails. Ele se conecta a uma conta do Gmail, processa e-mails não lidos usando um fluxo de agentes (LangGraph), e apresenta rascunhos de resposta em uma interface web (Streamlit) para aprovação humana.

## 🚀 Fluxo de Trabalho

O núcleo do projeto é um grafo de agentes que executa um fluxo de trabalho passo a passo para cada e-mail.

1. **Buscar E-mails (Gmail API):** O aplicativo busca e-mails não lidos da caixa de entrada.  
2. **Agente 1: Triador:** Classifica o e-mail (ex: "Suporte Técnico", "Orçamento") e define a prioridade (ex: "Alta", "Média").  
3. **Agente 2: Extrator de Dados:** Extrai informações-chave do e-mail (ex: `numero_pedido`, `remetente_nome`, `intencao`).  
4. **Agente 3: Redator de Resposta:** Usa a triagem e os dados extraídos para gerar um rascunho de resposta coeso e personalizado.  
5. **Revisão Humana (Streamlit):** O fluxo é **pausado**. O rascunho é exibido ao usuário na interface web para aprovação ou edição.  
6. **Envio (Gmail API):** Após a aprovação humana, o grafo é retomado, enviando a resposta final pela Gmail API e marcando o e-mail original como lido.

---

## 🛠️ Tecnologias Utilizadas

- **LangGraph:** Para construir o fluxo de estado entre os agentes de IA.  
- **LangChain (OpenAI):** Para se conectar ao modelo de linguagem (GPT-4o) para classificação, extração e geração de texto.  
- **Streamlit:** Para a interface de usuário (frontend) rápida e interativa.  
- **Google API (Gmail):** Para ler, enviar e modificar e-mails.  
- **Pydantic:** Para garantir a extração de dados estruturados (JSON) dos modelos de IA.

---

## ⚙️ Configuração do Ambiente

Para rodar este projeto, você precisa configurar suas chaves de API e credenciais de autenticação.

### 1. Instalar Dependências

Certifique-se de ter um arquivo `requirements.txt` com o conteúdo abaixo e instale-o:

```bash
pip install -r requirements.txt
```

### 2. Criar o Arquivo .env

Na raiz do projeto, crie um arquivo chamado `.env`. Ele armazena suas chaves secretas de API.  

**Nunca compartilhe este arquivo.**

```bash
# .env

# Sua chave de API da OpenAI (ex: sk-...)
OPENAI_API_KEY="SUA_CHAVE_OPENAI_AQUI"

# Caminhos para os arquivos de credenciais do Google
GMAIL_CREDENTIALS_PATH="credentials.json"
GMAIL_TOKEN_PATH="token.json"
```

---

## 🔑 Como Obter as Credenciais do Google

O fluxo de autenticação do Google usa dois arquivos:

- `credentials.json`: A "identidade" do seu aplicativo.  
- `token.json`: A "permissão" do usuário.  

### A. Como Obter o `credentials.json` (Download Manual)

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/).  
2. Crie um **Novo Projeto** (ex: "Smart Inbox App").  
3. No painel do projeto, vá para **APIs e Serviços → Biblioteca**.  
4. Procure por **Gmail API** e clique em **Ativar**.  
5. No menu lateral, vá para **APIs e Serviços → Tela de permissão OAuth**.  
6. Selecione **Externo (External)** e clique em **Criar**.  
7. Preencha os campos obrigatórios (nome do app, e-mail de suporte).  
8. Em **Usuários de teste**, clique em **ADD USERS** e adicione o e-mail que você usará para autenticar.  
9. Vá para **Credenciais → + Criar Credenciais → ID do cliente OAuth**.  
10. Escolha **Aplicativo de computador (Desktop app)**.  
11. Após a criação, clique em **Baixar JSON** e salve como `credentials.json` na raiz do projeto.

### B. Como Obter o `token.json` (Gerado Automaticamente)

Você não cria este arquivo. O script faz isso automaticamente na primeira execução:

1. Após configurar o `.env` e o `credentials.json`, rode o aplicativo Streamlit.  
2. Clique em **Buscar Novos E-mails** pela primeira vez.  
3. Faça login na conta do Google e permita o acesso.  
4. O arquivo `token.json` será criado automaticamente.  

---

## ▶️ Como Rodar o Aplicativo

Com o `.env` e o `credentials.json` no lugar, inicie o aplicativo Streamlit a partir do terminal:

```bash
streamlit run web_interface/app.py
```

Seu navegador abrirá automaticamente.  

1. Clique em **Buscar Novos E-mails** na barra lateral.  
2. (Se for a primeira vez, complete o fluxo de autenticação do Google.)  
3. Os e-mails não lidos aparecerão na barra lateral.  
4. Clique em um e-mail para que a IA o processe.  
5. Revise a análise e o rascunho de resposta.  
6. Edite (se necessário) e clique em **Aprovar e Enviar**.
