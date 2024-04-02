import h5py
from parametros import * 

def obterNivelCompressao(compressao=parametros['geral']['compressao']):
    saida = None
    if compressao=='gzip' : saida = 9
    return saida

def criarHDF5Vazio(hdf5File, tamanho, grupos=['principal'], datasets=['dado', 'rotulo'], compressao=parametros['geral']['compressao']):
    nvlComp = obterNivelCompressao() #É usado apenas para compressão do tipo gzip. Para mais detalhes: https://docs.h5py.org/en/stable/high/dataset.html
    with h5py.File(hdf5File, 'w') as f:
        for gp in grupos:
            grupo = f.create_group(gp)  # Cria um grupo com o nome especificado
            for ds in datasets:
                if isinstance(tamanho, int): tamanho = [tamanho]
                if nvlComp is None: grupo.create_dataset(ds,shape=(0, tamanho[0], tamanho[-1]), maxshape=(None, tamanho[0], tamanho[-1]), compression=compressao)
                else: grupo.create_dataset(ds,shape=(0, tamanho[0], tamanho[-1]), maxshape=(None, tamanho[0], tamanho[-1]), compression=compressao, compression_opts=nvlComp)
    return hdf5File

def carregarHDF5(hdf5File, indices=None, grupo='principal', datasets=['dado', 'rotulo']):
    saida = []
    with h5py.File(hdf5File, 'r') as f:
        gp = f[grupo]  # Acessa o grupo com o nome especificado
        for ds in datasets:
            if indices is None: info = gp[ds][:]  # Se os índices forem None, carrega todo o dataset
            else:
                data = gp[ds]
                tamanho = len(data)
                if isinstance(indices, int): indices = [indices] # Se o índice for um único número inteiro, converte para uma lista
                start = indices[0]
                end = min(tamanho, indices[-1])
                info = data[int(start):int(end)] # Carrega o dataset do índice inicial ao índice final
            saida.append(info)
    return saida
 
def incrementarHDF5(hdf5File, dadosNovos, grupo='principal', datasets=['dado', 'rotulo']): #Sendo dadosNovos uma lista de listas = [[],[], ...]
    with h5py.File(hdf5File, 'a') as f:
        gp = f[grupo]  # Acessa o grupo com o nome especificado
        for dadoNovo, ds in zip(dadosNovos, datasets):
            dados = gp[ds]
            dadosAntigosShape = dados.shape # Obtem o tamanho atual dos datasets
            dados.resize((dadosAntigosShape[0] + len(dadoNovo), *dadosAntigosShape[1:])) # Extende os datasets
            dados[dadosAntigosShape[0]:] = dadoNovo # Adiciona os novos dados

def lenHDF5(hdf5File, dataset='dado', grupo='principal'):
    with h5py.File(hdf5File, 'r') as f:
        gp = f[grupo]
        data = gp[dataset]
        qnt = len(data)
    return qnt

def sobrescreverHDF5(hdf5File, dadosNovos, grupo='principal', datasets=['dado', 'rotulo']):
    with h5py.File(hdf5File, 'a') as f:
        gp = f[grupo]  # Acessa o grupo com o nome especificado
        for dadoNovo, ds in zip(dadosNovos, datasets):
            dados = gp[ds]
            tamanhoDadosNovos, tamanhoDadosAntigos = len(dadoNovo), dados.shape[0]
            if tamanhoDadosNovos > tamanhoDadosAntigos: dados.resize((tamanhoDadosNovos, *dados.shape[1:]))
            dados[:tamanhoDadosNovos] = dadoNovo  # Sobrescreve os dados existentes