# -*- coding: utf-8 -*- # Adicionado para garantir compatibilidade de caracteres

import streamlit as st
import pandas as pd
import os # Importar o módulo os para verificar a existência do arquivo

# --- Configurações Iniciais e Constantes ---

# Opção 1: Usar o nome do arquivo (caminho relativo).
#           NECESSÁRIO para deploy no Streamlit Cloud/GitHub.
#           O arquivo Excel DEVE estar na mesma pasta do script no repositório.
ARQUIVO_EXCEL = "Cruzeiro Mineiro.xlsx"

# Opção 2: Usar o caminho absoluto (NÃO USAR PARA DEPLOY)
# ARQUIVO_EXCEL = r"C:\Caminho\Para\Seu\Arquivo\Local\Cruzeiro Mineiro.xlsx" # MANTENHA COMENTADO PARA DEPLOY

TERMOS_IGNORADOS = ["Penalti", "Sem ass", "Falta", "Gol contra"] # Mantido em minúsculas para comparação case-insensitive

ANALISES_DISPONIVEIS = {
    "Números Gerais (por jogador)": "numeros_gerais",
    "Jogos com Participações (por jogador)": "jogos_participacoes",
    "Ranking Geral (por competição)": "ranking", # Ajustado nome para clareza
    "Análise por Ano (Ranking)": "analise_por_ano",
    "Listar Gols (por jogador)": "gols",
    "Listar Assistências (por jogador)": "assistencias"
}

# --- Funções Auxiliares ---

@st.cache_resource # Usar cache de recurso para o objeto ExcelFile
def carregar_dados_excel(arquivo):
    """Carrega o arquivo Excel como um recurso e retorna o objeto ExcelFile."""
    # No ambiente de deploy, st.info/success podem poluir menos
    # st.info(f"Tentando carregar o recurso do arquivo: {arquivo}")
    if not os.path.exists(arquivo):
        # No deploy, talvez seja melhor logar o erro internamente
        st.error(f"❌ Erro Fatal: Arquivo '{arquivo}' NÃO ENCONTRADO no repositório.")
        st.error("Certifique-se de que o arquivo Excel foi enviado para o GitHub na mesma pasta que o script Python.")
        return None # Retorna None se não encontrar
    try:
        # Abrir o arquivo Excel como um recurso
        xls = pd.ExcelFile(arquivo)
        # st.success(f"Recurso do arquivo '{os.path.basename(arquivo)}' carregado com sucesso!")
        return xls
    except FileNotFoundError: # Redundante se os.path.exists funcionar, mas seguro ter
        st.error(f"❌ Erro: Arquivo '{arquivo}' não encontrado (FileNotFoundError).")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar o recurso do arquivo Excel '{arquivo}': {e}")
        st.error("Verifique se o arquivo Excel não está corrompido ou se é um formato válido.")
        return None

def obter_competicoes(xls):
    """Retorna a lista de nomes das abas (competições) com 'Todas' no início."""
    if xls:
        try:
            # Garante que sheet_names seja uma lista antes de concatenar
            sheet_names = xls.sheet_names if isinstance(xls.sheet_names, list) else list(xls.sheet_names)
            return ["Todas"] + sheet_names
        except Exception as e:
            st.error(f"Erro ao ler os nomes das abas do Excel: {e}")
            return ["Todas"]
    return ["Todas"] # Retorna 'Todas' mesmo se o arquivo não carregar

def limpar_nome(nome):
    """Remove espaços extras e converte para minúsculas para comparação."""
    return str(nome).strip().lower()

def verificar_participacao(texto, jogador_limpo):
    """Verifica se o jogador participou (gol/assist) e conta as ocorrências, ignorando termos."""
    if not isinstance(texto, str) or not jogador_limpo:
        return 0
    count = 0
    participacoes = texto.split(";")
    for p in participacoes:
        p_limpo = limpar_nome(p)
        # Verifica se é o jogador E não contém nenhum termo ignorado (case-insensitive)
        # Atenção à lógica: 'in' verifica substrings. Melhor comparar igualdade.
        e_jogador = (p_limpo == jogador_limpo)
        tem_termo_ignorado = any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS)

        if e_jogador and not tem_termo_ignorado:
            count += 1
    return count

# --- Interface do Streamlit (Sidebar para Controles) ---
st.set_page_config(page_title="Análise Cruzeiro", page_icon="🦊", layout="wide") # Configura título e layout

