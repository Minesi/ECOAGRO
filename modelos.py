from __future__ import annotations # Para adiar a avaliação dos Type Hints
import datetime
import re

class ValidadorDocumento:
    @staticmethod
    def limpar_documento(doc: str) -> str:
        return re.sub(r'\D', '', str(doc))
    
    @staticmethod
    def validar_cpf(cpf: str) -> bool:
        cpf = ValidadorDocumento.limpar_documento(cpf)
        if len(cpf) != 11 or cpf == cpf[0] * 11:
            return False
        #Validação do CPF, O CPF é validado pelos dois últimos dígitos, chamados dígitos verificadores.
        #Primeiro digito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        digito_1 = 0 if resto == 10 else resto

        #Segundo digito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        digito_2 = 0 if resto == 10 else resto

        return int(cpf[9]) == digito_1 and int(cpf[10]) == digito_2
    
    @staticmethod
    def validar_cnpj(cnpj: str) -> bool:    
        cnpj = ValidadorDocumento.limpar_documento(cnpj)
        if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
            return False
        #Validação do CNPJ é semlhante ao CPF, os dois últimos dígitos são os dígitos verificadores, calculados a partir dos 12 primeiros dígitos.
        #Primeiro digito
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
        resto = soma % 11
        digito_1 = 0 if resto < 2 else 11 - resto

        #Segundo digito
        pesos_2 = [6] + pesos_1
        soma = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
        resto = soma % 11
        digito_2 = 0 if resto < 2 else 11 - resto

        return int(cnpj[12]) == digito_1 and int(cnpj[13]) == digito_2
    
    @classmethod
    def validar_doc(cls, doc: str) -> bool:
        doc_limpo = cls.limpar_documento(doc)
        if len(doc_limpo) == 11:
            return cls.validar_cpf(doc_limpo)
        elif len(doc_limpo) == 14:
            return cls.validar_cnpj(doc_limpo)
        return False
    
class DireitoCreditorio:
    def __init__(self, id_titulo, cedente, cpf_cnpj, sacado, valor_nominal,
                 data_aquisicao, data_vencimento, status, numero_parcela):
        self.id = int(id_titulo)
        self.cedente = str(cedente)
        self.cpf_cnpj = str(cpf_cnpj)
        self.sacado = str(sacado)
        self.valor_nominal = float(valor_nominal)

        #Conversão de datas caso venham em formato errado
        self.data_aquisicao = self._parse_data(data_aquisicao)
        self.data_vencimento = self._parse_data(data_vencimento)

        self.status = str(status)
        self.numero_parcela = int(numero_parcela)

        #Flag de documento inválido
        self.documento_valido = not ValidadorDocumento.validar_doc(self.cpf_cnpj)
             
        self._data_corte = datetime.date(2026, 1, 1)  # Data de corte para considerar títulos vencidos

    def _parse_data(self, dt):
        if isinstance(dt, datetime.date):
            return dt
        if isinstance(dt, str):
            return datetime.datetime.strptime(dt, "%d/%m/%Y").date()
        return dt.date(0)
        
    def esta_vencido(self) -> bool:
        # Status não liquidado e data de vencimento anterior à data de corte
        if self.status in ['liquidado']:
            return False
        return self.data_vencimento < self._data_corte
        
    def dias_em_atraso(self) -> int:
        if not self.esta_vencido():
            return 0
        delta = self._data_corte - self.data_vencimento
        return max(0, delta.days)
        
    def inconsistencias(self) -> list[str]:
        erros = []
        if self.data_aquisicao > self.data_vencimento:
            erros.append("Data de aquisição posterior à data de vencimento.")
        if self.valor_nominal <= 0:
            erros.append("Valor nominal zerado ou negativo.")
        if self.numero_parcela <= 0:
            erros.append("Número de parcela inválido (menor ou igual a zero).")

        # Resolução para conflitos de Status vs Tempo
        if self.data_vencimento <self._data_corte and self.status == 'a_vencer':
            erros.append("Status 'a_vencer' para um titulo já vencido em relação à data de corte.")
        if self.data_vencimento >= self._data_corte and self.status == 'vencido':
            erros.append("Status 'vencido' para um titulo com data de vencimento futura.")

        return erros

    def tem_inconsistencias(self) -> bool:
        return len(self.inconsistencias()) > 0

class Carteira:
    def __init__(self, nome: str, direitos: list[DireitoCreditorio] = None):
        self.nome = str(nome)
        self.direitos = direitos if direitos is not None else []
        
    def valor_total(self) -> float:
        return sum(d.valor_nominal for d in self.direitos)
        
    def taxa_inadimplencia(self) -> float:
        total = self.valor_total()
        if total == 0:
            return 0.0
        valor_inadimplente = sum(d.valor_nominal for d in self.direitos if d.status == 'inadimplente')
        return (valor_inadimplente / total) * 100
        
    def titulos_vencidos(self) -> list[DireitoCreditorio]:
        return [d for d in self.direitos if d.esta_vencido()]
        
    def relatorio_por_cedente(self) -> dict:
        resumo = {}
        for d in self.direitos:
            if d.cedente not in resumo:
                resumo[d.cedente] = {"valor_total": 0.0, "quantidade": 0}
                resumo[d.cedente]["valor_total"] += d.valor_nominal
                resumo[d.cedente]["quantidade"] += 1
        return resumo
        
    def inconsistencias(self) -> list[DireitoCreditorio]:
        return [d for d in self.direitos if d.tem_inconsistencias()]