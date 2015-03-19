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

Ver_major = 1
Ver_minor = 2
Ver_rel = 1

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
defaultPort = 'COM1'
defaultbr = 250000
origen = [] # coordenada sin que salten los finales de carrera

# from Tkinter import *
from Tix import *
hits = None
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
    def __init__(self, port="COM1", br=250000, timeout=0):

        self.port = port
        self.br = br
        self.timeout = timeout
        self.lpftdi = []
        self.conectada = False

        try:
            self.log = open("Calibration.txt", "wb")
        except IOError:
            self.log.close()


    def list_ports(self):
        self.lpftdi = []
        listports = serial.tools.list_ports.comports()
        for port, desc, hwid in sorted(listports):
            # print "%s: %s [%s]" % (port, desc, hwid)
            if 'FTDI' in hwid:
                print "puerto posible encontrado: %s: %s [%s]" % (port, desc, hwid)
                self.lpftdi.append([port, desc])

    def open(self, port="COM1", br=250000, timeout=0):
        if self.conectada is True:
            self.ser.close()
            self.conectada = False
        try:
            self.ser = serial.Serial(port, br, timeout=self.timeout)
            self.conectada = True
            self.port = port
            self.br = br
            self.timeout = timeout
        except IOError:
            print "IOError: Error al abrirlo. {0}".format(port)
            pass
        except ValueError:
            print "ValueError: Puerto inválido. Error al abrirlo. {0}".format(port)

        time.sleep(0.2)

    def send(self, msg):
        if self.conectada == False:
            print "Impresora no conectada"
            return
        r = self.ser.write(msg.upper() + "\n")
        self.ser.flush()
        self.log.write("SEND:" + str(msg) + "\n")
        self.log.flush()

    def sendGCode(self, msg, resp=False):
        findecarrera = False
        if self.conectada == False:
            print "Impresora no conectada"
            return
        self.send(msg)
        time.sleep(0.4)
        l = self.read()
        self.CheckRead(l)
        if resp:  #si resp es True, devuelve la lectura realizada
            return l

    def read(self):
        # l = self.ser.readlines()
        if self.conectada == False:
            return ""
        ct = time.clock()
        while True:
            niw = self.ser.inWaiting()
            if niw > 0:
                time.sleep(0.2)
                l = self.ser.readlines()
                break
            time.sleep(0.2)
            if time.clock() - ct > 60:
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

    def CheckRead(self, r):
        global finaldecarrera
        if type(r) is list:
            for i in range(len(r)):
                if 'endstops hit' in r[i]:
                    finaldecarrera = True
                    break
            pass
        else:
            if 'endstops hit' in r:
                finaldecarrera = True



pc = PrinterConnection()
pc.list_ports()


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
        distacelerando = accel * modulo ** 2 / 2
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
        pc.log.writelines(self._msg_print() + "\n")

    def _msg_print(self):
        msg = "TC axis " + straxis[self.axis] + " V: " + str(self.vel) + \
              " A: " + str(self.accel) + " fails: " + str(self.fails) + "/" + \
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
        nsteps = int(nsteps)
        if nsteps < 1:
            nsteps = 1
            vpasos = [vmin]
        else:
            vpasos = np.linspace(vmin, vmax, nsteps)
        for v in vpasos:
            amin = ta.amin
            amax = ta.amax
            asteps = ta.anp
            asteps = int(asteps)
            if asteps < 1:
                asteps = 1
                apasos = [amin]
            else:
                apasos = np.linspace(amin, amax, asteps)
            for a in apasos:
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

    if tc.axis == 2:
        testZ = True
    else:
        testZ = False

    erroradm = origen[tc.axis]

    velretorno = [300, 2]

    msg = "TEST: eje:{0} v: {1} a: {2}".format(straxis[tc.axis], tc.vel,
                                               tc.accel)
    print msg
    pc.log.write(msg + '\n')

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

    # Activa monitorización de finales de carrera
    pc.sendGCode("M121")

    for i in range(tc.nreps):
        pc.sendGCode("G28 {0} ".format(straxis[tc.axis]))

        if testZ:
            pc.sendGCode("M203 X500 Y500 Z{0}".format(tc.vel))
        else:
            pc.sendGCode("M203 X{0} Y{0}".format(tc.vel))

        pc.sendGCode("G1 {0}{1} F{2}".format(straxis[tc.axis], round(tc.dist, 3), \
                                             round(tc.vel * 60, 1)))
        pc.sendGCode("M400")

        ### RETORNO
        pc.sendGCode("M203 X{0} Y{0} Z{1}".format(velretorno[0],
                                                  velretorno[1]))  # velestandar
        # Aceleración de retorno
        if testZ:
            pc.sendGCode("M201 Z{0}".format(100))
        else:
            pc.sendGCode("M201 X{0} Y{1}".format(100.0, 100.0))
        if testZ:
            pc.sendGCode("G1 {0}{2} F{1}".format(straxis[tc.axis], round(velretorno[1]*60, 1),
                                                 erroradm))
        else:
            pc.sendGCode("G1 {0}{2} F{1}".format(straxis[tc.axis], round(velretorno[0]*60, 1),
                                                 erroradm))
        pc.sendGCode("M400")

        time.sleep(0.01)

        cfc = check_fin_de_carrera()
        if straxis[tc.axis] in cfc:
            msg = "ERROR: TC hit endstop  v:{0} a:{1}\n".format(tc.vel,
                                                                tc.accel)
            pc.log.write(msg)
            print msg
            pc.sendGCode('M114')
            # finaldecarrera = False
            tc.fails = tc.fails + 1
    tc.checked = True

