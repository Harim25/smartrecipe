# Pruebas de calidad: casos límite y consistencia

- Fecha: 12/10/2026 19:31
- Modo: gemini · gemini-3.8-flash

## Casos límite

| Caso | Descripción | Comensales | Resultado | Tiempo (s) | % ingredientes usados | Observación automática |
|---|---|---|---|---|---|---|
| L01 | Máximo de ingredientes (20) | 4 | OK | 20.49 | 95 % | comensales correctos; trae nota |
| L02 | Máximo de comensales (20) | 20 | OK | 23.39 | 100 % | comensales correctos; trae nota |
| L03 | Faltas de ortografía | 2 | OK | 44.25 | 25 % | comensales correctos; trae nota |
| L04 | Ingredientes en inglés | 2 | OK | 15.96 | 0 % | comensales correctos; trae nota |
| L05 | Solo condimentos | 2 | OK | 38.46 | 100 % | comensales correctos; trae nota |
| L06 | Carne que requiere cocción completa | 2 | OK | 15.65 | 100 % | comensales correctos; trae nota |
| L07 | Ingredientes dulces | 3 | OK | 15.23 | 100 % | comensales correctos; trae nota |

## Consistencia

### K1 · Desayuno: huevo, tortilla, frijol, queso para 2

- Repeticiones correctas: 3 de 3
- Títulos: Enfrijoladas rellenas de huevo con queso / Huevos sobre tortilla con frijoles y queso / Enfrijoladas con huevo revuelto y queso
- Tiempo de preparación indicado: de 15 a 20 min
- Tiempo de respuesta: de 8.43 a 11.99 s
- Número de pasos: 7, 5, 6

| Ingrediente del usuario | Rep. 1 | Rep. 2 | Rep. 3 | Variación |
|---|---|---|---|---|
| huevo | 4 pieza | 4 pieza | 4 pieza | igual |
| tortilla | 4 pieza | 4 pieza | 4 pieza | igual |
| frijol | 300 g | 200 g | 250 g | x1.5 entre la menor y la mayor |
| queso | 80 g | 80 g | 80 g | igual |

### K2 · Pasta: pasta, jitomate, ajo para 4

- Repeticiones correctas: 3 de 3
- Títulos: Pasta clásica con salsa rústica de jitomate y ajo / Pasta clásica con salsa rústica de jitomate y ajo / Pasta con salsa rústica de jitomate y ajo
- Tiempo de preparación indicado: de 25 a 25 min
- Tiempo de respuesta: de 7.97 a 21.2 s
- Número de pasos: 7, 7, 8

| Ingrediente del usuario | Rep. 1 | Rep. 2 | Rep. 3 | Variación |
|---|---|---|---|---|
| pasta | 400 g | 400 g | 400 g | igual |
| jitomate | 500 g | 500 g | 500 g | igual |
| ajo | 4 pieza | 4 pieza | 4 pieza | igual |

## Detalle de cada caso

### L01 · Máximo de ingredientes (20)

- Ingredientes: pollo, arroz, frijol, jitomate, cebolla, ajo, zanahoria, papa, calabacita, elote, queso, crema, huevo, tortilla, chile, limón, cilantro, aguacate, lechuga, pasta · Comensales: 4
- Se esperaba: receta coherente; no tiene que usar los 20, pero sí explicar lo que deja fuera
- Resultado: **OK** en 20.49 s

**Guisado de Pollo con Verduras Campestres, Arroz a la Mexicana y Guarnición Completa** (45 min)

