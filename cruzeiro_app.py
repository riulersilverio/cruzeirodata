import streamlit as st
import pandas as pd
import os # Importar o módulo os para verificar a existência do arquivo

# --- Configurações Iniciais e Constantes ---

# Escolha UMA das opções abaixo para ARQUIVO_EXCEL:
# Opção 1: Se o arquivo estiver na MESMA pasta do script .py (DESCOMENTE A LINHA ABAIXO)
# ARQUIVO_EXCEL = "Cruzeiro Mineiro.xlsx"
# Opção 2: Usar o caminho absoluto fornecido (Use 'r' antes das aspas no Windows)
ARQUIVO_EXCEL = r"C:\Users\riule\OneDrive\Documentos\Cruzeiro Mineiro.xlsx"

TERMOS_IGNORADOS = ["Penalti", "Sem ass", "Falta", "Gol contra"] # Mantido em minúsculas para comparação case-insensitive

ANALISES_DISPONIVEIS = {
    "Números Gerais (por jogador)": "numeros_gerais",
    "Jogos com Participações (por jogador)": "jogos_participacoes",
    "Ranking Geral (por competição/ano)": "ranking",
    "Análise por Ano (Ranking)": "analise_por_ano",
    "Listar Gols (por jogador)": "gols",
    "Listar Assistências (por jogador)": "assistencias"
}

# --- Funções Auxiliares ---

# Alterado de @st.cache_data para @st.cache_resource para lidar com o objeto ExcelFile
@st.cache_resource # <- CORREÇÃO APLICADA AQUI
def carregar_dados_excel(arquivo):
    """Carrega o arquivo Excel como um recurso e retorna o objeto ExcelFile."""
    st.info(f"Tentando carregar o recurso do arquivo: {arquivo}") # Mensagem de debug
    if not os.path.exists(arquivo):
        st.error(f"❌ Erro Fatal: Arquivo NÃO ENCONTRADO em: {arquivo}")
        st.error("Verifique se o caminho está correto ou se o arquivo está na mesma pasta do script .py (se estiver usando o nome relativo).")
        return None # Retorna None se não encontrar
    try:
        # Abrir o arquivo Excel como um recurso
        xls = pd.ExcelFile(arquivo)
        st.success(f"Recurso do arquivo '{os.path.basename(arquivo)}' carregado com sucesso!")
        return xls
    except FileNotFoundError:
        # Esta exceção é mais genérica, o os.path.exists é mais direto
        st.error(f"❌ Erro: Arquivo '{arquivo}' não encontrado (FileNotFoundError).")
        return None
    except Exception as e:
        st.error(f"❌ Erro ao carregar o recurso do arquivo Excel '{arquivo}': {e}")
        st.error("Verifique se o arquivo não está corrompido ou protegido por senha.")
        return None

def obter_competicoes(xls):
    """Retorna a lista de nomes das abas (competições) com 'Todas' no início."""
    if xls:
        # Garante que sheet_names seja uma lista antes de concatenar
        sheet_names = xls.sheet_names if isinstance(xls.sheet_names, list) else list(xls.sheet_names)
        return ["Todas"] + sheet_names
    return ["Todas"] # Retorna 'Todas' mesmo se o arquivo não carregar para evitar erros

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
        if p_limpo == jogador_limpo and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
            count += 1
    return count

# --- Interface do Streamlit (Sidebar para Controles) ---
st.sidebar.title("Análise de Dados - Cruzeiro 🦊")
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/9/90/Cruzeiro_Esporte_Clube_%28logo%29.svg/1200px-Cruzeiro_Esporte_Clube_%28logo%29.svg.png", width=100) # Adicione um logo se quiser

# --- Carregamento dos Dados ---
# Chamada da função atualizada que usa @st.cache_resource
xls = carregar_dados_excel(ARQUIVO_EXCEL)

# --- VERIFICAÇÃO CRÍTICA ---
if xls is None:
    st.warning("A aplicação não pode continuar sem os dados do Excel.")
    st.info("Verifique as mensagens de erro acima e o caminho do arquivo.")
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
competicao_escolhida = None
jogador_escolhido = None

# Input de Competição
# Garante que o widget seja recriado se as opções mudarem (embora improvável aqui)
if tipo_analise not in ["gols", "assistencias"]:
     competicao_escolhida = st.sidebar.selectbox(
        "Selecione a Competição:",
        options=competicoes,
        key="competicao_select" # Adiciona chave
    )

# Input de Ano
if tipo_analise in ["analise_por_ano", "gols", "assistencias"]:
    ano_escolhido_input = st.sidebar.text_input("Digite o Ano (deixe em branco para todos):", key="ano_input")

