import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import math
from scipy.optimize import curve_fit
from scipy.special import erf
import re
from scipy.stats import norm
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path

filepath = '/home/raspi/Desktop/power_sweep_data.csv'

re_basename = os.path.splitext(os.path.basename(filepath))[0]
basename_pre = re_basename.replace(' ', '')
basename = basename_pre.replace('power_sweep_data_', '')

df = pd.read_csv(filepath, names = ['position', 'power1_dBm', 'power2_dBm'], skiprows = 1)

posi = np.array(df['position'])*0.02
power1 = 10**(df['power1_dbm']/10)
power2 = 10**(df['power2_dbm']/10)

def quadratic_func(x, a, b, c, d):
    return -((np.pi)*(a**2)/4)*((1+(erf(((np.sqrt(2))*(x-b))/a)))*c)+d

def analyze_beam(posi, power, label):
    initial_params = [40, 60, 0.01, 0.01]
    try:
        popt, pcov = curve_fit(quadratic_func, posi, power, p0 = initial_params)
        error = np.sqrt(np.diag(pcov))
        return popt, error
    except Exception as e:
        print(f"Fitting failed for {label}: {e}")
        return None, None

results = {}
for power, name in zip([power1, power2], ['Sensor1', 'Sensor2']):
    popt, err = analyze_beam(posi, power, name)
    results[name] = {'popt': popt, 'err': err, 'y': power}

plt.figure(figsize = (10, 6))
colors = ['blue', 'green']

for i, (name, res) in enumerate(results.items()):
    if res['popt'] is None: continue
    p = res['popt']
    e = res['err']
    beam_size = abs(p[0]*2)
    center = p[1]

    print(f"Beam Size (2a): {beam_size:.4f} mm (±{e[0]*2:.4f})")
    print(f"Beam Center (b): {center:.4f} mm (±{e[1]:.4f})")
    
    x_fit = np.linspace(posi.min(), posi.max(), 500)
    y_fit = quadratic_func(x_fit, *p)
    
    plt.scatter(posi, res['y'], color = colors[i], alpha = 0.5, label = f'{name} Data')
    plt.plot(x_fit, y_fit, color = colors[i], lw = 2, label = f'{name} Fit (2a = {beam_size:.2f} mm)')

plt.title(basename + '_fitting', fontsize = 10)
plt.xlabel('position[mm]', fontsize = 10)
plt.ylabel('Amplitude[mW]', fontsize = 10)
plt.legend(fontsize = 10)
plt.grid(True, linestyle = '--', alpha = 0.6)

save_name = os.path.join('/home/raspi/Desktop', f'{basename}_knife_edge_fitting.pdf')
plt.savefig(save_name)
print(f"\nAnalysis plot saved as: {save_name}")
plt.show()