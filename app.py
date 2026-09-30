import io
import sqlite3
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

# Configuração da página UseIria
st.set_page_config(
    page_title="UseIria - Gestão Moda Infantil", page_icon="🎀", layout="wide"
)

# Estilo Profissional de Alto Contraste
st.markdown(
    """
    <style>
    div[data-testid="stMetric"] {
        background-color: #1e1e2e !important;
        padding: 16px !important;
        border-radius: 10px !important;
        border-left: 5px solid #d946ef !important;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] p {
        color: #a6adc8 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stMetricValue"] div {
        color: #f5c2e7 !important;
        font-weight: bold !important;
        font-size: 1.6rem !important;
    }
    div.stButton > button {
        background-color: #d946ef !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        border: none !important;
        font-weight: bold !important;
        padding: 8px 16px !important;
    }
    div.stButton > button:hover {
        background-color: #c026d3 !important;
        color: #ffffff !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------------
# BANCO DE DADOS
# -------------------------------------------------------------------


def conectar_bd():
  return sqlite3.connect("useiria_v2.db", check_same_thread=False)


def criar_tabelas():
  conn = conectar_bd()
  cursor = conn.cursor()

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_mae TEXT NOT NULL,
            nome_crianca TEXT,
            telefone TEXT,
            canal_origem TEXT,
            data_nascimento_crianca TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT,
            tamanho TEXT,
            preco_custo REAL,
            frete_compra REAL,
            preco_venda REAL,
            estoque INTEGER
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            taxa_entrega REAL,
            valor_total REAL,
            forma_pagamento TEXT,
            canal_venda TEXT,
            data_venda TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descricao TEXT NOT NULL,
            categoria TEXT,
            valor REAL,
            data_despesa TEXT
        )
    """)

  conn.commit()
  conn.close()


criar_tabelas()

# -------------------------------------------------------------------
# MENU LATERAL
# -------------------------------------------------------------------
st.sidebar.title("🎀 UseIria Moda Infantil")
st.sidebar.markdown("*Sistema de Gestão & Análise*")

menu = st.sidebar.radio(
    "Navegação",
    [
        "📊 Dashboard",
        "📦 Cadastrar Produto",
        "👤 Cadastrar Cliente",
        "💵 Registrar Venda",
        "💸 Despesas Operacionais",
        "💾 Backup / Exportar",
    ],
)

conn = conectar_bd()

CANAIS_ORIGEM = [
    "Instagram @UseIria",
    "Stories / Reels Influenciadora",
    "Indicação de Amigos/Clientes",
    "WhatsApp / Status",
    "Anúncios / Tráfego Pago",
    "Outros",
]

