# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP3 de Redes - Nó da Rede
# Douglas R. Almeida

## TODO: Implementar try..except no sendall para clientes

from collections import namedtuple
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
EXIBIR_LOG          = False

# VARIÁVEIS DO PROGRAMA
# =====================
bd = None
Cliente = namedtuple("Cliente", ["numseq", "ip", "porta", "texto"])
clientes = None
historico = None
mensagens = None
parametros = {'ip': '', 'porta': 0, 'timeout': 6, 'servidores': {}, 'bd': ''}
remetentes = None
soquetes = None

# CLASSES DO PROGRAMA
# ===================
# Banco de Dados do servente
class BancoDados():
	def __init__(self):
		self.dados = {}
		linhas = self.carregar()
		for l in linhas:
			i = l.find(' ')
			chave = l[0:i]
			self.dados[chave] = l[i:].lstrip().strip('\n')

	def carregar(self):
		nomearquivo = parametros['bd']
		for linha in open(nomearquivo, 'rt'):
			if not linha.startswith('#'):
				yield linha

	def contem(self, chave):
		return (chave in self.dados)

	def pesquisar(self, chave):
		return self.dados[chave]

# Gerencia a lista de clientes conectados
class Clientes():
	def __init__(self):
		self.portas = dict()

	def adicionar(self, ip, portaescuta):
		self.portas[ip] = portaescuta

	def obterPorta(self, ip):
		return self.portas[ip]

# Dados no formato de transmissão
class Dados():
	def __init__(self):
		self.pos = 0
		self.valor = bytearray()
		self.texto = "".encode("ascii", "ignore")

	def apensarInt(self, numero):
		bytesvalor = bytearray(pack("!I", int(numero)))
		self.valor += bytesvalor
	
	def apensarIp(self, ip):
		ipint = unpack("!I", socket.inet_aton(ip))[0]
		bytesvalor = bytearray(pack("!I", int(ipint)))
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

	def extrairIp(self):
		pos1 = self.pos
		pos2 = self.pos + 4
		self.pos = pos2
		return Bytes.paraIp(self.valor[pos1:pos2])

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
	def paraIp(bytesarray):
		ipint = unpack('!I', bytesarray)[0]
		return socket.inet_ntoa(pack("!I", ipint))

	@staticmethod
	def paraShort(bytesarray):
		return unpack('!H', bytesarray)[0]

	def definir(self, novovalor, novotexto):
		self.valor = novovalor
		self.texto = novotexto

	def obter(self):
		return self.valor + self.texto

# Gerador de mensagens
class Mensagens():
	def __init__(self, modoservent):
		self.numseq = 0
		self.modoservent = modoservent

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
			dados.apensarShort(parametros['portaescuta'])

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

	def gerarKeyFlood(self, cliente, ttl = 3):
		dados = self.gerar(MSG_KEYFLOOD)
		# ttl
		dados.apensarShort(ttl)
		# sequencial
		dados.apensarInt(cliente.numseq)
		# ip e porta
		dados.apensarIp(cliente.ip)
		dados.apensarShort(cliente.porta)
		#texto
		dados.apensarShort(len(cliente.texto))
		dados.apensarTexto(cliente.texto)

		return dados.obter()

	def gerarTopoFlood(self, cliente, ttl = 3):
		dados = self.gerar(MSG_TOPOFLOOD)
		# ttl
		dados.apensarShort(ttl)
		# sequencial
		dados.apensarInt(cliente.numseq)
		# ip e porta
		dados.apensarIp(cliente.ip)
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

# Manipula o envio de mensagens
class Remetente():
	def __init__(self, conexao):
		self.conexao = conexao

	@staticmethod
	def alagar(dados):
		log("Processando alagamento ({0} soquetes)...".format(len(serventes)))
		for soq in serventes:
			soq.sendall(dados)
		log("Processado.")

	def processar(self, dados):
		endereco = self.conexao.getpeername()
		self.conexao.sendall(dados)
		log("Dados para servente {0}.".format(endereco))

	@staticmethod
	def enviarAoCliente(endereco, dados):
		despachante = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		despachante.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		try:
			despachante.connect(endereco)
			despachante.sendall(dados)
			despachante.close()
		except:
			pass

		log("Dados para cliente {0}.".format(endereco))

