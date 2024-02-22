'''
                           ooooo          .oooooo.    .oooooo..o 
                            `888'         d8P'  `Y8b  d8P'    `Y8     ++#==========================================#++
                             888         888      888 Y88bo.             LABORATÓRIO DE OCEANOGRAFIA POR SATÉLITE
                             888         888      888  `"Y8888o.       ALGORITMO CONSTRUTOR DE DATASET - VERSÃO 2.0  
                             888         888      888      `"Y88b      Autor: __David Oliveira__    Data: 21/02/2024
                             888       o `88b    d88' oo     .d8P     ++#==========================================#++
                            o888ooooood8  `Y8bood8P'  8""88888P
'''                 
parametros = {
    
    'diretorios': {
        'netcdfs':       r"/mnt/camobi_process/david/NETCDFs/",            #Dados.
        'jsons':         r"/mnt/camobi_process/david/JSONs/",              #Rotulos.
        'temporarios':   r"/mnt/camobi_process/david/TEMPs/",            
        'dataset':       r"/mnt/camobi_process/david/DATASETs/",
        'grafos':        r"/home/los/david/Graphs/",
        'gpt':           r"/home/camobi/snap/bin/gpt",
    },
     
    'geral': {
        'tamanhos':          [64, 128, 256, 512],  #Refere-se aos tamanhos de cada pacote durante o recorte. (Para cada tamanho um conj. de dados é gerado).
        'limiteResolucao':   512,                  #Refere-se ao valor limite antes que o redimensionamento atue, reduzindo o tamanho para este valor.
        'limiar':            0.1,                  #Refere-se ao percentual mínimo de pixels que uma fatia deve aparesentar para ser considerado al, vo.
        'probabilidade':     1.0,                  #Refere-se a probabilidade de realizar o aumento dos dados para cada uma das rotações e espelhamentos.
        'retirarSolo':       False,                #Se verdadeiro, o código retira os pixels de solo do NetCDF antes de fatiar.
        'aprimorarRotulo':   False,                #Se verdadeiro, mapeia todo oceano e terreno nos rotulos considerando os pixels de solo do netcdf.
        'retirarExcessos':   True,                 #Se verdadeiro, a imagem será cortada na região de interesse, onde estão os poligonos.
        'manterVazios':      False,                #Se verdadeiro, os pacotes formados com apenas classe null são mantidos durante o corte.
        'realizarAumento':   True,                 #Se verdadeiro, realiza o aumento na classe alvo. (Usa apenas rotações em angulo retos e espelhamentos).
        'redimensionar':     True,                 #Se verdadeiro, reduz a resolução das fatias para valores menores.
        'modoRetirarSolo':   'glmWithNE',          #Seleciona o modo de remoção de pixels de solo. (Ex: 'glmWithNE' Velocidade, 'snap' Qualidade). 
        'compressao':        'lzf',                #Seleciona o filtro de compressão para arquivos HDF5. (Ex:'gzip' Menos espaço, 'lzf' Mais rápido)
        'classeAlvo':        'oil',                
        'classesAumentadas': ['oil', 'ship', 'wind'],
    },

    'visualizar': {
        'plotarSemExcessos':       False,      #Se verdadeiro realiza o plot das labels durante a remoção dos excessos.
        'exibirQuantidadeFatias':  False,      #Se verdadeiro exibe o total de fatias que foram obtidas após o recorte dos dados e rótulos.
        'detalharFiltragem':       True,       #Se verdadeiro exibe detalhes sobre a etapa de filtragem das classes.
    },

    'classes': { #A ordem em que as classes aparecem nesse arquivo define a prioridade na outra de filtrar. Utilize o alvo em primeiro lugar.
        'oil':          {'valor': 1, 'cor': '#7A6352', 'indicadores': ['oil', 'oilspill']},
        'wind':         {'valor': 6, 'cor': '#FF643F', 'indicadores': ['wind', 'lowwind']},
        'biofilm':      {'valor': 5, 'cor': '#05FF58', 'indicadores': ['biofilm', 'phyto', 'phytoplancton', 'chlorophyll']},
        'ship':         {'valor': 4, 'cor': '#E2E2E2', 'indicadores': ['ship', 'boat']},
        'rain':         {'valor': 7, 'cor': '#0066FF', 'indicadores': ['rain', 'rainfall']},
        'lookalike':    {'valor': 8, 'cor': '#CEA24A', 'indicadores': ['lookalike', 'darkocean']},
        'land':         {'valor': 3, 'cor': '#FFFF99', 'indicadores': ['ground', 'land', 'darkland']},
        'ocean':        {'valor': 2, 'cor': '#66CCFF', 'indicadores': ['ocean', 'sea', 'water']},
        'null':         {'valor': 0, 'cor': '#FF00FF', 'indicadores': []},
    },

    # O VALOR é responsável por associar a cada classe um valor discreto. Lembre-se sempre de habilitar a conversão se o alterar os valores das classes.
    # Em COR é definida a cor em hexadecimal que aparece nos plots do rótulos com um colormap custom.
    # Os INDICADORES são responsáveis por indicar as strings válidas, para cada classe. Poligonos com rótulos diferentes são ignorados.
}
