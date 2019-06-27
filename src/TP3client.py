# -*- coding: utf-8 -*-
#! /usr/bin/python3.6

# TP3 de Redes - Programa Cliente
# Douglas R. Almeida

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
PROMPT             = ""
ARGS_INSUFICIENTES = "Erro com o comando {0}: Argumentos insuficientes."
CMD_NAOENCONTRADO  = "Comando desconhecido"
MSG_INESPERADA     = "Mensagem incorreta recebida de {0}:{1}"
MSG_NENHUMA        = "Nenhuma mensagem recebida"

# VARIAVEIS DO PROGRAMA
# =====================
parametros = {'ip': '', 'porta': 0, 'portaescuta': 0, 'timeout': 4}

# CLASSES DO PROGRAMA
# ===================

# comandos
def cmd_teste(args):
    print("Teste!")

def cmd_pergunta(args):
    if len(args) > 1:
        chave = args[1]
        dados = mensagens.gerarKeyReq(chave)
        rede.enviar(dados)
        if not rede.escutar():
            print(MSG_NENHUMA)
    else:
        print(ARGS_INSUFICIENTES.format(args[0]))

def cmd_topologia(args):
    dados = mensagens.gerarTopoReq()
    rede.enviar(dados)
    if not rede.escutar():
        print(MSG_NENHUMA)

def cmd_sair(args):
    app_sair()

# Linha de comando
class CmdLine():
    def __init__(self):
        self.cmdatual = ''
        self.cmds = {
            "teste": cmd_teste,
            "?": cmd_pergunta,
            "Q": cmd_sair,
            "T": cmd_topologia
        }

    def executar(self):
        args = self.cmdatual.split(' ')
        if args[0] in self.cmds.keys():
            self.cmds[args[0]](args)
        else:
            print(CMD_NAOENCONTRADO.format(args[0]))

    def manipular(self):
        while (True):
            self.obter()
            self.executar()

    def obter(self):
        s = ''
        while len(s) == 0:
            try:
                s = input(PROMPT)
            except:
                app_sair()
        self.cmdatual = ' '.join(s.split())

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

    def ultimoSeqGerado(self):
        return self.numseq - 1

# Gerencia as conexões de rede
class Rede():
    def __init__(self):
        self.soqueteEnvia = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.soqueteEnvia.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def conectar(self):
        dest = (parametros['ip'], parametros["porta"])
        self.soqueteEnvia.connect(dest)
        log("Cliente {0} na porta {1}.".format(dest[0], dest[1]))
        dados = mensagens.gerarId()
        self.enviar(dados)

    def enviar(self, dados):
        self.soqueteEnvia.sendall(dados)

    def escutar(self):
        recebeuMsg = False
        local = ("127.0.0.1", parametros["portaescuta"])
        soqueteRecebe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soqueteRecebe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        soqueteRecebe.bind(local)
        soqueteRecebe.listen()
        soqueteRecebe.settimeout(parametros['timeout'])
        log("Ouvindo na porta {0}.".format(parametros["portaescuta"]))
        while True:
            try:
                con, endereco = soqueteRecebe.accept()
                dados = con.recv(2)
                if not dados:
                    break
                tipo = Dados.paraShort(dados)
                log("Dados de {0}.".format(endereco))
                resposta = Resposta(con)
                resposta.processar[tipo]()
                recebeuMsg = True
            except socket.timeout:
                return recebeuMsg
        return recebeuMsg

    def encerrar(self):
        self.soqueteEnvia.close()

class Resposta():
    def __init__(self, soquete):
        endereco = soquete.getpeername()
        self.ip = endereco[0]
        self.porta = endereco[1]
        self.conexao = soquete
        self.processar = [
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
        self.seqAguardado = mensagens.ultimoSeqGerado()

    def processarId(self):
        temp = self.conexao.recv(2)
        print(MSG_INESPERADA.format(self.ip, self.porta))

    def processarKeyReq(self):
        dados = self.conexao.recv(6)
        tam = Dados.paraShort(dados[4:6])
        texto = self.conexao.recv(tam)
        print(MSG_INESPERADA.format(self.ip, self.porta))

    def processarTopoReq(self):
        dados = self.conexao.recv(4)
        print(MSG_INESPERADA.format(self.ip, self.porta))

    def processarKeyFlood(self):
        dados = self.conexao.recv(14)
        tam = Dados.paraShort(dados[12:14])
        texto = self.conexao.recv(tam)
        print(MSG_INESPERADA.format(self.ip, self.porta))
        
    def processarTopoFlood(self):
        dados = self.conexao.recv(14)
        tam = Dados.paraShort(dados[12:14])
        texto = self.conexao.recv(tam)
        print(MSG_INESPERADA.format(self.ip, self.porta))

    def processarResp(self):
        dados = self.conexao.recv(6)
        seq = Dados.paraInt(dados[:4])
        tam = Dados.paraShort(dados[4:6])
        texto = self.conexao.recv(tam).decode("ascii")
        if seq != self.seqAguardado:
            print(MSG_INESPERADA.format(self.ip, self.porta))
            return
        print("{0} {1}:{2}".format(texto, self.ip, self.porta))

    def processarNada(self, conexao, endereco):
        print(MSG_INESPERADA.format(self.ip, self.porta))

# FUNCOES DO PROGRAMA
# ===================
def log(*args, **kwargs):
    if EXIBIR_LOG:
        print(*args, file=sys.stderr, **kwargs)

# -----------------------------------------
# Lê os argumentos do programa
# arg1 = porta de escuta
# arg2 = ip:porta
def args_processar():
    parametros['portaescuta'] = int(sys.argv[1])
    temp = sys.argv[2].split(':')
    parametros['ip'] = temp[0]
    parametros['porta'] = int(temp[1])

def app_sair():
    rede.encerrar()
    sys.exit()

# CORPO DO PROGRAMA
# =================
if len(sys.argv) > 1:
    args_processar()
    # inicia o gerenciador de msgs no modo cliente
    mensagens = Mensagens(False)
    # conecta com o servent
    rede = Rede()
    rede.conectar()
    # inicia o prompt de comando
    cmdline = CmdLine()
    cmdline.manipular()