def check_fin_de_carrera():

    resp = pc.sendGCode('M119', resp=True)
    # ['Reporting endstop status\n', 'x_min: TRIGGERED\n', 'y_min: open\n', 'z_min: open\n', 'ok\n']
    cfc = []
    for i in [1,2,3]:
        if "TRIG" in resp[i]:
            cfc.append(straxis[i-1])
    return cfc

def calcula_limites_ejes(lta):
    global pc
    global finaldecarrera
    global hits

    distanciatestfdc = 0.2
    redondeo = 0.002 # redondeo al segundo decimal

    #desplazarse en cada eje al home
    resp = pc.sendGCode("G28")
    # alejarse hasta no hacer contacto 1mm
    pc.sendGCode("G1 X1 Y1 Z1 F2000")
    # moverse hasta hacer contacto
    hits = [[0,0,0],
            [0,0,0],
            [0,0,0]]
    listaejes = []
    for a in range(len(lta)):
        if lta[a].check is True:
            listaejes.append(a)
    finprueba = False
    for i in listaejes:
        resp = pc.sendGCode("G28 {0}".format(straxis[i]))
        pc.sendGCode("G1 X1 Y1 Z1 F200")
        resp = pc.sendGCode("G1 {0}1.000 F200".format(straxis[i]))
        finprueba = False
        for j in range(0, 11):
            hits[i][0] = 0
            finaldecarrera = False
            resp = pc.sendGCode("G1 {0}{1} F200".format(straxis[i],
                                                        round( distanciatestfdc-0.1*j,3)))
            pc.sendGCode('M400')
            cfc = check_fin_de_carrera()
            if straxis[i] in cfc:
                hits[i][0] = j-1
                # resp = pc.sendGCode("M114", resp=True)
                # print resp
                # sep = re.split(r'[XYZE]\:\s*[-+]?(\d*(\.\d*)?)', resp[0])
                # print sep

                resp = pc.sendGCode("G28 {0}".format(straxis[i]))
                pc.sendGCode("G1 X1 Y1 Z1 F200")
                pc.sendGCode("M400")
                # resp = pc.sendGCode("G1 {0}1.000 F200".format(straxis[i]))

                for k in range(0, 11):
                    hits[i][1] = 0
                    # finaldecarrera = False
                    resp = pc.sendGCode("G1 {0}{1} F200".format(straxis[i],
                                                                round(distanciatestfdc-0.1*(j-1) - 0.01*k,3)))
                    cfc = check_fin_de_carrera()
                    if straxis[i] in cfc:
                        hits[i][1] = k-1
                        # resp = pc.sendGCode("M114", resp=True)
                        # print resp
                        # sep = re.split(r'[XYZE]\:\s*[-+]?(\d*(\.\d*)?)', resp[0])
                        # print sep

                        resp = pc.sendGCode("G28 {0}".format(straxis[i]))
                        pc.sendGCode("G1 X1 Y1 Z1 F100")
                        # resp = pc.sendGCode("G1 {0}1.000 F100".format(straxis[i]))

                        for l in range(0, 11):
                            hits[i][2] = 0
                            # finaldecarrera = False
                            resp = pc.sendGCode("G1 {0}{1} F100".format(straxis[i],
                                                                        round(distanciatestfdc-0.1*(j-1)
                                                                        - 0.01*(k-1)
                                                                        -0.001*l,3)))
                            cfc = check_fin_de_carrera()
                            if straxis[i] in cfc:
                                hits[i][2] = l-1
                                # resp = pc.sendGCode("M114", resp=True)
                                # print resp
                                #sep = re.split(r'[XYZE]\:\s*[-+]?(\d*(\.\d*)?)', resp[0])
                                #print sep
                                finprueba = True
                                break
                    if finprueba is True: break
            if finprueba is True: break
    # print hits

    global origen
    origen = [0,0,0]
    for a in listaejes:
        origen[a] = (distanciatestfdc-hits[a][0]*0.1-hits[a][1]*0.01-hits[a][2]*0.001)
        origen[a] = round(origen[a],3)
    # print origen

    # ultima comprobación. Comprobar donde está el limite cuando el eje se está moviendo a una velocidad moderada de retorno
    #desplazarse en cada eje al home

    # alejarse hasta no hacer contacto 1mm
    for a in listaejes:
        # resp = pc.sendGCode("G28")
        testpass = 0
        if a==2:
            vel = 2*60
        else:
            vel=60*60
        while True:
            resp = pc.sendGCode("G28 {0}".format(straxis[a]))
            pc.sendGCode("G1 X10 Y10 Z10 F100")
            resp = pc.sendGCode('M400')
            resp = pc.sendGCode('G1 {0}{1} F{2}'.format(straxis[a], origen[a], vel))
            resp = pc.sendGCode('M400')
            cfc = check_fin_de_carrera()
            if straxis[a] in cfc:
                origen[a] = origen[a] + 0.002
                testpass = 0
                # print 'Origen ',straxis[a],":" , origen[a]
            else:
                testpass = testpass+1
                if testpass >= 3:
                    break
            time.sleep(0.01)
        # print origen
        origen[a] = np.ceil(origen[a]/redondeo)*redondeo
        # print origen


