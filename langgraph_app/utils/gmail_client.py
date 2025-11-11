import os.path
import base64
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Importa as configurações (caminhos dos arquivos)
try:
    # Tentativa de import relativo (quando usado dentro do app)
    from .config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH
except ImportError:
    # Fallback para execução direta (quando testando este script)
    from config import GMAIL_CREDENTIALS_PATH, GMAIL_TOKEN_PATH

# Escopos da API do Gmail. Se mudar, delete o token.json.
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly', # Ler e-mails
    'https://www.googleapis.com/auth/gmail.modify',  # Modificar (ex: marcar como lido)
    'https://www.googleapis.com/auth/gmail.send'    # Enviar e-mails
]

def get_gmail_service():
    """
    Autentica com a API do Gmail e retorna um objeto de serviço.
    Cuida do fluxo OAuth2, criando ou atualizando o 'token.json'.
    """
    creds = None
    # O 'token.json' armazena os tokens de acesso e atualização.
    if os.path.exists(GMAIL_TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH, SCOPES)
    
    # Se não há credenciais válidas, pede login ao usuário.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Erro ao atualizar token: {e}. Re-autenticando...")
                # Se falhar, força a re-autenticação
                if os.path.exists(GMAIL_TOKEN_PATH):
                    os.remove(GMAIL_TOKEN_PATH)
                return get_gmail_service() # Recursivo
        else:
            if not os.path.exists(GMAIL_CREDENTIALS_PATH):
                raise FileNotFoundError(
                    f"Arquivo de credenciais '{GMAIL_CREDENTIALS_PATH}' não encontrado. "
                    "Faça o download no Google Cloud Console e coloque na raiz."
                )
            # Inicia o fluxo de autorização local (abrirá um navegador)
            flow = InstalledAppFlow.from_client_secrets_file(
                GMAIL_CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Salva as credenciais para a próxima execução
        with open(GMAIL_TOKEN_PATH, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'Ocorreu um erro ao construir o serviço: {error}')
        return None

def fetch_unread_emails():
    """
    Busca e-mails não lidos da caixa de entrada.
    Este será o "Email Inbound Node" do seu fluxo.
    Retorna uma lista de dicionários com dados dos e-mails.
    """
    service = get_gmail_service()
    if not service:
        print("Não foi possível conectar ao Gmail.")
        return []

    try:
        # Busca por e-mails não lidos (is:unread) no Inbox
        results = service.users().messages().list(
            userId='me', 
            q='is:unread in:inbox'
        ).execute()
        
        messages = results.get('messages', [])
        email_data_list = []

        if not messages:
            print('Nenhuma mensagem não lida encontrada.')
            return []

        print(f'Encontradas {len(messages)} mensagens não lidas.')

        for message_info in messages:
            msg_id = message_info['id']
            # 'full' para obter payload completo (corpo, headers)
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            
            payload = msg.get('payload', {})
            headers = payload.get('headers', [])
            
            email_data = {
                'id': msg_id,
                'snippet': msg.get('snippet'),
                'thread_id': msg.get('threadId'),
                'headers': {},
                'body': ''
            }

            # Extrai headers principais
            for header in headers:
                name = header.get('name')
                value = header.get('value')
                if name in ['From', 'To', 'Subject', 'Date', 'Message-ID']:
                    email_data['headers'][name] = value

            # Extrai o corpo do e-mail (prioriza text/plain)
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        body_data = part['body'].get('data')
                        if body_data:
                            email_data['body'] = base64.urlsafe_b64decode(body_data).decode('utf-8')
                        break
            elif 'body' in payload and payload['body'].get('data'):
                # Fallback para e-mails simples
                body_data = payload['body']['data']
                email_data['body'] = base64.urlsafe_b64decode(body_data).decode('utf-8')
            
            if email_data['body']: # Só adiciona se conseguimos extrair o corpo
                email_data_list.append(email_data)
        
        return email_data_list

    except HttpError as error:
        print(f'Ocorreu um erro ao buscar e-mails: {error}')
        return []

def send_reply(to_email: str, subject: str, message_text: str, thread_id: str):
    """
    Envia uma resposta de e-mail e RETORNA a confirmação.
    """
    service = get_gmail_service()
    if not service:
        print("Erro: Não foi possível obter o serviço do Gmail.")
        return None # Retorna None em caso de falha na conexão

    try:
        message = MIMEText(message_text, 'plain', 'utf-8') # Especifica utf-8
        message['to'] = to_email
        message['subject'] = subject
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        body = {
            'raw': raw_message,
            'threadId': thread_id
        }

        sent_message = service.users().messages().send(
            userId='me',
            body=body
        ).execute()
        
        print(f"Mensagem enviada. ID: {sent_message['id']}")
        # Retorna a confirmação da API
        return sent_message 

    except HttpError as error:
        print(f'Ocorreu um erro ao enviar e-mail: {error}')
        # Propaga o erro para o nó capturar
        raise error
    except Exception as e:
        print(f'Erro inesperado no send_reply: {e}')
        raise e

def mark_email_as_processed(message_id: str):
    """
    Marca um e-mail como 'lido' removendo o label 'UNREAD'.
    Poderia também adicionar um label customizado (ex: 'Processado-IA').
    """
    service = get_gmail_service()
    if not service:
        return

    try:
        # Remove o label 'UNREAD' para marcar como lido
        service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        
        print(f"Mensagem {message_id} marcada como processada (lida).")

    except HttpError as error:
        print(f'Ocorreu um erro ao modificar labels: {error}')

# Bloco para permitir testar este módulo diretamente
if __name__ == '__main__':
    print("Testando o cliente Gmail...")
    print("Buscando e-mails não lidos...")
    emails = fetch_unread_emails()
    
    if emails:
        print(f"\n--- {len(emails)} E-mail(s) Encontrado(s) ---")
        primeiro_email = emails[0]
        print(f"De: {primeiro_email['headers'].get('From')}")
        print(f"Assunto: {primeiro_email['headers'].get('Subject')}")
        print("\nCorpo (primeiros 200 caracteres):")
        print(primeiro_email['body'][:200] + "...")
        
        # ATENÇÃO: Descomente a linha abaixo para testar a marcação como lido
        # mark_email_as_processed(primeiro_email['id'])
        # print(f"E-mail {primeiro_email['id']} foi marcado como lido.")
    else:
        print("Nenhum e-mail não lido encontrado para testar.")