Ingredientes:
- pechuga de pollo cortada en cubos: 600 g
- arroz: 240 g
- frijoles cocidos: 300 g
- jitomate: 3 pieza
- cebolla: 1 pieza
- dientes de ajo: 3 pieza
- zanahoria: 2 pieza
- papa: 2 pieza
- calabacita: 2 pieza
- granos de elote: 150 g
- huevo: 2 pieza
- lechuga fileteada: 150 g
- aguacate: 1 pieza
- queso: 120 g
- crema: 100 ml
- chile: 2 pieza
- limón: 2 pieza
- cilantro fresco picado: 20 g
- tortillas de maíz: 8 pieza
- aceite: 40 ml
- agua: 1200 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Poner a cocer los dos huevos en agua hirviendo durante 10 minutos; enfriar, pelar, picar en cubos y reservar.
2. Licuar 2 jitomates con media cebolla, 2 dientes de ajo y 500 ml de agua con una pizca de sal para preparar el caldillo del arroz.
3. En una cacerola, calentar 15 ml de aceite y sofreír el arroz hasta que tome un tono dorado ligero; verter el caldillo licuado, tapar y cocinar a fuego bajo durante 20 minutos hasta que el líquido se absorba.
4. En una sartén amplia u olla, calentar 15 ml de aceite y sellar el pollo salpimentado a fuego medio-alto durante 6 minutos hasta dorar.
5. Picar en cubos pequeños la zanahoria y la papa; agregarlas al pollo junto con 300 ml de agua, tapar y dejar cocer por 8 minutos.
6. Cortar la calabacita en cubos y sumarla al guisado junto con los granos de elote, el jitomate restante picado, la otra mitad de la cebolla picada, un diente de ajo picado finamente y los chiles en rodajas. Cocinar 7 minutos más hasta que todo esté tierno.
7. Calentar los frijoles en una sartén pequeña con 10 ml de aceite, machacándolos ligeramente al gusto.
8. Preparar una ensalada fresca mezclando la lechuga, el huevo cocido picado, el cilantro, el aguacate en rebanadas y el jugo de los limones, sazonando con una pizca de sal y pimienta.
9. Calentar las tortillas de maíz en un comal.
10. Servir el guisado de pollo con verduras acompañado del arroz a la mexicana, los frijoles y la ensalada fresca; coronar con crema y queso espolvoreado.

Nota del modelo: Se excluyó la pasta de esta preparación para mantener un plato equilibrado y armónico sin duplicar innecesariamente fuentes de almidón junto al arroz y las tortillas.

### L02 · Máximo de comensales (20)

- Ingredientes: pollo, arroz, zanahoria · Comensales: 20
- Se esperaba: cantidades para 20 personas (kilos de pollo y arroz)
- Resultado: **OK** en 23.39 s

**Arroz con Pollo y Zanahoria a Gran Escala** (45 min)

Ingredientes:
- pollo (troceado): 3500 g
- arroz: 1600 g
- zanahoria: 1200 g
- aceite: 150 ml
- agua: 3600 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Lavar, pelar y cortar las zanahorias en dados pequeños o rodajas finas.
2. Cortar el pollo en trozos de tamaño bocado y salpimentar al gusto.
3. En una olla grande o cazuela amplia, calentar el aceite a fuego medio-alto y sellar el pollo hasta que esté dorado por todos lados (aproximadamente 10-12 minutos).
4. Añadir la zanahoria a la olla y sofreír junto con el pollo durante 5 minutos para que empiece a ablandarse.
5. Incorporar el arroz y remover durante 2 minutos para nacararlo y que absorba los sabores del fondo de cocción.
6. Verter el agua, rectificar de sal y pimienta, y llevar a ebullición.
7. Reducir el fuego a medio-bajo, tapar la olla y dejar cocinar durante 18-20 minutos hasta que el arroz esté tierno y haya absorbido el líquido.
8. Retirar del fuego, dejar reposar tapado durante 5 minutos y servir caliente repartiendo equitativamente entre los 20 comensales.

Nota del modelo: Se han escalado las cantidades de pollo, arroz y zanahoria proporcionalmente para abastecer a 20 personas, utilizando únicamente los básicos de despensa permitidos.

### L03 · Faltas de ortografía

- Ingredientes: poyo, aros, sevolla, jitomate · Comensales: 2
- Se esperaba: entiende pollo, arroz y cebolla
- Resultado: **OK** en 44.25 s

**Arroz con Pollo y Salsa de Jitomate** (35 min)

Ingredientes:
- Pollo (pechuga o muslo en trozos): 350 g
- Arroz: 160 g
- Jitomate: 2 pieza
- Cebolla: 0.5 pieza
- Aceite vegetal: 20 ml
- Agua: 400 ml
- Sal: al gusto
- Pimienta: al gusto