st.sidebar.title("Análise de Dados - Cruzeiro 🦊")
# Tenta carregar a imagem localmente ou de URL (mais seguro para deploy)
try:
    # Se tiver a imagem no repo:
    # st.sidebar.image("logo_cruzeiro.png", width=100)
    # Ou usar uma URL pública:
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Cruzeiro_Esporte_Clube_%28logo%29.svg/1200px-Cruzeiro_Esporte_Clube_%28logo%29.svg.png", width=100)
except Exception:
    st.sidebar.warning("Não foi possível carregar o logo.")


# --- Carregamento dos Dados ---
# Chamada da função que usa @st.cache_resource
xls = carregar_dados_excel(ARQUIVO_EXCEL)

# --- VERIFICAÇÃO CRÍTICA ---
if xls is None:
    st.warning("⛔ A aplicação não pode continuar sem os dados do Excel.")
    st.info("Verifique as mensagens de erro acima. O arquivo 'Cruzeiro Mineiro.xlsx' precisa estar no repositório GitHub junto com este script.")
    st.stop() # Interrompe a execução do script se o arquivo não foi carregado

# --- Continua com o restante da interface e lógica ---
competicoes = obter_competicoes(xls)

tipo_analise_display = st.sidebar.selectbox(
    "Escolha o tipo de análise:",
    options=list(ANALISES_DISPONIVEIS.keys()),
    key="tipo_analise_select" # Adiciona chave para evitar problemas de estado
)
tipo_analise = ANALISES_DISPONIVEIS[tipo_analise_display] # Mapeia de volta para a chave interna

# --- Inputs Condicionais na Sidebar ---
ano_escolhido_input = None
competicao_escolhida = "Todas" # Default para 'Todas'
jogador_escolhido = None

# Input de Competição
if tipo_analise not in ["gols", "assistencias"]:
     competicao_escolhida = st.sidebar.selectbox(
        "Selecione a Competição:",
        options=competicoes,
        index=0, # Começa com 'Todas' selecionado
        key="competicao_select"
    )

# Input de Ano
if tipo_analise in ["analise_por_ano", "gols", "assistencias"]:
    ano_escolhido_input = st.sidebar.text_input("Digite o Ano (ex: 2023, deixe em branco para todos):", key="ano_input")

# Input de Jogador
if tipo_analise not in ["ranking", "analise_por_ano"]:
    jogador_escolhido = st.sidebar.text_input("Digite o nome exato do Jogador:", key="jogador_input").strip()

# --- Validação e Processamento do Ano ---
ano_filtrar = None
if ano_escolhido_input:
    try:
        ano_filtrar = int(ano_escolhido_input)
    except ValueError:
        st.sidebar.warning(f"'{ano_escolhido_input}' não é um ano válido. Mostrando todos os anos.")

# --- Lógica Principal e Exibição dos Resultados ---
st.header(f"📊 Resultados: {tipo_analise_display}")

# Determina as abas a serem analisadas
abas_para_analisar = []
# Verifica se xls não é None antes de acessar sheet_names
if xls:
    if competicao_escolhida and competicao_escolhida != "Todas":
        if competicao_escolhida in xls.sheet_names:
            abas_para_analisar = [competicao_escolhida]
        else:
            # Isso não deve acontecer se 'competicoes' foi gerado corretamente
            st.warning(f"Competição '{competicao_escolhida}' selecionada mas não encontrada.")
    elif competicao_escolhida == "Todas" or tipo_analise in ["gols", "assistencias"]:
        abas_para_analisar = xls.sheet_names
    else: # Fallback caso algo estranho ocorra
         abas_para_analisar = xls.sheet_names
else:
    # xls é None, já tratado antes com st.stop(), mas por segurança:
    st.error("Erro interno: Objeto Excel não está carregado.")
    st.stop()


# --- Execução da Análise Escolhida ---

# Adiciona uma verificação se há abas para analisar
if not abas_para_analisar and competicao_escolhida != "Todas":
     st.warning(f"Nenhuma aba encontrada para a competição '{competicao_escolhida}'.")
     # st.stop() # Decide se quer parar ou continuar (pode não exibir nada)
elif not abas_para_analisar and competicao_escolhida == "Todas":
     st.warning("Nenhuma aba/competição encontrada no arquivo Excel.")
     st.stop()


