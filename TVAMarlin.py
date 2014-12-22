# -*- coding: utf-8 -*-
"""
Editor de Spyder

Aplicaciçon: TVA Test de Velocidad y Aceleración para firmware Marlin v1.0.0

Autor: Rafael Torres rtorresca en yahoo punto es

Licencia: CC-by-nc-sa
Condiciones adicionales a la Licencia: Ningún tipo de restricción, registro
o compensación será requerido para acceder al código o a los productos
derivados, debiendo ser el acceso libre y directo.
1.- hacer publicas y accesibles a todo el mundo, sin condiciones ni
requisitos de ningún tipo (como registros, etc.) al código completo
derivado de este código.
2.- comunicar las modificacones y código completo resultante de
dichas modificaciones al autor, en la dirección de email antes indicada
"""


""" Comienzo de la comunicación y configuración con Marlin
start
echo: External Reset
Marlin 1.0.0
echo: Last Updated: Aug  6 2014 06:59:30 | Author: (none, default config)
Compiled: Aug  6 2014
echo: Free Memory: 5241  PlannerBufferBytes: 1232
echo:Hardcoded Default Settings Loaded
echo:Steps per unit:
echo:  M92 X80.45 Y80.76 Z4000.00 E630.00
echo:Maximum feedrates (mm/s):
echo:  M203 X200.00 Y200.00 Z2.50 E30.00
echo:Maximum Acceleration (mm/s2):
echo:  M201 X2000 Y2000 Z100 E10000
echo:Acceleration: S=acceleration, T=retract acceleration
echo:  M204 S500.00 T500.00
echo:Advanced variables: S=Min feedrate (mm/s), T=Min travel feedrate (mm/s), B=minimum segment time (ms), X=maximum XY jerk (mm/s),  Z=maximum Z jerk (mm/s),  E=maximum E jerk (mm/s)
echo:  M205 S0.00 T0.00 B20000 X0.10 Z0.10 E1.00
echo:Home offset (mm):
echo:  M206 X0.00 Y0.00 Z0.00
echo:PID settings:
echo:   M301 P23.30 I0.89 D153.05
TEST: eje:X v: 40.0 a: 500.0
SEND:G1 Z10 F400
SinResultadoenReadSEND:M201 X500.0 Y500.0
SinResultadoenReadSEND:M202 X500.0 Y500.0
ok
ok
ok
ok
SEND:G28 X
"""


import os
import time
import numpy as np

import tkFont

import re

print os.name

if True:
    import serial
    from serial.tools import *
    import serial.tools.list_ports

finaldecarrera = False
pc = None
straxis = "XYZE"
defaultPort='COM1'
defaultbr=250000

#from Tkinter import *
from Tix import *
root = 0

class TestAxis:
    def __init__(self):
        self.axis = 'E'
        self.check = False
        self.vmin = 0
        self.vmax = 0
        self.vnp = 0
        self.amin = 0
        self.amax = 0
        self.anp = 0
        self.dist = 0
        self.nrep = 0

    def mprint(self):
        print self.axis, self.check, self.vmin, self.vmax, self.vnp, \
            self.amin, self.amax, self.anp, self.dist, self.nrep


#####
## ATención: cambiar el puerto de conexión. Por defecto está en COM3
## si tu impresora no está ahí.... cámbialo
#######