Pasos:
1. Lavar y cortar los jitomates y la cebolla. Licuar los jitomates con la mitad de la cebolla picada y unos 100 ml de agua para formar una salsa homogénea.
2. Salpimentar los trozos de pollo al gusto.
3. En una cacerola amplia, calentar el aceite a fuego medio y dorar las piezas de pollo por todos sus lados durante 6-8 minutos. Retirar el pollo y reservar.
4. En la misma cacerola con el aceite restante, sofreír el resto de la cebolla picada finamente y añadir el arroz, removiendo constantemente hasta que tome un tono dorado ligero.
5. Verter la salsa de jitomate sobre el arroz y cocinar por 2 minutos hasta que cambie de color y reduzca ligeramente.
6. Reincorporar el pollo a la cacerola, verter los 300 ml restantes de agua caliente y rectificar la sal.
7. Tapar, bajar el fuego al mínimo y cocinar durante 15 a 18 minutos, o hasta que el líquido se haya absorbido y el arroz esté tierno.
8. Apagar el fuego, dejar reposar tapado durante 5 minutos y servir caliente.

Nota del modelo: Se interpretaron los ingredientes con errores ortográficos como pollo, arroz, cebolla y jitomate, complementándolos con los básicos de despensa permitidos.

### L04 · Ingredientes en inglés

- Ingredientes: chicken, rice, onion · Comensales: 2
- Se esperaba: receta en español con esos ingredientes
- Resultado: **OK** en 15.96 s

**Arroz con pollo y cebolla dorada** (35 min)

Ingredientes:
- Pollo: 350 g
- Arroz: 160 g
- Cebolla: 1 pieza
- Aceite: 20 ml
- Agua: 400 ml
- Sal: al gusto
- Pimienta: al gusto

Pasos:
1. Cortar el pollo en trozos de tamaño bocado y picar la cebolla finamente. Sazonar el pollo con sal y pimienta al gusto.
2. Calentar el aceite en una cazuela o sartén honda a fuego medio-alto y dorar los trozos de pollo durante 5 a 6 minutos hasta que tomen buen color. Retirar y reservar.
3. En la misma cazuela con los jugos del pollo, sofreír la cebolla a fuego medio durante 5 minutos hasta que esté tierna y translúcida.
4. Agregar el arroz a la cazuela y rehogar durante 1 a 2 minutos junto con la cebolla para nacararlo.
5. Reincorporar el pollo a la cazuela, verter el agua y ajustar con una pizca de sal y pimienta.
6. Llevar a ebullición, luego reducir el fuego al mínimo, tapar y cocinar durante 16 a 18 minutos hasta que el arroz esté tierno y haya absorbido el líquido.
7. Retirar del fuego y dejar reposar tapado durante 5 minutos antes de servir.

Nota del modelo: Se aprovecha el fondo de cocción del dorado del pollo y la cebolla para brindar sabor y aroma al arroz utilizando únicamente básicos de despensa.

### L05 · Solo condimentos

- Ingredientes: sal, azúcar · Comensales: 2
- Se esperaba: rechaza o explica que no alcanza para un platillo
- Resultado: **OK** en 38.46 s

**Caramelos crujientes con toque de sal** (20 min)

Ingredientes:
- azúcar: 100 g
- agua: 35 ml
- aceite: 5 ml
- sal: al gusto

Pasos:
1. Unta el aceite con un papel absorbente sobre una superficie resistente al calor (como papel vegetal o una bandeja metálica) para evitar que el caramelo se pegue.
2. Coloca el azúcar y el agua en un cazo pequeño a fuego medio, sin remover con cuchara para evitar que cristalice, solo moviendo ligeramente el cazo si es necesario.
3. Cocina la mezcla durante 8 a 10 minutos hasta que tome un tono dorado ámbar.
4. Retira inmediatamente del fuego y vierte el caramelo con cuidado sobre la superficie engrasada formando pequeñas porciones o una capa fina.
5. Espolvorea una pizca muy ligera de sal sobre el caramelo caliente antes de que solidifique por completo.
6. Deja enfriar a temperatura ambiente durante 10 minutos hasta que esté duro y crujiente antes de servir.