# 1. Números Gerais (por jogador)
if tipo_analise == "numeros_gerais":
    if not jogador_escolhido:
        st.info("👈 Por favor, digite o nome de um jogador na barra lateral.")
    else:
        st.subheader(f"Números Gerais de {jogador_escolhido.title()}")
        # ... (resto da lógica como estava antes)
        resultados_gerais = []
        jogador_limpo = limpar_nome(jogador_escolhido)
        total_geral_gols = 0
        total_geral_assists = 0

        with st.spinner(f"Analisando dados de {jogador_escolhido.title()}..."): # Feedback visual
            for aba in abas_para_analisar:
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns] # Limpa nomes das colunas

                    cols_essenciais = ['gols', 'assistências', 'campeonato', 'ano']
                    colunas_faltando = [c for c in cols_essenciais if c not in df.columns]
                    if colunas_faltando:
                        st.warning(f"⚠️ Aba '{aba}': Faltando colunas: {', '.join(colunas_faltando)}. Pulando.")
                        continue

                    df['gols_jogador'] = df['gols'].apply(lambda x: verificar_participacao(x, jogador_limpo))
                    df['assists_jogador'] = df['assistências'].apply(lambda x: verificar_participacao(x, jogador_limpo))

                    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
                    df.dropna(subset=['ano'], inplace=True) # Remove anos inválidos
                    df['ano'] = df['ano'].astype(int)

                    resumo_aba = df.groupby(['campeonato', 'ano'])[['gols_jogador', 'assists_jogador']].sum().reset_index()
                    resumo_aba = resumo_aba[(resumo_aba['gols_jogador'] > 0) | (resumo_aba['assists_jogador'] > 0)]

                    if not resumo_aba.empty:
                        total_camp_gols = resumo_aba['gols_jogador'].sum()
                        total_camp_assists = resumo_aba['assists_jogador'].sum()
                        nome_campeonato_atual = "" # Para armazenar o nome do último camp processado
                        for _, row in resumo_aba.iterrows():
                            nome_campeonato_atual = row['campeonato']
                            resultados_gerais.append({
                                "Competição": nome_campeonato_atual,
                                "Ano": int(row['ano']),
                                "Gols": int(row['gols_jogador']),
                                "Assistências": int(row['assists_jogador'])
                            })
                        # Adiciona total do campeonato (usa nome_campeonato_atual)
                        if nome_campeonato_atual: # Garante que houve pelo menos uma linha
                            resultados_gerais.append({
                                "Competição": nome_campeonato_atual,
                                "Ano": "Total",
                                "Gols": int(total_camp_gols),
                                "Assistências": int(total_camp_assists)
                            })
                        total_geral_gols += total_camp_gols
                        total_geral_assists += total_camp_assists

                except Exception as e:
                    st.error(f"⚠️ Erro ao processar a aba '{aba}' para Números Gerais: {e}")

        if resultados_gerais:
            df_resultados = pd.DataFrame(resultados_gerais)
            if total_geral_gols > 0 or total_geral_assists > 0:
                 df_total_geral = pd.DataFrame([{"Competição": "Total Geral", "Ano": "", "Gols": int(total_geral_gols), "Assistências": int(total_geral_assists)}])
                 # Usar pd.concat para adicionar a linha de total geral
                 df_resultados = pd.concat([df_resultados, df_total_geral], ignore_index=True)


            st.dataframe(
                df_resultados.style.format({
                    "Ano": lambda x: "" if pd.isna(x) or x == "Total" or x == "" else f"{x:.0f}", # Formata ano
                    "Gols": "{:.0f}",
                    "Assistências": "{:.0f}"
                 }).apply(lambda x: ['background-color: #eee; font-weight: bold;' if x.name == len(df_resultados)-1 else '' for i in x], axis=1 # Destaca Total Geral
                 ).apply(lambda x: ['font-weight: bold;' if x.Ano == "Total" else '' for i in x], axis=1), # Negrito nos Totais de Competição
                 use_container_width=True,
                 hide_index=True # Esconde o índice numérico padrão
            )
        elif jogador_escolhido: # Só mostra essa mensagem se um jogador foi inserido
            st.info(f"Nenhuma participação em gols ou assistências encontrada para '{jogador_escolhido.title()}' nos filtros selecionados.")