class PrinterConnection:
    def __init__(self, port=defaultPort, br=defaultbr, timeout=0):

        self.port    = port
        self.br      = br
        self.timeout = timeout
        self.lpftdi = []
        self.conectada = False

        try:
            self.log = open("Calibration.txt", "wb")
        except IOError:
            self.log.close()


    def list_ports(self):
        self.lpftdi = []
        listports =  serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(listports):
            # print "%s: %s [%s]" % (port, desc, hwid)
            if 'FTDI' in hwid:
                print "puerto posible encontrado: %s: %s [%s]" % (port, desc, hwid)
                self.lpftdi.append([port, desc])

    def open(self, port=defaultPort, br=defaultbr, timeout=0):
        if self.conectada is True:
            self.ser.close()
            self.conectada = False
        try:
            self.ser = serial.Serial(port, self.br, timeout=self.timeout)
            self.conectada = True
        except IOError:
            self.ser.close()
        time.sleep(0.2)

    def send(self, msg):
        if self.conectada == False:
            print "Impresora no conectada"
            return
        r = self.ser.write(msg.upper()+"\n")
        self.ser.flush()
        self.log.write("SEND:"+str(msg)+"\n")
        self.log.flush()

    def sendGCode(self, msg, resp=False):
        findecarrera = False
        self.send(msg)
        time.sleep(0.4)
        l = self.read()
        CheckRead(l)
        if resp: #si resp es True, devuelve la lectura realizada
            return l

    def read(self):
        # l = self.ser.readlines()
        if self.conectada == False:
            return ""
        ct = time.clock()
        while True:
            niw = self.ser.inWaiting()
            if niw > 0:
                time.sleep(0.5)
                l = self.ser.readlines()
                break
            time.sleep(1)
            if time.clock()-ct > 60:
                l = "SinResultadoenRead"
                break

        self.log.writelines(l)
        self.log.flush()
        return l

    # def readPosition(self):
    #     pass

    def close(self):
        if self.conectada == True:
            self.ser.close()

pc = PrinterConnection()
pc.list_ports()

def CheckRead(l):
    global finaldecarrera
    if type(l) is list:
        for i in range(len(l)):
            if 'endstops hit' in l[i]:
                finaldecarrera = True
                break
        pass
    pass



#==============================================================================
# Prueba un caso concreto
#==============================================================================
class TestCase:
    def __init__(self, axis, dist, vel, accel, xyjerk, zjerk, nreps=2):
        self.axis = axis
        self.dist = dist
        self.vel = vel
        self.accel = accel
        self.xyjerk = xyjerk
        self.zjerk = zjerk
        self.nreps = nreps

        # ¿Da tiempo a alcanzar la velocidad máxima o hay que frenar antes
        # de acabar de acelerar?
        modulo = vel / accel
        distacelerando = accel * modulo**2 / 2
        if distacelerando * 2 > dist:
            self.status = False
        else:
            self.status = True
            # print axis, dist, vel, accel, xyjerk, zjerk, self.status
        # probar todos, incluso los lentos
        self.status = True

        self.fails = 0
        self.checked = False
    def myprint(self):
        # if self.status == False:
        #     return
        print self._msg_print()

    def printlog(self):
        pc.log.writelines(self._msg_print()+"\n")

    def _msg_print(self):
        msg = "TC axis " + straxis[self.axis] + " V: " + str(self.vel) +\
            " A: " + str(self.accel) + " fails: " + str(self.fails)+"/"+\
            str(self.nreps) + " Checked: " + str(self.checked)
        return msg

def ListaTestCases(listaTestAxis):
    tc = []

    for ta in listaTestAxis:

        ax = ta.axis
        check = ta.check
        if check == False:
            continue
        dist = ta.dist
        nr = ta.nrep
        vmin = ta.vmin
        vmax = ta.vmax
        nsteps = ta.vnp
        if nsteps < 1:
            nsteps = 1
        nsteps = int(nsteps)
        for v in np.linspace(vmin, vmax, nsteps):
            amin = ta.amin
            amax = ta.amax
            asteps = ta.anp
            if asteps < 1:
                asteps = 1
            asteps = int(asteps)
            for a in np.linspace(amin, amax, asteps):
                ntc = TestCase(ax, dist, float(v), float(a), 50.0, 30.0, nr)
                if ntc.status == True:
                    tc.append(ntc)
    return tc


def enable_endstops_checking():
    pc.sendGCode("M121")