def main_prog(ltc, lta):
    global pc
    # pc.list_ports()

    # min vel max vel ntest minacc max acc ntest
    #==============================================================================
    #     TablaLimites = [[60, 300, 1, 1000, 9000, 1, 190, 1, True],
    #                     [60, 300, 1, 1000, 9000, 1, 190, 1, True],
    #                     [1,  3,   5,   20, 2000, 1,  20, 1, True]
    #                     ]
    #==============================================================================

    # Activa la monitorización de los finales de carrera
    # enable_endstops_checking()
    pc.sendGCode("M121")

    ## Calcula hasta donde se puede mover en cada eje
    calcula_limites_ejes(lta)

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
    pc.sendGCode("M84")

    # pc.close()

    return ltc


class GUI:
    def __init__(self):
        self.root = Tk()


    def leetabla(self):

        self.ta1 = TestAxis()
        self.ta2 = TestAxis()
        self.ta3 = TestAxis()

        self.ta1.check = self.stest1.get()
        self.ta2.check = self.stest2.get()
        self.ta3.check = self.stest3.get()
        if self.ta1.check == 1:
            self.ta1.check = True
        else:
            self.ta1.check = False
        if self.ta2.check == 1:
            self.ta2.check = True
        else:
            self.ta2.check = False
        if self.ta3.check == 1:
            self.ta3.check = True
        else:
            self.ta3.check = False

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

        self.canvas0scalex = self.canvasHeight * 0.8 / self.ta1.vmax
        self.canvas0scaley = self.canvasHeight * 0.8 / self.ta1.amax
        self.canvas1scalex = self.canvasHeight * 0.8 / self.ta2.vmax
        self.canvas1scaley = self.canvasHeight * 0.8 / self.ta2.amax
        self.canvas2scalex = self.canvasHeight * 0.8 / self.ta3.vmax
        self.canvas2scaley = self.canvasHeight * 0.8 / self.ta3.amax

        return [self.ta1, self.ta2, self.ta3]

    def conectPrinter(self):
        # lee el valor de las opciones elegidas
        # abre la conexion con la impresora
        global pc

        selpt = self.listpuertos.entry.get()
        selbr = self.listbr.entry.get()
        print "selección: ", selpt, selbr
        puerto = selpt
        bitrate = selbr

        pc.open(port=puerto, br=bitrate)

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
        t12 = tkFont.Font(family='Times', size='12', weight='normal')
        self.frameT = Frame(self.root)

        self.label1 = Label(self.frameT, text="  TVA Test de Velocidad y Aceleración  ",
                            bg="Blue", fg='white', font=t24).grid(row=0,
                                                                  column=1)
        self.label1b = Label(self.frameT, text="  Ver: {0}.{1}.{2}  by R. Torres".format(Ver_major, Ver_minor, Ver_rel),
                            bg="Blue", fg='white', font=t12).grid(row=1,
                                                                  column=1)

        self.frameI = Frame(self.frameT)
        self.frameI.grid(row=10, column=0)
        Label(self.frameI, text='OPERACIONES', bg='dark green', fg='white').pack()
        Label(self.frameI, text='  ').pack()
        Label(self.frameI, text='  ').pack()
        self.frameIC = Frame(self.frameI)
        # comboBox puerto #########################
        self.portsv = StringVar()
        self.listpuertos = ComboBox(self.frameIC, variable=self.portsv, editable=True,
                                    label="Puerto", listwidth=20)
        # self.listpuertos['listwidth'] = 20
        self.listpuertos.entry['width'] = 10

        for i in pc.lpftdi:
            print "-->", i[0]
            self.listpuertos.insert(END, i[0])

        if len(pc.lpftdi) > 0:
            self.listpuertos.set_silent(pc.lpftdi[0][0])
        self.listpuertos.pack()

        # fin comboBox ###############################
        # comboBox br  #########################
        self.brsv = StringVar()
        self.listbr = ComboBox(self.frameIC, variable=self.brsv, editable=True,
                                    label="BitRate")
        self.listbr.entry['width'] = 10
        # self.listbr['listwidth'] = 20
        self.listabr = ["250000", "128000", "9600", "1200"]
        for i in self.listabr:
            print "-->", i
            self.listbr.insert(END, i)
        self.listbr.set_silent(self.listabr[0])
        self.listbr.pack()
        # fin comboBox ###############################

        Button(self.frameIC, command=self.conectPrinter, text='Conecta', bg='black', fg='white').pack()
        # Label(self.frameIC, text='  ').pack()
        Button(self.frameIC, command=self.disconectPrinter, text='Desconecta', bg='black', fg='white').pack()
        self.frameIC.pack()

        Label(self.frameI, text='  ').pack()
        # Label(self.frameI, text='  ').pack()

        self.frameI2 = Frame(self.frameI)

        self.startButton = Button(self.frameI2, command=self.start, text='START!', bg='green', fg='white').pack()
        # Label(self.frameI2, text='  ').pack()
        # self.startButton['state'] = 'disable'
        Button(self.frameI2, command=self.stop, text='EXIT!', bg='red', fg='white').pack()

        self.frameI2.pack()


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

        self.frdertop.grid(row=10, column=0)

        self.frameD.grid(row=10, column=2)

        # button1 = Button(root, text="Hello, World!", bg="blue").grid(row=1, column=1)

        self.frameTabla = Frame(self.frameC)
        #LabelFrame(frameTabla, text='Definicion de test').pack()

        Label(self.frameTabla, text='Eje').grid(row=1, column=1)
        Label(self.frameTabla, text='Test').grid(row=1, column=0)
        Label(self.frameTabla, text='VelMin\nmm/min').grid(row=1, column=2)
        Label(self.frameTabla, text='VlMax\nmm/min').grid(row=1, column=3)
        Label(self.frameTabla, text='NtestVel').grid(row=1, column=4)
        Label(self.frameTabla, text='Acel.Min\nmm/s^2').grid(row=1, column=5)
        Label(self.frameTabla, text='Acel.Max\nmm/s^2').grid(row=1, column=6)
        Label(self.frameTabla, text='NtestAccel').grid(row=1, column=7)
        Label(self.frameTabla, text='Distancia\nmm').grid(row=1, column=8)
        Label(self.frameTabla, text='NRepet.').grid(row=1, column=9)

        Label(self.frameTabla, text='Velocidad').grid(row=0,
                                                      column=2, columnspan=3)
        Label(self.frameTabla, text='Aceleración').grid(row=0,
                                                        column=5, columnspan=3)

        self.stest1 = IntVar()
        self.stest2 = IntVar()
        self.stest3 = IntVar()

        self.cb1 = Checkbutton(self.frameTabla, variable=self.stest1)
        self.cb1.grid(row=2, column=0)
        self.cb2 = Checkbutton(self.frameTabla, variable=self.stest2)
        self.cb2.grid(row=3, column=0)
        self.cb3 = Checkbutton(self.frameTabla, variable=self.stest3)
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

        self.evmin1 = Entry(self.frameTabla, textvariable=self.svelmin1,
                            width=5).grid(row=2, column=2)
        self.evmin2 = Entry(self.frameTabla, textvariable=self.svelmin2,
                            width=5).grid(row=3, column=2)
        self.evmin3 = Entry(self.frameTabla, textvariable=self.svelmin3,
                            width=5).grid(row=4, column=2)

        self.svelmax1 = StringVar(value="400")
        self.svelmax2 = StringVar(value="400")
        self.svelmax3 = StringVar(value="10")

        self.evmax1 = Entry(self.frameTabla, textvariable=self.svelmax1,
                            width=5).grid(row=2, column=3)
        self.evmax2 = Entry(self.frameTabla, textvariable=self.svelmax2,
                            width=5).grid(row=3, column=3)
        self.evmax3 = Entry(self.frameTabla, textvariable=self.svelmax3,
                            width=5).grid(row=4, column=3)

        self.snvel1 = StringVar(value="4")
        self.snvel2 = StringVar(value="4")
        self.snvel3 = StringVar(value="5")

        self.enpv1 = Entry(self.frameTabla, textvariable=self.snvel1,
                           width=2).grid(row=2, column=4)
        self.enpv2 = Entry(self.frameTabla, textvariable=self.snvel2,
                           width=2).grid(row=3, column=4)
        self.enpv3 = Entry(self.frameTabla, textvariable=self.snvel3,
                           width=2).grid(row=4, column=4)


        # --------------------------------------------
        self.sacelmin1 = StringVar(value="500")
        self.sacelmin2 = StringVar(value="500")
        self.sacelmin3 = StringVar(value="10")

        self.eamin1 = Entry(self.frameTabla, textvariable=self.sacelmin1,
                            width=5).grid(row=2,
                                          column=5)
        self.eamin2 = Entry(self.frameTabla, textvariable=self.sacelmin2,
                            width=5).grid(row=3,
                                          column=5)
        self.eamin3 = Entry(self.frameTabla, textvariable=self.sacelmin3,
                            width=5).grid(row=4,
                                          column=5)

        self.sacelmax1 = StringVar(value="9000")
        self.sacelmax2 = StringVar(value="9000")
        self.sacelmax3 = StringVar(value="3000")

        self.eamax1 = Entry(self.frameTabla, textvariable=self.sacelmax1,
                            width=5).grid(row=2, column=6)
        self.eamax2 = Entry(self.frameTabla, textvariable=self.sacelmax2,
                            width=5).grid(row=3, column=6)
        self.eamax3 = Entry(self.frameTabla, textvariable=self.sacelmax3,
                            width=5).grid(row=4, column=6)

        self.snacel1 = StringVar(value="3")
        self.snacel2 = StringVar(value="3")
        self.snacel3 = StringVar(value="5")

        self.enpa1 = Entry(self.frameTabla, textvariable=self.snacel1,
                           width=2).grid(row=2, column=7)
        self.enpa2 = Entry(self.frameTabla, textvariable=self.snacel2,
                           width=2).grid(row=3, column=7)
        self.enpa3 = Entry(self.frameTabla, textvariable=self.snacel3,
                           width=2).grid(row=4, column=7)

        # ------------------------------------------------

        self.sdist1 = StringVar(value="190")
        self.sdist2 = StringVar(value="190")
        self.sdist3 = StringVar(value="30")

        self.ed1 = Entry(self.frameTabla, textvariable=self.sdist1,
                         width=3).grid(row=2, column=8)
        self.ed2 = Entry(self.frameTabla, textvariable=self.sdist2,
                         width=3).grid(row=3, column=8)
        self.ed3 = Entry(self.frameTabla, textvariable=self.sdist3,
                         width=3).grid(row=4, column=8)

        # ------------------------------------------------

        self.snrep1 = StringVar(value="1")
        self.snrep2 = StringVar(value="1")
        self.snrep3 = StringVar(value="1")

        self.enr1 = Entry(self.frameTabla, textvariable=self.snrep1,
                          width=1).grid(row=2, column=9)
        self.enr2 = Entry(self.frameTabla, textvariable=self.snrep2,
                          width=1).grid(row=3, column=9)
        self.enr3 = Entry(self.frameTabla, textvariable=self.snrep3,
                          width=1).grid(row=4, column=9)

        # ------------------------------------------------

        self.frameTabla.grid(row=2, column=1)
        self.frameC.grid(row=10, column=1)

        self.frameT.pack()

        self.frderbot = LabelFrame(self.root, label='Test',
                                   relief=GROOVE)
        self.canvasHeight = 150 * 1.2
        self.canvasWidth = 150 * 1.2
        self.canvasyoff = 150 * 0.05
        self.canvasxoff = 150 * 0.05

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
        if pc.conectada == False:
            return
        lta = self.leetabla()
        ltc = ListaTestCases(lta)
        print 'Empieza el test'
        for l in ltc:
            l.myprint()

        ltc = main_prog(ltc, lta)

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

        cx0 = offsetx + 0 * self.canvas0scalex
        cy0 = offsety + 0 * self.canvas0scaley
        cx1 = offsetx + self.ta1.vmax * self.canvas0scalex
        cy1 = offsety + self.ta1.amax * self.canvas0scaley
        t = str(0)
        self.canvas0.create_text(cx0, cy0, text=t)
        self.canvas0.create_text(cx1, cy0, text=str(self.ta1.vmax), anchor=W)
        self.canvas0.create_text(cx0, cy1, text=str(self.ta1.amax), anchor=W)

        cx0 = offsetx + 0 * self.canvas1scalex
        cy0 = offsety + 0 * self.canvas1scaley
        cx1 = offsetx + self.ta2.vmax * self.canvas1scalex
        cy1 = offsety + self.ta2.amax * self.canvas1scaley
        self.canvas1.create_text(cx0, cy0, text=str(0))
        self.canvas1.create_text(cx1, cy0, text=str(self.ta2.vmax), anchor=W)
        self.canvas1.create_text(cx0, cy1, text=str(self.ta2.amax), anchor=W)

        cx0 = offsetx + 0 * self.canvas2scalex
        cy0 = offsety + 0 * self.canvas2scaley
        cx1 = offsetx + self.ta3.vmax * self.canvas2scalex
        cy1 = offsety + self.ta3.amax * self.canvas2scaley
        self.canvas2.create_text(cx0, cy0, text=str(0))
        self.canvas2.create_text(cx1, cy0, text=str(self.ta3.vmax), anchor=W)
        self.canvas2.create_text(cx0, cy1, text=str(self.ta3.amax), anchor=W)

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

                cx = offsetx + tc.vel * escalax
                cy = offsety + tc.accel * escalay

                if tc.fails > 0:
                    rfill = 'red'
                else:
                    rfill = 'green'

                #cx=cx+*2*self.sizerect
                #cy=cy+tc.axis*2*self.sizerect
                plotcanvas.create_rectangle(cx - self.sizerect,
                                            cy - self.sizerect,
                                            cx + self.sizerect,
                                            cy + self.sizerect,
                                            fill=rfill, outline=rfill)


###############################################################################
if __name__ == '__main__':

    mgui = GUI()
    mgui.populate_root()

    mgui.root.mainloop()

