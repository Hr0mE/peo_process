from os import listdir as ld
from os import getcwd as getcwd
from os import rename as re_name
from os import mkdir as mkdir
from numpy import arange
from math import sqrt
import matplotlib.pyplot as plt
import numpy as np

#Главная функция
def main():
    result_name = 'Results_of_analysis'
    
    if result_name not in ld('.'):
        mkdir(result_name)
    else:
        print(f'!!! Папка {result_name} уже существовала ранее.\nРезультаты будут пересчитаны !!!\n')

    box_plot_data = []
    box_plot_data_legends = []
    
    plot_data = []
    plot_data_legends = []

    max_time = []
    max_voltage = []

    samples = read_folders(ld('.'), result_name)
   
    for  ndex, _ in enumerate(samples):
        folder, size = _[0], _[1]
        path = f'./{folder}'
        print(f'Opening folder {folder}')
        retyping(path)
        
        data = fitting_data(reading(path))
        medium_voltage, medium_current = medium(data)
        current_density = np.array(medium_current)/size
        time = data[0][0]
        deviation_voltage,deviation_current = deviation(data, medium_voltage, medium_current)
        deviation_current = np.array(deviation_current)/size
        dataset = (time, medium_voltage, medium_current, deviation_voltage, deviation_current, current_density)
        legends = ['time', 'medium_voltage', 'medium_current', 'deviation_voltage', 'deviation_current', 'current_density']
        save_data(dataset, legends, result_name, folder)
        
        for i in [time, current_density, time, deviation_current]:
            plot_data.append(i)
        #plot_data_legends.append(f'Образец {size}mm², Плотность тока (mA/mm²)')
        #plot_data_legends.append(f'Образец {size}mm², отклонение плотности тока')
        plot_data_legends.append(f'№{ndex+1}, Плотность тока (mA/mm²)')
        plot_data_legends.append(f'№{ndex+1}, отклонение плотности тока')

        # TODO. Где-то в друго месте разделять анодную и катодную части процесса
        box_plot_data.append(current_density)
        box_plot_data_legends.append(f'{ndex+1}')

        if len(medium_voltage) > len(max_voltage):
            max_voltage = medium_voltage.copy()
        if len(time) > len(max_time):
            max_time = time.copy()
            
        print('\n')

    #Рисуем первый график зависимости напруги от времени
    plot_data.append(max_time)
    plot_data.append(max_voltage)

    box_plot(result_name, box_plot_data, box_plot_data_legends)
    plotting(result_name, plot_data, plot_data_legends)

#Считывание только папок, высчитывание площади образца
def read_folders(path, result_name):
    folder_paths = []
    for ndex, folder in enumerate(path):
        if folder.split('.')[-1] != 'py' and folder != result_name and folder.split('.')[-1] != 'txt' :
            folder_paths.append(folder)

    _ = [(elem, int(elem.split('x')[0]) * int(elem.split('x')[1])) for elem in folder_paths]
    folder_paths = sorted(_, key=lambda x: x[1])
    return folder_paths

def save_data(dataset, legends, result_name, folder):
    print(f'Saving results of {folder}...', end='\t')
    with open(f'./{result_name}/{folder}.txt', 'w') as new_file:
        title = ' '.join(legends)
        new_file.write(title + '\n')

        for string in range(len(dataset[0])):
            result_string = ''
            for data in dataset:
                result_string += str(round(data[string], 2)) + ' '
            new_file.write(result_string + '\n')
    print('Done!')

#Построение ящика с усами
def box_plot(result_name, dataset, legends):
    """
    Функция рисует ящики с усами. В биполярном режиме важно разделять катодную и анодную части процесса
    Потому что в ином случае всё ломается(
    """

    #Дублируем массив легенд, но уже с разбиением на анодную и катодную части.
    bipolar_legends = [legends[int(i)] + ' an' if (i%1)==0 else legends[int(i)] + ' cat' for i in arange(0, len(legends), 0.5)]
    #Разбиваем поступивший массив на катодные и анодные части. Разбиение идёт по середине массива при помощи round(len(dataset[int(i)])/2)
    #При помощи arange(0, len(dataset), 0.5) мы можем один и тот же исходный массив два раза взять.
    data = [dataset[int(i)][:round(len(dataset[int(i)])/2)] if not (i%1) else dataset[int(i)][round(len(dataset[int(i)])/2):] for i in arange(0, len(dataset), 0.5)]

    fs = 18
    fn = 'Arial'
    fig, ax = plt.subplots(figsize=(16, 9))
    ax.boxplot(data, showfliers=False, labels=bipolar_legends)
    ax.grid(c='k', lw='0.3', axis='y', ls='--')
    ax.set_ylabel(f'Плотность тока(mA/mm²)', fontsize=fs)#, fontname=fn)
    ax.set_xlabel(f'Число образцов площадью 300mm² (шт.)', fontsize=fs)#, fontname=fn)
    ax.tick_params(axis='both', which='major', labelsize=fs)#, fontname=fn)
    plt.yticks(arange(-5, 21, 1.0))
    plt.xticks(rotation=0)
    plt.savefig(f'./{result_name}/box_plot.png')
    fig.show()