def CheckTestCase(pc, tc):
    '''Ejecuta un caso de prueba y comprueba resultado
    '''
    global finaldecarrera

    if tc.axis == 2: #♥ special actions for z testing
        testZ = True
    else:
        testZ = False

    if testZ:
        erroradm = 0.05
    else:
        erroradm = 0.05

    velretorno = [500, 2]

    msg = "TEST: eje:{0} v: {1} a: {2}".format(straxis[tc.axis], tc.vel,
                                            tc.accel)
    print msg
    pc.log.write(msg+'\n')

    # pc.sendGCode("G28 X0 Y0 Z0")
    if testZ:
        pc.sendGCode("G1 Z5 F500")
        pc.sendGCode("G1 X90 Y90 F500")
	else:
        pc.sendGCode("G1 Z10 F400")

    if testZ:
        pc.sendGCode("M201 Z{0}".format(tc.accel))
        #pc.sendGCode("M202 Z{0}".format(tc.accel))
    else:
        pc.sendGCode("M201 X{0} Y{1}".format(tc.accel, tc.accel))
        #pc.sendGCode("M202 X{0} Y{1}".format(tc.accel, tc.accel))

    if tc.axis == 0:
        pc.sendGCode("G1 Y10")
    if tc.axis == 1:
        pc.sendGCode("G1 X10")

	pc.sendGCode("M121")

    for i in range(tc.nreps):
        pc.sendGCode("G28 {0} ".format(straxis[tc.axis]))

        if testZ:
            pc.sendGCode("M203 X500 Y500 Z{0}".format(tc.vel))
        else:
            pc.sendGCode("M203 X{0} Y{0}".format(tc.vel))

        pc.sendGCode("G1 {0}{1} F{2}".format(straxis[tc.axis], tc.dist,\
                     tc.vel * 60))
        pc.sendGCode("M400")

        pc.sendGCode("M203 X{0} Y{0} Z{1}".format(velretorno[0],
                     velretorno[1])) # velestandar

        pc.sendGCode("G1 {0}{2} F{1}".format(straxis[tc.axis], tc.vel*0.5*60,
                     erroradm))
        pc.sendGCode("M400")
        if finaldecarrera == True:
            msg = "ERROR: TC hit endstop  v:{0} a:{1}\n".format(tc.vel,
                         tc.accel)
            pc.log.write(msg)
            print msg
            pc.sendGCode('M114')
            finaldecarrera = False
            tc.fails = tc.fails+1
    tc.checked = True


def main_prog(ltc):
    global pc
    pc.list_ports()

    # min vel max vel ntest minacc max acc ntest
    #==============================================================================
    #     TablaLimites = [[60, 300, 1, 1000, 9000, 1, 190, 1, True],
    #                     [60, 300, 1, 1000, 9000, 1, 190, 1, True],
    #                     [1,  3,   5,   20, 2000, 1,  20, 1, True]
    #                     ]
    #==============================================================================

    # Activa la monitorización de los finales de carrera
    enable_endstops_checking()
    pc.sendGCode("M121")


    lastaxis = -1
    for i in ltc:
        if lastaxis != i.axis:
            lastaxis = i.axis
            pc.sendGCode("G28")
        CheckTestCase(pc, i)

    for t in ltc:
        t.myprint()
        t.printlog()

    # Disable all stepper motors
    l = pc.sendGCode("M84")

    pc.close()

    return ltc

