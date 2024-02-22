import numpy as np
from python.auxiliares import *
from python.etapas import *
from parametros import * 

for tamanho in parametros['geral']['tamanhos']:
    hdf5Fatiados = recortarEmFatias(tamanho=tamanho)
    hdf5Filtrados = separarFatiasPorClasses(hdf5Fatiados, tamanho)
    if parametros['geral']['realizarAumento']: hdf5Filtrados = aumentoDeDadosHDF5(hdf5Filtrados, tamanho)
    datasetHDF5 = criarConjuntoDeDados(hdf5Filtrados, tamanho)
    deletarPastas([parametros['diretorios']['temporarios']])