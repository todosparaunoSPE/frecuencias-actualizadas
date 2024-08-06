# -*- coding: utf-8 -*-
"""
Created on Tue Aug  6 08:32:41 2024

@author: jperezr
"""

import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import skew, kurtosis
import openpyxl

# Encabezado
st.header("Generador de Archivo Excel con Transformaciones de Datos")

# Sección de Ayuda
st.sidebar.header("Ayuda")
st.sidebar.markdown("""
## Ayuda: Generador de Archivo Excel con Transformaciones de Datos

### Descripción
Esta aplicación de Streamlit permite generar un archivo Excel que contiene datos originales y transformados basados en una serie de intervalos de tiempo y frecuencias asociadas. El usuario puede aplicar diferentes transformaciones matemáticas a los intervalos de tiempo y ajustar las frecuencias correspondientes.

### Funcionalidades

1. **Datos Iniciales**
   - Se proporciona un conjunto de intervalos de tiempo y frecuencias asociadas. Estos datos se muestran en la sección de Datos Originales.

2. **Transformaciones Disponibles**
   - El usuario puede seleccionar una transformación matemática para los intervalos de tiempo usando un menú desplegable:
     - **Original**: Mantiene los intervalos y frecuencias originales.
     - **y = x^2**: Transforma los intervalos aplicando la función cuadrática.
     - **y = sqrt(x)**: Transforma los intervalos aplicando la función raíz cuadrada.
     - **y = ln(x)**: Transforma los intervalos aplicando el logaritmo natural (solo para valores positivos).
     - **y = 1/x**: Transforma los intervalos aplicando la función inversa.

3. **Transformación de Datos**
   - La aplicación calcula nuevos intervalos y ajusta las frecuencias de acuerdo con la transformación seleccionada. Los intervalos transformados se redistribuyen para que la suma total de frecuencias se mantenga lo más cercana posible a la suma original.

4. **Visualización de Datos**
   - Se muestran dos tablas:
     - **Datos Originales**: Intervalos y frecuencias antes de la transformación.
     - **Datos Transformados**: Intervalos y frecuencias después de aplicar la transformación seleccionada.

5. **Generación de Archivo Excel**
   - Al hacer clic en el botón "Generar Archivo Excel", se crea un archivo Excel (`transformaciones.xlsx`) que contiene dos hojas:
     - **Original**: Datos originales.
     - **[Nombre de la Transformación]**: Datos transformados según la selección del usuario.
   - Se proporciona un enlace para descargar el archivo generado.

### Cómo Usar
1. **Selecciona una transformación** del menú desplegable.
2. **Revisa los datos originales y transformados** que se muestran en la página.
3. **Haz clic en "Generar Archivo Excel"** para crear y descargar el archivo con los datos originales y transformados.

Si necesitas ayuda adicional o tienes preguntas, no dudes en contactar al desarrollador.
""")

# Datos
intervalos = ['[0, 1)', '[1, 2)', '[2, 3)', '[3, 4)', '[4, 5)', '[5, 6)', '[6, 7)', '[7, 8)', '[8, 9)']
frecuencia = [45, 28, 13, 8, 3, 1, 1, 0, 1]

# Crear un DataFrame
data = {'Intervalo': intervalos, 'Frecuencia': frecuencia}
df = pd.DataFrame(data)

