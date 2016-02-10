# TVA-Marlin


**Test de Velocidad y Aceleración - Speed and acceleration test - 3d printer with firmware Marlin**
---

## Autor: 

Rafael Torres rtorresca (en) yahoo punto es

## Licencia: 

Este codigo esta cubierto por la licencia *CC-by-nc-sa*

**Agradecimiento**: 
A todos aquellos que han contribuido con su trabajo a que la comunidad freeX pueda trabajar, aprender y avanzar.
En este caso, quiero agradecer al autor de QTMarlin (bkubicek/QTMarlin) por su trabajo que me inspiró enormemente para realizar este.

## Descripción:

Aplicación para realizar pruebas de pérdida de pasos en los ejes de las impresoras 3D por FFD. No creo que aporte nada respecto al trabajo de bkubicek, salvo la implementación en Python2 y el uso del interfaz gráfico Tk, de modo que su portabilidad no suponga un problema. Debería poder ejecutarse en Windows, Linux y en cualquier S.O. que disponga de un interprete de Python2.
Solamente esta probado con el firmware Marlin_v1.

**Disculpas:**

El trabajo se origino por la necesidad de comprobar los límites de funcionamiento de una impresora 3D y ante los problemas que surgían para compilar QTMarlin, me planteé relizar una aplicación con el mismo objetivo pero que fuese portable y facil de modificar.
De este modo, la aplicación esta hecha muy deprisa y bastante mal pensada, ausente de toda reflexión y llena de código inutil, mal escrito y seguramente con muchos bugs. Así que me disculpo por ello y or animo a que la mejoreis tanto como podais.

---
## Instalación
Funciona sin problemas en Linux y en Windows.
En MAC no lo se. No dispongo de Mac para probar.

### Necesario para instalar la aplicación
- interprete de python 2. Importante: asegúrate de que usas el interprete de Python 2. Laa última versión a ser posible. Yo utilizo Anaconda https://store.continuum.io/cshop/anaconda/
- librería *numpy*. Incluido en Anaconda y en otras distribuciones. Si no, hay que instalarlo. 
- librería *pyserial*. La puedes encontrar en sourceforge, o en el instalador de tu distribución. 
- librería Tix. Para parte del interfaz gráfico. Instalarla con la distribución.

### Para ejecutar la versión Python
Tener instalado un interprete de python 2.7
ejecutar 

	python2 TVAMarlin.py

_et voilà!_ ya debería aparecer la ventana del interfaz de la aplicación.

### Para la versión compilada
Por el momento no hay versión compilada por lo que la única manera es siguiendo las instrucciones del apartado anterior.


### Librerías externas:
Necesitas tener instalada la librería pyserial y tix
Si usas Anaconda, puedes escribir en el terminal: 
````
	conda install pyserial
````

## Uso
* Arrancar la aplicación
Para ello utilizar el interprete de python instalado
* Selección de los ejes a comprobar: marcar las checkbox correspondientes al eje o ejes que desees comprobar.
* Selección de pruebas de velocidad: a continuación introduce el rango de velocidades que quieres probar en cada eje, como velocidad mínima, velocidad máxima y numero de velocidades a hacer. 
  - 1 punto solo prueba la velocidad mínima
  - 2 puntos la minima y la maxima
  - 3 puntos la mínima, el valor central y la máxima
  - 4 o más puntos: divide la velocidad en intervalos iguales entre el numero de pruebas a hacer
* repite lo mismo para cada aceleración que quieras probar, valor mínimo, máximo y numero de pruebas de aceleración.
* nreps es el numero de veces que repetirá cada prueba.
* cuando tengas seleccionados todos los datos, pincha en el boton START a la izquierda y comenzará la ejecución de todos los test que correspondan.

**_Notas_**

Presta atención al número de pruebas en cada eje y al número de repeticiones. 
El número total de pruebas que realizará es 

 (testX).Xnpv.Xnpa.Xnreps + (testY).Ynpv.Ynpa.Ynreps + (testZ).Znpv.Znpa.Znreps 

con lo que es recomendable que primero vayas haciendo pruebas con pocos puntos en cada eje y pocas repeticiones. 
Una vez ya conozcas por donde andan los límites de tu máquina, puedes hacer dos cosas:
  1. ajustar intensidades de los motores para alcanzar el límite deseado sin problemas
  2. Ajustar los valores de velocidad máximos en el firmware para no tener problemas de impresión.
 
Cuando tengas los límites de trabajo de velocidad y aceleración definitivos, introducelos en el codigo fuente de Marlin y actualiza el firmware, o introducelos en la EPROM. A tu elección.
Yo no utilizo los límites indicados por TVA. Los reduzco a un 50% o a un 75% y esos son los límites efectivos que utilizo. Es recomendable hacerlo así y experimentar, acabando de ajustarlos a tu máquina.

**Nota importante**

Cuando acabes de hacer la calibración / pruebas de los ejes, no olvides resetear la tarjeta de control (Arduino Mega) pues TVA ha cambiado los límites de trabajo y puede haber puesto al firmware en algun modo no deseado para imprimir.

**Nota más importante**
Al probar un eje que tenga dos motores, como es el caso del eje Z en las prusas i2 e i3. La perdida de pasos se puede producir en uno de los motores antes que en el otro, de modo que, en el caso de las prusas, el eje X *dejará* de ser paralelo a la plataforma de la pieza.
Será necesario hace de nuevo un ajuste de la inclinación y de la altura del eje Z y, en su caso, volver a nivelar la plataforma.

## TO-DO
- [ ] Ejecutable .exe para windows. En linux no debería de haber problema. Retrasado hasta encontrar una forma de hacerlo.
- [X] Lista para seleccionar el puerto serie donde esta la impresora
- [X] Incorporar la lista al interfaz gráfico con una ListBox
- [X] Autoconfigurar el error admisible
- [ ] Completar el gui con la información puntual del test que se está realizando en cada momento
- [ ] Emitir un informe con las recomendaciones tras los resultados obtenidos
- [ ] Eliminar el uso de la librería tix y usar solamente tkinter para ser más compatible


Que la prusa te acompañe :sunglasses:

*Rafael Torres*