Nota del modelo: Al disponer únicamente de azúcar y sal entre los ingredientes proporcionados, se optó por elaborar caramelos duros artesanales utilizando agua y una mínima cantidad de aceite de la despensa para la cocción y el desmoldado.

### L06 · Carne que requiere cocción completa

- Ingredientes: carne molida, lechuga, jitomate · Comensales: 2
- Se esperaba: cuece bien la carne; no la sirve cruda
- Resultado: **OK** en 15.65 s

**Tacos de lechuga con carne molida y jitomate** (20 min)

Ingredientes:
- carne molida: 300 g
- jitomate: 2 pieza
- lechuga: 1 pieza
- aceite: 15 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Lavar y desinfectar las hojas de lechuga con cuidado de mantenerlas enteras; escurrirlas y secarlas bien para usarlas como base.
2. Lavar y picar los jitomates en cubos pequeños.
3. Calentar el aceite en una sartén a fuego medio e incorporar la carne molida.
4. Cocinar la carne durante 6 a 8 minutos, desmenuzándola con una espátula hasta que esté cocida y comience a dorarse ligeramente.
5. Agregar el jitomate picado a la sartén, sazonar con sal y pimienta al gusto, y cocinar por 5 minutos más hasta que el jitomate se ablande y se integren los sabores.
6. Retirar del fuego y servir el guisado caliente dentro de las hojas de lechuga a modo de tacos o barquitas.

Nota del modelo: Se aprovechan las hojas frescas de lechuga como base para presentar la carne, logrando un platillo balanceado, ligero y sin necesidad de ingredientes adicionales.

### L07 · Ingredientes dulces

- Ingredientes: plátano, avena, leche, miel · Comensales: 3
- Se esperaba: propone un postre o desayuno, no un guisado salado
- Resultado: **OK** en 15.23 s

**Porridge cremoso de avena con plátano y miel** (15 min)

Ingredientes:
- avena en hojuelas: 150 g
- leche: 600 ml
- plátano: 3 pieza
- miel: 45 g
- sal: al gusto

Pasos:
1. Pelar 1.5 plátanos y machacarlos con un tenedor hasta obtener un puré homogéneo. Cortar los 1.5 plátanos restantes en rodajas para decorar al final.
2. En una olla mediana a fuego medio, verter la leche, la avena en hojuelas, el puré de plátano y una pizca de sal.
3. Cocinar a fuego medio-bajo durante aproximadamente 8 a 10 minutos, removiendo continuamente con una cuchara de madera para evitar que se pegue al fondo, hasta que la mezcla adquiera una textura espesa y cremosa.
4. Retirar la olla del fuego e incorporar la mitad de la miel (unos 20-25 g), integrándola bien en la avena caliente.
5. Repartir la avena cremosa de manera equitativa en 3 boles.
6. Decorar cada porción con las rodajas de plátano reservadas y verter por encima el resto de la miel en hilo antes de servir.

Nota del modelo: Se aprovecha la fruta tanto cocida dentro de la avena para aportar dulzor y cremosidad natural, como fresca en la superficie para dar contraste de textura.

### K1-1 · Desayuno (repetición 1)

- Ingredientes: huevo, tortilla, frijol, queso · Comensales: 2
- Se esperaba: debe parecerse a las otras repeticiones
- Resultado: **OK** en 11.99 s

**Enfrijoladas rellenas de huevo con queso** (20 min)

Ingredientes:
- huevo: 4 pieza
- tortilla: 4 pieza
- frijol cocido: 300 g
- queso: 80 g
- aceite: 15 ml
- agua: 60 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Licuar o machacar los frijoles con el agua hasta obtener una salsa homogénea y ligera.
2. Verter la salsa de frijol en una olla pequeña a fuego medio, sazonar con sal al gusto y dejar que rompa en ligero hervor.
3. Batir los huevos en un tazón con una pizca de sal y pimienta.
4. Calentar la mitad del aceite en una sartén y cocinar los huevos revueltos hasta que cuajen al punto deseado; retirar y reservar.
5. En la misma sartén con el aceite restante, pasar las tortillas unos segundos por lado para suavizarlas sin que se endurezcan.
6. Sumergir cada tortilla en la salsa caliente de frijol, rellenar con una porción del huevo revuelto y doblar por la mitad.
7. Colocar dos enfrijoladas por plato, bañar con la salsa de frijol restante y coronar con el queso desmoronado o rallado.