class GUI:
    def __init__(self):
        self.root = Tk()


    def leetabla(self):

        self.ta1 = TestAxis()
        self.ta2 = TestAxis()
        self.ta3 = TestAxis()

        self.ta1.check =  self.stest1.get()
        self.ta2.check =  self.stest2.get()
        self.ta3.check =  self.stest3.get()
        if self.ta1.check == 1:         self.ta1.check = True
        else:                           self.ta1.check = False
        if self.ta2.check == 1:         self.ta2.check = True
        else:                           self.ta2.check = False
        if self.ta3.check == 1:         self.ta3.check = True
        else:                           self.ta3.check = False

        self.ta1.axis = 0
        self.ta2.axis = 1
        self.ta3.axis = 2

        self.ta1.vmin = float(self.svelmin1.get())
        self.ta2.vmin = float(self.svelmin2.get())
        self.ta3.vmin = float(self.svelmin3.get())

        self.ta1.vmax = float(self.svelmax1.get())
        self.ta2.vmax = float(self.svelmax2.get())
        self.ta3.vmax = float(self.svelmax3.get())

        self.ta1.vnp = int(self.snvel1.get())
        self.ta2.vnp = int(self.snvel2.get())
        self.ta3.vnp = int(self.snvel3.get())


        self.ta1.amin = float(self.sacelmin1.get())
        self.ta2.amin = float(self.sacelmin2.get())
        self.ta3.amin = float(self.sacelmin3.get())

        self.ta1.amax = float(self.sacelmax1.get())
        self.ta2.amax = float(self.sacelmax2.get())
        self.ta3.amax = float(self.sacelmax3.get())

        self.ta1.anp = int(self.snacel1.get())
        self.ta2.anp = int(self.snacel2.get())
        self.ta3.anp = int(self.snacel3.get())

        self.ta1.dist = float(self.sdist1.get())
        self.ta2.dist = float(self.sdist2.get())
        self.ta3.dist = float(self.sdist3.get())

        self.ta1.nrep = int(self.snrep1.get())
        self.ta2.nrep = int(self.snrep2.get())
        self.ta3.nrep = int(self.snrep3.get())

        self.canvas0scalex = self.canvasHeight*0.8 / self.ta1.vmax
        self.canvas0scaley = self.canvasHeight*0.8 / self.ta1.amax
        self.canvas1scalex = self.canvasHeight*0.8 / self.ta2.vmax
        self.canvas1scaley = self.canvasHeight*0.8 / self.ta2.amax
        self.canvas2scalex = self.canvasHeight*0.8 / self.ta3.vmax
        self.canvas2scaley = self.canvasHeight*0.8 / self.ta3.amax

        return [self.ta1, self.ta2, self.ta3]

    def conectPrinter(self):
        # lee el valor de las opciones elegidas
        # abre la conexion con la impresora
        global pc

        sel = self.listpuertos.entry.get()
        print "selección: ", sel
        puerto = sel

        pc.open(port=puerto)

        # self.startButton['state'] = 'enable'

    def disconectPrinter(self):
        # lee el valor de las opciones elegidas
        # abre la conexion con la impresora
        pc.close()
        # pc.log.close()


    #
    # def onselect(evt):
    #     # Note here that Tkinter passes an event object to onselect()
    #     w = evt.widget
    #     index = int(w.curselection()[0])
    #     value = w.get(index)
    #     print 'You selected item %d: "%s"' % (index, value)
    #
    # lb = Listbox(frame, name='lb')
    # lb.bind('<<ListboxSelect>>', onselect)
    #


    def populate_root(self):
        global pc
        t24 = tkFont.Font(family='Times', size='24', weight='bold')
        self.frameT = Frame(self.root)

        self.label1 = Label(self.frameT, text="  TVA Test de Velocidad y Aceleración  ",
                   bg="Blue", fg='white', font=t24).grid(row=0,
                    column=1)

        self.frameI = Frame(self.frameT)
        self.frameI.grid(row=1, column=0)
        Label(self.frameI, text='OPERACIONES', bg='dark green', fg='white').pack()
        Label(self.frameI, text='  ').pack()
        Label(self.frameI, text='  ').pack()


        self.portsv = StringVar()
        self.listpuertos = ComboBox(self.frameI, variable=self.portsv)
        for i in pc.lpftdi:
            print "-->", i[0]
            self.listpuertos.insert(END, i[0])

        self.listpuertos.pack()
        self.listpuertos.set_silent(pc.lpftdi[0][0])


        Button(self.frameI, command=self.conectPrinter, text='Conecta', bg='black', fg='white').pack()
        Label(self.frameI, text='  ').pack()
        Button(self.frameI, command=self.disconectPrinter, text='Desconecta', bg='black', fg='white').pack()

        Label(self.frameI, text='  ').pack()
        Label(self.frameI, text='  ').pack()

        self.startButton = Button(self.frameI, command=self.start, text='START!', bg='green', fg='white').pack()
        Label(self.frameI, text='  ').pack()
        #self.startButton['state'] = 'disable'
        Button(self.frameI, command=self.stop, text='EXIT!', bg='red', fg='white').pack()



        self.frameC = Frame(self.frameT)
        #Label(frameC, text='TEST A REALIZAR', bg='dark green', fg='white').pack()
        #frameC.grid(row=1, column=1)


        self.frameD = LabelFrame(self.frameT, label='Estado',
                                  relief=GROOVE)
        self.frdertop = LabelFrame(self.frameD, label='Estado',
                                  relief=GROOVE)

        Label(self.frdertop, text='Velocidad:').grid(row=1, column=0)
        Label(self.frdertop, text='Aceleración:').grid(row=2, column=0)
        Label(self.frdertop, text='Repetición:').grid(row=3, column=0)
        Label(self.frdertop, text='OK?').grid(row=4, column=0)
        Label(self.frdertop, text='Velocidad').grid(row=5, column=0)

        self.frdertop.grid(row=1, column=0)


        self.frameD.grid(row=1, column=2)

        # button1 = Button(root, text="Hello, World!", bg="blue").grid(row=1, column=1)

        self.frameTabla= Frame(self. frameC)
        #LabelFrame(frameTabla, text='Definicion de test').pack()

        Label(self.frameTabla,text='Eje').grid(row=1, column=1)
        Label(self.frameTabla,text='Test').grid(row=1, column=0)
        Label(self.frameTabla,text='VelMin\nmm/min').grid(row=1, column=2)
        Label(self.frameTabla,text='VlMax\nmm/min').grid(row=1, column=3)
        Label(self.frameTabla,text='NtestVel').grid(row=1, column=4)
        Label(self.frameTabla,text='Acel.Min\nmm/s^2').grid(row=1, column=5)
        Label(self.frameTabla,text='Acel.Max\nmm/s^2').grid(row=1, column=6)
        Label(self.frameTabla,text='NtestAccel').grid(row=1, column=7)
        Label(self.frameTabla,text='Distancia\nmm').grid(row=1, column=8)
        Label(self.frameTabla,text='NRepet.').grid(row=1, column=9)

        Label(self.frameTabla, text='Velocidad').grid(row=0,
            column=2, columnspan=3)
        Label(self.frameTabla, text='Aceleración').grid(row=0,
            column=5, columnspan=3)


        self.stest1 = IntVar()
        self.stest2 = IntVar()
        self.stest3 = IntVar()

        self.cb1=Checkbutton(self.frameTabla, variable=self.stest1)
        self.cb1.grid(row=2, column=0)
        self.cb2=Checkbutton(self.frameTabla, variable=self.stest2)
        self.cb2.grid(row=3, column=0)
        self.cb3=Checkbutton(self.frameTabla, variable=self.stest3)
        self.cb3.grid(row=4, column=0)
        self.cb1.select()
        self.cb2.select()


        Label(self.frameTabla, text='X').grid(row=2, column=1)
        Label(self.frameTabla, text='Y').grid(row=3, column=1)
        Label(self.frameTabla, text='Z').grid(row=4, column=1)


        # --------------------------------------------
        self.svelmin1 = StringVar(value="40")
        self.svelmin2 = StringVar(value="40")
        self.svelmin3 = StringVar(value="1")

        self.evmin1=Entry(self.frameTabla, textvariable=self.svelmin1,
                          width=5).grid(row=2, column=2)
        self.evmin2=Entry(self.frameTabla, textvariable=self.svelmin2,
                          width=5).grid(row=3, column=2)
        self.evmin3=Entry(self.frameTabla, textvariable=self.svelmin3,
                          width=5).grid(row=4, column=2)

        self.svelmax1 = StringVar(value="400")
        self.svelmax2 = StringVar(value="400")
        self.svelmax3 = StringVar(value="10")

        self.evmax1=Entry(self.frameTabla, textvariable=self.svelmax1,
                          width=5).grid(row=2, column=3)
        self.evmax2=Entry(self.frameTabla, textvariable=self.svelmax2,
                          width=5).grid(row=3, column=3)
        self.evmax3=Entry(self.frameTabla, textvariable=self.svelmax3,
                          width=5).grid(row=4, column=3)

        self.snvel1 = StringVar(value="4")
        self.snvel2 = StringVar(value="4")
        self.snvel3 = StringVar(value="5")

        self.enpv1=Entry(self.frameTabla, textvariable=self.snvel1,
                         width=2).grid(row=2, column=4)
        self.enpv2=Entry(self.frameTabla, textvariable=self.snvel2,
                         width=2).grid(row=3, column=4)
        self.enpv3=Entry(self.frameTabla, textvariable=self.snvel3,
                         width=2).grid(row=4, column=4)


        # --------------------------------------------
        self.sacelmin1 = StringVar(value="500")
        self.sacelmin2 = StringVar(value="500")
        self.sacelmin3 = StringVar(value="10")

        self.eamin1=Entry(self.frameTabla, textvariable=self.sacelmin1,
                          width=5).grid(row=2,
            column=5)
        self.eamin2=Entry(self.frameTabla, textvariable=self.sacelmin2,
                          width=5).grid(row=3,
            column=5)
        self.eamin3=Entry(self.frameTabla, textvariable=self.sacelmin3,
                          width=5).grid(row=4,
            column=5)

        self.sacelmax1 = StringVar(value="9000")
        self.sacelmax2 = StringVar(value="9000")
        self.sacelmax3 = StringVar(value="3000")

        self.eamax1=Entry(self.frameTabla, textvariable=self.sacelmax1,
                          width=5).grid(row=2, column=6)
        self.eamax2=Entry(self.frameTabla, textvariable=self.sacelmax2,
                          width=5).grid(row=3, column=6)
        self.eamax3=Entry(self.frameTabla, textvariable=self.sacelmax3,
                          width=5).grid(row=4, column=6)

        self.snacel1 = StringVar(value="3")
        self.snacel2 = StringVar(value="3")
        self.snacel3 = StringVar(value="5")

        self.enpa1=Entry(self.frameTabla, textvariable=self.snacel1,
                         width=2).grid(row=2, column=7)
        self.enpa2=Entry(self.frameTabla, textvariable=self.snacel2,
                         width=2).grid(row=3, column=7)
        self.enpa3=Entry(self.frameTabla, textvariable=self.snacel3,
                         width=2).grid(row=4, column=7)

        # ------------------------------------------------

        self.sdist1 = StringVar(value="190")
        self.sdist2 = StringVar(value="190")
        self.sdist3 = StringVar(value="30")

        self.ed1=Entry(self.frameTabla, textvariable=self.sdist1,
                       width=3).grid(row=2, column=8)
        self.ed2=Entry(self.frameTabla, textvariable=self.sdist2,
                       width=3).grid(row=3, column=8)
        self.ed3=Entry(self.frameTabla, textvariable=self.sdist3,
                       width=3).grid(row=4, column=8)

        # ------------------------------------------------

        self.snrep1 = StringVar(value="1")
        self.snrep2 = StringVar(value="1")
        self.snrep3 = StringVar(value="1")

        self.enr1=Entry(self.frameTabla, textvariable=self.snrep1,
                        width=1).grid(row=2, column=9)
        self.enr2=Entry(self.frameTabla, textvariable=self.snrep2,
                        width=1).grid(row=3, column=9)
        self.enr3=Entry(self.frameTabla, textvariable=self.snrep3,
                        width=1).grid(row=4, column=9)

        # ------------------------------------------------

        self.frameTabla.grid(row=2,column=1)
        self.frameC.grid(row=1, column=1)

        self.frameT.pack()


        self.frderbot = LabelFrame(self.root, label='Test',
                                 relief=GROOVE)
        self.canvasHeight = 150*1.2
        self.canvasWidth  = 150*1.2
        self.canvasyoff = 150*0.05
        self.canvasxoff = 150*0.05


        self.frcan0 = LabelFrame(self.frderbot, label='Eje X',
                                 relief=GROOVE)
        self.canvas0 = Canvas(self.frcan0, height=self.canvasHeight,
                             width=self.canvasWidth, relief=GROOVE)
        self.canvas0.pack()
        self.frcan0.grid(row=0, column=0)

        self.frcan1 = LabelFrame(self.frderbot, label='Eje Y',
                                 relief=GROOVE)
        self.canvas1 = Canvas(self.frcan1, height=self.canvasHeight,
                             width=self.canvasWidth)
        self.canvas1.pack()
        self.frcan1.grid(row=0, column=1)

        self.frcan2 = LabelFrame(self.frderbot, label='Eje Z',
                                 relief=GROOVE)
        self.canvas2 = Canvas(self.frcan2, height=self.canvasHeight,
                             width=self.canvasWidth)
        self.canvas2.pack()
        self.frcan2.grid(row=0, column=2)

        self.frderbot.pack()



    def start(self):
        lta = self.leetabla()
        ltc = ListaTestCases(lta)
        print 'Empieza el test'
        for l in ltc:
            l.myprint()

        ltc = main_prog(ltc)

        for l in ltc:
            l.myprint()

        self.plot(ltc)

    def stop(self):
        self.root.destroy()


    def plot(self, ltc):
        self.sizerect = 3
        offsetx = self.canvasxoff
        offsety = self.canvasyoff
        # recorre los casos y dibuja los resultados.


        #ltcx = [c for c in ltc if c.axis==0]
        #ltcy = [c for c in ltc if c.axis==1]
        #ltcz = [c for c in ltc if c.axis==2]

        cx0 = offsetx + 0*self.canvas0scalex
        cy0 = offsety + 0*self.canvas0scaley
        cx1 = offsetx + self.ta1.vmax*self.canvas0scalex
        cy1 = offsety + self.ta1.amax*self.canvas0scaley
        t = str(0)
        self.canvas0.create_text(cx0, cy0, text=t)
        self.canvas0.create_text(cx1, cy0, text=str(self.ta1.vmax),anchor=W)
        self.canvas0.create_text(cx0, cy1, text=str(self.ta1.amax),anchor=W)

        cx0 = offsetx + 0*self.canvas1scalex
        cy0 = offsety + 0*self.canvas1scaley
        cx1 = offsetx + self.ta2.vmax*self.canvas1scalex
        cy1 = offsety + self.ta2.amax*self.canvas1scaley
        self.canvas1.create_text(cx0, cy0, text=str(0))
        self.canvas1.create_text(cx1, cy0, text=str(self.ta2.vmax),anchor=W)
        self.canvas1.create_text(cx0, cy1, text=str(self.ta2.amax),anchor=W)

        cx0 = offsetx + 0*self.canvas2scalex
        cy0 = offsety + 0*self.canvas2scaley
        cx1 = offsetx + self.ta3.vmax*self.canvas2scalex
        cy1 = offsety + self.ta3.amax*self.canvas2scaley
        self.canvas2.create_text(cx0, cy0, text=str(0))
        self.canvas2.create_text(cx1, cy0, text=str(self.ta3.vmax),anchor=W)
        self.canvas2.create_text(cx0, cy1, text=str(self.ta3.amax),anchor=W)



        for tc in ltc:
            if tc.checked or True:
                if tc.axis == 0:
                    escalax = self.canvas0scalex
                    escalay = self.canvas0scaley
                    plotcanvas = self.canvas0
                elif tc.axis == 1:
                    escalax = self.canvas1scalex
                    escalay = self.canvas1scaley
                    plotcanvas = self.canvas1
                elif tc.axis == 2:
                    escalax = self.canvas2scalex
                    escalay = self.canvas2scaley
                    plotcanvas = self.canvas2

                cx = offsetx + tc.vel*escalax
                cy = offsety + tc.accel*escalay

                if tc.fails > 0:
                        rfill='red'
                else:
                    rfill='green'

                #cx=cx+*2*self.sizerect
                #cy=cy+tc.axis*2*self.sizerect
                plotcanvas.create_rectangle(cx - self.sizerect,
                                             cy - self.sizerect,
                                             cx + self.sizerect,
                                             cy + self.sizerect,
                                             fill=rfill, outline=rfill)




###############################################################################
if __name__ == "__main__":

    mgui = GUI()
    mgui.populate_root()

    mgui.root.mainloop()

