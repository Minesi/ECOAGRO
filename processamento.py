import os
import json
import datetime
import pandas as pd
import numpy as np

from modelos import DireitoCreditorio, Carteira

def executar_pipeline(caminho_csv: str):
    alertas = []
    
    print("Leitura e Limpeza de Dados")
    if not os.path.exists(caminho_csv):
        raise FileNotFoundError(f"Arquivo {caminho_csv} não encontrado.")
        
    nomes_colunas = [
        'id', 'cedente', 'cpf_cnpj', 'sacado', 'valor_nominal', 
        'data_aquisicao', 'data_vencimento', 'status', 'numero_parcela'
    ]
    
    # Leitura inicial sem processar tipos ainda para evitar conflitos
    df = pd.read_csv(
        caminho_csv, 
        sep=';', 
        header=None, 
        dtype=str,  
        encoding='utf-8-sig'
    )
    
    # Remove a linha de cabeçalho que está no fim do arquivo
    df = df[df[0] != 'id']
    
    # Batiza as colunas
    df.columns = nomes_colunas
    
    # Remove linha duplicada
    df = df.drop_duplicates(subset=['id', 'sacado', 'numero_parcela'])
    
    total_linhas_original = len(df)
    
    # Substitui , por . 
    df['valor_nominal'] = df['valor_nominal'].str.replace(',', '.', regex=False)
    df['valor_nominal'] = pd.to_numeric(df['valor_nominal'], errors='coerce')
    
    # Converte os IDs e as Parcelas tratando possíveis falhas
    df['id'] = pd.to_numeric(df['id'], errors='coerce')
    df['numero_parcela'] = pd.to_numeric(df['numero_parcela'], errors='coerce').fillna(1)
    
    # Limpeza caso alguma linha tenha ficado vazio
    df = df.dropna(subset=['id', 'valor_nominal'])
    
    # Garante a tipagem final correta
    df['id'] = df['id'].astype(int)
    df['valor_nominal'] = df['valor_nominal'].astype(float)
    df['numero_parcela'] = df['numero_parcela'].astype(int)

    
    # Tratamento de Strings vazias e padronização
    for col in ['cedente', 'sacado', 'status', 'cpf_cnpj']:
        df[col] = df[col].fillna("NAO_INFORMADO").astype(str).str.strip()

    # Tratamento de Datas usando o padrão brasileiro (DD/MM/YYYY)
    for col in ['data_aquisicao', 'data_vencimento']:
        df[col] = pd.to_datetime(df[col], format="%d/%m/%Y", errors='coerce')
        if df[col].isnull().any():
            nulas_count = df[col].isnull().sum()
            msg = f"Foram encontradas {nulas_count} datas nulas/inválidas em '{col}'. Tratadas para 2026-01-01."
            alertas.append(msg)
            print(f"[ALERTA] {msg}")
            df[col] = df[col].fillna(pd.to_datetime('2026-01-01'))

    print(f"Dados limpos com sucesso. Registros válidos: {len(df)} de {total_linhas_original}\n")
    
    print("Instanciação OOP e Validação Manual")
    lista_direitos = []
    flags_documento_invalido = []
    lista_de_inconsistencias_logicas = []
    
    for _, row in df.iterrows():
        direito = DireitoCreditorio(
            id_titulo=row['id'],
            cedente=row['cedente'],
            cpf_cnpj=row['cpf_cnpj'],
            sacado=row['sacado'],
            valor_nominal=row['valor_nominal'],
            data_aquisicao=row['data_aquisicao'].to_pydatetime().date(),
            data_vencimento=row['data_vencimento'].to_pydatetime().date(),
            status=row['status'],
            numero_parcela=row['numero_parcela']
        )
        lista_direitos.append(direito)
        
        is_invalido = not direito.documento_valido
        flags_documento_invalido.append(is_invalido)
        lista_de_inconsistencias_logicas.append(", ".join(direito.inconsistencias()) if direito.tem_inconsistencias() else "Nenhuma")
        
        if is_invalido:
            alertas.append(f"Documento inválido detectado para ID {direito.id} (Cedente: {direito.cedente}).")
        if direito.tem_inconsistencias():
            for inc in direito.inconsistencias():
                alertas.append(f"Inconsistência lógica no ID {direito.id}: {inc}")

    df['documento_invalido'] = flags_documento_invalido
    df['inconsistencias_logicas'] = lista_de_inconsistencias_logicas

    carteira_fidc = Carteira(nome="FIDC_CARTEIRA_TESTE", direitos=lista_direitos)

    print("Analise da Carteira")
    valor_total_carteira = carteira_fidc.valor_total()
    taxa_inad = carteira_fidc.taxa_inadimplencia()
    
    resumo_status_df = df.groupby('status').agg(quantidade=('id', 'count'), valor_total=('valor_nominal', 'sum')).to_dict(orient='index')
    resumo_status_json = {}
    for status, metrica in resumo_status_df.items():
        resumo_status_json[status] = {
            "quantidade": int(metrica['quantidade']),
            "valor_total": float(round(metrica['valor_total'], 2))
        }

    resumo_cedente_dict = carteira_fidc.relatorio_por_cedente()
    resumo_cedente_json = {}
    for cedente, metrica in resumo_cedente_dict.items():
        pct = (metrica['valor_total'] / valor_total_carteira * 100) if valor_total_carteira > 0 else 0.0
        resumo_cedente_json[cedente] = {
            "valor_total": float(round(metrica['valor_total'], 2)),
            "percentual_sobre_carteira_pct": float(round(pct, 2))
        }

    print("Geração do Relatório JSON")
    agora_formatado = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    relatorio = {
        "data_geracao": agora_formatado,
        "nome_carteira": carteira_fidc.nome,
        "total_registros": len(carteira_fidc.direitos),
        "valor_total": float(round(valor_total_carteira, 2)),
        "taxa_inadimplencia_pct": float(round(taxa_inad, 2)),
        "resumo_por_status": resumo_status_json,
        "resumo_por_cedente": resumo_cedente_json,
        "alertas": alertas
    }

    with open('relatorio.json', 'w', encoding='utf-8') as f:
        json.dump(relatorio, f, indent=4, ensure_ascii=False)

    print("\n=== Gerando Cópias de Auditoria (CSV e Excel) ===")
    
    df['data_aquisicao'] = df['data_aquisicao'].dt.strftime('%Y-%m-%d')
    df['data_vencimento'] = df['data_vencimento'].dt.strftime('%Y-%m-%d')
    
    df.to_csv('carteira_corrigida.csv', sep=';', index=False, decimal=',', encoding='utf-8-sig')
    print("Arquivo CSV corrigido gerado: 'carteira_corrigida.csv'")
    
    
if __name__ == "__main__":
    executar_pipeline("carteira.csv")