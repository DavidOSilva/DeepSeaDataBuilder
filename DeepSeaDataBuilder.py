from python.steps import *
from python.filesManager import *
from parametros import * 

for tamanho in parametros['geral']['tamanhos']:
    hdf5Fatiados = recortarEmFatias(tamanho=tamanho)
    hdf5Filtrados = separarFatiasPorClasses(hdf5Fatiados, tamanho)
    hdf5Filtrados, classesAumentadas = aumentoDeDadosHDF5(hdf5Filtrados, tamanho)
    datasetHDF5 = criarConjuntoDeDados(hdf5Filtrados, tamanho, classesAumentadas)
    deletarPastas([parametros['diretorios']['temporarios']])