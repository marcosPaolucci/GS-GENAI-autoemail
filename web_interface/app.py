import streamlit as st
import sys
import os
import json
# Não precisamos mais do uuid

# --- Configuração de Path (igual a antes) ---
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

# --- Imports do Nosso Backend (igual a antes) ---
try:
    from langgraph_app.graph_builder import build_graph
    from langgraph_app.utils.gmail_client import fetch_unread_emails
except ImportError as e:
    st.error(f"Erro fatal de importação: {e}")
    st.stop()

# --- 1. Carregamento do Grafo (Cache) (igual a antes) ---
@st.cache_resource
def load_compiled_graph():
    print("Carregando e compilando o grafo...")
    try:
        app = build_graph()
        print("Grafo carregado e pronto.")
        return app
    except Exception as e:
        print(f"Erro ao construir o grafo: {e}")
        st.error(f"Falha ao carregar o grafo: {e}")
        return None

app = load_compiled_graph()
if app is None:
    st.stop()

# --- 2. Inicialização do Estado da Sessão (REVERTIDO) ---
if "email_queue" not in st.session_state:
    st.session_state.email_queue = []
if "current_email_id" not in st.session_state:
    st.session_state.current_email_id = None
if "current_graph_state" not in st.session_state:
    # Este é o único estado que precisamos
    st.session_state.current_graph_state = None
# Não precisamos mais do current_convo_id

# --- 3. Renderização da UI (Barra Lateral) (REVERTIDO) ---
st.sidebar.title("Smart Inbox")
st.sidebar.header("Ações")

if st.sidebar.button("Buscar Novos E-mails", type="primary", use_container_width=True):
    with st.spinner("Conectando ao Gmail e buscando e-mails..."):
        try:
            new_emails = fetch_unread_emails()
            st.session_state.email_queue = new_emails
            st.session_state.current_email_id = None
            st.session_state.current_graph_state = None # Limpa o estado
            if new_emails:
                st.sidebar.success(f"{len(new_emails)} e-mail(s) não lido(s) encontrado(s)!")
            else:
                st.sidebar.info("Nenhum e-mail não lido.")
        except Exception as e:
            st.sidebar.error(f"Erro ao buscar e-mails: {e}")

st.sidebar.header("Fila de Revisão")
if not st.session_state.email_queue:
    st.sidebar.caption("Nenhum e-mail na fila.")
else:
    for email in st.session_state.email_queue:
        subject = email.get("headers", {}).get("Subject", "Sem Assunto")
        from_email = email.get("headers", {}).get("From", "Desconhecido")
        email_id = email['id']
        
        if st.sidebar.button(
            f"**{subject}**\n*De: {from_email[:30]}...*", 
            use_container_width=True, 
            key=email_id
        ):
            st.session_state.current_email_id = email_id
            st.session_state.current_graph_state = None # Força re-análise

# --- 4. Renderização da UI (Área Principal) (igual a antes) ---
st.title("Revisão de Resposta")
if not st.session_state.current_email_id:
    st.info("Selecione um e-mail na fila da barra lateral para começar.")
    st.stop()
try:
    selected_email_data = next((e for e in st.session_state.email_queue if e['id'] == st.session_state.current_email_id), None)
    if selected_email_data is None:
        st.error("E-mail selecionado não está mais na fila."); st.stop()
except StopIteration:
    st.error("Erro ao procurar e-mail."); st.stop()

# --- 5. Execução do Grafo (Parte 1: Geração do Rascunho) (REVERTIDO) ---
if not st.session_state.current_graph_state:
    with st.spinner("A IA está analisando o e-mail (Agentes 1, 2, 3)..."):
        try:
            # Sem config, apenas o input
            graph_input = {"email_data": selected_email_data}
            
            # Roda o grafo até o ponto de pausa
            paused_state = app.invoke(graph_input)
            
            st.session_state.current_graph_state = paused_state
            st.success("Análise da IA concluída! Pronto para revisão.")
        except Exception as e:
            st.error(f"Erro ao processar o grafo: {e}"); st.stop()

current_state = st.session_state.current_graph_state

# --- 6. Exibição dos Dados (Análise e Rascunho) (igual a antes) ---
# (Esta seção é idêntica, não precisa mudar)
with st.expander("Ver E-mail Original", expanded=False):
    st.caption(f"De: {selected_email_data.get('headers', {}).get('From')}")
    st.caption(f"Assunto: {selected_email_data.get('headers', {}).get('Subject')}")
    st.divider(); st.text(selected_email_data.get('body', 'Corpo vazio.'))

st.subheader("Análise da IA"); col_triage, col_extract = st.columns(2)
with col_triage:
    triage = current_state.get('triage_result', {}); st.metric("Categoria", triage.get('categoria', 'N/A')); st.metric("Prioridade", triage.get('prioridade', 'N/A'))
with col_extract:
    st.caption("Dados Extraídos"); extracted_data = current_state.get('extracted_data', {}); st.json(extracted_data, expanded=False)

st.subheader("Rascunho da Resposta (Editável)")
draft_body = current_state.get('draft_response', {}).get('body', 'Erro: Nenhum rascunho gerado.')
edited_response = st.text_area("Edite a resposta abaixo:", value=draft_body, height=300, key=f"editor_{st.session_state.current_email_id}")
st.subheader("Aprovação"); col1, col2, _ = st.columns([1, 1, 3])

# --- 7. Execução do Grafo (Parte 2: Envio) (REVERTIDO) ---
with col1:
    if st.button("Aprovar e Enviar", type="primary"):
        with st.spinner("Continuando o fluxo... Enviando e-mail..."):
            try:
                # Prepara o estado para "continuar" (resume)
                # Passa o ESTADO ANTERIOR COMPLETO
                resumption_state = current_state.copy()
                # Adiciona a resposta final
                resumption_state["final_response"] = edited_response
                
                # CHAMA O GRAFO NOVAMENTE, passando o estado completo
                # O novo "route_start" vai direcionar para o "sender"
                final_state = app.invoke(resumption_state)
                
                # Lê o feedback do nó de envio
                send_status = final_state.get("send_status")
                log_message = final_state.get("log")

                if send_status == "Sucesso":
                    st.success(f"Envio Concluído! Log: {log_message}")
                    st.balloons()
                    
                    st.session_state.email_queue = [e for e in st.session_state.email_queue if e['id'] != st.session_state.current_email_id]
                    st.session_state.current_email_id = None
                    st.session_state.current_graph_state = None
                    st.rerun()
                else:
                    st.error(f"Falha no envio: {log_message}")

            except Exception as e:
                st.error(f"Erro Crítico ao tentar enviar: {e}")

with col2:
    if st.button("Descartar E-mail"):
        st.warning("E-mail descartado e movido da fila.")
        st.session_state.email_queue = [e for e in st.session_state.email_queue if e['id'] != st.session_state.current_email_id]
        st.session_state.current_email_id = None
        st.session_state.current_graph_state = None
        st.rerun()