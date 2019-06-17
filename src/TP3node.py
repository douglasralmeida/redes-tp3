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
def args_processar(parametros):
  temp = sys.argv[1].split(':')
  parametros['ip'] = temp[0]
  parametros['porta'] = int(temp[1])
  parametros['bd'] = sys.argv[2]
  i = len(sys.argv) 
  if i > 3:
    j = i
    while (j > 2):
      parametros['servidores'] = sys.argv[3]

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
  args_processar(parametros)