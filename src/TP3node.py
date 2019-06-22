# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP3 de Redes - Nó da Rede
# Douglas R. Almeida

import queue
import select
import socket
from struct import pack, unpack
import sys

# CONSTANTES DO PROGRAMA
# ======================
MSG_ID 				= 4
EXIBIR_LOG          = True

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'ip': '', 'porta': 0, 'timeout': 6, 'servidores': {}, 'bd': ''}
bd = {}
soquetes = None

# CLASSES DO PROGRAMA
# ===================
# Conversor bytes/int
class Bytes():
	def __init__(self):
		self.pos = 0
		self.valor = bytearray()

	def apensarInt(self, numero):
		bytesvalor = bytearray(pack('!I', int(numero)))
		self.valor += bytesvalor

	def apensarShort(self, numero):
		bytesvalor = bytearray(pack('!H', int(numero)))
		self.valor += bytesvalor

	def apensarZero(self, quantidade):
		for i in range(quantidade):
			self.valor.append(0)

	def extrairInt(self):
		pos1 = self.pos
		pos2 = self.pos + 4
		self.pos = pos2
		return Bytes.paraInt(self.valor[pos1:pos2])

	def extrairShort(numero):
		pos1 = self.pos
		pos2 = self.pos + 2
		self.pos = pos2
		return Bytes.paraShort(self.valor[pos1:pos2])

	@staticmethod
	def paraInt(bytesarray):
		return unpack('!I', bytesarray)[0]

	@staticmethod
	def paraShort(bytesarray):
		return unpack('!H', bytesarray)[0]

	def obterBytes(self):
		return self.valor

	def definirBytes(self, novovalor):
		self.valor = novovalor


# Gerador de mensagens
class Mensagens():
	@staticmethod
	def gerarId():
		bytesParaEnviar = Bytes()
		bytesParaEnviar.apensarShort(MSG_ID)
		bytesParaEnviar.apensarZero(2)

		return bytesParaEnviar.obterBytes()

# Gerencia a lista de serventes
class Serventes():
	def __init__(self):
		self.lista = {}

	def adicionar(self, ip, porta):
		self.lista[ip] = porta

# Gerencia vários soquetes
class Soquetes():
	def __init__(self):
		endereco = (parametros['ip'], parametros['porta'])
		self.filas_mensagens = {}
		self.receberDadosComo = [
  			self.receberNada,
			self.receberNada,
			self.receberNada,
			self.receberNada,
			self.receberId,
			self.receberKeyReq,
			self.receberTopoReq,
			self.receberKeyFlood,
			self.receberTopoFlood,
			self.receberResp
		]
		self.servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.servidor.setblocking(0)
		self.servidor.bind(endereco)
		self.servidor.listen()
		self.entradas = [self.servidor]

	def adicionarCliente(self, conexao):
		conexao.setblocking(0)
		self.entradas.append(conexao)
		self.filas_mensagens[conexao] = queue.Queue()

	def conectarAtivamente(self, servidores):
		for (ip, porta) in servidores.items():
			dest = (ip, porta)
			con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			con.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			con.connect(dest)
			self.adicionarCliente(con)
			con.sendall(Mensagens.gerarId())

	def receberDados(self, conexao):
		bytetipo = conexao.recv(2)
		if not bytetipo:
			return False
		tipo = Bytes.paraShort(bytetipo)
		self.receberDadosComo[tipo](conexao)

		return True

	def receberId(self, conexao):
		byteporta = conexao.recv(2)
		porta = Bytes.paraShort(byteporta)
		if porta > 0:
			log("Pedido de conexão de um cliente.")
		else:
			log("Pedido de conexão de um servente.")

	def receberKeyReq(self, conexao):
		bytedados = conexao.recv(6)
		seq = Bytes.paraInt(bytedados[:3])
		tam = Bytes.paraShort(bytedados[4:5])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Pedido de consulta com a chave X e num seq {0}.".format(seq))

	def receberTopoReq(self, conexao):
		bytedados = conexao.recv(4)
		seq = Bytes.paraInt(bytedados)
		log("Pedido de topologia com num seq {0}.".format(seq))
	
	def receberKeyFlood(self, conexao):
		bytedados = conexao.recv(14)
		ttl = Bytes.paraShort(bytedados[:1])
		seq = Bytes.paraInt(bytedados[2:5])
		tam = Bytes.paraShort(bytesdados[12:13])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Pedido de alagamento para consulta com a chave X com num seq {0}.".format(seq))
	
	def receberTopoFlood(self, conexao):
		bytedados = conexao.recv(14)
		ttl = Bytes.paraShort(bytedados[:1])
		seq = Bytes.paraInt(bytedados[2:5])
		tam = Bytes.paraShort(bytesdados[12:13])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Pedido de alagamento para topoologia com num seq {0}.".format(seq))
	
	def receberResp(self, conexao):
		bytedados = conexao.recv(6)
		seq = Bytes.paraInt(bytedados[:3])
		tam = Bytes.paraShort(bytesdados[4:5])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Resposta com num seq {0}.".format(seq))

	def receberNada(self, conexao):
		log("Ops!")

	def removerCliente(self, conexao):
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
					self.adicionarCliente(con)
				else:
					# soquete que aguarda por dados de entrada
					if self.receberDados(s):
						#processar os dados aqui...
						print("OK")
					else:
						self.removerCliente(s)
					
			# Soquetes com erros
			for s in x:
				self.removerCliente(s)

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
            parametros['servidores'][temp[0]] = int(temp[1])
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
	serventes = Serventes()
	soquetes = Soquetes()
	if len(parametros['servidores']) > 0:
		soquetes.conectarAtivamente(parametros['servidores'])
	soquetes.manipular()