# -------------------------------------------------------------------
# ABA: DASHBOARD DE ANÁLISE
# -------------------------------------------------------------------
if menu == "📊 Dashboard":
  st.header("📊 Análise Geral do Negócio - UseIria")

  df_vendas = pd.read_sql_query(
      """
        SELECT 
            v.id,
            v.data_venda,
            v.quantidade,
            v.taxa_entrega,
            v.valor_total,
            v.forma_pagamento,
            v.canal_venda,
            p.nome AS produto,
            p.categoria,
            p.tamanho,
            ((p.preco_custo + p.frete_compra) * v.quantidade) AS custo_pecas_vendidas
        FROM vendas v
        JOIN produtos p ON v.produto_id = p.id
    """,
      conn,
  )

  df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)
  df_despesas = pd.read_sql_query("SELECT * FROM despesas", conn)

  faturamento = (
      df_vendas["valor_total"].sum() if not df_vendas.empty else 0.0
  )
  custo_pecas_vendidas = (
      df_vendas["custo_pecas_vendidas"].sum() if not df_vendas.empty else 0.0
  )

  lucro_bruto = faturamento - custo_pecas_vendidas
  despesas_operacionais = (
      df_despesas["valor"].sum() if not df_despesas.empty else 0.0
  )
  lucro_liquido = lucro_bruto - despesas_operacionais
  margem_liquida = (
      (lucro_liquido / faturamento * 100) if faturamento > 0 else 0.0
  )

  pedidos = len(df_vendas)
  ticket_medio = (faturamento / pedidos) if pedidos > 0 else 0.0

  if not df_produtos.empty:
    investido_compras = (
        (df_produtos["preco_custo"] + df_produtos["frete_compra"])
        * df_produtos["estoque"]
    ).sum() + custo_pecas_vendidas
    dinheiro_parado_estoque = (
        (df_produtos["preco_custo"] + df_produtos["frete_compra"])
        * df_produtos["estoque"]
    ).sum()
    produtos_repor = len(df_produtos[df_produtos["estoque"] <= 2])
  else:
    investido_compras = 0.0
    dinheiro_parado_estoque = 0.0
    produtos_repor = 0

  col1, col2, col3, col4, col5 = st.columns(5)
  col1.metric("Faturamento", f"R$ {faturamento:,.2f}")
  col2.metric("Lucro bruto", f"R$ {lucro_bruto:,.2f}")
  col3.metric("Lucro líquido", f"R$ {lucro_liquido:,.2f}")
  col4.metric("Margem líquida", f"{margem_liquida:.1f}%")
  col5.metric("Pedidos", pedidos)

  st.markdown("<br>", unsafe_allow_html=True)

  col6, col7, col8, col9, col10 = st.columns(5)
  col6.metric("Ticket médio", f"R$ {ticket_medio:,.2f}")
  col7.metric("Investido em compras", f"R$ {investido_compras:,.2f}")
  col8.metric("Despesas operacionais", f"R$ {despesas_operacionais:,.2f}")
  col9.metric("Dinheiro parado em estoque", f"R$ {dinheiro_parado_estoque:,.2f}")
  col10.metric("Produtos para repor", produtos_repor)

  st.markdown("---")

  # --- GRÁFICO DE VENDAS DIÁRIAS ---
  if not df_vendas.empty:
    st.subheader("📅 Análise de Vendas por Dia")

    df_vendas["Data"] = df_vendas["data_venda"].str.slice(0, 10)
    df_diario = (
        df_vendas.groupby("Data")
        .agg(
            {
                "id": "count",
                "quantidade": "sum",
                "valor_total": "sum",
            }
        )
        .reset_index()
    )
    df_diario.columns = [
        "Data",
        "Qtd Pedidos",
        "Peças Vendidas",
        "Faturamento (R$)",
    ]

    col_g1, col_g2 = st.columns(2)
    with col_g1:
      fig_vendas_dia = px.bar(
          df_diario,
          x="Data",
          y="Qtd Pedidos",
          title="Quantidade de Vendas / Pedidos por Dia",
          color_discrete_sequence=["#d946ef"],
          text="Qtd Pedidos",
      )
      st.plotly_chart(fig_vendas_dia, use_container_width=True)

    with col_g2:
      fig_fat_dia = px.line(
          df_diario,
          x="Data",
          y="Faturamento (R$)",
          title="Faturamento Diário (R$)",
          markers=True,
          color_discrete_sequence=["#38bdf8"],
      )
      st.plotly_chart(fig_fat_dia, use_container_width=True)

    st.markdown("#### Tabela Consolidada de Vendas Diárias")
    st.dataframe(df_diario, use_container_width=True)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
      fig_canal = px.pie(
          df_vendas,
          values="valor_total",
          names="canal_venda",
          title="Faturamento por Origem de Cliente",
          hole=0.4,
          color_discrete_sequence=px.colors.qualitative.Pastel,
      )
      st.plotly_chart(fig_canal, use_container_width=True)
    with c2:
      fig_pag = px.bar(
          df_vendas,
          x="forma_pagamento",
          y="valor_total",
          title="Vendas por Forma de Pagamento",
          color="forma_pagamento",
          color_discrete_sequence=px.colors.qualitative.Set2,
      )
      st.plotly_chart(fig_pag, use_container_width=True)