# 2. Jogos com Participações (por jogador)
elif tipo_analise == "jogos_participacoes":
    if not jogador_escolhido:
        st.info("👈 Por favor, digite o nome de um jogador na barra lateral.")
    else:
        st.subheader(f"Jogos com Participação em Gols/Assistências de {jogador_escolhido.title()}")
        # ... (resto da lógica como estava antes)
        jogos_encontrados = []
        jogador_limpo = limpar_nome(jogador_escolhido)

        with st.spinner(f"Buscando jogos de {jogador_escolhido.title()}..."):
            for aba in abas_para_analisar:
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns]

                    cols_essenciais = ['gols', 'assistências', 'partida', 'campeonato', 'ano']
                    colunas_faltando = [c for c in cols_essenciais if c not in df.columns]
                    if colunas_faltando:
                        st.warning(f"⚠️ Aba '{aba}': Faltando colunas: {', '.join(colunas_faltando)}. Pulando.")
                        continue

                    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')

                    df_potencial = df[
                        df['gols'].astype(str).str.contains(jogador_escolhido, case=False, na=False, regex=False) |
                        df['assistências'].astype(str).str.contains(jogador_escolhido, case=False, na=False, regex=False)
                    ].copy()

                    if not df_potencial.empty:
                        df_potencial['num_gols'] = df_potencial['gols'].apply(lambda x: verificar_participacao(x, jogador_limpo))
                        df_potencial['num_assists'] = df_potencial['assistências'].apply(lambda x: verificar_participacao(x, jogador_limpo))
                        df_filtrado = df_potencial[(df_potencial['num_gols'] > 0) | (df_potencial['num_assists'] > 0)]

                        for _, row in df_filtrado.iterrows():
                            try:
                                ano_str = f"{int(row['ano'])}" if pd.notna(row['ano']) else "N/A"
                            except (ValueError, TypeError):
                                ano_str = row.get('ano', 'N/A')

                            campeonato = row.get('campeonato', 'N/A')
                            partida = row.get('partida', 'N/A')
                            num_gols = row['num_gols']
                            num_assists = row['num_assists']

                            for _ in range(num_gols):
                                jogos_encontrados.append(f"⚽ **Gol:** {ano_str} - {campeonato} - {partida}")
                            for _ in range(num_assists):
                                jogos_encontrados.append(f"👟 **Assistência:** {ano_str} - {campeonato} - {partida}")

                except Exception as e:
                    st.error(f"⚠️ Erro ao processar a aba '{aba}' para Jogos com Participações: {e}")

        if jogos_encontrados:
            # Ordena a lista antes de exibir e numera
            jogos_encontrados.sort()
            jogos_formatados = [f"{i+1}. {item}" for i, item in enumerate(jogos_encontrados)]
            st.markdown("\n".join(jogos_formatados))
        elif jogador_escolhido:
            st.info(f"Nenhuma participação encontrada para '{jogador_escolhido.title()}' nos filtros selecionados.")

# 3. Ranking Geral (por competição)
elif tipo_analise == "ranking":
    comp_selecionada = competicao_escolhida if competicao_escolhida else "Todas" # Deveria ser 'Todas' ou uma competição
    st.subheader(f"Ranking de Participações - Competição: {comp_selecionada}")
    # ... (resto da lógica como estava antes)
    player_stats = {}

    with st.spinner(f"Calculando ranking para {comp_selecionada}..."):
        for aba in abas_para_analisar: # abas_para_analisar foi definido baseado na seleção
            try:
                df = pd.read_excel(xls, sheet_name=aba)
                df.columns = [limpar_nome(col) for col in df.columns]

                if 'gols' not in df.columns and 'assistências' not in df.columns:
                    st.warning(f"⚠️ Aba '{aba}': Faltando 'gols' e 'assistências'. Pulando para ranking.")
                    continue

                for index, row in df.iterrows():
                    if 'gols' in df.columns and isinstance(row['gols'], str):
                        gols_list = [p.strip() for p in row['gols'].split(";") if p.strip()]
                        for p in gols_list:
                            p_nome_original = p
                            p_limpo = limpar_nome(p)
                            if p_limpo and p_limpo != 'nan' and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
                                player_stats[p_nome_original] = player_stats.get(p_nome_original, {'Gols': 0, 'Assistências': 0})
                                player_stats[p_nome_original]['Gols'] += 1
                    if 'assistências' in df.columns and isinstance(row['assistências'], str):
                        assists_list = [p.strip() for p in row['assistências'].split(";") if p.strip()]
                        for p in assists_list:
                            p_nome_original = p
                            p_limpo = limpar_nome(p)
                            if p_limpo and p_limpo != 'nan' and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
                                player_stats[p_nome_original] = player_stats.get(p_nome_original, {'Gols': 0, 'Assistências': 0})
                                player_stats[p_nome_original]['Assistências'] += 1

            except Exception as e:
                st.error(f"⚠️ Erro ao processar a aba '{aba}' para Ranking: {e}")

    if player_stats:
        ranking_lista = []
        for player, stats in player_stats.items():
            total = stats['Gols'] + stats['Assistências']
            if total > 0:
                ranking_lista.append({
                    "Jogador": player,
                    "Gols": stats['Gols'],
                    "Assistências": stats['Assistências'],
                    "Total Participações": total
                })

        if ranking_lista:
            ranking_lista = sorted(ranking_lista, key=lambda x: (x['Total Participações'], x['Gols'], x['Assistências']), reverse=True)
            df_ranking = pd.DataFrame(ranking_lista)
            # Adiciona coluna de Rank
            df_ranking.insert(0, 'Rank', range(1, len(df_ranking) + 1))
            st.dataframe(df_ranking, use_container_width=True, hide_index=True)
        else:
             st.info(f"Nenhum jogador com participação válida encontrado para a competição '{comp_selecionada}'.")
    else:
        st.info(f"Nenhum dado de participação encontrado para a competição '{comp_selecionada}'.")

