'''
                           ooooo          .oooooo.    .oooooo..o 
                            `888'         d8P'  `Y8b  d8P'    `Y8     ++#==========================================#++
                             888         888      888 Y88bo.             LABORATÓRIO DE OCEANOGRAFIA POR SATÉLITE
                             888         888      888  `"Y8888o.       ALGORITMO CONSTRUTOR DE DATASET - VERSÃO 2.1  
                             888         888      888      `"Y88b      Autor: __David Oliveira__    Data: 23/03/2024
                             888       o `88b    d88' oo     .d8P     ++#==========================================#++
                            o888ooooood8  `Y8bood8P'  8""88888P
'''                 
parametros = {
    
    'diretorios': {
        'netcdfs':       r"/mnt/camobi_2/david/NETCDFs/",            #Dados.
        'jsons':         r"/mnt/camobi_2/david/JSONs/",              #Rotulos.
        'temporarios':   r"/mnt/camobi_2/david/TEMPs/",            
        'dataset':       r"/mnt/camobi_2/david/DATASETs/",
        'grafos':        r"/home/los/david/Graphs/",
        'gpt':           r"/home/camobi/snap/bin/gpt",
    },
     
    'geral': {
        'tamanhos':          [64],                 #Refere-se aos tamanhos de cada pacote durante o recorte. (Para cada tamanho um conj. de dados é gerado).
        'limiar':            0.1,                  #Refere-se ao percentual mínimo de pixels que uma fatia deve aparesentar para ser considerado alvo.
        'probabilidade':     1.0,                  #Refere-se a probabilidade de realizar o aumento dos dados para cada uma das rotações e espelhamentos.
        'retirarSolo':       False,                #Se verdadeiro, o código retira os pixels de solo do NetCDF antes de fatiar.
        'aprimorarRotulo':   False,                #Se verdadeiro, mapeia todo oceano e terreno nos rotulos considerando os pixels de solo do netcdf.
        'retirarExcessos':   True,                 #Se verdadeiro, a imagem será cortada na região de interesse, onde estão os poligonos.
        'manterVazios':      False,                #Se verdadeiro, os pacotes formados com apenas classe null são mantidos durante o corte.
        'realizarAumento':   True,                 #Se verdadeiro, realiza o aumento na classe alvo. (Usa apenas rotações em angulos retos e espelhamentos).
        'modoRetirarSolo':   'glmWithNE',          #Seleciona o modo de remoção de pixels de solo. (Ex: 'glmWithNE' Mais rápido, 'snap' Maior qualidade). 
        'compressao':        'lzf',                #Seleciona o filtro de compressão para arquivos HDF5. (Ex:'gzip' Menos espaço, 'lzf' Mais rápido)
        'classeAlvo':        'oil',
    },

    'visualizar': {
        'plotarSemExcessos':       False,      #Se verdadeiro realiza o plot das labels durante a remoção dos excessos.
        'exibirQuantidadeFatias':  False,      #Se verdadeiro exibe o total de fatias que foram obtidas após o recorte dos dados e rótulos.
        'detalharFiltragem':       True,       #Se verdadeiro exibe detalhes sobre a etapa de filtragem das classes.
        'detalharConstrucao':      False,      #Se verdadeiro exibe detalhes sobre a etapa final de construção do conjunto de dados.
    },

    'classes': { #A ordem em que as classes aparecem nesse arquivo define a prioridade na outra de filtrar.
        'oil':          {'valor': 1, 'cor': '#7A6352', 'proporcao': 0.60, 'indicadores': ['oil', 'oilspill']},
        'ship':         {'valor': 3, 'cor': '#E2E2E2', 'proporcao': 0.05, 'indicadores': ['ship', 'boat']},
        'wind':         {'valor': 2, 'cor': '#FF643F', 'proporcao': 0.10, 'indicadores': ['wind', 'lowwind']},
        'lookalike':    {'valor': 4, 'cor': '#CEA24A', 'proporcao': 0.10, 'indicadores': ['lookalike', 'darkocean']},
        'ocean':        {'valor': 5, 'cor': '#66CCFF', 'proporcao': 0.10, 'indicadores': ['ocean', 'sea', 'water']},
        'land':         {'valor': 6, 'cor': '#FFFF99', 'proporcao': 0.05, 'indicadores': ['ground', 'land', 'darkland']},
        'biofilm':      {'valor': 7, 'cor': '#05FF58', 'proporcao': 0.00, 'indicadores': ['biofilm', 'phyto', 'phytoplancton', 'chlorophyll']},
        'rain':         {'valor': 8, 'cor': '#0066FF', 'proporcao': 0.00, 'indicadores': ['rain', 'rainfall']},
        'null':         {'valor': 0, 'cor': '#FF00FF', 'proporcao': 0.00, 'indicadores': []},
    },

    # O VALOR é responsável por associar a cada classe um valor discreto. Lembre-se sempre de habilitar a conversão se o alterar os valores das classes.
    # Em COR é definida a cor em hexadecimal que aparece nos plots do rótulos com um colormap custom.
    # Os INDICADORES são responsáveis por indicar as strings válidas, para cada classe. Poligonos com rótulos diferentes são ignorados.
}