# -------------------------------------------------------------------
# ABA: CADASTRO E GESTÃO DE ESTOQUE
# -------------------------------------------------------------------
elif menu == "📦 Cadastrar Produto":
  st.header("📦 Cadastro & Gestão de Estoque")

  with st.form("form_produto"):
    col1, col2 = st.columns(2)
    with col1:
      nome = st.text_input("Nome do Produto (ex: Vestido Floral)")
      categoria = st.selectbox(
          "Categoria", ["Vestidos", "Conjuntos", "Acessórios", "Calçados", "Outros"]
      )
      tamanho = st.selectbox(
          "Tamanho", ["RN", "P", "M", "G", "1", "2", "4", "6", "8", "10", "12"]
      )
      estoque = st.number_input(
          "Quantidade de Peças no Estoque/Lote", min_value=1, value=1, step=1
      )

    with col2:
      preco_custo = st.number_input(
          "Preço de Custo Unitário (R$)", min_value=0.0, step=0.5
      )
      frete_total_lote = st.number_input(
          "Frete Total do Lote/Nota (R$)",
          min_value=0.0,
          step=1.0,
          help="Digite o valor total pago no frete do lote. O sistema calcula o valor por peça sozinho!",
      )
      preco_venda = st.number_input("Preço de Venda (R$)", min_value=0.0, step=0.5)

    frete_unitario = (
        (frete_total_lote / estoque)
        if (frete_total_lote > 0 and estoque > 0)
        else 0.0
    )
    st.caption(
        f"💡 *Cálculo automático: O frete por unidade deste produto será de **R$"
        f" {frete_unitario:.2f}**.*"
    )

    submetido = st.form_submit_button("Salvar Produto")
    if submetido and nome:
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO produtos (nome, categoria, tamanho, preco_custo, frete_compra, preco_venda, estoque)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
          (
              nome,
              categoria,
              tamanho,
              preco_custo,
              frete_unitario,
              preco_venda,
              estoque,
          ),
      )
      conn.commit()
      st.success(f"Produto '{nome}' cadastrado com sucesso!")
      st.rerun()

  st.markdown("---")
  st.subheader("📋 Estoque Atual & Alertas de Reposição")

  df_produtos = pd.read_sql_query("SELECT * FROM produtos", conn)

  if df_produtos.empty:
    st.info("Nenhum produto cadastrado.")
  else:
    df_repor = df_produtos[df_produtos["estoque"] <= 2]
    if not df_repor.empty:
      st.warning(
          f"⚠️ **ATENÇÃO:** Tem **{len(df_repor)} produto(s)** com estoque"
          " baixo (2 unidades ou menos)! Prepare a reposição."
      )
      st.dataframe(
          df_repor[
              ["id", "nome", "categoria", "tamanho", "estoque", "preco_venda"]
          ],
          use_container_width=True,
      )

    st.markdown("#### Todos os Produtos no Estoque")
    st.dataframe(df_produtos, use_container_width=True)

    st.markdown("### 🗑 Excluir Produto")
    opcoes_exclusao = {
        row["id"]: (
            f"ID {row['id']} - {row['nome']} ({row['tamanho']}) - R$"
            f" {row['preco_venda']:.2f}"
        )
        for _, row in df_produtos.iterrows()
    }

    col_sel, col_btn = st.columns([3, 1])
    with col_sel:
      produto_id_excluir = st.selectbox(
          "Selecione o produto que deseja excluir:",
          options=list(opcoes_exclusao.keys()),
          format_func=lambda x: opcoes_exclusao[x],
      )

    with col_btn:
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("🗑️ Excluir Produto"):
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM vendas WHERE produto_id = ?", (produto_id_excluir,)
        )
        cursor.execute(
            "DELETE FROM produtos WHERE id = ?", (produto_id_excluir,)
        )
        conn.commit()
        st.success("Produto excluído com sucesso!")
        st.rerun()