# Manipula o recebimento de respostas
class Recebedor():
	def  __init__(self, conexao):
		self.conexao = conexao
		self.endereco = conexao.getpeername()
		self.processarComo = [
  		self.processarNada,
			self.processarNada,
			self.processarNada,
			self.processarNada,
			self.processarId,
			self.processarKeyReq,
			self.processarTopoReq,
			self.processarKeyFlood,
			self.processarTopoFlood,
			self.processarResp
		]

	def processar(self):
		dadotipo = self.conexao.recv(2)
		if not dadotipo:
			app_sair()
		tipo = Dados.paraShort(dadotipo)
		log("Dados de {0}.".format(self.endereco))
		self.processarComo[tipo]()

	def processarId(self):
		dadoporta = self.conexao.recv(2)
		porta = Dados.paraShort(dadoporta)
		if porta > 0:
			log("Pedido de conexão de um cliente {0} que houve na porta {1}.".format(self.endereco[0], porta))
			clientes.adicionar(self.endereco[0], porta)
		else:
			log("Pedido de conexão de um servente {0} na porta {1}.".format(self.endereco[0], self.endereco[1]))
			serventes.adicionar(self.conexao)

	def processarKeyReq(self):
		dados = self.conexao.recv(6)
		seq = Dados.paraInt(dados[:4])
		tam = Dados.paraShort(dados[4:6])
		texto = self.conexao.recv(tam).decode("ascii")
		ip = self.endereco[0]
		porta = self.endereco[1]
		portaescuta = clientes.obterPorta(ip)
		tupla = (ip, portaescuta, seq)
		historico.add(tupla)
		log("Pedido de consulta com a chave '{0}' e num seq {1}.".format(texto, seq))
		# consulta dicionário e responde
		if bd.contem(texto):
			resposta = bd.pesquisar(texto) 
			msg = mensagens.gerarResp(seq, resposta)
			Remetente.enviarAoCliente((ip, portaescuta), msg)
		# gera um KeyFlood para alagamento
		cliente = Cliente(seq, ip, portaescuta, texto)
		msg = mensagens.gerarKeyFlood(cliente)
		Remetente.alagar(msg)

	def processarTopoReq(self):
		dados = self.conexao.recv(4)
		seq = Dados.paraInt(dados)
		ip = self.endereco[0]
		porta = self.endereco[1]
		portaescuta = clientes.obterPorta(ip)
		tupla = (ip, portaescuta, seq)
		historico.add(tupla)
		log("Pedido de topologia com num seq {0}.".format(seq))
		# responde ao cliente
		resposta = "{0}:{1}".format(parametros["ip"], parametros["porta"])
		msg = mensagens.gerarResp(seq, resposta)
		Remetente.enviarAoCliente((ip, portaescuta), msg)
		# gera um TopoFlood para alagamento
		cliente = Cliente(seq, ip, portaescuta, resposta)
		msg = mensagens.gerarTopoFlood(cliente)
		Remetente.alagar(msg)
	
	def processarKeyFlood(self):
		dados = self.conexao.recv(14)
		ttl = Dados.paraShort(dados[:2])
		seq = Dados.paraInt(dados[2:6])
		iporigem = Dados.paraIp(dados[6:10])
		portaorigem = Dados.paraShort(dados[10:12])
		tam = Dados.paraShort(dados[12:14])
		texto = self.conexao.recv(tam).decode("ascii")
		# Implementa alagamento confiavel
		# descartando msgs já vistas anteriormente
		tupla = (iporigem, portaorigem, seq)
		if tupla in historico:
			return
		historico.add(tupla)
		# consulta dicionário e responde
		if bd.contem(texto):
			resposta = bd.pesquisar(texto) 
			msg = mensagens.gerarResp(seq, resposta)
			Remetente.enviarAoCliente((iporigem, portaorigem), msg)
		# mata a msg se ttl for igual a zero
		if ttl == 0:
			return
		# gera um KeyFlood para alagamento
		cliente = Cliente(seq, iporigem, portaorigem, texto)
		msg = mensagens.gerarKeyFlood(cliente, ttl - 1)
		Remetente.alagar(msg)
		log("Pedido de alagamento para consulta com a chave '{0}' com num seq {1}.".format(texto, seq))
	
	def processarTopoFlood(self):
		dados = self.conexao.recv(14)
		ttl = Dados.paraShort(dados[:2])
		seq = Dados.paraInt(dados[2:6])
		iporigem = Dados.paraIp(dados[6:10])
		portaorigem = Dados.paraShort(dados[10:12])
		tam = Dados.paraShort(dados[12:14])
		texto = self.conexao.recv(tam).decode("ascii")
		# Implementa alagamento confiavel
		# descartando msgs já vistas anteriormente
		if (iporigem, portaorigem, seq) in historico:
			return
		historico.add((iporigem, portaorigem, seq))
		log("Pedido de topologia com num seq {0}.".format(seq))
		# responde ao cliente
		resposta = texto + ' ' + "{0}:{1}".format(parametros["ip"], parametros["porta"])
		msg = mensagens.gerarResp(seq, resposta)
		Remetente.enviarAoCliente((iporigem, portaorigem), msg)
		# mata a msg se ttl for igual a zero
		if ttl == 0:
			return
		# gera um TopoFlood para alagamento
		cliente = Cliente(seq, iporigem, portaorigem, resposta)
		msg = mensagens.gerarTopoFlood(cliente, ttl - 1)
		Remetente.alagar(msg)
		log("Pedido de alagamento para topoologia com num seq {0}.".format(seq))
	
	def processarResp(self):
		Resposta = namedtuple("Resposta", ["numseq", "texto", "ip", "porta"])
		dados = self.conexao.recv(6)
		seq = Dados.paraInt(dados[:4])
		tam = Dados.paraShort(dados[4:6])
		texto = self.conexao.recv(tam).decode("ascii")
		resposta = Resposta(seq, texto, self.endereco[0], self.endereco[1])
		log("Resposta inesperada {0} {1}:{2}".format(texto, endereco[0], endereco[1]))

	def processarNada(self, conexao, endereco):
		log("Ops!")

