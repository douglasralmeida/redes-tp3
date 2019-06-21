# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP3 de Redes - Nó da Rede
# Douglas R. Almeida

import socket
import sys

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'ip': '127.0.0.1', 'porta': 0, 'timeout': 6, 'servidores': {}, 'bd': ''}
bd = {}

# FUNCOES DO PROGRAMA
# ===================
def log(*args, **kwargs):
    if EXIBIR_LOG:
        print(*args, file=sys.stderr, **kwargs)

# -----------------------------------------
# Lê os argumentos do programa
# arg1 = ip:porta
# arg2 = arquivo com banco de dados
# arg3 = opcional, servidores (até 10) para conectar
#   parametros = dicionario onde serão gravados os argumentos
def args_processar():
    temp = sys.argv[1].split(':')
    parametros['ip'] = temp[0]
    parametros['porta'] = int(temp[1])
    parametros['bd'] = sys.argv[2]
    i = len(sys.argv) 
    if i > 3:
        j = 3
        while (j < i):
            temp = sys.argv[j].split(':')
            parametros['servidores']['ip'] = temp[0]
            parametros['servidores']['porta'] = temp[1]
            j = j + 1

def bd_carregar():
	nomearquivo = parametros['bd']
	for linha in open(nomearquivo, 'rt'):
		if not linha.startswith('#'):
			yield linha

def bd_processar():
	linhas = bd_carregar()
	for l in linhas:
		i = l.find(' ')
		chave = l[0:i]
		bd[chave] = l[i:].lstrip().strip('\n')

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
	args_processar()
	bd_processar()
	print(bd)