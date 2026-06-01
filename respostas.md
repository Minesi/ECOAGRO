1. No Bloco 1, quais problemas você encontrou nos dados? Liste cada um e descreva exatamente como tratou e por quê tomou essa decisão.

R: Os problemas que encontrei no primeiro bloco foram:
- O Cabeçalho se encontrava no final, e ao tentar converter tudo direto, o código quebrava, para isso li o arquivo primeiro como texto e usei o Pandas para filtrar e jogar fora qualquer linha que tivesse o texto 'id'.
- Encontrei linha duplicadas e com base no ID, Sacado e Parcela utilizei o drop_duplicates para apagar as repetições e não somar o mesmo valor duas vezes
- O Formato de valores de moeda estava causando dinheiro por conta de estar com virgula e o python so entender ponto, realizei a troca da string de virgula para ponto com str.replace
- As datas estavam no formato brasileiro dd/mm/yyyy e para o funcionamento correto do pandas informei que o formato se manteria utilizando format="%d/%m%Y"
- Algumas linhas podiam vir com o campo ID quebrado e para isso forcei a conversão para número e usei o dropna para deletar a linha se o ID ou valor estivessem nulos, pois estavam dificultando a criação do título.

2. Explique o algoritmo que você implementou para validar CPF e CNPJ. Como funciona o cálculo dos dígitos verificadores em cada caso?
R: Busquei diretamente no GOV o calculo que é realizado para certificação do CPF e do CNPJ que são parecidos
- CPF: O código pega os 9 primeiros números e multiplica cada um por um sequência de 10 a 2. Soma tudo, multiplica por 10 e pega o resto da divisão por 11 para achar o primeiroo dígito. Depois, faz a mesma coisa com os 10 primeiros números (multiplicando de 11 a 2) para achar o segundo dígito.
- CNPJ: A lógica é parecida, porem possui algumas mudanças. Pro primeiro dígito, multiplica os 12 primeiros números por uma lista que vai de 5 a 2 e depois de 9 a 2. Pro segundo dígito, faz a mesma conta incluindo o dígito que acabou de achar, usando os pesos de 6 a 2 e depois de 9 a 2.
- Como validação extra coloquei uma trava simples: se o documento tiver todos os números iguais, o código rejeita direto, porque a conta matemática deles bate, mas o documento é falso. Se estiver errado, a variável documento_valido vira false.

3. Quais inconsistências lógicas entre campos você implementou no Bloco 3 e no método tem_inconsistencia()? Por que escolheu essas e não outras?
R: Dentro do método tem_insconsistencias(), criei regras para cruzar as informações das colunas e pegar erros de digitação do sistema
- Identifiquei data de compara depois do vencimento, oque não faz sentindo, comprar um título que já venceu.
- Existiam alguns status errado em relação ao tempo, como tinhamos a data de corte e a data de vencimento já passou, o status não poderia ser 'a_vencer'. Do mesmo jeito, se o vencimento é no futuro, o status não pode estar como 'vencido'
- Encontrei parcelas igual ou menor que 0, algo que não faz sentindo, pois já deveria estar quitado.
- A ideia foi manter uma lógica simples e fácil de dar manutenção, utilzei encapsulamento assim, o scrip do processo so precisa chamar o método sem saber como a conta interna é feito. No caso de elevar o nível do projeto substituiria os if/else manuais por arquiteturas mais robustas, utilizando de classes separadas para cada regra de validação e poderia utilizar ate mesmos outras bibliotecas de dados para checagem dos dados logo na entrada.

4. No método taxa_inadimplencia() da classe Carteira, o que acontece se a carteira estiver vazia? Como você tratou esse caso?
R: Se o arquivo CSV viesse vazio ou todas as linhas fossem deletadas na limpeza ( Oque ocorreu no primeiro teste) a conta do valor total daria 0. Na hora do calculo o python tratia o erro ZeroDivisionError, travando o programa.
- Como tratamento coloquei uma verificação simples no começo do método:
if total == 0:
    return 0.0
Assim o código para neste exato momento, devolve 0.0 e evita erro e deixa o pipeline rodar até o final de forma segura.

5. Se você precisasse adaptar este pipeline para rodar diariamente de forma automatizada, o que mudaria na sua implementação?
R: Para essa mudança temos alguns pontos.
- Ao inves de realizar a leitura na minha pasta, mudaria o scrip para buscar o arquivo direto em um servidor de nuvem como AWS, usando a data do dia no nome do arquivo
- Em vez de salvar arquivos excel ou CSV na minha area de trabalho eu usaria o Pandas para salvar os dados corrigidos e os alertas diretos em tabelas de um banco de dados, para o time poder usar no Power BI
- Utilizaria o lambda para o script rodar toda madrugada, e colocaria um aviso por email caso tenha algum erro no caminho.

6. Se a carteira tivesse 10 milhões de linhas, o que mudaria na sua abordagem de leitura, validação e geração do relatório?
R: Neste caso para não termos erro, ao inves de fazer a leitura por inteiro, mudaria para leitura em pedaços, para diminuir o consumo de RAM.
- E mudaria o formato de saida ao inves de usar o excel usaria Parquet