# -------------------------------------------------------------------
# ABA: CLIENTES & ANIVERSARIANTES
# -------------------------------------------------------------------
elif menu == "👤 Cadastrar Cliente":
  st.header("👤 Cadastro de Clientes & Campanhas")

  with st.form("form_cliente"):
    col1, col2 = st.columns(2)
    with col1:
      nome_mae = st.text_input("Nome do Cliente / Mãe")
      nome_crianca = st.text_input("Nome da Criança")
      canal_origem = st.selectbox(
          "Por onde conheceu a UseIria?", CANAIS_ORIGEM
      )
    with col2:
      telefone = st.text_input("WhatsApp / Telefone")
      data_nasc = st.date_input("Data de Nascimento da Criança")

    submetido = st.form_submit_button("Salvar Cliente")
    if submetido and nome_mae:
      cursor = conn.cursor()
      cursor.execute(
          """
                INSERT INTO clientes (nome_mae, nome_crianca, telefone, canal_origem, data_nascimento_crianca)
                VALUES (?, ?, ?, ?, ?)
            """,
          (nome_mae, nome_crianca, telefone, canal_origem, str(data_nasc)),
      )
      conn.commit()
      st.success(f"Cliente '{nome_mae}' cadastrada com sucesso!")
      st.rerun()

  st.markdown("---")
  st.subheader("🎂 Aniversariantes do Mês (Campanha Direcionada)")
  df_clientes_raw = pd.read_sql_query("SELECT * FROM clientes", conn)

  if not df_clientes_raw.empty:
    mes_atual = datetime.now().month
    nome_meses = [
        "Janeiro",
        "Fevereiro",
        "Março",
        "Abril",
        "Maio",
        "Junho",
        "Julho",
        "Agosto",
        "Setembro",
        "Outubro",
        "Novembro",
        "Dezembro",
    ]

    def eh_aniversariante_mes(data_str):
      try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
        return dt.month == mes_atual
      except:
        return False

    df_aniversariantes = df_clientes_raw[
        df_clientes_raw["data_nascimento_crianca"].apply(
            eh_aniversariante_mes
        )
    ]

    if not df_aniversariantes.empty:
      st.balloons()
      st.success(
          f"🎉 Temos **{len(df_aniversariantes)} criança(s)** fazendo"
          f" aniversário no mês de **{nome_meses[mes_atual-1]}**! Envie uma"
          " mensagem especial no WhatsApp com cupom de desconto."
      )
      st.dataframe(
          df_aniversariantes[[
              "nome_mae",
              "nome_crianca",
              "data_nascimento_crianca",
              "telefone",
          ]],
          use_container_width=True,
      )
    else:
      st.info(
          f"Nenhum aniversariante cadastrado para o mês de"
          f" {nome_meses[mes_atual-1]}."
      )

  st.markdown("---")
  st.subheader("🎯 CRM Completo de Clientes")

  query_crm = """
        SELECT 
            c.id,
            c.nome_mae AS [Mãe],
            c.nome_crianca AS [Criança],
            c.telefone AS [WhatsApp],
            c.canal_origem AS [Origem],
            c.data_nascimento_crianca AS [Nascimento],
            COALESCE(SUM(v.quantidade), 0) AS [Peças Compradas],
            COALESCE(SUM(v.valor_total), 0.0) AS [Total Gasto (R$)],
            MAX(v.data_venda) AS [Última Compra]
        FROM clientes c
        LEFT JOIN vendas v ON c.id = v.cliente_id
        GROUP BY c.id
    """
  df_crm = pd.read_sql_query(query_crm, conn)

  if not df_crm.empty:

    def calcular_idade(data_str):
      try:
        nasc = datetime.strptime(data_str, "%Y-%m-%d")
        hoje = datetime.now()
        idade_anos = (
            hoje.year
            - nasc.year
            - ((hoje.month, hoje.day) < (nasc.month, nasc.day))
        )
        if idade_anos == 0:
          meses = (hoje.year - nasc.year) * 12 + hoje.month - nasc.month
          return f"{meses} meses"
        return f"{idade_anos} anos"
      except:
        return "N/I"

    df_crm["Idade Criança"] = df_crm["Nascimento"].apply(calcular_idade)

    def formatar_data(data_str):
      if data_str and data_str != "None":
        try:
          return datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").strftime(
              "%d/%m/%Y"
          )
        except:
          return data_str[:10]
      return "Sem compras"

    df_crm["Última Compra"] = df_crm["Última Compra"].apply(formatar_data)

    df_exibicao = df_crm[[
        "Mãe",
        "Criança",
        "Idade Criança",
        "WhatsApp",
        "Peças Compradas",
        "Total Gasto (R$)",
        "Última Compra",
        "Origem",
    ]]
    st.dataframe(df_exibicao, use_container_width=True)

    st.markdown("### 🗑 Excluir Cliente")
    opcoes_cli_excluir = {
        row["id"]: f"ID {row['id']} - {row['nome_mae']} (Mãe de {row['nome_crianca']})"
        for _, row in df_clientes_raw.iterrows()
    }

    c_sel, c_btn = st.columns([3, 1])
    with c_sel:
      cli_id_excluir = st.selectbox(
          "Selecione a cliente para remover:",
          options=list(opcoes_cli_excluir.keys()),
          format_func=lambda x: opcoes_cli_excluir[x],
      )
    with c_btn:
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("🗑️ Excluir Cliente"):
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM vendas WHERE cliente_id = ?", (cli_id_excluir,)
        )
        cursor.execute("DELETE FROM clientes WHERE id = ?", (cli_id_excluir,))
        conn.commit()
        st.success("Cliente removida com sucesso!")
        st.rerun()

