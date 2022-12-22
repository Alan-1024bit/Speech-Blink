from ast import If
from enum import Flag
from fileinput import filename
from os import system
from pyclbr import Function
from tkinter import *
from PIL import Image
from PIL import ImageTk
from cv2 import imshow
from scipy.spatial import distance as dist
from imutils.video import FileVideoStream
from imutils.video import VideoStream
from imutils import face_utils
import numpy as np
import imutils
import time
import dlib
import cv2
import json
import winsound
import sqlite3
from tkinter import ttk
import os.path
from tkinter import filedialog
from tkinter import ttk,messagebox
import base64
import io
from threading import Thread
import pyttsx3

root = Tk()

class Speech(Thread):
    # Método de reprodução da voz
    def playAudio(self,answer):
        self.engine = pyttsx3.init() # Inicializa a engine

        self.engine.setProperty('rate',175) # Pré define um rate

        self.engine.setProperty('volume',1.0) # Seta um volume padrão
        self.engine.say(answer)
        self.engine.runAndWait()

class Variaveis():
    # Variaveis configuráveis
    with open("../json/config.json") as json_data_file:
        config = json.load(json_data_file)

    # Variaveis do escopo

    acaoAnterior = "nenhum"  # Controle da última ação
    acaoDefinida = -1  # Controle da ação atual

    frames = 0  # Contador de frames
    counter = 0  # Contador de frames do olho fechado

    dif = -1
    acao = []

    delayTime = int(1000 / config["video"]["frameRate"])
    delayFrame = config["acao"]["delay"]

    # inicialização do detector
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(config["predictor"]["path"])

    # Index das marcas do olho direito e esquerdo
    (lStart, lEnd) = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    (rStart, rEnd) = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    #indices para selecao de categoria
    Category_Esquerda = 0
    Category_Centro = 1
    Category_Direita = 2

    #lista de categorias
    listaCateg = []

    #indices para selecao de acao
    Action_Esquerda = 0
    Action_Centro = 1
    Action_Direita = 2

    #lista de ações da categoria selecionada
    listaAction = []

    #flag para indicar se há ou não uma confirmação de categoria, ou seja, se houve uma categoria selecionada.
    selectedCategory = False # Se há uma categoria selecionada isso implica em uma movimentação do carousel das ações.

    bytes_photoCategory = Variable()
    bytes_photoAction = Variable()

    FotoUmCategory = Variable()
    FotoDoisCategory = Variable()
    FotoTresCategory = Variable()

    FotoUmAction = Variable()
    FotoDoisAction = Variable()
    FotoTresAction = Variable()
    
