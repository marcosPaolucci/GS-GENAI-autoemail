import json

try:
    from ..utils.gmail_client import send_reply, mark_email_as_processed
except ImportError:
    import sys
    import os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
    from langgraph_app.utils.gmail_client import send_reply, mark_email_as_processed

def run_email_sender_node(state: dict):
    """
    Executa o nó de envio de e-mail com feedback de API.
    """
    print("--- 5. Executando Nó de Envio de E-mail ---")
    
    final_response = state.get("final_response")
    email_data = state.get("email_data", {})
    
    if not final_response:
        print("ERRO: Nenhuma resposta final encontrada para enviar.")
        return {"send_status": "Falha - Resposta vazia", "log": "Resposta final estava vazia."}

    try:
        original_headers = email_data.get("headers", {})
        to_email = original_headers.get("From")
        subject = original_headers.get("Subject")
        thread_id = email_data.get("thread_id")
        
        if not to_email or not thread_id:
            raise ValueError("Destinatário ('From' original) ou ID da Thread não encontrados.")

        if not subject.lower().startswith("re:"):
            subject = f"Re: {subject}"
            
        # 1. Envia a resposta
        print(f"Enviando resposta para: {to_email} (Thread: {thread_id})")
        
        # Chama a função atualizada
        sent_confirmation = send_reply(
            to_email=to_email,
            subject=subject,
            message_text=final_response,
            thread_id=thread_id
        )
        
        # Verifica a confirmação da API
        if sent_confirmation and sent_confirmation.get('id'):
            sent_message_id = sent_confirmation.get('id')
            print(f"Confirmação de API recebida. ID da Mensagem: {sent_message_id}")
            
            # 2. Marca o e-mail original como processado
            original_message_id = email_data.get("id")
            if original_message_id:
                mark_email_as_processed(original_message_id)
                
            return {
                "send_status": "Sucesso",
                "log": f"Enviado com sucesso para {to_email}. ID da Mensagem: {sent_message_id}"
            }
        else:
            return {
                "send_status": "Falha",
                "log": "Função send_reply não retornou confirmação."
            }

    except Exception as e:
        print(f"Erro no Nó de Envio de E-mail: {e}")
        return {
            "send_status": "Falha",
            "log": f"Erro da API: {str(e)}"
        }