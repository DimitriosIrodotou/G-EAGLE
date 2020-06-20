import re
import time
import warnings
import matplotlib
import plot_tools

matplotlib.use('Agg')

import numpy as np
import matplotlib.cbook
import matplotlib.pyplot as plt

from matplotlib import gridspec

date = time.strftime('%d_%m_%y_%H%M')  # Date.
start_global_time = time.time()  # Start the global time.
warnings.filterwarnings("ignore", category=matplotlib.cbook.mplDeprecation)  # Ignore some plt warnings.


class AngularMomentumVsMass:
    """
    For all galaxies create: angular momentum versus stellar mass colour-coded by disc to total ratio.
    """
    
    
    def __init__(self, simulation_path, tag):
        """
        A constructor method for the class.
        :param simulation_path: simulation directory.
        :param tag: redshift directory.
        """
        start_local_time = time.time()  # Start the local time.
        
        stellar_masses = np.load(data_path + 'glx_stellar_masses.npy')
        disc_fractions_IT20 = np.load(data_path + 'glx_disc_fractions_IT20.npy')
        stellar_angular_momenta = np.load(data_path + 'glx_stellar_angular_momenta.npy')
        print('Loaded data for ' + re.split('Planck1/|/PE', simulation_path)[1] + ' in %.4s s' % (time.time() - start_local_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
        
        # Plot the data #
        start_local_time = time.time()  # Start the local time.
        
        self.plot(stellar_masses, disc_fractions_IT20, stellar_angular_momenta)
        print('Plotted data for ' + re.split('Planck1/|/PE', simulation_path)[1] + ' in %.4s s' % (time.time() - start_local_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
        
        print('Finished AM_M for ' + re.split('Planck1/|/PE', simulation_path)[1] + '_' + str(tag) + ' in %.4s s' % (time.time() - start_global_time))
        print('–––––––––––––––––––––––––––––––––––––––––––––')
    
    
    def plot(self, stellar_masses, disc_fractions_IT20, stellar_angular_momenta):
        """
        Plot star formation rate versus stellar mass colour-coded by disc to total ratio
        :param stellar_masses: defined as the mass of all stellar particles within 30kpc from the most bound particle.
        :param disc_fractions_IT20: where the disc consists of particles whose angular momentum angular separation is 30deg from the densest pixel.
        :param stellar_angular_momenta: defined as the sum of each stellar particle's angular momentum.
        :return: None
        """
        # Generate the figure and define its parameters #
        plt.close()
        figure = plt.figure(figsize=(10, 7.5))
        gs = gridspec.GridSpec(2, 1, wspace=0.0, hspace=0.0, height_ratios=[0.05, 1])
        axis00 = figure.add_subplot(gs[0, 0])
        axis10 = figure.add_subplot(gs[1, 0])
        
        axis10.grid(True, which='both', axis='both')
        axis10.set_xscale('log')
        axis10.set_yscale('log')
        axis10.set_ylim(1e0, 1e5)
        axis10.set_xlim(1e9, 1e12)
        axis10.set_xlabel(r'$\mathrm{log_{10}(M_{\bigstar}/M_{\odot})}$', size=16)
        axis10.set_ylabel(r'$\mathrm{(|\vec{J}_{\bigstar}|/M_{\bigstar})/(kpc\;km\;s^{-1})}$', size=16)
        axis10.tick_params(direction='out', which='both', top='on', right='on',  labelsize=16)
        
        bulge_fractions_IT20 = 1 - disc_fractions_IT20
        spc_stellar_angular_momenta = np.linalg.norm(stellar_angular_momenta, axis=1) / stellar_masses
        sc = axis10.scatter(stellar_masses, spc_stellar_angular_momenta, c=bulge_fractions_IT20, s=8, cmap='RdYlBu_r', marker='h')
        plot_tools.create_colorbar(axis00, sc, r'$\mathrm{B/T_{30\degree}}$', 'horizontal')
        
        # Read observational data from FR18 #
        FR18 = np.genfromtxt('./Obs_Data/FR18.csv', delimiter=',', names=['Mstar', 'jstar'])
        
        # Plot observational data from FR18 #
        plt.plot(np.power(10, FR18['Mstar'][0:2]), np.power(10, FR18['jstar'][0:2]), color='blue', lw=3, linestyle='dashed',
                 label=r'$\mathrm{Fall\; &\; Romanowsky\, 18:Discs}$', zorder=4)
        plt.plot(np.power(10, FR18['Mstar'][2:4]), np.power(10, FR18['jstar'][2:4]), color='red', lw=3, linestyle='dashed',
                 label=r'$\mathrm{Fall\; &\; Romanowsky\, 18:Bulges}$', zorder=4)
        
        # Save the figure #
        plt.savefig(plots_path + 'AM_M' + '-' + date + '.png', bbox_inches='tight')
        return None


if __name__ == '__main__':
    tag = '027_z000p101'
    simulation_path = '/cosma7/data/Eagle/ScienceRuns/Planck1/L0100N1504/PE/REFERENCE/data/'  # Path to EAGLE data.
    plots_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/plots/'  # Path to save plots.
    data_path = '/cosma7/data/dp004/dc-irod1/EAGLE/python/data/'  # Path to save/load data.
    x = AngularMomentumVsMass(simulation_path, tag)
