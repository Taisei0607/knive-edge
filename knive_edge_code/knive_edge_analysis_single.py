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

filepath = '/home/raspi/Desktop'

re_basename = os.path.splitext(os.path.basename(filepath))[0]
basename_pre = re_basename.replace(' ', '')
basename = basename_pre.replace('power_sweep_data_', '')

df = pd.read_csv(filepath, names = ['position', 'power'], skiprows = 1)
# print(pd.concat([df], axis = 1))

position = np.array(df['position'])
posi = position*0.02
power_dBm = np.array(df['power'])
power = 10**(power_dBm/10)
pi = np.pi
sampling_points = 1000

def quadratic_func(x, a, b, c, d):
    return -(pi*(a**2)/4)*((1+(erf(((np.sqrt(2))*(x-b))/a)))*c)+d

# initial_params = [40, 60, 0.01, 0.01]
# popt, pcov = curve_fit(quadratic_func, posi, power, p0 = initial_params)
# error = np.sqrt(np.diag(pcov))
# print(f"フィッティングによって得られたパラメータfitting parameters (a, b, c): {popt}")
# print(f"a = {popt[0]:.3f}, b = {popt[1]:.3f}, c = {popt[2]:.3f}")
# print('error =', np.sqrt(np.diag(pcov)))

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
popt, err = analyze_beam(posi, power, basename)
results[basename] = {'popt': popt, 'err': err, 'y': power}
res_data = results[basename]

if res_data['popt'] is not None:
    p = res_data['popt']
    e = res_data['err']
    beam_size = abs(p[0]*2)
    center = p[1]

    print(f"Beam Size (2a): {beam_size:.4f} mm (±{e[0]*2:.4f})")
    print(f"Beam Center (b): {center:.4f} mm (±{e[1]:.4f})")
    
    x_fit = np.linspace(posi.min(), posi.max(), 500)
    y_fit = quadratic_func(x_fit, *p)

# x_fit = np.linspace(posi.min(), posi.max(), sampling_points)
# y_fit = quadratic_func(x_fit, *popt)

fig, ax = plt.subplots()
ax.scatter(posi, power, label = 'measurement', color = 'blue')
ax.plot(x_fit, y_fit, label = 'fitting_function', color = 'red', linewidth = 2)
ax.set_title(basename + '_fitting', fontsize = 10)
ax.set_xlabel('position[mm]', fontsize = 10)
ax.set_ylabel('Amplitude[mW]', fontsize = 10)
ax.legend(fontsize = 10)
ax.grid(True, linestyle = '--', alpha = 0.6)

# formula_latex = r"$y(x) = -\left(\frac{\pi a^2}{4}\right)\left(1+\text{erf}\left(\frac{\sqrt{2}(x-b)}{2 a}\right)\right)c+d$"

# param_text = (
#    f"2a = {popt[0]:.4f}  (error = {np.sqrt(np.diag(pcov))[0]:.3})\n"
#    f"b = {popt[1]:.4f}  (error = {np.sqrt(np.diag(pcov))[1]:.3})\n"
#    f"c = {popt[2]:.4f}  (error = {np.sqrt(np.diag(pcov))[2]:.3})\n"
#    f"d = {popt[3]:.4f}  (error = {np.sqrt(np.diag(pcov))[3]:.3})"
#    )

# text_box = f"Function:\n{formula_latex}\n\nParameters:\n{param_text}"

# plt.text(0.55, 0.5, text_box, transform = ax[0].transAxes, fontsize = 10, verticalalignment = 'top', bbox = dict(boxstyle = 'square,pad = 1', facecolor = 'white', alpha = 0.8))
# plt.text(0.55, 0.5, text_box, transform = ax[1].transAxes, fontsize = 10, verticalalignment = 'top', bbox = dict(boxstyle = 'square,pad = 1', facecolor = 'white', alpha = 0.8))
# plt.xlim([0.00, 120.00])

save_name = os.path.join('/home/raspi/Desktop', f'{basename}_knife_edge_fitting.png')
plt.savefig(save_name)
# plt.savefig(f'{basename}_knife_edge_fitting.png', bbox_inches = 'tight', format = 'png', dpi = 100)

plt.show()