# Función para transformar los intervalos y ajustar las frecuencias
def transformar_intervalos_y_frecuencias(df, transformacion):
    nuevos_intervalos = []
    
    def interseccion_longitud(inf1, sup1, inf2, sup2):
        """ Calcula la longitud de la intersección entre dos intervalos. """
        inf_max = max(inf1, inf2)
        sup_min = min(sup1, sup2)
        return max(0, sup_min - inf_max)

    def transformar_intervalo(inf, sup, transformacion):
        if transformacion == 'y = x^2':
            return inf ** 2, sup ** 2
        elif transformacion == 'y = sqrt(x)':
            return np.sqrt(inf), np.sqrt(sup)
        elif transformacion == 'y = ln(x)':
            return (np.log(inf) if inf > 0 else float('-inf'), 
                    np.log(sup) if sup > 0 else float('-inf'))
        elif transformacion == 'y = 1/x':
            return (1 / sup if sup != 0 else float('inf'), 
                    1 / inf if inf != 0 else float('inf'))
        return inf, sup

    if transformacion == 'Original':
        df_transformado = df.copy()
        df_transformado['Nuevo intervalo'] = df['Intervalo']
        df_transformado['Nueva frecuencia'] = df['Frecuencia']
        return df_transformado, 'Nuevo intervalo', 'Nueva frecuencia'

    for i, intervalo in enumerate(df['Intervalo']):
        inf, sup = map(float, intervalo[1:-1].split(', '))
        nuevo_inf, nuevo_sup = transformar_intervalo(inf, sup, transformacion)
        if np.isinf(nuevo_inf) or np.isinf(nuevo_sup):
            nuevo_intervalo = f'{nuevo_inf}-{nuevo_sup}'
        else:
            nuevo_intervalo = f'{nuevo_inf:.2f}-{nuevo_sup:.2f}'
        nuevos_intervalos.append(nuevo_intervalo)

    # Crear un DataFrame para el nuevo intervalo transformado
    df_transformado = pd.DataFrame({'Nuevo intervalo': nuevos_intervalos})
    
    # Redistribuir las frecuencias
    intervalos_transformados = []
    for x in nuevos_intervalos:
        try:
            intervalos_transformados.append(tuple(map(float, x.split('-'))))
        except ValueError:
            # Manejar casos en que los intervalos no son convertibles a float
            intervalos_transformados.append((float('nan'), float('nan')))

    intervalos_originales = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (8, 9)]

    frecuencias_transformadas = []
    
    for int_trans in intervalos_transformados:
        if np.isnan(int_trans[0]) or np.isnan(int_trans[1]) or np.isinf(int_trans[0]) or np.isinf(int_trans[1]):
            frecuencias_transformadas.append(0)
            continue
        
        freq_sum = 0
        for i, int_orig in enumerate(intervalos_originales):
            inf_orig, sup_orig = int_orig
            inf_trans, sup_trans = int_trans
            interseccion_len = interseccion_longitud(inf_orig, sup_orig, inf_trans, sup_trans)
            intervalo_len = sup_orig - inf_orig
            if intervalo_len > 0:
                freq_sum += df['Frecuencia'][i] * (interseccion_len / intervalo_len)
        frecuencias_transformadas.append(freq_sum)

    # Ajustar la suma de frecuencias transformadas para que sea igual a la suma de las frecuencias originales
    suma_frecuencias_originales = df['Frecuencia'].sum()
    suma_frecuencias_transformadas = sum(frecuencias_transformadas)
    if suma_frecuencias_transformadas != 0:
        frecuencias_transformadas = [f * suma_frecuencias_originales / suma_frecuencias_transformadas for f in frecuencias_transformadas]

    # Redondear las frecuencias a enteros
    frecuencias_transformadas = [round(f) for f in frecuencias_transformadas]

    # Asegurar que la suma de frecuencias transformadas sea 100
    suma_frecuencias_transformadas = sum(frecuencias_transformadas)
    if suma_frecuencias_transformadas != 0:
        frecuencias_transformadas = [int(round(f * 100 / suma_frecuencias_transformadas)) for f in frecuencias_transformadas]

    df_transformado['Nueva frecuencia'] = frecuencias_transformadas
    return df_transformado, 'Nuevo intervalo', 'Nueva frecuencia'

# Crear un combobox para que el usuario seleccione la transformación
transformacion = st.selectbox('Selecciona una transformación', ['Original', 'y = x^2', 'y = sqrt(x)', 'y = ln(x)', 'y = 1/x'])

# Aplicar la transformación seleccionada y mostrar los resultados
df_transformado, intervalo_col, frecuencia_col = transformar_intervalos_y_frecuencias(df, transformacion)

st.write('Datos Originales de la Frecuencia de Piezas por Intervalo de Tiempo')
st.dataframe(df)

st.write('Datos Transformados')
st.dataframe(df_transformado)

# Crear el archivo Excel
if st.button('Generar Archivo Excel'):
    with pd.ExcelWriter('transformaciones.xlsx', engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Original', index=False)
        # Reemplazar caracteres no permitidos en el nombre de la hoja
        sheet_name = transformacion.replace('/', '_').replace(' ', '_')
        df_transformado.to_excel(writer, sheet_name=sheet_name, index=False)
    
    st.success('Archivo Excel generado exitosamente. Descargue el archivo desde el siguiente enlace:')
    with open('transformaciones.xlsx', 'rb') as f:
        st.download_button(label='Descargar transformaciones.xlsx', data=f, file_name='transformaciones.xlsx')


st.sidebar.write("© 2024 Creado por: Javier Horacio Pérez Ricárdez")