# 4. Análise por Ano (Ranking)
elif tipo_analise == "analise_por_ano":
    ano_str = str(ano_filtrar) if ano_filtrar else "Todos os Anos"
    comp_str = competicao_escolhida if competicao_escolhida and competicao_escolhida != "Todas" else "Todas Competições"
    st.subheader(f"Ranking de Participações - Ano: {ano_str} / Competição: {comp_str}")
    # ... (resto da lógica como estava antes)
    player_stats_ano = {}

    with st.spinner(f"Calculando ranking para Ano: {ano_str} / Competição: {comp_str}..."):
        for aba in abas_para_analisar: # abas_para_analisar já foi filtrada se comp != 'Todas'
            try:
                df = pd.read_excel(xls, sheet_name=aba)
                df.columns = [limpar_nome(col) for col in df.columns]

                if 'ano' not in df.columns:
                    if ano_filtrar:
                        st.warning(f"⚠️ Aba '{aba}': Faltando coluna 'ano'. Pulando para ranking anual.")
                        continue
                    else:
                         df['ano'] = pd.NA
                else:
                    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')

                if ano_filtrar:
                    df_filtrada = df[df['ano'] == ano_filtrar].copy()
                else:
                    df_filtrada = df.copy()

                if df_filtrada.empty:
                    continue

                if 'gols' not in df_filtrada.columns and 'assistências' not in df_filtrada.columns:
                    st.warning(f"⚠️ Aba '{aba}' (filtrada): Faltando 'gols' e 'assistências'. Pulando.")
                    continue

                for index, row in df_filtrada.iterrows():
                    if 'gols' in df_filtrada.columns and isinstance(row['gols'], str):
                        gols_list = [p.strip() for p in row['gols'].split(";") if p.strip()]
                        for p in gols_list:
                            p_nome_original = p
                            p_limpo = limpar_nome(p)
                            if p_limpo and p_limpo != 'nan' and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
                                player_stats_ano[p_nome_original] = player_stats_ano.get(p_nome_original, {'Gols': 0, 'Assistências': 0})
                                player_stats_ano[p_nome_original]['Gols'] += 1
                    if 'assistências' in df_filtrada.columns and isinstance(row['assistências'], str):
                        assists_list = [p.strip() for p in row['assistências'].split(";") if p.strip()]
                        for p in assists_list:
                            p_nome_original = p
                            p_limpo = limpar_nome(p)
                            if p_limpo and p_limpo != 'nan' and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
                                player_stats_ano[p_nome_original] = player_stats_ano.get(p_nome_original, {'Gols': 0, 'Assistências': 0})
                                player_stats_ano[p_nome_original]['Assistências'] += 1

            except Exception as e:
                st.error(f"⚠️ Erro ao processar a aba '{aba}' para Análise por Ano: {e}")

    if player_stats_ano:
        ranking_ano_lista = []
        for player, stats in player_stats_ano.items():
            total = stats['Gols'] + stats['Assistências']
            if total > 0:
                ranking_ano_lista.append({
                    "Jogador": player,
                    "Gols": stats['Gols'],
                    "Assistências": stats['Assistências'],
                    "Total Participações": total
                })

        if ranking_ano_lista:
            ranking_ano_lista = sorted(ranking_ano_lista, key=lambda x: (x['Total Participações'], x['Gols'], x['Assistências']), reverse=True)
            df_ranking_ano = pd.DataFrame(ranking_ano_lista)
            df_ranking_ano.insert(0, 'Rank', range(1, len(df_ranking_ano) + 1))
            st.dataframe(df_ranking_ano, use_container_width=True, hide_index=True)
        else:
             st.info(f"Nenhum jogador com participação válida encontrado para Ano: {ano_str} / Competição: {comp_str}.")
    else:
        st.info(f"Nenhum dado de participação encontrado para Ano: {ano_str} / Competição: {comp_str}.")