class Functions():

    def db_connect():
        Functions.conn = sqlite3.connect("../database/acao.db")
        Functions.cursor = Functions.conn.cursor()

    def db_disconnect():
        Functions.conn.close()

    def db_exists_database():
        return os.path.exists('../database/acao.db')

    def db_create_tables():
        
        Functions.db_connect(); print("Conectado ao banco de dados")

        #CRIAR TABELAS NO BANCO DE DADOS
        Functions.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                nome_categoria CHAR(40) NOT NULL PRIMARY KEY,
                foto_categoria BLOB NOT NULL
            );
        """)

        Functions.cursor.execute("""
            CREATE TABLE IF NOT EXISTS acao (
                nome_acao CHAR(40) PRIMARY KEY,
                nome_categoria CHAR(40) NOT NULL,
                foto_acao BLOB NOT NULL,
                FOREIGN KEY (nome_categoria) REFERENCES categoria (nome_categoria)
            );
        """)

        Functions.conn.commit(); print("Banco de dados criado")
        Functions.db_disconnect()

    def db_exists_categoria():
        Functions.db_connect()
        Functions.cursor.execute(""" SELECT nome_categoria FROM categoria """)
        Functions.conn.commit()

        return Functions.cursor.fetchall()

    def db_select_categoria():
        Functions.db_connect()
        Functions.cursor.execute(""" SELECT nome_categoria FROM categoria """)
        Functions.conn.commit()

        return Functions.cursor.fetchall()

    def db_select_foto_categoria(nome_categoria):
        Functions.db_connect()
        Functions.cursor.execute(""" SELECT foto_categoria FROM categoria WHERE nome_categoria = (?)""", (nome_categoria))
        Functions.conn.commit()

        for row in Functions.cursor.fetchall():
            return row[0]
            break

    def db_select_acao():
        Functions.db_connect()

        if(len(Variaveis.listaCateg) == 1):
            categoria = str(Variaveis.listaCateg[0])
        else:
            categoria = str(Variaveis.listaCateg[Variaveis.Category_Centro])

        categoria = categoria[2:-3]

        Functions.cursor.execute(""" SELECT nome_acao FROM acao WHERE nome_categoria = ?""", [categoria])
        Functions.conn.commit()

        return Functions.cursor.fetchall()

    def db_select_foto_acao(nome_acao):
        Functions.db_connect()
        Functions.cursor.execute(""" SELECT foto_acao FROM acao WHERE nome_acao = (?) """, (nome_acao))
        Functions.conn.commit()

        for row in Functions.cursor.fetchall():
            return row[0]
            break

    def db_insert_categoria():
        nomeCategoria = Insert_Category.EntryNomeCateg.get()
        fotoCategoria = Variaveis.bytes_photoCategory

        if(nomeCategoria == "" or fotoCategoria == ""):
            messagebox.showerror("Erro","Nome da categoria e imagem obrigatórios")
        else:
            Variaveis.listaCateg.append(nomeCategoria)

            Functions.db_connect()

            Functions.cursor.execute(""" INSERT INTO categoria (nome_categoria, foto_categoria) VALUES (?, ?)""", (nomeCategoria, fotoCategoria))
            Functions.conn.commit()

            Functions.db_disconnect()

            #SE A VARIÁVEL messageCategory FOI DEFINIDA.
            # messageCategory CONTÉM A LABEL COM MENSAGEM EMTIDA QUANDO NÃO HÁ CATEGORIA CADASTRADA
            if 'messageCategory' in dir(Main):

                #REMOVER LABEL CONTIDA NA VARIÁVEL messageCategory
                Main.messageCategory.destroy()

                #EXCLUIR VARIÁVEL
                del Main.messageCategory

                #ADICIONAR BOTÃO PARA CADASTRO DE AÇÃO, OU SEJA, PERMITIR CADASTRO DE AÇÕES. 
                Main.buttonAction = Button(text="+", command=Config_Action.__init__)
                Main.buttonAction.place(relx=0.75, rely=0.52)

            if(len(Variaveis.listaCateg) > 3):
                if(Variaveis.Category_Direita == 0):
                    Variaveis.Category_Direita = int(len(Variaveis.listaCateg)) - 1

                elif(Variaveis.Category_Centro == 0):    
                    Variaveis.Category_Esquerda = int(len(Variaveis.listaCateg)) - 1

            elif(len(Variaveis.listaCateg) == 3):
                if(Variaveis.Category_Esquerda == 0):
                    Variaveis.Category_Direita = 2

                elif(Variaveis.Category_Centro == 0):
                    Variaveis.Category_Direita = 1
                    Variaveis.Category_Esquerda = 2

            if(len(Variaveis.listaCateg) == 1):
                Main.IconeEsquerdaCategory['text'] = "<"
                Main.IconeDireitaCategory['text'] = ">"

            elif(len(Variaveis.listaCateg) == 2):
                Main.IconeEsquerdaAction['text'] = ''
                Main.IconeDireitaAction['text'] = ''
                
                Main.labelVoltar['text'] = ''

                Variaveis.selectedCategory = False

            Functions.Carousel_Category()
            Functions.Carousel_Action()
            
    def db_insert_acao():
        Functions.db_connect()

        nome_categoria = Insert_Action.selectCateg.get()
        nome_acao = Insert_Action.EntryNomeAcao.get()
        fotoAcao = Variaveis.bytes_photoAction

        if(nome_categoria == "" or nome_acao == "" or fotoAcao == ""):
            messagebox.showerror("Erro","Seleção da categoria, inserção do nome da opção e imagem é obrigatório")
        else:
            Functions.cursor.execute(""" INSERT INTO acao (nome_acao, nome_categoria, foto_acao) VALUES (?, ?, ?)""", (nome_acao, nome_categoria, fotoAcao))
            Functions.conn.commit()

            Functions.db_disconnect()
            
            if(len(Variaveis.listaCateg) > 1):
                categoria_atual = "".join(Variaveis.listaCateg[Variaveis.Category_Centro])
            else:
                categoria_atual = "".join(Variaveis.listaCateg[0])

            if(categoria_atual == nome_categoria):
                
                Variaveis.listaAction.append(nome_acao)

                if(len(Variaveis.listaAction) > 3):
                    if(Variaveis.Action_Direita == 0):
                        Variaveis.Action_Direita = int(len(Variaveis.listaAction)) - 1

                    elif(Variaveis.Action_Centro == 0):
                        Variaveis.Action_Esquerda = int(len(Variaveis.listaAction)) - 1

                elif(len(Variaveis.listaAction) == 3):
                    if(Variaveis.Action_Esquerda == 0):
                        Variaveis.Action_Direita = 2

                    elif(Variaveis.Action_Centro == 0):
                        Variaveis.Action_Direita = 1
                        Variaveis.Action_Esquerda = 2
            
            Functions.Carousel_Category()
            Functions.Carousel_Action()

    def Carousel_Category():
        #ADICIONAR CATEGORIA CADASTRADA NA LISTA DE CATEGORIAS
        Variaveis.listaCateg = Functions.db_select_categoria()

        if(len(Variaveis.listaCateg) == 1):

            if(Functions.db_select_acao() != []):
                Main.labelConfirmar['text'] = "Confirmar: 1, 0, 1, 0, 1"

                if(Main.labelDireita['text'] == "Nenhum movimento disponível"):
                    Main.labelDireita['text'] = ""
            else:
                Main.labelDireita['text'] = "Nenhum movimento disponível"

            #LABEL'S COM OS NOMES DAS CATEGORIAS
            Main.OpcaoUmCategory = Label(text="", font=('Verdana', 10), anchor=CENTER)
            Main.OpcaoUmCategory.place(relx=0.38, rely=0.41, relwidth=0.16)

            Main.OpcaoDoisCategory = Label(text=Variaveis.listaCateg[0], font=('Verdana', 14, 'bold underline'), anchor=CENTER)
            Main.OpcaoDoisCategory.place(relx=0.55, rely=0.4, relwidth=0.26)

            Main.OpcaoTresCategory = Label(text="", font=('Verdana', 10), anchor=CENTER)
            Main.OpcaoTresCategory.place(relx=0.82, rely=0.41, relwidth=0.16)
            
            #IMAGEM DA CATEGORIA
            Variaveis.FotoUmCategory = Image.open(io.BytesIO(Functions.db_select_foto_categoria(Variaveis.listaCateg[0])))
            Variaveis.FotoUmCategory = ImageTk.PhotoImage(Variaveis.FotoUmCategory)

            Main.OpcaoDoisCategoryFoto = ttk.LabelFrame()
            Main.OpcaoDoisCategoryFoto.place(relx= 0.60, rely= 0.15, relwidth = 0.14, relheight= 0.24)
            
            labelFotoDois = Label(Main.OpcaoDoisCategoryFoto, image=Variaveis.FotoUmCategory)
            labelFotoDois.image = Variaveis.FotoUmCategory
            labelFotoDois.pack()
            
        elif(len(Variaveis.listaCateg) == 2):
            Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
            Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

            if(Functions.db_select_acao() != []):
                Main.labelConfirmar['text'] = "Confirmar: 1, 0, 1, 0, 1"
            else:
                Main.labelConfirmar['text'] = ""

            Main.OpcaoUmCategory = Label(text=Variaveis.listaCateg[Variaveis.Category_Esquerda], font=('Verdana', 10), anchor=CENTER)
            Main.OpcaoUmCategory.place(relx=0.38, rely=0.41, relwidth=0.16)

            Main.OpcaoDoisCategory = Label(text=Variaveis.listaCateg[Variaveis.Category_Centro], font=('Verdana', 14, 'bold underline'), anchor=CENTER)
            Main.OpcaoDoisCategory.place(relx=0.55, rely=0.4, relwidth=0.26)

            Main.OpcaoTresCategory = Label(text=Variaveis.listaCateg[Variaveis.Category_Esquerda], font=('Verdana', 10), anchor=CENTER)
            Main.OpcaoTresCategory.place(relx=0.82, rely=0.41, relwidth=0.16)
            
            #OBTER IMAGENS ARMAZENADAS NO BANCO
            Variaveis.FotoUmCategory = Image.open(io.BytesIO(Functions.db_select_foto_categoria(Variaveis.listaCateg[Variaveis.Category_Esquerda])))
            Variaveis.FotoUmCategory = ImageTk.PhotoImage(Variaveis.FotoUmCategory)

            Variaveis.FotoDoisCategory = Image.open(io.BytesIO(Functions.db_select_foto_categoria(Variaveis.listaCateg[Variaveis.Category_Centro])))
            Variaveis.FotoDoisCategory = ImageTk.PhotoImage(Variaveis.FotoDoisCategory)
            
            #ADICIONAR LABEL'S PARA ADIÇÃO DE CONTEÚDO NA JANELA
            Main.OpcaoUmCategoryFoto = ttk.LabelFrame()
            Main.OpcaoUmCategoryFoto.place(relx= 0.40, rely= 0.15, relwidth = 0.14, relheight= 0.24)

            Main.OpcaoDoisCategoryFoto = ttk.LabelFrame()
            Main.OpcaoDoisCategoryFoto.place(relx= 0.60, rely= 0.15, relwidth = 0.14, relheight= 0.24)
            
            Main.OpcaoTresCategoryFoto = ttk.LabelFrame()
            Main.OpcaoTresCategoryFoto.place(relx= 0.82, rely= 0.15, relwidth = 0.14, relheight= 0.24)
            
            #ADICIONAR IMAGENS AOS LABEL'S
            Main.labelFotoUm = Label(Main.OpcaoUmCategoryFoto, image=Variaveis.FotoUmCategory)
            Main.labelFotoUm.image = Variaveis.FotoUmCategory
            Main.labelFotoUm.pack()

            Main.labelFotoDois = Label(Main.OpcaoDoisCategoryFoto, image=Variaveis.FotoDoisCategory)
            Main.labelFotoDois.image = Variaveis.FotoDoisCategory
            Main.labelFotoDois.pack()

            Main.labelFotoTres = Label(Main.OpcaoTresCategoryFoto, image=Variaveis.FotoUmCategory)
            Main.labelFotoTres.image = Variaveis.FotoUmCategory
            Main.labelFotoTres.pack()

        elif(len(Variaveis.listaCateg) > 2):

            Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
            Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

            if(Functions.db_select_acao() != []):
                Main.labelConfirmar['text'] = "Confirmar: 1, 0, 1, 0, 1"
            else:
                Main.labelConfirmar['text'] = ""

            Main.OpcaoUmCategory = Label(text=Variaveis.listaCateg[Variaveis.Category_Esquerda], font=('Verdana', 10), anchor=CENTER)
            Main.OpcaoUmCategory.place(relx=0.38, rely=0.41, relwidth=0.16)

            Main.OpcaoDoisCategory = Label(text=Variaveis.listaCateg[Variaveis.Category_Centro], font=('Verdana', 14, 'bold underline'), anchor=CENTER)
            Main.OpcaoDoisCategory.place(relx=0.55, rely=0.4, relwidth=0.26)

            Main.OpcaoTresCategory = Label(text=Variaveis.listaCateg[Variaveis.Category_Direita], font=('Verdana', 10), anchor=CENTER)
            Main.OpcaoTresCategory.place(relx=0.82, rely=0.41, relwidth=0.16)
            
            #OBTER IMAGENS ARMAZENADAS NO BANCO
            Variaveis.FotoUmCategory = Image.open(io.BytesIO(Functions.db_select_foto_categoria(Variaveis.listaCateg[Variaveis.Category_Esquerda])))
            Variaveis.FotoUmCategory = ImageTk.PhotoImage(Variaveis.FotoUmCategory)

            Variaveis.FotoDoisCategory = Image.open(io.BytesIO(Functions.db_select_foto_categoria(Variaveis.listaCateg[Variaveis.Category_Centro])))
            Variaveis.FotoDoisCategory = ImageTk.PhotoImage(Variaveis.FotoDoisCategory)
            
            Variaveis.FotoTresCategory = Image.open(io.BytesIO(Functions.db_select_foto_categoria(Variaveis.listaCateg[Variaveis.Category_Direita])))
            Variaveis.FotoTresCategory = ImageTk.PhotoImage(Variaveis.FotoTresCategory)
            
            #ADICIONAR LABEL'S PARA ADIÇÃO DE CONTEÚDO NA JANELA
            Main.OpcaoUmCategoryFoto = ttk.LabelFrame()
            Main.OpcaoUmCategoryFoto.place(relx= 0.40, rely= 0.15, relwidth = 0.14, relheight= 0.24)

            Main.OpcaoDoisCategoryFoto = ttk.LabelFrame()
            Main.OpcaoDoisCategoryFoto.place(relx= 0.60, rely= 0.15, relwidth = 0.14, relheight= 0.24)
            
            Main.OpcaoTresCategoryFoto = ttk.LabelFrame()
            Main.OpcaoTresCategoryFoto.place(relx= 0.82, rely= 0.15, relwidth = 0.14, relheight= 0.24)
            
            #ADICIONAR IMAGENS AOS LABEL'S
            Main.labelFotoUm = Label(Main.OpcaoUmCategoryFoto, image=Variaveis.FotoUmCategory)
            Main.labelFotoUm.image = Variaveis.FotoUmCategory
            Main.labelFotoUm.pack()

            Main.labelFotoDois = Label(Main.OpcaoDoisCategoryFoto, image=Variaveis.FotoDoisCategory)
            Main.labelFotoDois.image = Variaveis.FotoDoisCategory
            Main.labelFotoDois.pack()

            Main.labelFotoTres = Label(Main.OpcaoTresCategoryFoto, image=Variaveis.FotoTresCategory)
            Main.labelFotoTres.image = Variaveis.FotoTresCategory
            Main.labelFotoTres.pack()

    def Carousel_Action():
        Main.messageAction['text'] = ""

        if('OpcaoUmActionFoto' in dir(Main)):
            Main.OpcaoUmActionFoto.destroy()

        if('OpcaoDoisActionFoto' in dir(Main)):
            Main.OpcaoDoisActionFoto.destroy()

        if('OpcaoTresActionFoto' in dir(Main)):
            Main.OpcaoTresActionFoto.destroy()

        #VERIFICAR A EXISTENCIA DE AÇÕES DESSA CATEGORIA CADASTRADA
        if(Functions.db_select_acao() == []):

            if('OpcaoUmAction' in dir(Main)):

                #REMOVER CONTEÚDO DAS LABEL'S CONTIDAS NAS VARIÁVEIS
                Main.OpcaoUmAction['text'] = ""
                Main.OpcaoDoisAction['text'] = ""
                Main.OpcaoTresAction['text'] = ""

            #ADICIONAR BOTÃO PARA CADASTRO DE AÇÃO, OU SEJA, PERMITIR CADASTRO DE AÇÕES. 
            Main.buttonAction = Button(text="+", command=Config_Action.__init__)
            Main.buttonAction.place(relx=0.75, rely=0.52)
        
        else:
            Main.messageAction['text'] = ""
            
            #OBTER AÇÕES CADASTRADAS E ATRIBUIR À LISTA. ESSAS AÇÕES PERTENCEM A CATEGORIA SELECIONADA
            Variaveis.listaAction = Functions.db_select_acao()

            if(len(Variaveis.listaAction) == 1):
                Main.buttonAction = Button(text="+", command=Config_Action.__init__)
                Main.buttonAction.place(relx=0.75, rely=0.52)

                Main.OpcaoUmAction = Label(text="", font=('Verdana', 10), anchor=CENTER)
                Main.OpcaoUmAction.place(relx=0.38, rely=0.91, relwidth=0.16)

                Main.OpcaoDoisAction = Label(text=Variaveis.listaAction[0], font=('Verdana', 14, 'bold underline'), anchor=CENTER)
                Main.OpcaoDoisAction.place(relx=0.55, rely=0.9, relwidth=0.26)

                Main.OpcaoTresAction = Label(text="", font=('Verdana', 10), anchor=CENTER)
                Main.OpcaoTresAction.place(relx=0.82, rely=0.91, relwidth=0.16)
                
                #IMAGEM DA AÇÃO
                Variaveis.FotoUmAction = Image.open(io.BytesIO(Functions.db_select_foto_acao(Variaveis.listaAction[0])))
                Variaveis.FotoUmAction = ImageTk.PhotoImage(Variaveis.FotoUmAction)

                Main.OpcaoDoisActionFoto = ttk.LabelFrame()
                Main.OpcaoDoisActionFoto.place(relx= 0.60, rely= 0.65, relwidth = 0.14, relheight= 0.24)
                
                labelFotoDois = Label(Main.OpcaoDoisActionFoto, image=Variaveis.FotoUmAction)
                labelFotoDois.image = Variaveis.FotoUmAction
                labelFotoDois.pack()

            elif(len(Variaveis.listaAction) == 2):
                if(Variaveis.selectedCategory == True):
                    Main.labelDireita["text"] = "Direita: 1, 0, 1, 0, 0"
                    Main.labelEsquerda["text"] = "Esquerda: 1, 0, 1, 1, 1"

                Main.buttonAction = Button(text="+", command=Config_Action.__init__)
                Main.buttonAction.place(relx=0.75, rely=0.52)

                Main.OpcaoUmAction = Label(text=Variaveis.listaAction[Variaveis.Action_Esquerda], font=('Verdana', 10), anchor=CENTER)
                Main.OpcaoUmAction.place(relx=0.38, rely=0.91, relwidth=0.16)

                Main.OpcaoDoisAction = Label(text=Variaveis.listaAction[Variaveis.Action_Centro], font=('Verdana', 14, 'bold underline'), anchor=CENTER)
                Main.OpcaoDoisAction.place(relx=0.55, rely=0.9, relwidth=0.26)

                Main.OpcaoTresAction = Label(text=Variaveis.listaAction[Variaveis.Action_Esquerda], font=('Verdana', 10), anchor=CENTER)
                Main.OpcaoTresAction.place(relx=0.82, rely=0.91, relwidth=0.16)

                #OBTER IMAGENS ARMAZENADAS NO BANCO
                Variaveis.FotoUmAction = Image.open(io.BytesIO(Functions.db_select_foto_acao(Variaveis.listaAction[Variaveis.Action_Esquerda])))
                Variaveis.FotoUmAction = ImageTk.PhotoImage(Variaveis.FotoUmAction)

                Variaveis.FotoDoisAction = Image.open(io.BytesIO(Functions.db_select_foto_acao(Variaveis.listaAction[Variaveis.Action_Centro])))
                Variaveis.FotoDoisAction = ImageTk.PhotoImage(Variaveis.FotoDoisAction)
                
                #ADICIONAR LABEL'S PARA ADIÇÃO DE CONTEÚDO NA JANELA
                Main.OpcaoUmActionFoto = ttk.LabelFrame()
                Main.OpcaoUmActionFoto.place(relx= 0.40, rely= 0.65, relwidth = 0.14, relheight= 0.24)

                Main.OpcaoDoisActionFoto = ttk.LabelFrame()
                Main.OpcaoDoisActionFoto.place(relx= 0.60, rely= 0.65, relwidth = 0.14, relheight= 0.24)
                
                Main.OpcaoTresActionFoto = ttk.LabelFrame()
                Main.OpcaoTresActionFoto.place(relx= 0.82, rely= 0.65, relwidth = 0.14, relheight= 0.24)
                
                #ADICIONAR IMAGENS AOS LABEL'S
                Main.labelFotoUm = Label(Main.OpcaoUmActionFoto, image=Variaveis.FotoUmAction)
                Main.labelFotoUm.image = Variaveis.FotoUmAction
                Main.labelFotoUm.pack()

                Main.labelFotoDois = Label(Main.OpcaoDoisActionFoto, image=Variaveis.FotoDoisAction)
                Main.labelFotoDois.image = Variaveis.FotoDoisAction
                Main.labelFotoDois.pack()

                Main.labelFotoTres = Label(Main.OpcaoTresActionFoto, image=Variaveis.FotoUmAction)
                Main.labelFotoTres.image = Variaveis.FotoUmAction
                Main.labelFotoTres.pack()

            elif(len(Variaveis.listaAction) > 2):
                if(Variaveis.selectedCategory == True):
                    Main.labelDireita["text"] = "Direita: 1, 0, 1, 0, 0"
                    Main.labelEsquerda["text"] = "Esquerda: 1, 0, 1, 1, 1"

                Main.buttonAction = Button(text="+", command=Config_Action.__init__)
                Main.buttonAction.place(relx=0.75, rely=0.52)

                Main.OpcaoUmAction = Label(text=Variaveis.listaAction[Variaveis.Action_Esquerda], font=('Verdana', 10), anchor=CENTER)
                Main.OpcaoUmAction.place(relx=0.38, rely=0.91, relwidth=0.16)

                Main.OpcaoDoisAction = Label(text=Variaveis.listaAction[Variaveis.Action_Centro], font=('Verdana', 14, 'bold underline'), anchor=CENTER)
                Main.OpcaoDoisAction.place(relx=0.55, rely=0.9, relwidth=0.26)

                Main.OpcaoTresAction = Label(text=Variaveis.listaAction[Variaveis.Action_Direita], font=('Verdana', 10), anchor=CENTER)
                Main.OpcaoTresAction.place(relx=0.82, rely=0.91, relwidth=0.16)
                
                #OBTER IMAGENS ARMAZENADAS NO BANCO
                Variaveis.FotoUmAction = Image.open(io.BytesIO(Functions.db_select_foto_acao(Variaveis.listaAction[Variaveis.Action_Esquerda])))
                Variaveis.FotoUmAction = ImageTk.PhotoImage(Variaveis.FotoUmAction)

                Variaveis.FotoDoisAction = Image.open(io.BytesIO(Functions.db_select_foto_acao(Variaveis.listaAction[Variaveis.Action_Centro])))
                Variaveis.FotoDoisAction = ImageTk.PhotoImage(Variaveis.FotoDoisAction)

                Variaveis.FotoTresAction = Image.open(io.BytesIO(Functions.db_select_foto_acao(Variaveis.listaAction[Variaveis.Action_Direita])))
                Variaveis.FotoTresAction = ImageTk.PhotoImage(Variaveis.FotoTresAction)
                
                #ADICIONAR LABEL'S PARA ADIÇÃO DE CONTEÚDO NA JANELA
                Main.OpcaoUmActionFoto = ttk.LabelFrame()
                Main.OpcaoUmActionFoto.place(relx= 0.40, rely= 0.65, relwidth = 0.14, relheight= 0.24)

                Main.OpcaoDoisActionFoto = ttk.LabelFrame()
                Main.OpcaoDoisActionFoto.place(relx= 0.60, rely= 0.65, relwidth = 0.14, relheight= 0.24)
                
                Main.OpcaoTresActionFoto = ttk.LabelFrame()
                Main.OpcaoTresActionFoto.place(relx= 0.82, rely= 0.65, relwidth = 0.14, relheight= 0.24)
                
                #ADICIONAR IMAGENS AOS LABEL'S
                Main.labelFotoUm = Label(Main.OpcaoUmActionFoto, image=Variaveis.FotoUmAction)
                Main.labelFotoUm.image = Variaveis.FotoUmAction
                Main.labelFotoUm.pack()

                Main.labelFotoDois = Label(Main.OpcaoDoisActionFoto, image=Variaveis.FotoDoisAction)
                Main.labelFotoDois.image = Variaveis.FotoDoisAction
                Main.labelFotoDois.pack()

                Main.labelFotoTres = Label(Main.OpcaoTresActionFoto, image=Variaveis.FotoTresAction)
                Main.labelFotoTres.image = Variaveis.FotoTresAction
                Main.labelFotoTres.pack()

    def defineAcao(acao):
        acaoDefinida = -1

        if (acao[0] == 1 and acao[1] == 0 and acao[2] == 1 and acao[3] == 1 and acao[4] == 1):  # Esquerda
            acaoDefinida = 1

        elif (acao[0] == 1 and acao[1] == 0 and acao[2] == 1 and acao[3] == 0 and acao[4] == 0):  # Direita
            acaoDefinida = 2

        elif (acao[0] == 1 and acao[1] == 0 and acao[2] == 1 and acao[3] == 0 and acao[4] == 1):  # Ação 1
            acaoDefinida = 3

        elif (acao[0] == 1 and acao[1] == 0 and acao[2] == 1 and acao[3] == 1 and acao[4] == 0):  # Ação 2
            acaoDefinida = 4

        return acaoDefinida

    def eyeAspectRatio(eye):# Calculo do EAR (Eye Aspect Ratio)

        # Distância euclideana vertical entre os pontos p2-p6 e p3-p5
        A = dist.euclidean(eye[1], eye[5])
        B = dist.euclidean(eye[2], eye[4])

        # Distância euclideana horizontal entre os pontos p1-p4
        C = dist.euclidean(eye[0], eye[3])

        # Equação do eye aspect ratio
        ear = (A + B) / (2.0 * C)

        # Return the eye aspect ratio
        return ear

    def moveCarousels(acaoDefinida):
        
        if(Functions.db_select_categoria() != []):
            if(Variaveis.selectedCategory == False and acaoDefinida != -1):
                
                qtdd_Categorias = len(Functions.db_select_categoria())
                qtdd_Categorias -= 1
 
                Main.IconeEsquerdaAction['text'] = ""
                Main.IconeDireitaAction['text'] = ""

                Main.IconeEsquerdaCategory['text'] = "<"
                Main.IconeDireitaCategory['text'] = ">"

                if(len(Variaveis.listaCateg) == 1):
                    Functions.Carousel_Category()
                    
                    Main.labelDireita["text"] = ""
                    Main.labelEsquerda["text"] = ""
                    
                    if(Functions.db_select_acao() != []):
                        
                        Main.labelConfirmar['text'] = "Confirmar: 1, 0, 1, 0, 1"

                        if (acaoDefinida == 3):
                            Variaveis.selectedCategory = True
                            winsound.Beep(550, 100)

                elif(len(Variaveis.listaCateg) == 2):

                    if(Main.labelDireita['text'] == "" and Main.labelEsquerda['text'] == ""):
                        Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
                        Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

                    if(acaoDefinida == 1 or acaoDefinida == 2):

                        if (Variaveis.Category_Esquerda == 0):
                            Variaveis.Category_Esquerda = qtdd_Categorias #ultimo valor
                            Variaveis.Category_Centro -= 1
                
                        elif (Variaveis.Category_Esquerda == qtdd_Categorias):
                            Variaveis.Category_Esquerda -= 1
                            Variaveis.Category_Centro = qtdd_Categorias #ultimo valor
                    
                        Variaveis.Action_Esquerda = 0
                        Variaveis.Action_Centro = 1
                        Variaveis.Action_Direita = 2

                        Functions.Carousel_Category()
                        Functions.Carousel_Action()

                    if(Functions.db_select_acao() != []):

                        if (acaoDefinida == 3):
                            Variaveis.selectedCategory = True
                            winsound.Beep(550, 100)

                elif(len(Variaveis.listaCateg) > 2):


                    if(Main.labelDireita['text'] == "" and Main.labelEsquerda['text'] == ""):
                        Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
                        Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

                    if(acaoDefinida == 1):

                        if (Variaveis.Category_Esquerda == 0):
                            Variaveis.Category_Esquerda = qtdd_Categorias #ultimo valor
                            Variaveis.Category_Centro -= 1
                            Variaveis.Category_Direita -= 1
                
                        elif (Variaveis.Category_Esquerda == qtdd_Categorias):
                            Variaveis.Category_Esquerda -= 1
                            Variaveis.Category_Centro = qtdd_Categorias #ultimo valor
                            Variaveis.Category_Direita -= 1
                    
                        elif (Variaveis.Category_Direita == 0):
                            Variaveis.Category_Esquerda -= 1
                            Variaveis.Category_Centro -= 1 
                            Variaveis.Category_Direita = qtdd_Categorias #ultimo valor
                    
                        else:
                            Variaveis.Category_Esquerda -= 1
                            Variaveis.Category_Centro -= 1 
                            Variaveis.Category_Direita -= 1

                    elif(acaoDefinida == 2):

                        if(Variaveis.Category_Direita == qtdd_Categorias):
                            Variaveis.Category_Esquerda += 1
                            Variaveis.Category_Centro += 1
                            Variaveis.Category_Direita = 0 
                    
                        elif(Variaveis.Category_Direita == 0):
                            Variaveis.Category_Esquerda = qtdd_Categorias
                            Variaveis.Category_Centro = 0
                            Variaveis.Category_Direita += 1
                    
                        elif(Variaveis.Category_Esquerda == qtdd_Categorias):
                            Variaveis.Category_Esquerda = 0
                            Variaveis.Category_Centro += 1
                            Variaveis.Category_Direita += 1
                    
                        else:
                            Variaveis.Category_Esquerda += 1
                            Variaveis.Category_Centro += 1
                            Variaveis.Category_Direita += 1

                    Functions.Carousel_Category()
                    
                    Variaveis.Action_Esquerda = 0
                    Variaveis.Action_Centro = 1
                    Variaveis.Action_Direita = 2

                    Functions.Carousel_Action()

                    if(Functions.db_select_acao() != []):

                        if (acaoDefinida == 3):
                            Variaveis.selectedCategory = True
                            winsound.Beep(550, 100)
                            
            elif(Variaveis.selectedCategory == True):
                
                Main.IconeEsquerdaCategory['text'] = " "
                Main.IconeDireitaCategory['text'] = " "

                Main.IconeEsquerdaAction['text'] = "<"
                Main.IconeDireitaAction['text'] = ">"

                Main.labelVoltar['text'] = "Voltar: 1, 0, 1, 1, 0"

                qtdd_Acoes = len(Functions.db_select_acao())
                qtdd_Acoes -= 1

                if(len(Variaveis.listaAction) == 1):

                    if(Main.labelDireita['text'] != "" and Main.labelEsquerda['text'] != ""):
                        Main.labelDireita['text'] = ""
                        Main.labelEsquerda['text'] = ""

                    if (acaoDefinida == 3):
                        Main.labelAcaoAnterior['text'] = "Anterior: %s" % (Variaveis.listaAction[0])# SUBSTITUIR

                        Functions.voice_sound(Variaveis.listaAction[0])

                    elif (acaoDefinida == 4):
                        if(len(Variaveis.listaCateg) >= 2):
                            Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
                            Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

                        Main.labelVoltar['text'] = ""
                        Variaveis.selectedCategory = False

                        Main.IconeEsquerdaAction['text'] = ""
                        Main.IconeDireitaAction['text'] = ""

                        Main.IconeEsquerdaCategory['text'] = "<"
                        Main.IconeDireitaCategory['text'] = ">"

                        winsound.Beep(550, 100)

                elif(len(Variaveis.listaAction) == 2):

                    if(Main.labelDireita['text'] == "" and Main.labelEsquerda['text'] == ""):
                        Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
                        Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

                    if(acaoDefinida == 1 or acaoDefinida == 2):

                        if (Variaveis.Action_Esquerda == 0):
                            Variaveis.Action_Esquerda = qtdd_Acoes #ultimo valor
                            Variaveis.Action_Centro -= 1
                
                        elif (Variaveis.Action_Esquerda == qtdd_Acoes):
                            Variaveis.Action_Esquerda -= 1
                            Variaveis.Action_Centro = qtdd_Acoes #ultimo valor

                        Functions.Carousel_Action()

                    elif (acaoDefinida == 3):
                        Main.labelAcaoAnterior['text'] = "Anterior: %s" % (Variaveis.listaAction[Variaveis.Action_Centro])# SUBSTITUIR
                        
                        Functions.voice_sound(Variaveis.listaAction[Variaveis.Action_Centro])

                    elif (acaoDefinida == 4):

                        if(len(Variaveis.listaCateg) == 1):
                            Main.labelDireita['text'] = ""
                            Main.labelEsquerda['text'] = ""

                        Main.labelVoltar['text'] = ""
                        Variaveis.selectedCategory = False

                        Main.IconeEsquerdaAction['text'] = ""
                        Main.IconeDireitaAction['text'] = ""

                        Main.IconeEsquerdaCategory['text'] = "<"
                        Main.IconeDireitaCategory['text'] = ">"

                        winsound.Beep(550, 100)

                elif(len(Variaveis.listaAction) > 2):

                    if(Main.labelDireita['text'] == "" and Main.labelEsquerda['text'] == ""):
                        Main.labelDireita['text'] = "Direita: 1, 0, 1, 0, 0"
                        Main.labelEsquerda['text'] = "Esquerda: 1, 0, 1, 1, 1"

                    if(acaoDefinida == 1):

                        if (Variaveis.Action_Esquerda == 0):
                            Variaveis.Action_Esquerda = qtdd_Acoes #ultimo valor
                            Variaveis.Action_Centro -= 1
                            Variaveis.Action_Direita -= 1
                
                        elif (Variaveis.Action_Esquerda == qtdd_Acoes):
                            Variaveis.Action_Esquerda -= 1
                            Variaveis.Action_Centro = qtdd_Acoes #ultimo valor
                            Variaveis.Action_Direita -= 1
                    
                        elif (Variaveis.Action_Direita == 0):
                            Variaveis.Action_Esquerda -= 1
                            Variaveis.Action_Centro -= 1 
                            Variaveis.Action_Direita = qtdd_Acoes #ultimo valor
                    
                        else:
                            Variaveis.Action_Esquerda -= 1
                            Variaveis.Action_Centro -= 1 
                            Variaveis.Action_Direita -= 1

                        Functions.Carousel_Action()

                    elif(acaoDefinida == 2):

                        if(Variaveis.Action_Direita == qtdd_Acoes):
                            Variaveis.Action_Esquerda += 1
                            Variaveis.Action_Centro += 1
                            Variaveis.Action_Direita = 0 
                    
                        elif(Variaveis.Action_Direita == 0):
                            Variaveis.Action_Esquerda = qtdd_Acoes
                            Variaveis.Action_Centro = 0
                            Variaveis.Action_Direita += 1
                    
                        elif(Variaveis.Action_Esquerda == qtdd_Acoes):
                            Variaveis.Action_Esquerda = 0
                            Variaveis.Action_Centro += 1
                            Variaveis.Action_Direita += 1
                    
                        else:
                            Variaveis.Action_Esquerda += 1
                            Variaveis.Action_Centro += 1
                            Variaveis.Action_Direita += 1

                        Functions.Carousel_Action()

                    elif (acaoDefinida == 3):
                        Main.labelAcaoAnterior['text'] = "Anterior: %s" % (Variaveis.listaAction[Variaveis.Action_Centro])# SUBSTITUIR
                        
                        Functions.voice_sound(Variaveis.listaAction[Variaveis.Action_Centro])

                    elif (acaoDefinida == 4):
                        if(len(Variaveis.listaCateg) == 1):
                            Main.labelDireita['text'] = ""
                            Main.labelEsquerda['text'] = ""

                        Main.labelVoltar['text'] = ""
                        Variaveis.selectedCategory = False

                        Main.IconeEsquerdaAction['text'] = ""
                        Main.IconeDireitaAction['text'] = ""

                        Main.IconeEsquerdaCategory['text'] = "<"
                        Main.IconeDireitaCategory['text'] = ">"

                        winsound.Beep(550, 100)

        Variaveis.acaoDefinida = -1
    
    def startCam():
        global cap
        cap = VideoStream(src=0).start()

    def getImage(fr):
        # Seleção do frame
        global FrameVideo
        FrameVideo = cap.read()
        FrameVideo = imutils.resize(FrameVideo, Variaveis.config["video"]["width"])

        # grey-scale
        gray = cv2.cvtColor(FrameVideo, cv2.COLOR_BGR2GRAY)

        # Detecção das face_utils
        rects = Variaveis.detector(gray, 0)
        
        # Dentro das face
        for rect in rects:
            # Determina as marcas da face e converte em coordenadas para o numpy
            shape = Variaveis.predictor(gray, rect)
            shape = face_utils.shape_to_np(shape)
        
            # Extrai os dois olhos
            leftEye = shape[Variaveis.lStart:Variaveis.lEnd]
            rightEye = shape[Variaveis.rStart:Variaveis.rEnd]

            # EAR dos olhos
            leftEAR = Functions.eyeAspectRatio(leftEye)
            rightEAR = Functions.eyeAspectRatio(rightEye)

            EAR = (leftEAR + rightEAR) / 2

            # Marcação dos olhos
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)

            # Desenha no frame
            cv2.drawContours(FrameVideo, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(FrameVideo, [rightEyeHull], -1, (0, 255, 0), 1)

            # Detecção da piscada
            # EAR Tresholding - olho fechado
            if EAR < Variaveis.config["EAR"]["Tresholding"]:
                Variaveis.counter += 1  # Conta os frames do olho fechado

            # Olho aberto
            else:
                Variaveis.counter = 0

            cv2.putText(FrameVideo, "EAR: {:.2f}".format(EAR), (300, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            cv2.putText(FrameVideo, "FRAMES: {:.2f}".format(Variaveis.frames), (30, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # Definição da ação

            if (len(Variaveis.acao) < 5):  # Caso a ação não tenha sido definida

                # Caso o olho esteja fechado por mais da metade do tempo de seleção da ação
                if (len(Variaveis.acao) < 1):
                    if (Variaveis.counter > int(Variaveis.delayFrame / 2)):
                        Variaveis.acao.append(1)
                        winsound.Beep(523, 100)

                # Caso o tempo de seleção tenha acabado
                if (Variaveis.frames == Variaveis.delayFrame):

                    # Caso o olho esteja fechado por mais da metade do tempo de seleção da ação
                    if (Variaveis.counter < int(Variaveis.delayFrame / 2)):
                        Variaveis.acao.append(0)
                        winsound.Beep(523, 100)

                    else:  # Caso contrário
                        Variaveis.acao.append(1)
                        winsound.Beep(523, 100)

                    Variaveis.frames = 0

                # Começa a contar os frames a partir da primeira ação
                if (len(Variaveis.acao) >= 1):
                    Variaveis.frames += 1
            
                #Checa assinatura de comando
                if(len(Variaveis.acao) == 3):
                    if (Variaveis.acao[0] != 1 or Variaveis.acao[1] != 0 or Variaveis.acao[2] != 1):
                        winsound.Beep(698, 300)

                        Variaveis.acao = []
                        Variaveis.frames = 0
                        cv2.waitKey(Variaveis.delayFrame * Variaveis.delayTime)

            else:  # Caso a ação tenha sido definida
                # Define a ação
                Variaveis.acaoDefinida = Functions.defineAcao(Variaveis.acao)

                # Zerando as váriaveis do escopo
                Variaveis.acao = []
                Variaveis.dif = -1

                cv2.waitKey(Variaveis.delayFrame * Variaveis.delayTime)
    
        if (len(Variaveis.acao) > 0):
            acaoString = ' ' .join(map(str, Variaveis.acao))
            cv2.putText(FrameVideo, acaoString, (30, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Movimentação
        Functions.moveCarousels(Variaveis.acaoDefinida)
        
        FrameVideo = cv2.cvtColor(FrameVideo, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(FrameVideo)
        img = ImageTk.PhotoImage(image=im)
        fr.labelVideo.configure(image=img)
        fr.labelVideo.image = img
        fr.labelVideo.after(Variaveis.delayTime, Functions.getImage,fr)
    
    def convertImage(filename):
        with open(filename, 'rb') as file:
            photo = file.read()
        
        return photo
    
    def uploadImgCategory():
        Insert_Category.EntryImage.destroy()

        Insert_Category.EntryImage = ttk.LabelFrame(Insert_Category.root4, text="")
        Insert_Category.EntryImage.place(relx= 0.35, rely= 0.3, relwidth = 0.34, relheight= 0.44)

        filename = filedialog.askopenfilename(initialdir =  "../image/Carrossel/Categorias", title = "Select an Image", filetype = (("PNG  files","*.png"), ("jpeg files","*.jpg")))
        image = Image.open(filename) # Read the Image
                
        resize_image = image.resize((100, 100)) # Resize the image using resize() method
                
        show_img = ImageTk.PhotoImage(resize_image) # create label and to add the resize image

        labelImage = Label(Insert_Category.EntryImage, image=show_img)
        labelImage.image = show_img
        labelImage.pack()

        Variaveis.bytes_photoCategory = Functions.convertImage(filename)

    def uploadImgAction():
        Insert_Action.EntryImage.destroy()

        Insert_Action.EntryImage = ttk.LabelFrame(Insert_Action.root5, text="")
        Insert_Action.EntryImage.place(relx= 0.35, rely= 0.5, relwidth = 0.30, relheight= 0.40)
        
        filename = filedialog.askopenfilename(initialdir =  "../image/Carrossel/Ações", title = "Select an Image", filetype = (("PNG  files","*.png"), ("jpeg files","*.jpg")))
        image = Image.open(filename) # Read the Image
                
        resize_image = image.resize((100, 100)) # Resize the image using resize() method
                
        show_img = ImageTk.PhotoImage(resize_image) # create label and to add the resize image
        
        labelImage = Label(Insert_Action.EntryImage, image=show_img)
        labelImage.image = show_img
        labelImage.pack()

        Variaveis.bytes_photoAction = Functions.convertImage(filename)

    def voice_sound(word):
        speech_word = ''.join(word) 

        Speech().start()
        Speech().playAudio(speech_word)

    def Close_Window(flag):
        
        if(flag == 1):
            Select_Category_Edit.root6.destroy()
        elif(flag == 2):
            Select_Action_Edit.root8.destroy()
        elif(flag == 3):
            Delete_Category.root10.destroy()
        elif(flag == 4):
            Select_Category_Delete.root12.destroy()

    def db_delete_categoria():
        
        nome_categoria = Delete_Category.selectCateg.get()

        Functions.db_connect()

        Functions.cursor.execute(""" DELETE from categoria where nome_categoria = (?) """, [nome_categoria])
        Functions.conn.commit()

        Functions.cursor.execute(""" DELETE from acao where nome_categoria = (?) """, [nome_categoria])
        Functions.conn.commit()

        Functions.db_disconnect()

        Variaveis.Category_Esquerda = 0
        Variaveis.Category_Centro = 1
        Variaveis.Category_Direita = 2

        Variaveis.listaCateg = Functions.db_select_categoria()

        if(len(Variaveis.listaCateg) >= 1):
            Main.labelFotoUm.image = None
            Main.labelFotoDois.image = None
            Main.labelFotoTres.image = None

            Functions.Close_Window(3)
            Functions.Carousel_Category()
            Functions.Carousel_Action()
            Delete_Category.__init__()

        elif(len(Variaveis.listaCateg) == 0):
            Functions.Carousel_Category()
            Functions.Close_Window(3)

    def db_select_acoes_delete():
    
        Functions.db_connect()

        categoria = Select_Category_Delete.selectCateg.get()

        Functions.cursor.execute(""" SELECT nome_acao FROM acao WHERE nome_categoria = ?""", [categoria])
        Functions.conn.commit()

        return Functions.cursor.fetchall()
    
    def db_delete_acao():
        nome_acao = Delete_Action.selectAction.get()# editar

        Functions.db_connect()

        Functions.cursor.execute(""" DELETE from acao where nome_acao = (?) """, [nome_acao])
        Functions.conn.commit()

        Functions.db_disconnect()

        Variaveis.Action_Esquerda = 0
        Variaveis.Action_Centro = 1
        Variaveis.Action_Direita = 2

        listaAction = Functions.db_select_acoes_delete()

        if(len(listaAction) >= 1):
            Main.labelFotoUm.image = None
            Main.labelFotoDois.image = None
            Main.labelFotoTres.image = None

            Functions.Carousel_Action()
            Delete_Action.__init__()

        elif(len(listaAction) == 0):
            Functions.Carousel_Action()

class Main():
    #CRIAÇÃO DA MAIN
    def __init__(self):
        self.root = root
        self.root.title("speech blink")
        self.root.geometry("900x500+200+70")
        self.root.state("zoomed")
        self.root.resizable(True, True)
        self.root.configure(background='#536D80')
        self.root.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
    
        if(Functions.db_exists_database() == False):
            Functions.db_create_tables()

        self.SupEsq()
        self.InfEsq()
        self.SupDir()
        self.InfDir()

        self.root.mainloop()

    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE MAIN

    def SupEsq(self):
        #CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_SupEsq = Frame(self.root)
        Quadro_SupEsq.place(relx= 0.009, rely= 0.01, relwidth = 0.35, relheight= 0.48)

        #CRIAÇÃO DE WIDGETS DENTRO DA FRAME
        Quadro_SupEsq.labelVideo = Label(self.root)
        Quadro_SupEsq.labelVideo.place(relx=0.01, rely=0.015, relwidth=0.34, relheight=0.47)
        
        
        Functions.startCam()
        img = Functions.getImage(Quadro_SupEsq)
    
    def InfEsq(self):
        #CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_InfEsq = Frame(self.root)
        Quadro_InfEsq.place(relx= 0.009, rely= 0.51, relwidth = 0.35, relheight= 0.48)

        #CRIAÇÃO DE WIDGETS DENTRO DA FRAME

        # LABEL COM TÍTULO
        Quadro_InfEsq.labelTitulo = Label(text= "Movimentos Disponíveis", font = ("Arial", 14, 'bold'), anchor=CENTER)
        Quadro_InfEsq.labelTitulo.place(relx= 0.02, rely= 0.52, relwidth = 0.33, relheight= 0.06)
        
        # LABEL COM AÇÃO UM
        Main.labelDireita = Label(text= "", font = ("Lucida", 12, 'bold'), anchor=CENTER)
        Main.labelDireita.place(relx= 0.02, rely= 0.60, relwidth = 0.33, relheight= 0.08)

        # LABEL COM AÇÃO DOIS
        Main.labelEsquerda = Label(text= "", font = ("Lucida", 12, 'bold'), anchor=CENTER)
        Main.labelEsquerda.place(relx= 0.02, rely= 0.66, relwidth = 0.33, relheight= 0.08)
        
        # LABEL COM AÇÃO TRÊS
        Main.labelConfirmar = Label(text= "", font = ("Lucida", 12, 'bold'), anchor=CENTER)
        Main.labelConfirmar.place(relx= 0.02, rely= 0.72, relwidth = 0.33, relheight= 0.08)

        # LABEL COM AÇÃO QUATRO
        Main.labelVoltar = Label(text= "", font = ("Lucida", 12, 'bold'), anchor=CENTER)
        Main.labelVoltar.place(relx= 0.02, rely= 0.78, relwidth = 0.33, relheight= 0.08)

        # LABEL COM AÇÃO ANTERIOR
        Main.labelAcaoAnterior = Label(text= "Anterior: Nenhuma", font = ("Lucida", 12, 'bold'), anchor=CENTER)
        Main.labelAcaoAnterior.place(relx= 0.02, rely= 0.88, relwidth = 0.33, relheight= 0.08)

    def SupDir(self):
        #CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_SupDir = Frame(self.root)
        Quadro_SupDir.place(relx= 0.37, rely= 0.01, relwidth = 0.62, relheight= 0.48)

        #CRIAÇÃO DE WIDGETS DENTRO DA FRAME
        Main.IconeEsquerdaCategory = Label(text="", font=("Arial", 25, 'bold'), fg="#075E54", anchor=CENTER)
        Main.IconeEsquerdaCategory.place(relx=0.37, rely=0.25)

        Main.IconeDireitaCategory = Label(text="", font=("Arial", 25, 'bold'), fg="#075E54", anchor=CENTER)
        Main.IconeDireitaCategory.place(relx=0.97, rely=0.25)

        Quadro_SupDir.Labeltitulo = Label(text="Seleção de Categoria", font=("Arial", 14, 'bold'), anchor=CENTER)
        Quadro_SupDir.Labeltitulo.place(relx=0.62, rely=0.015)

        Quadro_SupDir.buttonCategory = Button(text="+", command=Config_Category.__init__)
        Quadro_SupDir.buttonCategory.place(relx=0.78, rely=0.015)

        Main.messageCategory = Label(text="", fg='red', font=("Arial", 9, "underline"),  anchor=CENTER)
        Main.messageCategory.place(relx=0.37, rely=0.1, relwidth=0.62)

        if(Functions.db_exists_categoria() == []):
            Main.messageCategory['text'] = "Não há categorias para selecionar. Por favor, clique no '+' e cadastre alguma!"
        else:
            Main.IconeEsquerdaCategory['text'] = "<"
            Main.IconeDireitaCategory['text'] = ">"
            
            # EXIBIR BOTÃO PARA INSERÇÃO DE CATEGORIAS
            Main.buttonAction = Button(text="+", command=Config_Action.__init__)
            Main.buttonAction.place(relx=0.75, rely=0.52)

            Main.messageCategory['text'] = ""
            
            Functions.Carousel_Category()

    def InfDir(self):
        #CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_InfDir = Frame(self.root)
        Quadro_InfDir.place(relx= 0.37, rely= 0.51, relwidth = 0.62, relheight= 0.48)
        
        #CRIAÇÃO DE WIDGETS DENTRO DA FRAME
        Main.IconeEsquerdaAction = Label(text="", font=("Arial", 25, 'bold'), fg="#075E54", anchor=CENTER)
        Main.IconeEsquerdaAction.place(relx=0.37, rely=0.73)

        Main.IconeDireitaAction = Label(text="", font=("Arial", 25, 'bold'), fg="#075E54", anchor=CENTER)
        Main.IconeDireitaAction.place(relx=0.97, rely=0.73)

        Quadro_InfDir.Labeltitulo = Label(text="Seleção de Ação", font=("Arial", 14, 'bold'), anchor=CENTER)
        Quadro_InfDir.Labeltitulo.place(relx=0.38, rely=0.52, relwidth = 0.60)

        Main.messageAction = Label(text="", fg='red', font=("Arial", 8, "underline"),  anchor=CENTER)
        Main.messageAction.place(relx=0.37, rely=0.60, relwidth=0.62)

        if(Functions.db_exists_categoria() == []):
            Main.messageAction['text'] = "Não há ações sem categorias. Por favor, clique no '+' na Seleção de categorias e cadastre alguma!"
        else:
            Main.messageAction['text'] = ""

            Functions.Carousel_Action()

class Config_Category():
    #CRIAÇÃO DA JANELA
    def __init__():
        Config_Category.root2 = Toplevel()
        Config_Category.root2.title("speech blink - Configurações de Categorias")
        Config_Category.root2.geometry("490x340+0+0")
        Config_Category.root2.resizable(True, True)
        Config_Category.root2.configure(background='#128C7E')
        Config_Category.root2.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Config_Category.root2.transient(root)
        Config_Category.root2.focus_force()
        Config_Category.root2.grab_set()

        Config_Category.Quadro()

        Config_Category.root2.mainloop()

    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Config_Category.root2)
        Quadro_Unico.place(relx=0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Config_Category.Labeltitulo = Label(Config_Category.root2, text="Configuração de Categorias", font='verdana 14 bold', anchor=CENTER)
        Config_Category.Labeltitulo.place(relx=0.1, rely=0.2, relwidth = 0.8)

        #3 CRIAÇÃO DE BUTTON PARA O CADASTRO DE UMA CATEGORIA
        Config_Category.AddCategory = Button(Config_Category.root2, text="Adicionar", command=Insert_Category.__init__)
        Config_Category.AddCategory.place(relx=0.3, rely=0.43, relwidth = 0.4)

        #4 CRIAÇÃO DE BUTTON PARA A EDIÇÃO DE UMA CATEGORIA JÁ CADASTRADA
        Config_Category.EditCategory = Button(Config_Category.root2, text="Editar", command=Select_Category_Edit.__init__)
        Config_Category.EditCategory.place(relx=0.3, rely=0.53, relwidth = 0.4)

        #4 CRIAÇÃO DE BUTTON PARA A EXCLUSÃO DE UMA CATEGORIA JÁ CADASTRADA
        Config_Category.DeleteCategory = Button(Config_Category.root2, text="Excluir", command=Delete_Category.__init__)
        Config_Category.DeleteCategory.place(relx=0.3, rely=0.63, relwidth = 0.4)

class Config_Action():
    #CRIAÇÃO DA JANELA
    def __init__():
        Config_Action.root3 = Toplevel()
        Config_Action.root3.title("speech blink - Configurações de Ações")
        Config_Action.root3.geometry("490x340+0+0")
        Config_Action.root3.resizable(True, True)
        Config_Action.root3.configure(background='#128C7E')
        Config_Action.root3.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Config_Action.root3.transient(root)
        Config_Action.root3.focus_force()
        Config_Action.root3.grab_set()

        Config_Action.Quadro()

        Config_Action.root3.mainloop()

    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Config_Action.root3)
        Quadro_Unico.place(relx=0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Config_Action.Labeltitulo = Label(Config_Action.root3, text="Configuração de Ações", font='verdana 14 bold', anchor=CENTER)
        Config_Action.Labeltitulo.place(relx=0.1, rely=0.2, relwidth = 0.8)

        #3 CRIAÇÃO DE BUTTON PARA O CADASTRO DE UMA AÇÃO
        Config_Action.AddCategory = Button(Config_Action.root3, text="Adicionar", command=Insert_Action.__init__)
        Config_Action.AddCategory.place(relx=0.3, rely=0.43, relwidth = 0.4)

        #4 CRIAÇÃO DE BUTTON PARA A EDIÇÃO DE UMA AÇÃO JÁ CADASTRADA
        Config_Action.EditCategory = Button(Config_Action.root3, text="Editar", command=Select_Action_Edit.__init__)
        Config_Action.EditCategory.place(relx=0.3, rely=0.53, relwidth = 0.4)

        #4 CRIAÇÃO DE BUTTON PARA A EXCLUSÃO DE UMA AÇÃO JÁ CADASTRADA
        Config_Action.DeleteCategory = Button(Config_Action.root3, text="Excluir", command=Select_Category_Delete.__init__)
        Config_Action.DeleteCategory.place(relx=0.3, rely=0.63, relwidth = 0.4)

class Insert_Category():

    def __init__():
        Insert_Category.root4 = Toplevel()
        Insert_Category.root4.title("speech blink - Cadastro de Ações")
        Insert_Category.root4.geometry("490x340+0+0")
        Insert_Category.root4.resizable(True, True)
        Insert_Category.root4.configure(background='#128C7E')
        Insert_Category.root4.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Insert_Category.root4.transient(root)
        Insert_Category.root4.focus_force()
        Insert_Category.root4.grab_set()

        Insert_Category.Quadro()

        Insert_Category.root4.mainloop()
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1. CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Insert_Category.root4)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2. CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Insert_Category.Labeltitulo = Label(Insert_Category.root4, text="Cadastro de Categoria", font='verdana 14 bold', anchor=CENTER)
        Insert_Category.Labeltitulo.place(relx=0.1, rely=0.015, relwidth = 0.8)

        #2.2 CRIAÇÃO DE LABEL COM ENTRY PARA NOME DA CATEGORIA, NA LINHA 2
        Insert_Category.LabelNomeCateg = Label(Insert_Category.root4, text="Nome ")
        Insert_Category.LabelNomeCateg.place(relx= 0.18, rely= 0.15, relwidth = 0.2, relheight= 0.1)

        #2.2 CRIAÇÃO DE  ENTRY PARA NOME DA CATEGORIA, NA LINHA 2
        Insert_Category.EntryNomeCateg = Entry(Insert_Category.root4, font='10')
        Insert_Category.EntryNomeCateg.place(relx= 0.35, rely= 0.15, relwidth = 0.4, relheight= 0.10)

        Insert_Category.buttonAddImage = Button(Insert_Category.root4, text="+", command=Functions.uploadImgCategory)
        Insert_Category.buttonAddImage.place(relx=0.25, rely=0.33)

        Insert_Category.EntryImage = ttk.LabelFrame(Insert_Category.root4, text="")
        Insert_Category.EntryImage.place(relx= 0.35, rely= 0.3, relwidth = 0.34, relheight= 0.44)

        #2.3 CRIAÇÃO DO BOTÃO PARA INSERÇÃO DA CATEGORIA NO BANCO DE DADOS, NA LINHA 3
        Insert_Category.Buttonsign = Button(Insert_Category.root4,text="Cadastrar", font='montserrat', command=Functions.db_insert_categoria)
        Insert_Category.Buttonsign.place(relx= 0.35, rely= 0.85, relwidth = 0.30, relheight= 0.10)

class Insert_Action():
    #CRIAÇÃO DA JANELA
    def __init__():
        Insert_Action.root5 = Toplevel()
        Insert_Action.root5.title("speech blink - Cadastro de Ações")
        Insert_Action.root5.geometry("490x340+0+0")
        Insert_Action.root5.resizable(True, True)
        Insert_Action.root5.configure(background='#128C7E')
        Insert_Action.root5.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Insert_Action.root5.transient(root)
        Insert_Action.root5.focus_force()
        Insert_Action.root5.grab_set()

        Insert_Action.Quadro()

        Insert_Action.root5.mainloop()
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Insert_Action.root5)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)
        

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Insert_Action.Labeltitulo = Label(Insert_Action.root5, text="Cadastro de Ações", font='verdana 14 bold', anchor=CENTER)
        Insert_Action.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Insert_Action.LabelNomeCateg = Label(Insert_Action.root5, text="Categoria: ")
        Insert_Action.LabelNomeCateg.place(relx= 0.15, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Variaveis.listaCateg = Functions.db_select_categoria()

        Insert_Action.selectCateg = ttk.Combobox(Insert_Action.root5, values=Variaveis.listaCateg)
        Insert_Action.selectCateg.place(relx= 0.35, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        #2.4 CRIAÇÃO DA LABEL COM ENTRY PARA NOME DA AÇÃO, NA LINHA 3
        Insert_Action.LabelNomeAcao = Label(Insert_Action.root5, text="Nome ")
        Insert_Action.LabelNomeAcao.place(relx= 0.15, rely= 0.4, relwidth = 0.2, relheight= 0.1)

        Insert_Action.EntryNomeAcao = Entry(Insert_Action.root5, font='10')
        Insert_Action.EntryNomeAcao.place(relx= 0.35, rely= 0.4, relwidth = 0.4, relheight= 0.08)

        Insert_Action.buttonAddImage = Button(Insert_Action.root5, text="+", command=Functions.uploadImgAction)
        Insert_Action.buttonAddImage.place(relx=0.25, rely=0.53)

        Insert_Action.EntryImage = ttk.LabelFrame(Insert_Action.root5, text="")
        Insert_Action.EntryImage.place(relx= 0.35, rely= 0.5, relwidth = 0.30, relheight= 0.40)

        #2.5 CRIAÇÃO DO BOTÃO PARA INSERÇÃO DA AÇÃO NO BANCO DE DADOS, NA LINHA 4
        Insert_Action.Buttonsign = Button(Insert_Action.root5, text="Cadastrar", font='montserrat', command=Functions.db_insert_acao)
        Insert_Action.Buttonsign.place(relx= 0.35, rely= 0.90, relwidth = 0.3, relheight= 0.08)

class Select_Category_Edit():
    #CRIAÇÃO DA JANELA
    def __init__():
        Select_Category_Edit.root6 = Toplevel()
        Select_Category_Edit.root6.title("speech blink - Selecione uma Categoria para editar")
        Select_Category_Edit.root6.geometry("490x340+0+0")
        Select_Category_Edit.root6.resizable(True, True)
        Select_Category_Edit.root6.configure(background='#128C7E')
        Select_Category_Edit.root6.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Select_Category_Edit.root6.transient(root)
        Select_Category_Edit.root6.focus_force()
        Select_Category_Edit.root6.grab_set()

        Select_Category_Edit.Quadro()

        Select_Category_Edit.root6.mainloop()
    
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Select_Category_Edit.root6)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Select_Category_Edit.Labeltitulo = Label(Select_Category_Edit.root6, text="Categoria para Edição", font='verdana 14 bold', anchor=CENTER)
        Select_Category_Edit.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Select_Category_Edit.LabelNomeCateg = Label(Select_Category_Edit.root6, text="Categoria: ")
        Select_Category_Edit.LabelNomeCateg.place(relx= 0.1, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Variaveis.listaCateg = Functions.db_select_categoria()

        Select_Category_Edit.selectCateg = ttk.Combobox(Select_Category_Edit.root6, values=Variaveis.listaCateg)
        Select_Category_Edit.selectCateg.place(relx= 0.30, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        Select_Category_Edit.EditCategory = Button(Select_Category_Edit.root6, text="Editar", command=Edit_Category.__init__)
        Select_Category_Edit.EditCategory.place(relx=0.35, rely=0.43, relwidth = 0.3)

class Edit_Category():
    #CRIAÇÃO DA JANELA
    def __init__():
        Edit_Category.root7 = Toplevel()
        Edit_Category.root7.title("speech blink - Editar Categoria")
        Edit_Category.root7.geometry("490x340+0+0")
        Edit_Category.root7.resizable(True, True)
        Edit_Category.root7.configure(background='#128C7E')
        Edit_Category.root7.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Edit_Category.root7.transient(root)
        Edit_Category.root7.focus_force()
        Edit_Category.root7.grab_set()

        Functions.Close_Window(1)
        Edit_Category.Quadro()

        Edit_Category.root7.mainloop()

    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Edit_Category.root7)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Edit_Category.Labeltitulo = Label(Edit_Category.root7, text="Categoria para Edição", font='verdana 14 bold', anchor=CENTER)
        Edit_Category.Labeltitulo.place(relx=0.1, rely=0.05, relwidth = 0.8)

        Edit_Category.LabelNomeCateg = Label(Edit_Category.root7, text="Nome ")
        Edit_Category.LabelNomeCateg.place(relx= 0.18, rely= 0.15, relwidth = 0.2, relheight= 0.1)

        #2.2 CRIAÇÃO DE  ENTRY PARA NOME DA CATEGORIA, NA LINHA 2
        Edit_Category.EntryNomeCateg = Entry(Edit_Category.root7, font='10')
        Edit_Category.EntryNomeCateg.place(relx= 0.35, rely= 0.15, relwidth = 0.4, relheight= 0.10)

        Edit_Category.buttonAddImage = Button(Edit_Category.root7, text="+", command=Functions.uploadImgCategory)
        Edit_Category.buttonAddImage.place(relx=0.25, rely=0.33)

        Edit_Category.EntryImage = ttk.LabelFrame(Edit_Category.root7, text="")
        Edit_Category.EntryImage.place(relx= 0.35, rely= 0.3, relwidth = 0.34, relheight= 0.44)

        #2.3 CRIAÇÃO DO BOTÃO PARA INSERÇÃO DA CATEGORIA NO BANCO DE DADOS, NA LINHA 3
        Edit_Category.Buttonsign = Button(Edit_Category.root7,text="Editar", font='montserrat')
        Edit_Category.Buttonsign.place(relx= 0.35, rely= 0.85, relwidth = 0.30, relheight= 0.10)

class Select_Category_From_Action_Edit():
    #CRIAÇÃO DA JANELA
    def __init__():
        Select_Category_From_Action_Edit.root8 = Toplevel()
        Select_Category_From_Action_Edit.root8.title("speech blink - Editar Ação")
        Select_Category_From_Action_Edit.root8.geometry("490x340+0+0")
        Select_Category_From_Action_Edit.root8.resizable(True, True)
        Select_Category_From_Action_Edit.root8.configure(background='#128C7E')
        Select_Category_From_Action_Edit.root8.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Select_Category_From_Action_Edit.root8.transient(root)
        Select_Category_From_Action_Edit.root8.focus_force()
        Select_Category_From_Action_Edit.root8.grab_set()

        Select_Category_From_Action_Edit.Quadro()

        Select_Category_From_Action_Edit.root8.mainloop()
    
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Select_Category_From_Action_Edit.root8)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Select_Category_From_Action_Edit.Labeltitulo = Label(Select_Category_From_Action_Edit.root8, text="Categoria da Ação para Edição", font='verdana 14 bold', anchor=CENTER)
        Select_Category_From_Action_Edit.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Select_Category_From_Action_Edit.LabelNomeCateg = Label(Select_Category_From_Action_Edit.root8, text="Categoria: ")
        Select_Category_From_Action_Edit.LabelNomeCateg.place(relx= 0.1, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Variaveis.listaCateg = Functions.db_select_categoria()

        Select_Category_From_Action_Edit.selectCateg = ttk.Combobox(Select_Category_From_Action_Edit.root8, values=Variaveis.listaCateg)
        Select_Category_From_Action_Edit.selectCateg.place(relx= 0.30, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        Select_Category_From_Action_Edit.EditCategory = Button(Select_Category_From_Action_Edit.root8, text="Editar", command=Edit_Action.__init__)
        Select_Category_From_Action_Edit.EditCategory.place(relx=0.35, rely=0.43, relwidth = 0.3)


class Select_Action_Edit():
    #CRIAÇÃO DA JANELA
    def __init__():
        Select_Action_Edit.root13 = Toplevel()
        Select_Action_Edit.root13.title("Editar")
        Select_Action_Edit.root13.geometry("490x340+0+0")
        Select_Action_Edit.root13.resizable(True, True)
        Select_Action_Edit.root13.configure(background='#128C7E')
        Select_Action_Edit.root13.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Select_Action_Edit.root13.transient(root)
        Select_Action_Edit.root13.focus_force()
        Select_Action_Edit.root13.grab_set()

        Select_Action_Edit.Quadro()
    
        Select_Action_Edit.root13.mainloop()
    
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Select_Action_Edit.root13)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Select_Action_Edit.Labeltitulo = Label(Select_Action_Edit.root13, text="Selecione a Ação para editar", font='verdana 14 bold', anchor=CENTER)
        Select_Action_Edit.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Select_Action_Edit.LabelNomeAction = Label(Select_Action_Edit.root13, text="Ações: ")
        Select_Action_Edit.LabelNomeAction.place(relx= 0.1, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        #Select_Action_Edit.listaAction = A Q U I

        Select_Action_Edit.selectAction = ttk.Combobox(Select_Action_Edit.root13, values=Select_Action_Edit.listaAction)
        Select_Action_Edit.selectAction.place(relx= 0.30, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        Select_Action_Edit.EditAction = Button(Select_Action_Edit.root13, text="Selecionar", command=Edit_Action.__init__)
        Select_Action_Edit.EditAction.place(relx=0.35, rely=0.43, relwidth = 0.2)
''''''

class Edit_Action():
    #CRIAÇÃO DA JANELA
    def __init__():
        Edit_Action.root9 = Toplevel()
        Edit_Action.root9.title("speech blink - Selecionar Ação")
        Edit_Action.root9.geometry("490x340+0+0")
        Edit_Action.root9.resizable(True, True)
        Edit_Action.root9.configure(background='#128C7E')
        Edit_Action.root9.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Edit_Action.root9.transient(root)
        Edit_Action.root9.focus_force()
        Edit_Action.root9.grab_set()

        Functions.Close_Window(2)
        Edit_Action.Quadro()

        Edit_Action.root9.mainloop()

    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Edit_Action.root9)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)
        
        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Edit_Action.Labeltitulo = Label(Edit_Action.root9, text="Edição de Ação", font='verdana 14 bold', anchor=CENTER)
        Edit_Action.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Edit_Action.LabelNomeCateg = Label(Edit_Action.root9, text="Categoria: ")
        Edit_Action.LabelNomeCateg.place(relx= 0.15, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Variaveis.listaCateg = Functions.db_select_categoria()

        Edit_Action.selectCateg = ttk.Combobox(Edit_Action.root9, values=Variaveis.listaCateg)
        Edit_Action.selectCateg.place(relx= 0.35, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        #2.4 CRIAÇÃO DA LABEL COM ENTRY PARA NOME DA AÇÃO, NA LINHA 3
        Edit_Action.LabelNomeAcao = Label(Edit_Action.root9, text="Nome ")
        Edit_Action.LabelNomeAcao.place(relx= 0.15, rely= 0.4, relwidth = 0.2, relheight= 0.1)

        Edit_Action.EntryNomeAcao = Entry(Edit_Action.root9, font='10')
        Edit_Action.EntryNomeAcao.place(relx= 0.35, rely= 0.4, relwidth = 0.4, relheight= 0.08)

        Edit_Action.buttonAddImage = Button(Edit_Action.root9, text="+", command=Functions.uploadImgAction)
        Edit_Action.buttonAddImage.place(relx=0.25, rely=0.53)

        Edit_Action.EntryImage = ttk.LabelFrame(Edit_Action.root9, text="")
        Edit_Action.EntryImage.place(relx= 0.35, rely= 0.5, relwidth = 0.30, relheight= 0.40)

        #2.5 CRIAÇÃO DO BOTÃO PARA INSERÇÃO DA AÇÃO NO BANCO DE DADOS, NA LINHA 4
        Edit_Action.Buttonsign = Button(Edit_Action.root9, text="Cadastrar", font='montserrat', command=Functions.db_insert_acao)
        Edit_Action.Buttonsign.place(relx= 0.35, rely= 0.90, relwidth = 0.3, relheight= 0.08)

class Delete_Category():
    #CRIAÇÃO DA JANELA
    def __init__():
        Delete_Category.root10 = Toplevel()
        Delete_Category.root10.title("speech blink - Selecione uma Categoria para editar")
        Delete_Category.root10.geometry("490x340+0+0")
        Delete_Category.root10.resizable(True, True)
        Delete_Category.root10.configure(background='#128C7E')
        Delete_Category.root10.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Delete_Category.root10.transient(root)
        Delete_Category.root10.focus_force()
        Delete_Category.root10.grab_set()

        Delete_Category.Quadro()

        Delete_Category.root10.mainloop()
    
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Delete_Category.root10)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Delete_Category.Labeltitulo = Label(Delete_Category.root10, text="Categoria para Edição", font='verdana 14 bold', anchor=CENTER)
        Delete_Category.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Delete_Category.LabelNomeCateg = Label(Delete_Category.root10, text="Categoria: ")
        Delete_Category.LabelNomeCateg.place(relx= 0.1, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Variaveis.listaCateg = Functions.db_select_categoria()

        Delete_Category.selectCateg = ttk.Combobox(Delete_Category.root10, values=Variaveis.listaCateg)
        Delete_Category.selectCateg.place(relx= 0.30, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        Delete_Category.EditCategory = Button(Delete_Category.root10, text="Excluir", command=Functions.db_delete_categoria)
        Delete_Category.EditCategory.place(relx=0.35, rely=0.43, relwidth = 0.3)

#Seleção de categoria para excluir suas ações
class Select_Category_Delete():
    #CRIAÇÃO DA JANELA
    def __init__():
        Select_Category_Delete.root11 = Toplevel()
        Select_Category_Delete.root11.title("Editar")
        Select_Category_Delete.root11.geometry("490x340+0+0")
        Select_Category_Delete.root11.resizable(True, True)
        Select_Category_Delete.root11.configure(background='#128C7E')
        Select_Category_Delete.root11.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Select_Category_Delete.root11.transient(root)
        Select_Category_Delete.root11.focus_force()
        Select_Category_Delete.root11.grab_set()

        Select_Category_Delete.Quadro()

        Select_Category_Delete.root11.mainloop()
    
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Select_Category_Delete.root11)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Select_Category_Delete.Labeltitulo = Label(Select_Category_Delete.root11, text="Categoria para excluir suas Ações", font='verdana 14 bold', anchor=CENTER)
        Select_Category_Delete.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Select_Category_Delete.LabelNomeCateg = Label(Select_Category_Delete.root11, text="Categoria: ")
        Select_Category_Delete.LabelNomeCateg.place(relx= 0.1, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Variaveis.listaCateg = Functions.db_select_categoria()

        Select_Category_Delete.selectCateg = ttk.Combobox(Select_Category_Delete.root11, values=Variaveis.listaCateg)
        Select_Category_Delete.selectCateg.place(relx= 0.30, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        Select_Category_Delete.EditCategory = Button(Select_Category_Delete.root11, text="OK", command=Delete_Action.__init__)
        Select_Category_Delete.EditCategory.place(relx=0.35, rely=0.43, relwidth = 0.2)

class Delete_Action():
    #CRIAÇÃO DA JANELA
    def __init__():
        Delete_Action.root12 = Toplevel()
        Delete_Action.root12.title("Editar")
        Delete_Action.root12.geometry("490x340+0+0")
        Delete_Action.root12.resizable(True, True)
        Delete_Action.root12.configure(background='#128C7E')
        Delete_Action.root12.iconbitmap("../image/icone.ico")#Define o caminho até uma imagem do tipo icone (.ICO), definindo-a como icone padrão. O caminho é relativo ao script.
        Delete_Action.root12.transient(root)
        Delete_Action.root12.focus_force()
        Delete_Action.root12.grab_set()

        Delete_Action.Quadro()
    
        Delete_Action.root12.mainloop()
    
    #CRIAÇÃO DE WIDGETS DENTRO DA CLASSE JANELA
    def Quadro():
        #1.CRIAÇÃO DE FRAME DENTRO DE ROOT
        Quadro_Unico = Frame(Delete_Action.root12)
        Quadro_Unico.place(relx= 0.009, rely= 0.01, relwidth = 0.98, relheight= 0.98)

        #2.CRIAÇÃO DE WIDGETS DENTRO DE FRAME

        #2.1 CRIAÇÃO DE LABEL PARA TÍTULO DO FRAME, NA LINHA 1
        Delete_Action.Labeltitulo = Label(Delete_Action.root12, text="Selecione a Ação para excluir", font='verdana 14 bold', anchor=CENTER)
        Delete_Action.Labeltitulo.place(relx=0.1, rely=0.1, relwidth = 0.8)

        #2.2 CRIAÇÃO DA LABEL COM COMBOBOX, NA LINHA 2
        Delete_Action.LabelNomeAction = Label(Delete_Action.root12, text="Ações: ")
        Delete_Action.LabelNomeAction.place(relx= 0.1, rely= 0.25, relwidth = 0.2, relheight= 0.1)

        #VARIÁVEL QUE RECEBE OS VALORES DE CADA OPÇÃO DO COMBOBOX
        Delete_Action.listaAction = Functions.db_select_acoes_delete()

        Delete_Action.selectAction = ttk.Combobox(Delete_Action.root12, values=Delete_Action.listaAction)
        Delete_Action.selectAction.place(relx= 0.30, rely= 0.25, relwidth = 0.4, relheight= 0.08)

        Delete_Action.EditAction = Button(Delete_Action.root12, text="excluir", command=Functions.db_delete_acao)
        Delete_Action.EditAction.place(relx=0.35, rely=0.43, relwidth = 0.2)

Main()