Nota del modelo: Se aprovechan todos los ingredientes disponibles para lograr un platillo tradicional equilibrado y completo.

### K1-2 · Desayuno (repetición 2)

- Ingredientes: huevo, tortilla, frijol, queso · Comensales: 2
- Se esperaba: debe parecerse a las otras repeticiones
- Resultado: **OK** en 8.43 s

**Huevos sobre tortilla con frijoles y queso** (15 min)

Ingredientes:
- huevo: 4 pieza
- tortilla: 4 pieza
- frijol cocido: 200 g
- queso: 80 g
- aceite: 15 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. En una sartén pequeña, calentar los frijoles machacándolos ligeramente hasta obtener una consistencia suave y cremosa (puedes agregar un chorrito de agua si están muy secos). Mantener calientes.
2. En otra sartén, calentar la mitad del aceite y dorar ligeramente las tortillas por ambos lados sin que se pongan duras. Distribuir 2 tortillas por plato.
3. Untar una capa generosa de frijoles calientes sobre cada una de las tortillas.
4. Añadir el resto del aceite a la sartén y cocinar los huevos al gusto (estrellados o revueltos), sazonándolos con sal y pimienta.
5. Colocar un huevo sobre cada tortilla untada con frijol y terminar espolvoreando el queso rallado o desmoronado por encima para que se funda ligeramente con el calor. Servir de inmediato.

Nota del modelo: Se aprovechan todos los ingredientes para armar una versión clásica de huevos rancheros/campesinos, empleando únicamente aceite, sal y pimienta de la despensa básica.

### K1-3 · Desayuno (repetición 3)

- Ingredientes: huevo, tortilla, frijol, queso · Comensales: 2
- Se esperaba: debe parecerse a las otras repeticiones
- Resultado: **OK** en 11.03 s

**Enfrijoladas con huevo revuelto y queso** (20 min)

Ingredientes:
- huevo: 4 pieza
- tortilla: 4 pieza
- frijol cocido: 250 g
- queso: 80 g
- aceite: 15 ml
- agua: 60 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Licúa o machaca los frijoles cocidos con el agua hasta obtener una salsa tersa y homogénea.
2. Calienta 5 ml de aceite en una sartén a fuego medio, vierte la salsa de frijol, sazona con sal y pimienta al gusto, y cocina durante 4 minutos hasta que hierva suavemente. Reserva caliente.
3. Bate los 4 huevos en un tazón con una pizca de sal y pimienta. Calienta 5 ml de aceite en otra sartén a fuego medio y cocina los huevos revolviendo suavemente hasta que alcancen el punto deseado.
4. En una sartén pequeña con los 5 ml restantes de aceite, pasa ligeramente las tortillas de ambos lados para suavizarlas sin que se doren de más.
5. Pasa cada tortilla por la salsa caliente de frijol, colócala en un plato y rellénala con una porción del huevo revuelto, doblándola por la mitad.
6. Baña las enfrijoladas con el resto de la salsa de frijol caliente y espolvorea el queso rallado o desmoronado por encima antes de servir.

Nota del modelo: Se aprovecharon todos los ingredientes para preparar un desayuno tradicional mexicano balanceado, utilizando los básicos de despensa indispensables para su elaboración.

### K2-1 · Pasta (repetición 1)

- Ingredientes: pasta, jitomate, ajo · Comensales: 4
- Se esperaba: debe parecerse a las otras repeticiones
- Resultado: **OK** en 21.2 s

**Pasta clásica con salsa rústica de jitomate y ajo** (25 min)