# Input de Jogador
if tipo_analise not in ["ranking", "analise_por_ano"]:
    # Usar st.session_state para persistir o valor entre reruns se necessário, mas text_input geralmente lida bem
    jogador_escolhido = st.sidebar.text_input("Digite o nome do Jogador:", key="jogador_input").strip()

# --- Validação e Processamento do Ano ---
ano_filtrar = None
if ano_escolhido_input:
    try:
        ano_filtrar = int(ano_escolhido_input)
    except ValueError:
        st.sidebar.warning("Ano inválido. Mostrando todos os anos.")

# --- Lógica Principal e Exibição dos Resultados ---
st.header(f"📊 Resultados: {tipo_analise_display}")

# Determina as abas a serem analisadas
abas_para_analisar = []
if competicao_escolhida and competicao_escolhida != "Todas":
    # Verifica se a competição escolhida existe nas abas carregadas
    if xls and competicao_escolhida in xls.sheet_names:
        abas_para_analisar = [competicao_escolhida]
    else:
        st.warning(f"Competição '{competicao_escolhida}' não encontrada nas abas do Excel.")
        # Pode ser útil parar aqui ou analisar todas como fallback
        # abas_para_analisar = [] # Ou xls.sheet_names se quiser analisar tudo
elif competicao_escolhida == "Todas" or tipo_analise in ["gols", "assistencias"]: # Gols/Assist busca em todas por padrão
    if xls:
        abas_para_analisar = xls.sheet_names
    else:
         abas_para_analisar = [] # Caso xls seja None (embora já verificado)
else: # Caso padrão ou se algo der errado com a seleção
     if xls:
         abas_para_analisar = xls.sheet_names # Default para todas se não for especificado
     else:
          abas_para_analisar = []

# --- Execução da Análise Escolhida ---