# 5 & 6. Listar Gols / Assistências (por jogador)
elif tipo_analise in ["gols", "assistencias"]:
    if not jogador_escolhido:
        st.info("👈 Por favor, digite o nome de um jogador na barra lateral.")
    else:
        tipo_evento = "Gols" if tipo_analise == "gols" else "Assistências"
        coluna_busca = limpar_nome(tipo_evento) # 'gols' ou 'assistências'
        emoji = "⚽" if tipo_analise == "gols" else "👟"
        ano_str = str(ano_filtrar) if ano_filtrar else "Todos os Anos"

        st.subheader(f"{emoji} Lista de {tipo_evento} de {jogador_escolhido.title()} ({ano_str})")
        # ... (resto da lógica como estava antes)
        resultados_lista = []
        jogador_limpo = limpar_nome(jogador_escolhido)

        # Itera por TODAS as abas do arquivo Excel carregado
        todas_as_abas = xls.sheet_names if xls else []

        with st.spinner(f"Buscando {tipo_evento.lower()} de {jogador_escolhido.title()} em todas as competições ({ano_str})..."):
            for aba in todas_as_abas:
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns]

                    cols_essenciais = [coluna_busca, 'partida', 'campeonato', 'ano']
                    colunas_faltando = [c for c in cols_essenciais if c not in df.columns]
                    if colunas_faltando:
                        st.warning(f"⚠️ Aba '{aba}': Faltando colunas: {', '.join(colunas_faltando)}. Pulando para lista de {tipo_evento}.")
                        continue

                    if 'ano' not in df.columns:
                        if ano_filtrar:
                            continue
                        else:
                             df['ano'] = pd.NA
                    else:
                        df['ano'] = pd.to_numeric(df['ano'], errors='coerce')

                    df_filtrada_ano = df.copy()
                    if ano_filtrar:
                        # Compara com NaN de forma segura
                        df_filtrada_ano = df_filtrada_ano[df_filtrada_ano['ano'] == ano_filtrar]

                    if df_filtrada_ano.empty:
                        continue

                    for index, row in df_filtrada_ano.iterrows():
                        participacoes_texto = row.get(coluna_busca, "")
                        num_participacoes = verificar_participacao(participacoes_texto, jogador_limpo)

                        if num_participacoes > 0:
                            try:
                                ano_valor = int(row['ano']) if pd.notna(row['ano']) else "N/A"
                            except (ValueError, TypeError):
                                ano_valor = row.get('ano', 'N/A')

                            campeonato = row.get('campeonato', 'N/A')
                            partida = row.get('partida', 'N/A')
                            for _ in range(num_participacoes):
                                resultados_lista.append(f"{emoji} {ano_valor} - {campeonato} - {partida}")

                except Exception as e:
                    st.error(f"⚠️ Erro ao processar a aba '{aba}' para listar {tipo_evento}: {e}")

        if resultados_lista:
            resultados_lista.sort()
            resultados_formatados = [f"{i+1}. {item}" for i, item in enumerate(resultados_lista)]
            st.markdown("\n".join(resultados_formatados))
        elif jogador_escolhido:
            st.info(f"Nenhum(a) {tipo_evento.lower()} encontrado(a) para '{jogador_escolhido.title()}' no ano {ano_str}.")

# --- Rodapé ---
st.sidebar.divider()
st.sidebar.caption("Desenvolvido por Riuler") # Opcional: Adicione seus créditos
st.caption("Aplicação de análise de dados do Cruzeiro")