# Gerencia a lista de serventes
class Serventes():
	def __init__(self):
		self.index = 0
		self.lista = []

	# Interador sobre a lista de serventes
	def __iter__(self):
		self.index = 0
		return self

	def __len__(self):
		return len(self.lista)

	def __next__(self):
		if self.index >= len(self.lista):
			raise StopIteration
		self.index = self.index + 1
    
		return self.lista[self.index - 1]

	def adicionar(self, soquete):
		self.lista.append(soquete)

	def remover(self, soquete):
		if soquete in self.lista:
			del self.lista[soquete]

# Gerencia vários soquetes
class Soquetes():
	def __init__(self):		
		endereco = (parametros['ip'], parametros['porta'])
		self.conexaoativa = None
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

	def conectarAtivamente(self, servidores):
		for (ip, porta) in servidores.items():
			dest = (ip, porta)
			con = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			con.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			con.connect(dest)
			self.adicionarCliente(con)
			serventes.adicionar(con)
			# Envia msg de ID
			dados = mensagens.gerarId()
			remetente = Remetente(con)
			remetente.processar(dados)

	def removerCliente(self, conexao):
		self.entradas.remove(conexao)
		conexao.close()

	def manipular(self):
		while (self.entradas):
			# Aguarda por soquetes que estão prontos para processamento
			l, e, x = select.select(self.entradas, [], self.entradas)

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
					recebedor = Recebedor(s)
					recebedor.processar()

			# Soquetes com erros
			for s in x:
				log("Erro encontrado.")
				soquete.remover(s)
				self.removerCliente(s)
				app_sair()

# FUNCOES DO PROGRAMA
# ===================
def log(*args, **kwargs):
    if EXIBIR_LOG:
        print("{0}".format(parametros["porta"]), *args, file=sys.stderr, **kwargs)

# -----------------------------------------
# Lê os argumentos do programa
# arg1 = porta
# arg3 = arquivo com banco de dados
# arg4 = opcional, servidores (até 10) para conectar
#   parametros = dicionario onde serão gravados os argumentos
def args_processar():
    parametros['ip'] = "127.0.0.1"
    parametros['porta'] = int(sys.argv[1])
    parametros['bd'] = sys.argv[2]
    i = len(sys.argv)
    if i > 3:
        j = 3
        while (j < i):
            temp = sys.argv[j].split(':')
            parametros['servidores'][temp[0]] = int(temp[1])
            j = j + 1

def app_sair():
	log("Desligando...")
	#for s in soquetes:
	#	s.close()
	sys.exit()

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 2:
	args_processar()
	bd = BancoDados()
	historico = set()
	# inicia o gerenciador de msgs no modo servente
	mensagens = Mensagens(True)
	clientes = Clientes()
	serventes = Serventes()
	soquetes = Soquetes()
	if len(parametros['servidores']) > 0:
		soquetes.conectarAtivamente(parametros['servidores'])
	soquetes.manipular()