# 1. Números Gerais (por jogador)
if tipo_analise == "numeros_gerais":
    if not jogador_escolhido:
        st.warning("Por favor, digite o nome de um jogador na barra lateral.")
    elif not abas_para_analisar:
         st.warning("Nenhuma competição selecionada ou encontrada para análise.")
    else:
        st.subheader(f"Números Gerais de {jogador_escolhido.title()}")
        resultados_gerais = []
        jogador_limpo = limpar_nome(jogador_escolhido)
        total_geral_gols = 0
        total_geral_assists = 0

        with st.spinner(f"Analisando dados de {jogador_escolhido.title()}..."): # Feedback visual
            for aba in abas_para_analisar:
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns] # Limpa nomes das colunas

                    # Verifica colunas essenciais (case-insensitive)
                    cols_essenciais = ['gols', 'assistências', 'campeonato', 'ano']
                    colunas_faltando = [c for c in cols_essenciais if c not in df.columns]
                    if colunas_faltando:
                        st.warning(f"⚠️ Aba '{aba}': Faltando colunas: {', '.join(colunas_faltando)}. Pulando.")
                        continue

                    # Aplica a função de verificação
                    df['gols_jogador'] = df['gols'].apply(lambda x: verificar_participacao(x, jogador_limpo))
                    df['assists_jogador'] = df['assistências'].apply(lambda x: verificar_participacao(x, jogador_limpo))

                    # Garante que 'ano' seja numérico para agrupamento correto
                    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
                    df.dropna(subset=['ano'], inplace=True) # Remove anos inválidos
                    df['ano'] = df['ano'].astype(int)

                    # Agrupa por Campeonato e Ano
                    resumo_aba = df.groupby(['campeonato', 'ano'])[['gols_jogador', 'assists_jogador']].sum().reset_index()
                    resumo_aba = resumo_aba[(resumo_aba['gols_jogador'] > 0) | (resumo_aba['assists_jogador'] > 0)] # Filtra anos sem participação

                    if not resumo_aba.empty:
                        total_camp_gols = resumo_aba['gols_jogador'].sum()
                        total_camp_assists = resumo_aba['assists_jogador'].sum()
                        for _, row in resumo_aba.iterrows():
                            resultados_gerais.append({
                                "Competição": row['campeonato'],
                                "Ano": int(row['ano']), # Garante que ano seja int
                                "Gols": int(row['gols_jogador']),
                                "Assistências": int(row['assists_jogador'])
                            })
                        # Adiciona total do campeonato
                        resultados_gerais.append({
                            "Competição": row['campeonato'], # Pega o último nome de camp.
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
            # Adiciona Total Geral se houver dados
            if total_geral_gols > 0 or total_geral_assists > 0:
                 df_total_geral = pd.DataFrame([{"Competição": "Total Geral", "Ano": "", "Gols": int(total_geral_gols), "Assistências": int(total_geral_assists)}])
                 df_resultados = pd.concat([df_resultados, df_total_geral], ignore_index=True)


            # Formatação para exibição mais limpa
            st.dataframe(
                df_resultados.style.format({
                    "Ano": lambda x: "" if pd.isna(x) or x == "Total" else f"{x:.0f}", # Formata ano como inteiro ou string vazia
                    "Gols": "{:.0f}",
                    "Assistências": "{:.0f}"
                 }).apply(lambda x: ['background-color: #f0f0f0' if x.name == len(df_resultados)-1 else '' for i in x], axis=1 # Destaca Total Geral
                 ).apply(lambda x: ['font-weight: bold' if x.Ano == "Total" else '' for i in x], axis=1), # Negrito nos Totais de Competição
                 use_container_width=True
            )
        elif jogador_escolhido: # Só mostra essa mensagem se um jogador foi inserido
            st.info(f"Nenhuma participação em gols ou assistências encontrada para {jogador_escolhido.title()} nos filtros selecionados.")

# 2. Jogos com Participações (por jogador)
elif tipo_analise == "jogos_participacoes":
    if not jogador_escolhido:
        st.warning("Por favor, digite o nome de um jogador na barra lateral.")
    elif not abas_para_analisar:
         st.warning("Nenhuma competição selecionada ou encontrada para análise.")
    else:
        st.subheader(f"Jogos com Participação em Gols/Assistências de {jogador_escolhido.title()}")
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

                    # Garante que 'ano' seja numérico
                    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
                    # Não vamos remover linhas aqui, podemos querer jogos mesmo sem ano válido
                    # df.dropna(subset=['ano'], inplace=True)
                    # df['ano'] = df['ano'].astype(int)


                    # Filtra linhas que *potencialmente* contêm o jogador (otimização)
                    # Usar regex=False para busca literal mais rápida
                    df_potencial = df[
                        df['gols'].astype(str).str.contains(jogador_escolhido, case=False, na=False, regex=False) |
                        df['assistências'].astype(str).str.contains(jogador_escolhido, case=False, na=False, regex=False)
                    ].copy() # .copy() para evitar SettingWithCopyWarning

                    if not df_potencial.empty:
                        # Calcula participações específicas
                        df_potencial['num_gols'] = df_potencial['gols'].apply(lambda x: verificar_participacao(x, jogador_limpo))
                        df_potencial['num_assists'] = df_potencial['assistências'].apply(lambda x: verificar_participacao(x, jogador_limpo))

                        # Filtra apenas jogos onde houve participação real
                        df_filtrado = df_potencial[(df_potencial['num_gols'] > 0) | (df_potencial['num_assists'] > 0)]

                        for _, row in df_filtrado.iterrows():
                            # Tenta formatar o ano como inteiro, mas mantém N/A se falhar
                            try:
                                ano_str = f"{int(row['ano'])}" if pd.notna(row['ano']) else "N/A"
                            except (ValueError, TypeError):
                                ano_str = row.get('ano', 'N/A')

                            campeonato = row.get('campeonato', 'N/A')
                            partida = row.get('partida', 'N/A')
                            num_gols = row['num_gols']
                            num_assists = row['num_assists']

                            # Adiciona à lista para cada gol/assistência
                            for _ in range(num_gols):
                                jogos_encontrados.append(f"⚽ **Gol:** {ano_str} - {campeonato} - {partida}")
                            for _ in range(num_assists):
                                jogos_encontrados.append(f"👟 **Assistência:** {ano_str} - {campeonato} - {partida}")

                except Exception as e:
                    st.error(f"⚠️ Erro ao processar a aba '{aba}' para Jogos com Participações: {e}")

        if jogos_encontrados:
            st.markdown("\n".join(sorted(jogos_encontrados))) # Exibe como lista markdown ordenada
        elif jogador_escolhido:
            st.info(f"Nenhuma participação encontrada para {jogador_escolhido.title()} nos filtros selecionados.")

# 3. Ranking Geral (por competição/ano - neste caso, só competição)
elif tipo_analise == "ranking":
    if not abas_para_analisar:
         st.warning("Nenhuma competição selecionada ou encontrada para análise.")
    else:
        comp_selecionada = competicao_escolhida if competicao_escolhida else "Todas"
        st.subheader(f"Ranking de Participações - Competição: {comp_selecionada}")
        player_stats = {}

        with st.spinner(f"Calculando ranking para {comp_selecionada}..."):
            for aba in abas_para_analisar:
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns]

                    # Verifica se pelo menos uma das colunas existe
                    if 'gols' not in df.columns and 'assistências' not in df.columns:
                        st.warning(f"⚠️ Aba '{aba}': Faltando colunas 'gols' e 'assistências'. Pulando para ranking.")
                        continue

                    for index, row in df.iterrows():
                        # Processa Gols
                        if 'gols' in df.columns and isinstance(row['gols'], str):
                            gols_list = [p.strip() for p in row['gols'].split(";") if p.strip()]
                            for p in gols_list:
                                p_nome_original = p # Guarda o nome original com caixa
                                p_limpo = limpar_nome(p)
                                if p_limpo and p_limpo != 'nan' and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
                                    player_stats[p_nome_original] = player_stats.get(p_nome_original, {'Gols': 0, 'Assistências': 0})
                                    player_stats[p_nome_original]['Gols'] += 1
                        # Processa Assistências
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
                if total > 0: # Adiciona apenas jogadores com alguma participação
                    ranking_lista.append({
                        "Jogador": player, # Usa o nome original
                        "Gols": stats['Gols'],
                        "Assistências": stats['Assistências'],
                        "Total Participações": total
                    })

            if ranking_lista:
                # Ordena
                ranking_lista = sorted(ranking_lista, key=lambda x: (x['Total Participações'], x['Gols'], x['Assistências']), reverse=True)

                df_ranking = pd.DataFrame(ranking_lista)
                df_ranking.index = range(1, len(df_ranking) + 1) # Começa índice em 1 (ranking)
                st.dataframe(df_ranking, use_container_width=True)
            else:
                 st.info(f"Nenhum jogador com participação válida encontrado para a competição '{comp_selecionada}'.")

        else:
            st.info(f"Nenhum dado de participação encontrado para a competição '{comp_selecionada}'.")


# 4. Análise por Ano (Ranking)
elif tipo_analise == "analise_por_ano":
    ano_str = str(ano_filtrar) if ano_filtrar else "Todos os Anos"
    comp_str = competicao_escolhida if competicao_escolhida and competicao_escolhida != "Todas" else "Todas"
    st.subheader(f"Ranking de Participações - Ano: {ano_str} / Competição: {comp_str}")

    if not abas_para_analisar:
         st.warning("Nenhuma competição selecionada ou encontrada para análise.")
    else:
        player_stats_ano = {}

        with st.spinner(f"Calculando ranking para Ano: {ano_str} / Competição: {comp_str}..."):
            for aba in abas_para_analisar: # abas_para_analisar já foi filtrada pela competição se necessário
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns]

                    # Garante que 'ano' exista e seja numérico antes de filtrar
                    if 'ano' not in df.columns:
                        if ano_filtrar: # Se um ano foi especificado, não podemos analisar esta aba
                            st.warning(f"⚠️ Aba '{aba}': Faltando coluna 'ano'. Pulando para ranking anual.")
                            continue
                        else: # Se for "todos os anos", apenas marque como N/A
                             df['ano'] = pd.NA
                    else:
                        df['ano'] = pd.to_numeric(df['ano'], errors='coerce')


                    # Filtro de Ano
                    if ano_filtrar:
                        df_filtrada = df[df['ano'] == ano_filtrar].copy()
                    else:
                        df_filtrada = df.copy() # Usa o dataframe inteiro se não houver filtro de ano

                    if df_filtrada.empty:
                        continue # Pula para próxima aba se o filtro esvaziar o DF

                    # Verifica colunas de participação
                    if 'gols' not in df_filtrada.columns and 'assistências' not in df_filtrada.columns:
                        st.warning(f"⚠️ Aba '{aba}' (filtrada): Faltando 'gols' e 'assistências'. Pulando.")
                        continue

                    # Lógica de agregação similar ao ranking geral, mas no df_filtrada
                    for index, row in df_filtrada.iterrows():
                        # Gols
                        if 'gols' in df_filtrada.columns and isinstance(row['gols'], str):
                            gols_list = [p.strip() for p in row['gols'].split(";") if p.strip()]
                            for p in gols_list:
                                p_nome_original = p
                                p_limpo = limpar_nome(p)
                                if p_limpo and p_limpo != 'nan' and not any(limpar_nome(term) in p_limpo for term in TERMOS_IGNORADOS):
                                    player_stats_ano[p_nome_original] = player_stats_ano.get(p_nome_original, {'Gols': 0, 'Assistências': 0})
                                    player_stats_ano[p_nome_original]['Gols'] += 1
                        # Assistências
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

        # Montar e exibir o ranking do ano/competição
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
                df_ranking_ano.index = range(1, len(df_ranking_ano) + 1) # Começa índice em 1
                st.dataframe(df_ranking_ano, use_container_width=True)
            else:
                 st.info(f"Nenhum jogador com participação válida encontrado para Ano: {ano_str} / Competição: {comp_str}.")
        else:
            st.info(f"Nenhum dado de participação encontrado para Ano: {ano_str} / Competição: {comp_str}.")


