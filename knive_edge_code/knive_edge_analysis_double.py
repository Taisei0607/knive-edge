import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import math
import time
from scipy.optimize import curve_fit
from scipy.special import erf
import re
from scipy.stats import norm
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
import sys

# filepath = '/home/raspi/Desktop'
filepath = sys.argv[1]

re_basename = os.path.splitext(os.path.basename(filepath))[0]
basename_pre = re_basename.replace(' ', '')
basename = basename_pre.replace('power_sweep_data_', '')

df = pd.read_csv(filepath, names = ['position', 'power1', 'power2'], skiprows = 1)

posi = np.array(df['position'])*0.02
power1 = 10**(df['power1']/10)
power2 = 10**(df['power2']/10)

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

fig, ax = plt.subplots(1, 2, figsize = (16, 8))
# plt.figure(figsize = (10, 6))
# colors = ['blue', 'green']

for i, (name, res) in enumerate(results.items()):
    if res['popt'] is None: continue
    p = res['popt']
    e = res['err']
    beam_size = abs(p[0]*2)
    beam_size_err = e[0]*2
    center = p[1]
    center_err = e[1]

    print(f"Beam Size (2a): {beam_size:.4f} (± {e[0]*2:.4f}) mm")
    print(f"Beam Center (b): {center:.4f} (± {e[1]:.4f}) mm")
    
    x_fit = np.linspace(posi.min(), posi.max(), 500)
    y_fit = quadratic_func(x_fit, *p)
    
    ax[i].scatter(posi, res['y'], alpha = 0.5, label = f'{name} Data')
    ax[i].plot(x_fit, y_fit, lw = 2, label = f'{name} Fit\n(2a = {beam_size:.2f} (± {e[0]*2:.4f}) mm\n(b = {center:.2f} (± {e[1]:.4f}) mm')
#   plt.scatter(posi, res['y'], color = colors[i], alpha = 0.5, label = f'{name} Data')
#   plt.plot(x_fit, y_fit, color = colors[i], lw = 2, label = f'{name} Fit (b = {center:.2f} mm)')

ax[0].set_title(basename + '_fitting', fontsize = 10)
ax[0].set_xlabel('position[mm]', fontsize = 10)
ax[0].set_ylabel('Amplitude[mW]', fontsize = 10)
ax[0].legend(fontsize = 10)
ax[0].grid(True, linestyle = '--', alpha = 0.6)
ax[1].set_title(basename + '_fitting', fontsize = 10)
ax[1].set_xlabel('position[mm]', fontsize = 10)
ax[1].set_ylabel('Amplitude[mW]', fontsize = 10)
ax[1].legend(fontsize = 10)
ax[1].grid(True, linestyle = '--', alpha = 0.6)

# plt.title(basename + '_fitting', fontsize = 10)
# plt.xlabel('position[mm]', fontsize = 10)
# plt.ylabel('Amplitude[mW]', fontsize = 10)
# plt.legend(fontsize = 10)
# plt.grid(True, linestyle = '--', alpha = 0.6)
timestamp_day = time.strftime('%Y%m%d')
save_name = os.path.join(f'/home/raspi/Desktop/{timestamp_day}', f'{basename}_knife_edge_fitting.png')
plt.savefig(save_name)
print(f"\nAnalysis plot saved as: {save_name}")
plt.show()
