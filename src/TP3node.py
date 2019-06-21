# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP3 de Redes - Nó da Rede
# Douglas R. Almeida

import Queue
import select
import socket
import sys

# CONSTANTES DO PROGRAMA
# ======================
EXIBIR_LOG         = True

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'ip': '127.0.0.1', 'porta': 0, 'timeout': 6, 'servidores': {}, 'bd': ''}
bd = {}
soquetes = None

# CLASSES DO PROGRAMA
# ===================
# Gerencia vários soquetes
class Soquetes():
	def __init__(self):
		self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		endereco = (parametros['ip'], parametros['porta'])
		servidor.setblocking(0)
		servidor.bind(endereco)
		servidor.listen()
		self.entradas = [servidor]

	def novocliente(self, conexao):
		conexao.setblocking(0)
		self.entradas.append(conexao)
		self.fila_mensagens[conexao] = Queue.Queue()

	def removercliente(self, conexao):
		self.entradas.remove(conexao)
		conexao.close()
		del self.filas_mensagens[conexao]

	def manipular(self):
		while (self.entradas):
			# Aguarda por soquetes que estão prontos para processamento
			l, e, x = select.select(self.entradas, [], self.entradas)

			# Fazer coisas aqui

			if not (l or x):
				continue
			
			# Soquetes prontos para leitura
			for s in l:
				if s is self.servidor:
					# soquete que aguarda por novas conexões
					con, endereco = s.accept()
					self.novocliente(con)
				else:
					# soquete que aguarda por dados de consulta
					dados = s.recv(2)
					if dados:
						#processar os dados aqui...
						print(dados)
					else:
						self.removercliente(s)
					
			# Soquetes com erros
			for s in x:
				self.removercliente(s)

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
	soquetes = Soquetes()
	soquetes.manipular()