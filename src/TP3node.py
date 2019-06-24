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
MSG_KEYREQ			= 5
MSG_TOPOREQ			= 6
MSG_KEYFLOOD		= 7
MSG_TOPOFLOOD		= 8
MSG_RESP			= 9
EXIBIR_LOG          = True

# VARIÁVEIS DO PROGRAMA
# =====================
parametros = {'ip': '', 'porta': 0, 'timeout': 6, 'servidores': {}, 'bd': ''}
bd = {}
mensagens = None
soquetes = None

# CLASSES DO PROGRAMA
# ===================
# Dados no formato de transmissão
class Dados():
	def __init__(self):
		self.pos = 0
		self.valor = bytearray()
		self.texto = "".encode("ascii", "ignore")

	def apensarInt(self, numero):
		bytesvalor = bytearray(pack("!I", int(numero)))
		self.valor += bytesvalor

	def apensarShort(self, numero):
		bytesvalor = bytearray(pack("!H", int(numero)))
		self.valor += bytesvalor

	def apensarTexto(self, texto):
		self.texto = texto.encode("ascii", "ignore")

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

	def extrairText(self):
		return self.texto.decode("ascii")

	@staticmethod
	def paraInt(bytesarray):
		return unpack('!I', bytesarray)[0]

	@staticmethod
	def paraShort(bytesarray):
		return unpack('!H', bytesarray)[0]

	def definir(self, novovalor, novotexto):
		self.valor = novovalor
		self.texto = novotexto

	def obter(self):
		return self.valor, self.texto

# Gerador de mensagens
class Mensagens():
	def __init__(self, modoservent):
		self.numseq = 0
		self.modoservent = modoservent
		self.ttlpadrao = 3

	def gerar(self, id):
		dados = Dados()
		dados.apensarShort(id)

		return dados

	def gerarId(self):		
		dados = self.gerar(MSG_ID)
		if self.modoservent:
			log("Enviando pedido de conexão.")
			dados.apensarZero(2)
		else:
			dados.apensarShort(parametros['porta'])

		return dados.obter()

	def gerarKeyReq(self, texto):
		dados = self.gerar(MSG_KEYREQ)
		# sequencial
		dados.apensarInt(self.numseq)
		self.numseq += 1
		#texto
		dados.apensarShort(len(texto))
		dados.apensarTexto(texto)

		return dados.obter()

	def gerarTopoReq(self):
		dados = self.gerar(MSG_TOPOREQ)
		# sequencial
		dados.apensarInt(self.numseq)
		self.numseq += 1

		return dados.obter()

	def gerarKeyFlood(self, cliente):
		dados = self.gerar(MSG_KEYFLOOD)
		# ttl
		dados.apensarShort(self.ttlpadrao)
		# sequencial
		dados.apensarInt(cliente.numseq)
		# ip e porta
		dados.apensarInt(cliente.ip)
		dados.apensarShort(cliente.porta)
		#texto
		dados.apensarShort(len(cliente.texto))
		dados.apensarTexto(cliente.texto)

		return dados.obter()

	def gerarTopoFlood(self, cliente):
		dados = self.gerar(MSG_TOPOFLOOD)
		# ttl
		dados.apensarShort(self.ttlpadrao)
		# sequencial
		dados.apensarInt(cliente.numseq)
		# ip e porta
		dados.apensarInt(cliente.ip)
		dados.apensarShort(cliente.porta)
		#texto
		dados.apensarShort(len(cliente.texto))
		dados.apensarTexto(cliente.texto)

		return dados.obter()

	def gerarResp(self, numseq, texto):
		dados = self.gerar(MSG_RESP)
		log("Enviando resposta '{0}'.".format(texto))
		# sequencial
		dados.apensarInt(numseq)
		#texto
		dados.apensarShort(len(texto))
		dados.apensarTexto(texto)

		return dados.obter()

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
		log("Servente {0} na porta {1}.".format(parametros['ip'], parametros['porta']))

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
			serventes.adicionar(ip, porta)
			# Envia msg de ID
			dados, texto = mensagens.gerarId()
			self.enviarDados(con, dados, texto)

	def enviarDados(self, conexao, dados, texto):
		endereco = conexao.getpeername()
		conexao.sendall(dados)
		if len(texto) > 0:
			conexao.sendall(texto)
		log("Dados para {0}.".format(endereco))

	def receberDados(self, conexao):
		dadotipo = conexao.recv(2)
		endereco = conexao.getpeername()
		if not dadotipo:
			return False
		tipo = Dados.paraShort(dadotipo)
		log("Dados de {0}.".format(endereco))
		self.receberDadosComo[tipo](conexao, endereco)

		return True

	def receberId(self, conexao, endereco):
		dadoporta = conexao.recv(2)
		porta = Dados.paraShort(dadoporta)
		if porta > 0:
			log("Pedido de conexão de um cliente {0} na porta {1}.".format(endereco[0], porta))
		else:
			log("Pedido de conexão de um servente {0} na porta {1}.".format(endereco[0], endereco[1]))
			serventes.adicionar(endereco[0], endereco[1])

			# -- TESTE -- #
			if EXIBIR_LOG:
				dados, texto = mensagens.gerarResp(0, "qualquer resposta")
				self.enviarDados(conexao, dados, texto)
			

	def receberKeyReq(self, conexao, endereco):
		dados = conexao.recv(6)
		seq = Dados.paraInt(dados[:4])
		tam = Dados.paraShort(dados[4:6])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Pedido de consulta com a chave X e num seq {0}.".format(seq))

	def receberTopoReq(self, conexao, endereco):
		dados = conexao.recv(4)
		seq = Dados.paraInt(dados)
		log("Pedido de topologia com num seq {0}.".format(seq))
	
	def receberKeyFlood(self, conexao, endereco):
		dados = conexao.recv(14)
		ttl = Dados.paraShort(dados[:2])
		seq = Dados.paraInt(dados[2:6])
		iporigem = Dados.paraInt(dados[6:10])
		portaorigem = Dados.paraShort(dados[10:12])
		tam = Dados.paraShort(dados[12:14])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Pedido de alagamento para consulta com a chave X com num seq {0}.".format(seq))
	
	def receberTopoFlood(self, conexao, endereco):
		dados = conexao.recv(14)
		ttl = Dados.paraShort(dados[:2])
		seq = Dados.paraInt(ados[2:6])
		iporigem = Dados.paraInt(dados[6:10])
		portaorigem = Dados.paraShort(dados[10:12])
		tam = Dados.paraShort(dados[12:14])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Pedido de alagamento para topoologia com num seq {0}.".format(seq))
	
	def receberResp(self, conexao, endereco):
		dados = conexao.recv(6)
		seq = Dados.paraInt(dados[:4])
		tam = Dados.paraShort(dados[4:6])
		texto = conexao.recv(tam)
		# falta decodificar
		log("Resposta '{0}' com num seq {1}.".format(texto.decode("ascii"), seq))

	def receberNada(self, conexao, endereco):
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
					if not self.receberDados(s):
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
	# inicia o gerenciador de msgs no modo servente
	mensagens = Mensagens(True)
	serventes = Serventes()
	soquetes = Soquetes()
	if len(parametros['servidores']) > 0:
		soquetes.conectarAtivamente(parametros['servidores'])
	soquetes.manipular()