Ingredientes:
- pasta: 400 g
- jitomate: 500 g
- dientes de ajo: 4 pieza
- aceite: 40 ml
- agua: 2500 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Picar finamente los dientes de ajo y cortar los jitomates en cubos pequeños.
2. Poner a calentar el agua en una olla grande con una pizca de sal. Cuando rompa a hervir, agregar la pasta y cocinar según las instrucciones del empaque hasta que esté al dente (aproximadamente 8 a 10 minutos).
3. Mientras la pasta se cocina, calentar el aceite en una sartén amplia a fuego medio. Agregar el ajo picado y sofreír durante 1 minuto cuidando que no se queme.
4. Incorporar los jitomates picados a la sartén, sazonar con sal y pimienta al gusto, y cocinar a fuego medio-bajo durante 10 minutos hasta que los jitomates se hayan deshecho y formado una salsa rústica.
5. Escurrir la pasta reservando unas cucharadas del agua de cocción.
6. Integrar la pasta cocida a la sartén con la salsa de jitomate y ajo, añadir un chorrito del agua de cocción reservada y mezclar todo a fuego bajo durante 1 o 2 minutos para que se impregnen los sabores.
7. Servir caliente dividido en 4 porciones.

Nota del modelo: Se utilizó el agua de cocción de la pasta para emulsionar la salsa y lograr una textura más sedosa sin necesidad de agregar ingredientes adicionales.

### K2-2 · Pasta (repetición 2)

- Ingredientes: pasta, jitomate, ajo · Comensales: 4
- Se esperaba: debe parecerse a las otras repeticiones
- Resultado: **OK** en 7.97 s

**Pasta clásica con salsa rústica de jitomate y ajo** (25 min)

Ingredientes:
- pasta: 400 g
- jitomate: 500 g
- dientes de ajo: 4 pieza
- aceite: 30 ml
- agua: 3000 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Picar finamente los dientes de ajo y cortar los jitomates en cubos pequeños.
2. Poner a calentar los 3000 ml de agua con una pizca generosa de sal en una olla grande hasta que hierva.
3. Agregar la pasta al agua hirviendo y cocinar según el tiempo recomendado en el empaque (aproximadamente 8 a 10 minutos) hasta que esté al dente.
4. Mientras se cocina la pasta, calentar el aceite en una sartén amplia a fuego medio y sofreír el ajo durante 1 minuto con cuidado de que no se queme.
5. Incorporar el jitomate picado a la sartén, sazonar con sal y pimienta al gusto, y cocinar a fuego medio-bajo durante 10 minutos machacando ligeramente hasta obtener una salsa jugosa.
6. Escurrir la pasta reservando un par de cucharadas del agua de cocción.
7. Integrar la pasta y el agua reservada en la sartén con la salsa de jitomate, mezclar bien durante 1 minuto a fuego suave y servir caliente.

Nota del modelo: Se aprovecharon todos los ingredientes base junto con básicos de despensa para preparar un plato clásico, aromático y reconfortante.

### K2-3 · Pasta (repetición 3)

- Ingredientes: pasta, jitomate, ajo · Comensales: 4
- Se esperaba: debe parecerse a las otras repeticiones
- Resultado: **OK** en 8.96 s

**Pasta con salsa rústica de jitomate y ajo** (25 min)

Ingredientes:
- pasta: 400 g
- jitomate: 500 g
- dientes de ajo: 4 pieza
- aceite: 30 ml
- agua: 3000 ml
- sal: al gusto
- pimienta: al gusto

Pasos:
1. Picar finamente los dientes de ajo y cortar los jitomates en cubos pequeños.
2. Poner a calentar los 3000 ml de agua en una olla grande con una pizca de sal hasta que hierva.
3. Agregar la pasta al agua hirviendo y cocinar según las instrucciones del empaque hasta que quede al dente (aproximadamente 8-10 minutos).
4. Mientras la pasta se cocina, calentar el aceite en una sartén amplia a fuego medio-bajo y dorar ligeramente el ajo picado sin dejar que se queme.
5. Añadir los jitomates picados a la sartén, sazonar con sal y pimienta al gusto, y cocinar a fuego medio durante 10-12 minutos hasta que los jitomates se hayan deshecho y formado una salsa rústica.
6. Escurrir la pasta reservando un par de cucharadas del agua de cocción.
7. Incorporar la pasta y las cucharadas de agua reservada directamente en la sartén con la salsa, mezclando todo a fuego bajo durante 1 o 2 minutos para que los sabores se integren.
8. Servir caliente de inmediato.

Nota del modelo: Se aprovecharon todos los ingredientes base con los básicos indispensables de despensa (aceite, agua, sal y pimienta) para lograr una salsa clásica y reconfortante.