#Построение графика
def plotting(result_name, dataset, legends):
    fs = 18
    fig, axes = plt.subplots(1, 1, figsize=(16, 8))
    dataset = dataset[:-2]
    axes.plot(*dataset)
    axes.set_xlabel(f'Время(с)', fontsize=fs)
    axes.set_ylabel(f'Плотность тока(mA/mm²) для 300mm²', fontsize=fs)
    axes.grid(c='k', lw='0.3', ls='--')
    axes.tick_params(axis='both', which='major', labelsize=fs)
    axes.legend(legends, fontsize=fs)
    
    plt.savefig(f'./{result_name}/plot.png')
    fig.show()

#Переформатирование из .dat в .txt
def retyping(path):
    old_type = 'dat'#без точки, потому что мы по этой точке делаем split
    new_type = 'txt'
    print(f'Retyping from .{old_type} to .{new_type}...', end='\t')
    for filename in ld(path):
        new_fname = ''
        if filename.split('.')[-1] == old_type:
            for i in filename.split('.')[:-1]:
                new_fname += i + '.'
            new_fname += new_type
            new_fname = f'{path}/{new_fname.replace(" ","")}'
            old_name = f'{path}/{filename}'
            re_name(old_name, new_fname)
    print('Done!')

#Для корректного суммирования чисел с двумя знаками после запятой
def summing_floats(result, value):
    return (int(float(result)*100)+int(float(value)*100))/100
    
#Возвращает индекс минимальной длины массива времени
def min_time_len(data): 
    minlen = len(data[0][0])
    index = 0
    for i in range(len(data)):
        if len(data[i][0]) < minlen:
            index = i
            minlen = len(data[i][0])
    return index

#Срезаем лишние длины массива, подгоняя под минимальный размер
def fitting_data(data):
    print('fitting data...', end='\t')
    min_time = data[min_time_len(data)]
    c = 0
    for file in data:
        c += 1
        n = 0
        while len(file[0]) > len(min_time[0]):
            try:
                if file[0][n] != min_time[0][n]:
                    file[0].pop(n)
                    file[1].pop(n)
                    file[2].pop(n)
                else:
                    n += 1
            except IndexError:
                print(f' INDEXERROR! len of current file = {len(file[0])}')
                print('BREAKED the loop')
                break
    print('Done!')
    return data



#Сюда считываем вообще все данные обо всех экспериментах в папке
def reading(path_1):
    path = ld(path_1) #path_1 чисто как адрес, а path - список файлов
    data = []
    postfix = 'txt'
    print(f'Start reading .{postfix.upper()} files from {path_1}...')
    filelist = np.array([i for i in path if i.split(".")[-1] == postfix])
    for file in filelist:
        print(file)
        #Каждый раз создаём новые массивы под данные,
        #которые в конце объединим в кортеж и засунем в data
        time, current, voltage = [], [], []
        with open(f'{path_1}/{file}', 'r') as opening:
            f = np.array([i.replace(",", '.') for i in opening])
            max_time = 0
            for ind, string in enumerate(f):
                cur_str = string.split() #Делим строку на отдельные данные
                try:
                    if cur_str[0] == 'A:':
                        time.append(round(float(cur_str[1]), 2))
                        if float(f[ind+1].split()[1]) < float(f[ind].split()[1]):
                            max_time = f[ind].split()[1]
                    else:
                        time.append(summing_floats(cur_str[1], max_time))# Sec
                            
                    voltage.append(round(float(cur_str[2]), 2))# Voltage
                    current.append(round(float(cur_str[3])*1000))#Переводим в mA

                except IndexError as e:
                        print('INDEXERROR! Continue execution')
                        continue
            
            data.append( (time, voltage, current) )
    print('Done!')
    return data
    

#Находим среднее значение
def medium(data):
    print('Calculating medium...', end='\t')
    sum_voltage = data[0][1].copy()
    sum_current = data[0][2].copy()
    len_data = len(data)
    for i in range(1, len_data):
        for j in range(len(data[i][0])):
            sum_voltage[j] += data[i][1][j]
            sum_current[j] += data[i][2][j]
    result_voltage = list(map(lambda x: round(x/len_data, 1), sum_voltage))
    result_current = list(map(lambda x: round(x/len_data, 1), sum_current))
    print('Done!')
    return result_voltage, result_current


#Считаем отклонение от среднего// В конце к положительному и отрицательному отклонению запихиваем ещё и средние значения
def deviation(data, medium_voltage, medium_current):
    print('Calculating deviation...', end='\t')
    deviation_voltage = [0 for i in range(len(data[0][0]))]
    deviation_current = [0 for i in range(len(data[0][0]))]
    for i in range(len(data)):
        for j in range(len(data[i][0])):
            deviation_voltage[j] += round((data[i][1][j]-medium_voltage[j])**2, 2)
            deviation_current[j] += round((data[i][2][j]-medium_current[j])**2, 2)
    temp_dev_voltage = list(map(lambda x: sqrt(x/len(data)), deviation_voltage)) #Поделили на количество членов, взяли корень
    temp_dev_current = list(map(lambda x: sqrt(x/len(data)),deviation_current))
    result_dev_voltage = [round(medium_voltage[i]+temp_dev_voltage[i], 1) for i in range(len(medium_voltage))]
    result_dev_current = [round(medium_current[i]+temp_dev_current[i], 1) for i in range(len(medium_current))]
    print('Done!')
    #temp_dev_current выводится отклонение вдоль нуля
    #result_dev_current выводится отклонение вдоль графика
    return temp_dev_voltage, temp_dev_current 

if __name__ == '__main__':
    main()