# 5 & 6. Listar Gols / Assistências (por jogador)
elif tipo_analise in ["gols", "assistencias"]:
    if not jogador_escolhido:
        st.warning("Por favor, digite o nome de um jogador na barra lateral.")
    # Nota: Esta análise VARRE TODAS as abas por padrão, ignorando a seleção de competição
    else:
        tipo_evento = "Gols" if tipo_analise == "gols" else "Assistências"
        coluna_busca = limpar_nome(tipo_evento) # 'gols' ou 'assistências'
        emoji = "⚽" if tipo_analise == "gols" else "👟"
        ano_str = str(ano_filtrar) if ano_filtrar else "Todos os Anos"

        st.subheader(f"{emoji} Lista de {tipo_evento} de {jogador_escolhido.title()} ({ano_str})")

        resultados_lista = []
        jogador_limpo = limpar_nome(jogador_escolhido)

        # Itera por TODAS as abas do arquivo Excel carregado
        todas_as_abas = xls.sheet_names if xls else []

        with st.spinner(f"Buscando {tipo_evento.lower()} de {jogador_escolhido.title()} em todas as competições ({ano_str})..."):
            for aba in todas_as_abas:
                try:
                    df = pd.read_excel(xls, sheet_name=aba)
                    df.columns = [limpar_nome(col) for col in df.columns]

                    # Verifica colunas essenciais
                    cols_essenciais = [coluna_busca, 'partida', 'campeonato', 'ano']
                    colunas_faltando = [c for c in cols_essenciais if c not in df.columns]
                    if colunas_faltando:
                        st.warning(f"⚠️ Aba '{aba}': Faltando colunas: {', '.join(colunas_faltando)}. Pulando para lista de {tipo_evento}.")
                        continue

                     # Garante que 'ano' seja numérico antes de filtrar
                    if 'ano' not in df.columns:
                        if ano_filtrar: # Se um ano foi especificado, não podemos analisar esta aba
                            continue
                        else: # Se for "todos os anos", apenas marque como N/A
                             df['ano'] = pd.NA
                    else:
                        df['ano'] = pd.to_numeric(df['ano'], errors='coerce')


                    # Filtro de Ano (se aplicável)
                    df_filtrada_ano = df.copy()
                    if ano_filtrar:
                        df_filtrada_ano = df_filtrada_ano[df_filtrada_ano['ano'] == ano_filtrar]


                    if df_filtrada_ano.empty:
                        continue

                    # Itera nas linhas filtradas por ano (ou todas se ano_filtrar for None)
                    for index, row in df_filtrada_ano.iterrows():
                        participacoes_texto = row.get(coluna_busca, "")
                        num_participacoes = verificar_participacao(participacoes_texto, jogador_limpo)

                        if num_participacoes > 0:
                            # Tenta formatar o ano como inteiro, mas mantém N/A se falhar
                            try:
                                ano_valor = int(row['ano']) if pd.notna(row['ano']) else "N/A"
                            except (ValueError, TypeError):
                                ano_valor = row.get('ano', 'N/A')

                            campeonato = row.get('campeonato', 'N/A')
                            partida = row.get('partida', 'N/A')
                            # Adiciona uma entrada para cada gol/assistência na mesma partida
                            for _ in range(num_participacoes):
                                resultados_lista.append(f"{emoji} {ano_valor} - {campeonato} - {partida}")

                except Exception as e:
                    st.error(f"⚠️ Erro ao processar a aba '{aba}' para listar {tipo_evento}: {e}")

        if resultados_lista:
            # Ordena a lista antes de exibir
            resultados_lista.sort()
            # Adiciona numeração e exibe
            resultados_formatados = [f"{i+1}. {item}" for i, item in enumerate(resultados_lista)]
            st.markdown("\n".join(resultados_formatados))
        elif jogador_escolhido:
            st.info(f"Nenhum(a) {tipo_evento.lower()} encontrado(a) para {jogador_escolhido.title()} no ano {ano_str}.")

# --- Mensagem Final ---
# Removido o st.sidebar.success daqui para que apareça mesmo se houver erros parciais
# st.sidebar.success("Análise concluída!") # Pode ser adicionado de volta se preferir
st.caption("Desenvolvido por Riuler")

# Adiciona um separador final na sidebar
st.sidebar.divider()