# -------------------------------------------------------------------
# ABA: REGISTRO E GESTÃO ANALÍTICA DE VENDAS
# -------------------------------------------------------------------
elif menu == "💵 Registrar Venda":
  st.header("💵 Lançamento de Vendas & Histórico Analítico")

  df_produtos = pd.read_sql_query(
      "SELECT id, nome || ' (' || tamanho || ')' AS item, preco_venda, estoque"
      " FROM produtos WHERE estoque > 0",
      conn,
  )
  df_clientes = pd.read_sql_query(
      "SELECT id, nome_mae, canal_origem FROM clientes", conn
  )

  if df_produtos.empty:
    st.warning(
        "Nenhum produto cadastrado com estoque disponível para realizar vendas."
    )
  else:
    with st.form("form_venda"):
      cliente_opcoes = (
          dict(zip(df_clientes["id"], df_clientes["nome_mae"]))
          if not df_clientes.empty
          else {0: "Cliente Avulso"}
      )
      produto_opcoes = dict(zip(df_produtos["id"], df_produtos["item"]))

      col1, col2 = st.columns(2)
      with col1:
        cliente_id = st.selectbox(
            "Cliente",
            options=list(cliente_opcoes.keys()),
            format_func=lambda x: cliente_opcoes[x],
        )
        produto_id = st.selectbox(
            "Produto",
            options=list(produto_opcoes.keys()),
            format_func=lambda x: produto_opcoes[x],
        )
        quantidade = st.number_input("Quantidade", min_value=1, value=1)

      with col2:
        taxa_entrega = st.number_input(
            "Taxa de Entrega / Frete Cobrado (R$)", min_value=0.0, step=1.0
        )
        forma_pagamento = st.selectbox(
            "Forma de Pagamento",
            ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"],
        )
        canal_venda = st.selectbox(
            "Canal da Venda", CANAIS_ORIGEM
        )

      preco_unitario = df_produtos[df_produtos["id"] == produto_id][
          "preco_venda"
      ].values[0]
      estoque_atual = df_produtos[df_produtos["id"] == produto_id][
          "estoque"
      ].values[0]

      valor_produtos = preco_unitario * quantidade
      valor_total_final = valor_produtos + taxa_entrega

      st.info(f"**Total Final da Venda: R$ {valor_total_final:.2f}**")

      submetido = st.form_submit_button("Confirmar Venda")
      if submetido:
        if quantidade > estoque_atual:
          st.error(f"Estoque insuficiente! Apenas {estoque_atual} disponíveis.")
        else:
          cursor = conn.cursor()
          data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

          cursor.execute(
              """
                        INSERT INTO vendas (cliente_id, produto_id, quantidade, taxa_entrega, valor_total, forma_pagamento, canal_venda, data_venda)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
              (
                  cliente_id,
                  produto_id,
                  quantidade,
                  taxa_entrega,
                  valor_total_final,
                  forma_pagamento,
                  canal_venda,
                  data_atual,
              ),
          )

          cursor.execute(
              """
                        UPDATE produtos SET estoque = estoque - ? WHERE id = ?
                    """,
              (quantidade, produto_id),
          )

          conn.commit()
          st.success("Venda salva com sucesso!")
          st.rerun()

  # --- HISTÓRICO ANALÍTICO DE CADA VENDA & OPÇÃO DE EXCLUSÃO ---
  st.markdown("---")
  st.subheader("📋 Visão Analítica de Vendas Registradas")

  query_vendas_detalhada = """
        SELECT 
            v.id AS [ID Venda],
            v.data_venda AS [Data/Hora],
            COALESCE(c.nome_mae, 'Cliente Avulso') AS [Cliente],
            p.nome AS [Produto],
            p.tamanho AS [Tamanho],
            v.quantidade AS [Qtd],
            v.taxa_entrega AS [Frete Cobrado (R$)],
            v.valor_total AS [Valor Total (R$)],
            v.forma_pagamento AS [Pagamento],
            v.canal_venda AS [Canal Venda],
            v.produto_id
        FROM vendas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.id DESC
    """
  df_vendas_analitico = pd.read_sql_query(query_vendas_detalhada, conn)

  if df_vendas_analitico.empty:
    st.info("Nenhuma venda registrada até ao momento.")
  else:
    colunas_exibicao = [
        "ID Venda",
        "Data/Hora",
        "Cliente",
        "Produto",
        "Tamanho",
        "Qtd",
        "Frete Cobrado (R$)",
        "Valor Total (R$)",
        "Pagamento",
        "Canal Venda",
    ]
    st.dataframe(
        df_vendas_analitico[colunas_exibicao], use_container_width=True
    )

    # --- EXCLUSÃO DE VENDA REGISTRADA ---
    st.markdown("### 🗑 Excluir Registro de Venda")
    opcoes_venda_excluir = {}
    for _, row in df_vendas_analitico.iterrows():
      opcoes_venda_excluir[row["ID Venda"]] = (
          f"Venda #{row['ID Venda']} - {row['Cliente']} - {row['Produto']}"
          f" ({row['Qtd']}x) - R$ {row['Valor Total (R$)']:.2f}"
      )

    col_vsel, col_vbtn = st.columns([3, 1])
    with col_vsel:
      venda_id_excluir = st.selectbox(
          "Selecione a venda para remover:",
          options=list(opcoes_venda_excluir.keys()),
          format_func=lambda x: opcoes_venda_excluir[x],
      )

    with col_vbtn:
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("🗑 Excluir Venda"):
        cursor = conn.cursor()

        info_venda = df_vendas_analitico[
            df_vendas_analitico["ID Venda"] == venda_id_excluir
        ].iloc[0]
        qtd_estorno = info_venda["Qtd"]
        prod_id_estorno = info_venda["produto_id"]

        cursor.execute(
            "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
            (qtd_estorno, prod_id_estorno),
        )

        cursor.execute("DELETE FROM vendas WHERE id = ?", (venda_id_excluir,))
        conn.commit()

        st.success(
            f"Venda #{venda_id_excluir} excluída e {qtd_estorno} unidade(s)"
            " devolvida(s) ao estoque!"
        )
        st.rerun()

# -------------------------------------------------------------------
# ABA: DESPESAS OPERACIONAIS
# -------------------------------------------------------------------
elif menu == "💸 Despesas Operacionais":
  st.header("💸 Registro de Despesas Operacionais")

  with st.form("form_despesa", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
      descricao = st.text_input(
          "Descrição da Despesa (ex: Sacolas, Tráfego Pago Instagram)"
      )
      categoria = st.selectbox(
          "Categoria",
          ["Marketing / Anúncios", "Embalagens", "Frete", "Taxas", "Outros"],
      )
    with col2:
      valor = st.number_input("Valor da Despesa (R$)", min_value=0.0, step=5.0)
      data_despesa = st.date_input("Data do Pagamento")

    submetido = st.form_submit_button("Lançar Despesa")
    if submetido:
      if not descricao or valor <= 0:
        st.error(
            "Por favor, preencha a descrição e insira um valor maior que R$"
            " 0,00."
        )
      else:
        cursor = conn.cursor()
        cursor.execute(
            """
                INSERT INTO despesas (descricao, categoria, valor, data_despesa)
                VALUES (?, ?, ?, ?)
            """,
            (descricao, categoria, float(valor), str(data_despesa)),
        )
        conn.commit()
        st.success(f"Despesa '{descricao}' no valor de R$ {valor:.2f} lançada!")
        st.rerun()

  st.markdown("---")
  st.subheader("📋 Despesas Lançadas")

  df_despesas = pd.read_sql_query(
      "SELECT id, descricao AS [Descrição], categoria AS [Categoria], valor AS"
      " [Valor (R$)], data_despesa AS [Data] FROM despesas ORDER BY id DESC",
      conn,
  )

  if df_despesas.empty:
    st.info("Nenhuma despesa operacional lançada até ao momento.")
  else:
    st.dataframe(df_despesas, use_container_width=True)

    st.markdown("### 🗑 Excluir Despesa Lançada")
    opcoes_desp = {}
    for _, row in df_despesas.iterrows():
      opcoes_desp[row["id"]] = (
          f"ID {row['id']} - {row['Descrição']} - R$ {row['Valor (R$)']:.2f}"
      )

    d_sel, d_btn = st.columns([3, 1])
    with d_sel:
      desp_id_excluir = st.selectbox(
          "Selecione a despesa para remover:",
          options=list(opcoes_desp.keys()),
          format_func=lambda x: opcoes_desp[x],
      )
    with d_btn:
      st.markdown("<br>", unsafe_allow_html=True)
      if st.button("🗑 Excluir Despesa"):
        cursor = conn.cursor()
        cursor.execute("DELETE FROM despesas WHERE id = ?", (desp_id_excluir,))
        conn.commit()
        st.success("Despesa excluída com sucesso!")
        st.rerun()

# -------------------------------------------------------------------
# ABA: BACKUP E EXPORTAÇÃO PARA EXCEL (.XLSX)
# -------------------------------------------------------------------
elif menu == "💾 Backup / Exportar":
  st.header("💾 Exportação de Dados & Backup em Excel")
  st.markdown(
      "Gere uma cópia completa de segurança com todas as abas consolidadas em"
      " um ficheiro de planilha `.xlsx`."
  )

  df_prod = pd.read_sql_query("SELECT * FROM produtos", conn)
  df_cli = pd.read_sql_query("SELECT * FROM clientes", conn)
  df_ven = pd.read_sql_query("SELECT * FROM vendas", conn)
  df_desp = pd.read_sql_query("SELECT * FROM despesas", conn)

  output = io.BytesIO()
  with pd.ExcelWriter(output, engine="openpyxl") as writer:
    df_prod.to_excel(writer, sheet_name="Estoque", index=False)
    df_cli.to_excel(writer, sheet_name="Clientes", index=False)
    df_ven.to_excel(writer, sheet_name="Vendas", index=False)
    df_desp.to_excel(writer, sheet_name="Despesas", index=False)

  processed_data = output.getvalue()

  data_hoje = datetime.now().strftime("%Y-%m-%d")
  st.download_button(
      label="📥 Baixar Backup Completo em Excel (.xlsx)",
      data=processed_data,
      file_name=f"Backup_UseIria_{data_hoje}.xlsx",
      mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  )
